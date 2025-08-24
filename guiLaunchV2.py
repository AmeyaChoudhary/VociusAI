#!/usr/bin/env python3
"""
GUI for AI Debate Analysis Tool (OpenRouter + AssemblyAI, dark UI)
- Step 1: Setup — verify AssemblyAI + OpenRouter (+ ffmpeg check)
- Step 2: Run — Debate (2-step with price confirm) and Speech analysis
- Live logs, progress bars, per-run folders, downloads, ZIP
- Curated model dropdown (no cost talk in descriptions)
"""

import os
import sys
import re
import json
import shutil
import tempfile
import subprocess
import time
import select
from pathlib import Path
from datetime import datetime
from typing import Optional

import requests
import streamlit as st

PROJ_ROOT = Path(__file__).resolve().parent
RUNS_DIR = (PROJ_ROOT / "runs")

# ───────────────────────────── Models (OpenRouter) ─────────────────────────────
OPENROUTER_MODELS = [
    {
        "id": "openai/o3-pro",
        "label": "⭐ GPT o3-Pro",
        "desc": (
            "<strong>Most decisive, highest-level judge.</strong> Ideal for dense, clash-heavy rounds when you want "
            "firm ballots, ruthless weighing, and confident calls. Compared to <em>GPT-4o</em> it digs deeper; "
            "compared to <em>Claude 3.5 Sonnet</em> it’s more forceful/less hedgy; more consistent than "
            "<em>Qwen 2.5 72B</em> on tricky theory and impact calculus."
        ),
        "in": 20.00/1000, "out": 80.00/1000,
    },
    {
        "id": "openai/gpt-4o-2024-11-20",
        "label": "GPT-4o",
        "desc": (
            "<strong>Balanced and reliable.</strong> Great default for most PF rounds with clear weighing and a mix "
            "of policy + philosophy. Compared to <em>o3-Pro</em> it’s calmer and faster; compared to <em>Claude</em> "
            "it’s more concise; more polished than <em>Qwen</em> under pressure."
        ),
        "in": 2.50/1000, "out": 10.00/1000,
    },
    {
        "id": "openai/gpt-5",
        "label": "GPT-5",
        "desc": (
            "<strong>Latest premium option.</strong> Use for layered offense/defense and very long transcripts when "
            "you want thorough, steady reasoning. Compared to <em>o3-Pro</em> it’s calmer; deeper than <em>GPT-4o</em> "
            "on messy flows; stronger than <em>Qwen</em> at strict instruction-following. (We’ll also ask it to "
            "<em>Think Deeply</em>.)"
        ),
        "in": 1.25/1000, "out": 10.00/1000,
    },
    {
        "id": "anthropic/claude-3.5-sonnet",
        "label": "Claude 3.5 Sonnet",
        "desc": (
            "<strong>Excellent long-form reader.</strong> Very good at digesting large transcripts and adhering to "
            "instructions. Compared to <em>GPT-4o</em> it’s more cautious/verbose; less aggressive than <em>o3-Pro</em> "
            "in choosing a side; steadier than <em>Qwen</em> on edge cases."
        ),
        "in": 3.00/1000, "out": 15.00/1000,
    },
    {
        "id": "qwen/qwen2.5-72b-instruct",
        "label": "Qwen 2.5 72B",
        "desc": (
            "<strong>Fast value pick.</strong> The weakest here, but still solid for many rounds—quick, clear RFDs on "
            "typical flows. Less polished than <em>GPT-4o</em>, less careful than <em>Claude</em>, and will lag "
            "<em>o3-Pro</em>/<em>GPT-5</em> on hard theory or tangled weighing."
        ),
        "in": 0.15/1000, "out": 0.15/1000,
    },
]

def _model_prices(model_id: str):
    for m in OPENROUTER_MODELS:
        if m["id"] == model_id:
            return m["in"], m["out"]
    return 0.0, 0.0

# ───────────────────────────── Dark theme styling ─────────────────────────────

def _inject_dark_theme():
    st.markdown("""
    <style>
    :root{
      --bg:#0b1020; --bg2:#0e1530;
      --panel:#0d1426; --card:#0f1a33; --card2:#111f3f;
      --text:#eef2ff; --muted:#c7d2fe;
      --border:#1f2a47; --glow:#5b8cff;
      --blueA:#2563eb; --blueB:#1d4ed8; --orangeA:#f97316; --orangeB:#fb923c;
      --ok:#10b981; --warn:#f59e0b; --err:#ef4444;
    }
    [data-testid="stAppViewContainer"]{
      background:
        radial-gradient(1000px 600px at 12% -5%, #0f172a 0%, var(--bg) 42%),
        linear-gradient(180deg, var(--bg2), var(--bg));
      color:var(--text);
    }
    [data-testid="stHeader"]{ background:transparent; }
    [data-testid="stSidebar"]{
      background: linear-gradient(180deg,#0a0f1f,#0b1224);
      color:var(--text); border-right:1px solid var(--border);
    }
    .block-container{ color:var(--text); padding-top:1.2rem; }
    h1,h2,h3,h4,h5,p,li,span,code,strong,em{ color:var(--text) !important; }
    .stCaption, .stMarkdown small{ color:var(--muted) !important; }

    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div,
    .stFileUploader > div > div{
      background:var(--card) !important; color:var(--text) !important;
      border:1px solid var(--border) !important; border-radius:12px !important;
    }
    .stFileUploader > div > div{ border-style:dashed !important; }

    .stButton > button, .stFormSubmitButton > button{
      background: linear-gradient(90deg,var(--blueA),var(--blueB)) !important;
      color:#fff !important; border:0 !important; border-radius:12px !important;
      box-shadow:0 0 18px rgba(37,99,235,.45); transition: transform .12s ease, filter .12s ease;
    }
    .stButton > button:hover{ transform:translateY(-1px); filter:brightness(1.05); }

    .stDownloadButton > button{
      background: linear-gradient(90deg,var(--orangeA),var(--orangeB)) !important;
      color:#111 !important; font-weight:600 !important; border:0 !important;
      border-radius:12px !important; box-shadow:0 0 18px rgba(249,115,22,.45);
    }

    [data-testid="stProgressBar"] div{ background:#0b2038 !important; border-radius:999px !important; height:10px; }
    [data-testid="stProgressBar"] div > div{
      background:linear-gradient(90deg,#60a5fa,#34d399) !important; border-radius:999px !important;
    }

    .stTabs [data-baseweb="tab-list"]{ gap:.5rem; border-bottom:1px solid var(--border); }
    .stTabs [data-baseweb="tab"]{
      background:#0b1a33; color:var(--text); border:1px solid var(--border); border-bottom:none;
      border-top-left-radius:10px; border-top-right-radius:10px;
    }
    .stTabs [aria-selected="true"]{ background:#122241; }

    /* Model description card */
    .model-desc{
      background: linear-gradient(180deg, var(--card), var(--card2));
      border:1px solid var(--border); border-radius:16px; padding:14px 16px;
      font-size:1.06rem; line-height:1.6rem; color:var(--text);
      box-shadow: 0 0 18px rgba(91,140,255,.14);
      margin-bottom:.5rem;
    }
    .model-desc strong{ color:#fff; text-shadow: 0 0 6px rgba(91,140,255,.35); }
    .model-chip{
      display:inline-flex; align-items:center; gap:.45rem; padding:.25rem .65rem; border-radius:999px;
      background:#0b1f3f; border:1px solid var(--border); box-shadow: 0 0 8px rgba(91,140,255,.18);
      font-weight:700; letter-spacing:.2px;
    }
    </style>
    """, unsafe_allow_html=True)

def _render_model_desc(model: dict):
    st.markdown(
        f"""<span class="model-chip">{model["label"]}</span>
<div class="model-desc">{model["desc"]}</div>""",
        unsafe_allow_html=True
    )

# ───────────────────────────── Utilities ─────────────────────────────

def _zip_dir(dir_path: Path) -> Path:
    dir_path = dir_path.resolve()
    archive = shutil.make_archive(str(dir_path.with_suffix("")), "zip", root_dir=str(dir_path))
    return Path(archive)

def _estimate_tokens_from_text(s: str) -> int:
    # ~5 chars/token (conservative)
    return max(1, int(len(s) / 5))

def save_uploaded_file(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return Path(tmp.name).resolve()

def _fresh_file_required(path: Path, start_ts: float, label: str):
    if not path.exists():
        return False, f"{label} not created."
    if path.stat().st_mtime < start_ts:
        return False, f"{label} is stale (older than this run)."
    if path.is_file() and path.stat().st_size == 0:
        return False, f"{label} is empty."
    return True, ""

def _bin_exists(name: str) -> bool:
    try:
        subprocess.check_output([name, "-version"], stderr=subprocess.STDOUT)
        return True
    except Exception:
        try:
            subprocess.check_output([name, "-hide_banner"], stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False

# ─────────────────────── Credential Validation ───────────────────────

def validate_assemblyai_key(key: str) -> dict:
    try:
        r = requests.get("https://api.assemblyai.com/v2/account",
                         headers={"Authorization": key}, timeout=10)
        if r.status_code == 200:
            return {"ok": True, "error": None}
        if r.status_code in (401,403):
            return {"ok": False, "error": "Unauthorized API key."}
        return {"ok": False, "error": f"Unexpected status {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _or_probe_completion(key: str, model: str) -> dict:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "X-Title": "Key probe"}
    payload = {"model": model, "messages": [{"role":"user", "content":"ping"}], "max_tokens": 1}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            return {"status": "ok", "error": None}
        if r.status_code in (401,403):
            return {"status": "invalid", "error": r.text}
        if r.status_code in (402,429):
            return {"status": "no_credits", "error": r.text}
        return {"status": "error", "error": f"Unexpected status {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def validate_openrouter_key(key: str) -> dict:
    try:
        r = requests.get("https://openrouter.ai/api/v1/models",
                         headers={"Authorization": f"Bearer {key}"}, timeout=8)
        if r.status_code == 401:
            return {"ok": False, "reason": "invalid", "error": "Unauthorized API key."}
    except Exception as e:
        return {"ok": False, "reason": "error", "error": str(e)}
    probe = _or_probe_completion(key, "openai/gpt-4o-2024-11-20")
    if probe["status"] == "ok":
        return {"ok": True, "reason": "ok", "error": None}
    if probe["status"] == "no_credits":
        return {"ok": False, "reason": "no_credits", "error": None}
    if probe["status"] == "invalid":
        return {"ok": False, "reason": "invalid", "error": "Unauthorized API key."}
    return {"ok": False, "reason": "error", "error": probe["error"]}

# ───────────── Live streaming + progress + narrator (no auto-timeouts) ─────────

def _progress_from_debate_line(line: str, prev: float) -> float:
    if "Uploading to AssemblyAI" in line: return max(prev, 0.10)
    if "Queued at AssemblyAI" in line:    return max(prev, 0.20)
    if "Transcription status:" in line:   return max(prev, 0.40)
    if "wrote transcript.txt" in line:    return max(prev, 0.80)
    if "wrote judging_feedback.txt" in line or "Done" in line: return 1.0
    return prev

def _status_from_debate_line(line: str, cur: Optional[str]) -> Optional[str]:
    s = line.lower()
    if "uploading to assemblyai" in s: return "Uploading audio to AssemblyAI…"
    if "queued at assemblyai" in s: return "Queued; AssemblyAI is processing…"
    if "transcription status" in s: return "Transcribing your audio…"
    if "wrote transcript.txt" in s: return "Transcript ready."
    if "calling" in s: return "Evaluating arguments and writing an RFD…"
    if "wrote judging_feedback.txt" in s: return "Judging complete. Packaging outputs…"
    return cur

def _progress_from_speech_line(line: str, prev: float) -> float:
    if "[1/5]" in line: return max(prev, 0.10)
    if "[2/5]" in line: return max(prev, 0.30)
    if "[3/5]" in line: return max(prev, 0.55)
    if "[4/5]" in line: return max(prev, 0.80)
    if "Report written" in line: return 1.0
    return prev

def _status_from_speech_line(line: str, cur: Optional[str]) -> Optional[str]:
    s = line.lower()
    if "[1/5]" in s: return "Normalizing audio to 16 kHz mono…"
    if "[2/5]" in s: return "Uploading to AssemblyAI…"
    if "[3/5]" in s: return "AssemblyAI diarization & intelligence…"
    if "[4/5]" in s: return "Analysing delivery metrics…"
    if "report written" in s: return "Delivery analysis complete."
    return cur

def run_and_stream(
    cmd, cwd, env, log_placeholder, prog_placeholder, status_placeholder,
    progress_parser, status_parser,
    idle_timeout_sec: Optional[int] = None, wall_timeout_sec: Optional[int] = None
):
    """Stream subprocess logs without blocking. Timeouts disabled by default."""
    proc = subprocess.Popen(
        [str(x) for x in cmd],
        cwd=str(cwd), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    lines = []; progress = 0.0; status: Optional[str] = None
    prog_placeholder.progress(progress)
    start = last_out = time.time()
    assert proc.stdout is not None

    while True:
        if proc.poll() is not None:
            ready, _, _ = select.select([proc.stdout], [], [], 0)
            while ready:
                chunk = proc.stdout.readline()
                if not chunk: break
                line = chunk.rstrip("\n"); lines.append(line)
                progress = progress_parser(line, progress); prog_placeholder.progress(progress)
                new_status = status_parser(line, status)
                if new_status and new_status != status:
                    status = new_status; status_placeholder.markdown(f"**{status}**")
                log_placeholder.text("\n".join(lines[-1200:]))
                ready, _, _ = select.select([proc.stdout], [], [], 0)
            break

        ready, _, _ = select.select([proc.stdout], [], [], 0.5)
        if ready:
            chunk = proc.stdout.readline()
            if chunk:
                last_out = time.time()
                line = chunk.rstrip("\n"); lines.append(line)
                new_prog = progress_parser(line, progress)
                if new_prog != progress:
                    progress = new_prog; prog_placeholder.progress(progress)
                new_status = status_parser(line, status)
                if new_status and new_status != status:
                    status = new_status; status_placeholder.markdown(f"**{status}**")
                log_placeholder.text("\n".join(lines[-1200:]))
        else:
            now = time.time()
            if idle_timeout_sec is not None and now - last_out > idle_timeout_sec:
                try: proc.kill()
                except Exception: pass
                lines.append(f"⏱️ Timeout: no output for {idle_timeout_sec}s. Process terminated.")
                break
            if wall_timeout_sec is not None and now - start > wall_timeout_sec:
                try: proc.kill()
                except Exception: pass
                lines.append(f"⏱️ Timeout: exceeded wall time of {wall_timeout_sec}s. Process terminated.")
                break

    rc = proc.poll() if proc.poll() is not None else -9
    prog_placeholder.progress(1.0 if rc == 0 else progress)
    log_placeholder.text("\n".join(lines[-1200:]))
    return rc, "\n".join(lines)

# ───────────────────── Subprocess runners ────────────────────

def _env_for_subprocess(openrouter_key: Optional[str], aai_key: Optional[str]):
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if openrouter_key:
        env["OPENROUTER_API_KEY"] = openrouter_key
    if aai_key:
        env["ASSEMBLYAI_API_KEY"] = aai_key
    return env

def run_debate_transcribe_only(audio_path: Path, topic: str, first_team: str, style: str,
                               model_id: str, openrouter_key, aai_key,
                               work_dir: Path, log_placeholder, prog_placeholder, status_placeholder):
    env = _env_for_subprocess(openrouter_key, aai_key)
    cmd = [
        sys.executable, "-u", str(PROJ_ROOT / "AnalyzeDebateV2.py"),
        "--audio", str(audio_path),
        "--topic", topic, "--first", first_team, "--style", style,
        "--work-dir", str(work_dir), "--aai-key", aai_key or "",
        "--provider", "openrouter", "--model", model_id, "--no-gpt"
    ]
    return run_and_stream(cmd, PROJ_ROOT, env, log_placeholder, prog_placeholder, status_placeholder,
                          _progress_from_debate_line, _status_from_debate_line)

def run_debate_judge_only(topic: str, first_team: str, style: str,
                          model_id: str, openrouter_key, aai_key,
                          work_dir: Path, log_placeholder, prog_placeholder, status_placeholder):
    env = _env_for_subprocess(openrouter_key, aai_key)
    cmd = [
        sys.executable, "-u", str(PROJ_ROOT / "AnalyzeDebateV2.py"),
        "--audio", "dummy",
        "--topic", topic, "--first", first_team, "--style", style,
        "--work-dir", str(work_dir), "--aai-key", aai_key or "",
        "--provider", "openrouter", "--model", model_id, "--reuse-transcript"
    ]
    return run_and_stream(cmd, PROJ_ROOT, env, log_placeholder, prog_placeholder, status_placeholder,
                          _progress_from_debate_line, _status_from_debate_line)

def run_analyze_speech(audio_path: Path, first_team: str, aai_key: Optional[str],
                       log_placeholder, prog_placeholder, status_placeholder):
    env = _env_for_subprocess(None, aai_key)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = (RUNS_DIR / f"speech_{ts}").resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-u", str(PROJ_ROOT / "AnalyzeSpeechV2.py"),
        str(audio_path), "--team1", "Aff", "--team2", "Neg",
        "--first", first_team, "--work-dir", str(work_dir),
        "--aai-key", aai_key or "",
    ]
    start_ts = time.time()
    rc, logs = run_and_stream(cmd, PROJ_ROOT, env, log_placeholder, prog_placeholder, status_placeholder,
                              _progress_from_speech_line, _status_from_speech_line)
    out_file = work_dir / "analyze_speech.txt"
    ok, why = _fresh_file_required(out_file, start_ts, "analyze_speech.txt")
    content = out_file.read_text(encoding="utf-8") if ok else ""
    return {"ok": rc == 0 and ok, "logs": logs, "content": content, "work_dir": str(work_dir), "out_file": str(out_file) if ok else None, "why": None if ok else why}

# ───────────────────────────── Setup ─────────────────────────

def setup_page():
    _inject_dark_theme()
    st.title("AI Debate Analysis Tool — Setup")
    st.caption("Complete this once to unlock the app.")

    openrouter_key = st.text_input("OPENROUTER_API_KEY", type="password", key="openrouter_key")
    aai_key = st.text_input("ASSEMBLYAI_API_KEY", type="password", key="aai_key")

    st.divider()
    st.subheader("Choose a model (you can change later)")
    labels = [m["label"] for m in OPENROUTER_MODELS]
    choice = st.selectbox("Model", labels, index=0, key="model_label")
    chosen = next(m for m in OPENROUTER_MODELS if m["label"] == choice)
    _render_model_desc(chosen)

    st.divider()
    if st.button("Verify & Continue", type="primary", use_container_width=True):
        # ffmpeg/ffprobe preflight
        ffm = _bin_exists("ffmpeg")
        ffp = _bin_exists("ffprobe")
        if not ffm or not ffp:
            st.warning("ffmpeg/ffprobe not detected. Please install both or add them to PATH.")

        # AssemblyAI
        if not aai_key:
            st.write("❌ AssemblyAI error: API key required.")
            aai_ok = False
        else:
            a = validate_assemblyai_key(aai_key)
            aai_ok = a["ok"]
            st.write("✅ AssemblyAI key valid" if aai_ok else f"❌ AssemblyAI error: {a['error'] or 'Unknown'}")

        # OpenRouter
        if not openrouter_key:
            st.write("❌ OpenRouter error: API key required.")
            ok_llm = False; reason = None
        else:
            k = validate_openrouter_key(openrouter_key)
            ok_llm = k["ok"]; reason = k.get("reason"); err = k.get("error")
            if ok_llm:
                st.write("✅ OpenRouter key valid")
            elif reason == "no_credits":
                st.write("❌ OpenRouter key valid but **no credits**.")
            elif reason == "invalid":
                st.write("❌ OpenRouter error: Invalid API key.")
            else:
                st.write(f"❌ OpenRouter error: {err or 'Unknown'}")

        if aai_ok and ok_llm and reason != "no_credits" and ffm and ffp:
            st.success("Setup complete. You can proceed.")
            st.session_state.setup_ok = True
            st.session_state.verified = {
                "openrouter_key": openrouter_key,
                "aai_key": aai_key,
                "model_id": chosen["id"],
            }
            st.button("Open the App →", on_click=lambda: set_stage("run"), type="primary")
        else:
            st.warning(
                "Fix the issues above before continuing.\n\n"
                "• Add credits to OpenRouter billing: https://openrouter.ai\n"
                "• Ensure ffmpeg and ffprobe are installed and on PATH."
            )

def set_stage(stage: str):
    st.session_state.stage = stage

# ───────────────────────────── Run (state machine) ────────────────────────────

def _init_debate_state():
    ss = st.session_state
    ss.setdefault("debate_phase", "idle")  # idle | transcribing | awaiting_confirm | judging | done
    ss.setdefault("debate_ctx", {})

def run_page():
    _inject_dark_theme()
    st.title("AI Debate Analysis Tool")

    ss = st.session_state
    openrouter_key = ss.verified["openrouter_key"]
    aai_key = ss.verified["aai_key"]
    _init_debate_state()

    # Model picker (sidebar)
    st.sidebar.subheader("Model")
    labels = [m["label"] for m in OPENROUTER_MODELS]
    try:
        default_idx = [m["id"] for m in OPENROUTER_MODELS].index(ss.verified.get("model_id", OPENROUTER_MODELS[0]["id"]))
    except ValueError:
        default_idx = 0
    choice = st.sidebar.selectbox("Choose model", labels, index=default_idx, key="run_model_label")
    chosen = next(m for m in OPENROUTER_MODELS if m["label"] == choice)
    ss.verified["model_id"] = chosen["id"]
    _render_model_desc(chosen)

    if "last_debate" not in ss: ss.last_debate = {}
    if "last_speech" not in ss: ss.last_speech = {}

    uploaded_file = st.file_uploader("Audio Upload (.m4a or .wav)", type=["m4a", "wav"], key="uploader")
    topic = st.text_input("Debate Topic", key="topic")
    first_team = st.selectbox("Who Speaks First?", options=["Aff", "Neg"], key="first_team")
    style = st.selectbox("Judging Style", options=["lay", "flay", "tech", "prog"], key="style")

    c1, c2 = st.columns(2)

    # Debate
    with c1:
        st.subheader("Debate Judging Analysis")

        if st.button("Run Debate Judging Analysis", use_container_width=True, key="btn_run_debate"):
            if uploaded_file is None:
                st.error("Please upload an audio file.")
            elif not topic.strip():
                st.error("Please enter a debate topic.")
            else:
                tmp = save_uploaded_file(uploaded_file)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                work_dir = (RUNS_DIR / f"debate_{ts}").resolve()
                work_dir.mkdir(parents=True, exist_ok=True)

                st.info("Step 1/2: Transcribing (AssemblyAI) to estimate cost…")
                status_box = st.empty()
                log_box = st.empty()
                prog = st.progress(0.0)

                rc1, logs1 = run_debate_transcribe_only(
                    tmp, topic.strip(), first_team.strip(), style.strip(),
                    chosen["id"], openrouter_key, aai_key,
                    work_dir, log_box, prog, status_box
                )
                tr_path = work_dir / "transcript.txt"
                if rc1 != 0 or not tr_path.exists():
                    st.error("Transcription failed. See logs below.")
                    st.text_area("Logs", value=logs1, height=420)
                else:
                    transcript = tr_path.read_text(encoding="utf-8")
                    in_tokens = _estimate_tokens_from_text(transcript) + 800   # prompt overhead
                    out_tokens = max(300, int(in_tokens * 0.35))               # rough completion size
                    pin, pout = _model_prices(chosen["id"])
                    est_cost = (in_tokens/1000.0)*pin + (out_tokens/1000.0)*pout

                    ss.debate_phase = "awaiting_confirm"
                    ss.debate_ctx = {
                        "work_dir": str(work_dir),
                        "transcript_full": transcript,   # full transcript visible
                        "in_tokens": in_tokens,
                        "out_tokens": out_tokens,
                        "est_cost": est_cost,
                        "logs1": logs1,
                        "topic": topic.strip(),
                        "first_team": first_team.strip(),
                        "style": style.strip(),
                        "model_id": chosen["id"],
                        "openrouter_key": openrouter_key,
                        "aai_key": aai_key,
                    }

        if ss.debate_phase == "awaiting_confirm" and ss.debate_ctx:
            ctx = ss.debate_ctx
            st.success(f"Estimated charge: **~${ctx['est_cost']:.2f}** "
                       f"(~{ctx['in_tokens']:,} in / ~{ctx['out_tokens']:,} out tokens).")
            st.subheader("Transcript")
            st.text_area("Full transcript", value=ctx["transcript_full"], height=420)
            st.info("Transcript ready. **Waiting for your confirmation** to proceed to judging.")
            if st.button("Proceed with Judging", type="primary", key="btn_proceed_judging"):
                ss.debate_phase = "judging"

        if ss.debate_phase == "judging" and ss.debate_ctx:
            ctx = ss.debate_ctx
            st.info("Step 2/2: Running LLM judging…")
            status_box2 = st.empty()
            log_box2 = st.empty()
            prog2 = st.progress(0.0)
            rc2, logs2 = run_debate_judge_only(
                ctx["topic"], ctx["first_team"], ctx["style"],
                ctx["model_id"], ctx["openrouter_key"], ctx["aai_key"],
                Path(ctx["work_dir"]), log_box2, prog2, status_box2
            )
            out_file = Path(ctx["work_dir"]) / "judging_feedback.txt"
            if rc2 != 0 or not out_file.exists():
                st.error("Judging step failed. See logs below.")
                st.text_area("Logs (transcribe)", value=ctx["logs1"], height=220)
                st.text_area("Logs (judge)", value=logs2, height=220)
                ss.debate_phase = "awaiting_confirm"
            else:
                tabs = st.tabs(["Feedback", "Logs", "Downloads"])
                with tabs[0]:
                    st.markdown(out_file.read_text(encoding="utf-8"))
                with tabs[1]:
                    st.text_area("Transcribe logs", value=ctx["logs1"], height=220)
                    st.text_area("Judge logs", value=logs2, height=220)
                with tabs[2]:
                    jf = out_file
                    st.download_button("Download judging_feedback.txt", data=jf.read_bytes(),
                                       file_name=jf.name, mime="text/plain")
                    for extra in ("prompt_used.txt", "judge_feedback.json", "run.json", "transcript.txt"):
                        p = Path(ctx["work_dir"]) / extra
                        if p.exists():
                            st.download_button(f"Download {extra}",
                                               data=p.read_bytes(),
                                               file_name=p.name,
                                               mime="application/json" if p.suffix==".json" else "text/plain")
                    zip_path = _zip_dir(Path(ctx["work_dir"]))
                    with zip_path.open("rb") as fh:
                        st.download_button("Download full run (.zip)", data=fh.read(),
                                           file_name=zip_path.name, mime="application/zip")

                st.session_state.last_debate = {
                    "content": out_file.read_text(encoding="utf-8"),
                    "logs": ctx["logs1"] + "\n\n--- JUDGE ---\n\n" + logs2,
                }
                ss.debate_phase = "done"

        if ss.debate_phase == "done":
            st.success("Debate judging run complete.")
            if st.button("Start Another Debate Run", key="btn_reset_debate"):
                ss.debate_phase = "idle"
                ss.debate_ctx = {}

    # Speech analysis
    with c2:
        st.subheader("Speech Feedback Analysis")
        if st.button("Run Speech Feedback Analysis", use_container_width=True, key="btn_run_speech"):
            if uploaded_file is None:
                st.error("Please upload an audio file.")
            else:
                tmp = save_uploaded_file(uploaded_file)
                status_box = st.empty()
                log_box = st.empty()
                prog = st.progress(0.0)
                result = run_analyze_speech(tmp, first_team.strip(), aai_key, log_box, prog, status_box)
                tabs = st.tabs(["Report", "Logs", "Downloads"])
                with tabs[0]:
                    st.text_area("analyze_speech.txt", value=result.get("content", ""), height=420)
                with tabs[1]:
                    st.text_area("Subprocess logs", value=result.get("logs", ""), height=420)
                with tabs[2]:
                    wd = Path(result.get("work_dir", RUNS_DIR))
                    out = wd / "analyze_speech.txt"
                    if out.exists():
                        st.download_button("Download analyze_speech.txt", data=out.read_bytes(),
                                           file_name=out.name, mime="text/plain")
                    for extra in ("delivery_metrics.json", "selected.json", "segments.json", "merged_segments.json", "run.json"):
                        p = wd / extra
                        if p.exists():
                            st.download_button(f"Download {extra}", data=p.read_bytes(),
                                               file_name=p.name, mime="application/json")
                    zip_path = _zip_dir(wd)
                    with zip_path.open("rb") as fh:
                        st.download_button("Download full run (.zip)", data=fh.read(),
                                           file_name=zip_path.name, mime="application/zip")

    st.divider()
    colA, colB = st.columns(2)
    with colA:
        if st.session_state.get("last_debate"):
            with st.expander("Last Debate Result (this session)"):
                st.markdown(st.session_state.last_debate.get("content",""))
                st.text_area("Logs", value=st.session_state.last_debate.get("logs",""), height=240)
    with colB:
        if st.session_state.get("last_speech"):
            with st.expander("Last Speech Result (this session)"):
                st.text_area("Report", value=st.session_state.last_speech.get("content",""), height=240)
                st.text_area("Logs", value=st.session_state.last_speech.get("logs",""), height=240)

# ───────────────────────────── App entry ─────────────────────────────

def main():
    st.set_page_config(page_title="AI Debate Analysis Tool", layout="wide", initial_sidebar_state="expanded")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    if "stage" not in st.session_state:
        st.session_state.stage = "setup"
    if st.session_state.stage == "setup":
        setup_page()
    else:
        if not st.session_state.get("setup_ok") or not st.session_state.get("verified"):
            st.session_state.stage = "setup"
            setup_page()
        else:
            run_page()

if __name__ == "__main__":
    main()
