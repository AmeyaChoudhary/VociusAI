#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Vocius Local Backend", version="1.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- helpers -----------------------------------------------------------
def make_run_dir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))

def write_upload(upload: UploadFile, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    upload.file.seek(0)

def run(cmd: list[str], env: Optional[Dict[str, str]] = None, cwd: Optional[Path] = None):
    return subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True)

def tail(text: str, n: int = 120) -> str:
    lines = (text or "").splitlines()
    return "\n".join(lines[-n:]) if len(lines) > n else (text or "")

def list_files(p: Path) -> list[str]:
    if not p.exists():
        return []
    out = []
    for c in p.rglob("*"):
        if c.is_file():
            try:
                out.append(str(c.relative_to(p)))
            except Exception:
                out.append(str(c))
    return sorted(out)

def coerce_flow_notes(raw: Any) -> List[Dict[str, str]]:
    """Normalize several possible shapes into [{speech,time,notes}]."""
    out: List[Dict[str, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                speech = str(item.get("speech") or item.get("label") or "")
                time_  = str(item.get("time") or item.get("timestamp") or "")
                notes  = str(item.get("notes") or item.get("text") or "")
                if notes or speech or time_:
                    out.append({"speech": speech, "time": time_, "notes": notes})
            elif isinstance(item, str):
                out.append({"speech": "", "time": "", "notes": item})
    return out

def extract_feedback(work_dir: Path) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Read out/judge_feedback.json or out/judging_feedback.txt and turn them into:
      - judgeAnalysis { overallScore?, rfd, flowNotes[] }
      - deliveryMetrics { overallScore? }
      - rawExtras (debug fields we also append)
    All keys are optional; caller decides how to render.
    """
    jf_json = work_dir / "judge_feedback.json"
    jf_txt  = work_dir / "judging_feedback.txt"

    judgeAnalysis: Optional[Dict[str, Any]] = None
    deliveryMetrics: Optional[Dict[str, Any]] = None
    extras: Dict[str, Any] = {}

    if jf_json.exists():
        try:
            data = json.loads(jf_json.read_text(encoding="utf-8"))
            extras["judge_feedback_json"] = data

            # Try common field names
            rfd = (
                data.get("verbal_rfd")
                or data.get("rfd")
                or data.get("verbalRFD")
                or data.get("verbal")
            )
            flow = data.get("flow_notes") or data.get("flow") or []

            # Optional scores
            judge_score = (
                data.get("argument_score")
                or data.get("judge_score")
                or (data.get("scores", {}).get("argument") if isinstance(data.get("scores"), dict) else None)
            )
            delivery_score = (
                data.get("delivery_score")
                or (data.get("scores", {}).get("delivery") if isinstance(data.get("scores"), dict) else None)
            )

            if rfd or flow:
                judgeAnalysis = {
                    "overallScore": int(judge_score) if isinstance(judge_score, (int, float)) else 85,
                    "rfd": str(rfd or ""),
                    "flowNotes": coerce_flow_notes(flow),
                }

            if delivery_score is not None:
                deliveryMetrics = {
                    "overallScore": int(delivery_score) if isinstance(delivery_score, (int, float)) else 78
                }

        except Exception as e:
            extras["judge_feedback_json_error"] = repr(e)

    # Fallback: plain text file
    if judgeAnalysis is None and jf_txt.exists():
        text = jf_txt.read_text(encoding="utf-8", errors="ignore")
        extras["judging_feedback_text"] = text
        # Heuristic: take the whole file as the RFD; flow notes unknown
        judgeAnalysis = {
            "overallScore": 85,
            "rfd": text,
            "flowNotes": [],
        }
        if deliveryMetrics is None:
            deliveryMetrics = {"overallScore": 78}

    return judgeAnalysis, deliveryMetrics, extras

# ---------- routes ------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True, "status": "up", "time": int(time.time())}

@app.post("/analyze/speech")
async def analyze_speech(
    request: Request,
    file: UploadFile = File(...),
    aai_key: Optional[str] = Form(None),
    first: Optional[str] = Form(None),
):
    run_dir = make_run_dir("vocius_speech_")
    work_dir = run_dir / "out"
    work_dir.mkdir(parents=True, exist_ok=True)

    audio_name = file.filename or f"audio_{uuid.uuid4().hex}.m4a"
    audio_path = run_dir / audio_name
    write_upload(file, audio_path)

    env = os.environ.copy()
    if aai_key:
        env["ASSEMBLYAI_API_KEY"] = aai_key

    script = "AnalyzeSpeechV2.py" if Path("AnalyzeSpeechV2.py").exists() else "AnalyzeSpeech.py"
    if not Path(script).exists():
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "kind": "speech",
                "message": "No AnalyzeSpeech script found. Returning placeholder.",
                "run_dir": str(run_dir),
                "work_dir": str(work_dir),
                "files": list_files(run_dir),
            },
        )

    cmd = ["python", "-u", script, str(audio_path), "--work-dir", str(work_dir)]
    if aai_key:
        cmd += ["--aai-key", aai_key]
    if first:
        cmd += ["--first", first]

    proc = run(cmd, env=env, cwd=Path("."))
    report = work_dir / "analyze_speech.txt"
    payload: Dict[str, Any] = {
        "ok": proc.returncode == 0,
        "kind": "speech",
        "returncode": proc.returncode,
        "run_dir": str(run_dir),
        "work_dir": str(work_dir),
        "files": list_files(run_dir),
        "stdout_tail": tail(proc.stdout),
        "stderr_tail": tail(proc.stderr),
    }
    if report.exists():
        payload["report_preview"] = tail(report.read_text(encoding="utf-8"), 400)

    # Always 200; UI decides based on ok
    return JSONResponse(status_code=200, content=payload)

@app.post("/analyze/debate")
async def analyze_debate(
    request: Request,
    file: UploadFile = File(...),
    aai_key: Optional[str] = Form(None),
    or_key: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    style: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    first: Optional[str] = Form(None),
):
    # Validate → still return 200, but with ok:false
    missing = []
    if not file: missing.append("file")
    if not aai_key: missing.append("aai_key")
    if not or_key: missing.append("or_key")
    if missing:
        return JSONResponse(status_code=200, content={"ok": False, "kind": "debate", "error": f"Missing: {', '.join(missing)}"})

    topic = topic or "N/A"
    style = style or "tech"
    model = model or "openai/gpt-4o-2024-11-20"
    first = first or "Aff"

    run_dir = make_run_dir("vocius_debate_")
    work_dir = run_dir / "out"
    work_dir.mkdir(parents=True, exist_ok=True)

    audio_path = run_dir / (file.filename or f"audio_{uuid.uuid4().hex}.m4a")
    write_upload(file, audio_path)

    env = os.environ.copy()
    env["ASSEMBLYAI_API_KEY"] = aai_key or ""
    env["OPENROUTER_API_KEY"] = or_key or ""

    script = "AnalyzeDebateV2.py" if Path("AnalyzeDebateV2.py").exists() else "AnalyzeDebate.py"
    if not Path(script).exists():
        payload = {
            "ok": True,
            "kind": "debate",
            "message": "No AnalyzeDebate script found. Returning placeholder.",
            "run_dir": str(run_dir),
            "work_dir": str(work_dir),
            "files": list_files(run_dir),
        }
        return JSONResponse(status_code=200, content=payload)

    cmd = [
        "python", "-u", script,
        "--audio", str(audio_path),
        "--topic", topic,
        "--first", first,
        "--style", style,
        "--model", model,
        "--work-dir", str(work_dir),
    ]

    proc = run(cmd, env=env, cwd=Path("."))
    stdout, stderr = tail(proc.stdout), tail(proc.stderr)

    # Try to merge run.json + judge_feedback
    base: Dict[str, Any] = {"ok": proc.returncode == 0, "kind": "debate"}
    run_json = work_dir / "run.json"
    if run_json.exists():
        try:
            base.update(json.loads(run_json.read_text(encoding="utf-8")))
        except Exception as e:
            base["run_json_error"] = repr(e)

    judgeA, deliveryM, extras = extract_feedback(work_dir)
    if judgeA:
        base["judgeAnalysis"] = judgeA
    if deliveryM:
        base["deliveryMetrics"] = deliveryM
    base.update({
        "run_dir": str(run_dir),
        "work_dir": str(work_dir),
        "files": list_files(run_dir),
        "stdout_tail": stdout,
        "stderr_tail": stderr,
        **extras,
    })

    # Always 200
    return JSONResponse(status_code=200, content=base)
