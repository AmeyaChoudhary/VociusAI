#!/usr/bin/env python3
# AnalyzeDebate.py – AssemblyAI transcription + OpenRouter/OpenAI judging
# - No WhisperX or Hugging Face
# - Reuse transcript / no-gpt supported
# - Friendly logs for the Streamlit GUI progress parser

import os, sys, time, subprocess, argparse, pathlib, json
import importlib, importlib.metadata
from typing import Optional
import requests
from openai import OpenAI

# ─── tweakables ─────────────────────────────────────────────────────
STYLE2_MODEL   = {"lay": "small", "flay": "small", "tech": "small", "prog": "small"}  # kept only for display parity
PROMPT_FILE    = {"lay":  "lay_judge_prompt.txt",
                  "flay": "lay_judge_prompt.txt",
                  "tech": "tech_judge_prompt.txt",
                  "prog": "prog_judge_prompt.txt"}

# Align default with GUI’s OpenRouter catalog; OpenAI default can stay generic
DEFAULT_OR_MODEL  = "openai/gpt-4o-2024-11-20"   # for provider=openrouter
DEFAULT_OAI_MODEL = "gpt-4o"                     # for provider=openai
AAI_POLL_SECS     = 3.0                          # polling cadence for transcript job
# ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

# ───────────────────────── helpers ─────────────────────────

def _ver(pkg: str) -> str:
    try:
        return importlib.metadata.version(pkg)
    except Exception:
        try:
            mod = __import__(pkg)
            return getattr(mod, "__version__", "unknown")
        except Exception:
            return "unknown"

def _git_state():
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        return {"head": head, "dirty": bool(status)}
    except Exception:
        return {"head": None, "dirty": None}

def _write_run_manifest(work_dir: pathlib.Path, payload: dict, start_time: float, status: str = "ok"):
    end_time = time.time()
    manifest = {
        "program": "AnalyzeDebate.py",
        "status": status,
        "args": payload,
        "timestamps": {
            "start": start_time,
            "end": end_time,
            "elapsed_sec": round(end_time - start_time, 3),
        },
        "versions": {
            "python": sys.version,
            "requests": _ver("requests"),
        },
        "git": _git_state(),
    }
    (work_dir / "run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("🧾  wrote run.json", flush=True)

def load_prompt(style: str, topic: str, first: str, transcript: str) -> str:
    prompt_path = SCRIPT_DIR / PROMPT_FILE[style]
    if not prompt_path.exists():
        sys.exit(f"❌ prompt file missing: {prompt_path}")
    template = prompt_path.read_text(encoding="utf-8")
    return (template
            .replace("[insert topic here]", topic)
            .replace("[insert team name here]", first)
            .replace("[insert transcript here]", transcript))

def _normalize_model(provider: str, model_arg: Optional[str]) -> str:
    """
    Accepts 'openai/gpt-4o' for OpenRouter or 'gpt-4o' for OpenAI.
    Normalizes to the provider's expected form.
    """
    m = (model_arg or "").strip()
    if provider == "openrouter":
        if "/" not in m:
            return f"openai/{m}" if m else DEFAULT_OR_MODEL
        return m
    else:
        if m and "/" in m and m.split("/", 1)[0] in {"openai"}:
            return m.split("/", 1)[1]
        return m or DEFAULT_OAI_MODEL

def _is_gpt5(normalized_model: str) -> bool:
    tail = normalized_model.split("/", 1)[-1]
    return tail.startswith("gpt-5")

# ───────────────────────── AssemblyAI transcription ─────────────────────────

def aai_upload_file(file_path: pathlib.Path, api_key: str) -> str:
    """
    Streams the local file to AssemblyAI's /upload and returns the 'upload_url'.
    """
    url = "https://api.assemblyai.com/v2/upload"
    headers = {"authorization": api_key}
    chunk_size = 5 * 1024 * 1024  # 5 MB

    print("📤 Uploading to AssemblyAI…", flush=True)
    def _read_chunks():
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    r = requests.post(url, headers=headers, data=_read_chunks())
    if r.status_code != 200:
        raise SystemExit(f"❌ Upload failed: {r.status_code} {r.text[:300]}")
    upload_url = r.json().get("upload_url")
    if not upload_url:
        raise SystemExit("❌ Upload response missing upload_url.")
    return upload_url

def aai_request_transcription(upload_url: str, api_key: str) -> str:
    """
    Creates a transcription job and returns the transcript id.
    """
    url = "https://api.assemblyai.com/v2/transcript"
    headers = {"authorization": api_key, "content-type": "application/json"}
    payload = {
        "audio_url": upload_url,
        "speaker_labels": False,         # diarization not required for debate judging
        "punctuate": True,
        "format_text": True,
        "disfluencies": True,            # keeps ums/uhs if present
        # You can add "language_code": "en" to hard-pin, but AAI auto-detects well
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code not in (200, 201):
        raise SystemExit(f"❌ Transcription create failed: {r.status_code} {r.text[:300]}")
    tid = r.json().get("id")
    if not tid:
        raise SystemExit("❌ No transcript id returned by AssemblyAI.")
    print("⏳ Queued at AssemblyAI…", flush=True)
    return tid

def aai_poll_transcript(transcript_id: str, api_key: str) -> dict:
    """
    Polls transcript status until 'completed' or 'error'. Returns the JSON.
    """
    headers = {"authorization": api_key}
    url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise SystemExit(f"❌ Poll failed: {r.status_code} {r.text[:300]}")
        js = r.json()
        status = js.get("status")
        print(f"Transcription status: {status}", flush=True)
        if status == "completed":
            return js
        if status == "error":
            raise SystemExit(f"❌ AssemblyAI error: {js.get('error')}")
        time.sleep(AAI_POLL_SECS)

def aai_transcribe_to_file(audio_path: pathlib.Path, api_key: str, work_dir: pathlib.Path) -> str:
    """
    Full AAI pipeline: upload → create job → poll → write transcript.txt
    Returns the transcript text.
    """
    t0 = time.time()
    upload_url = aai_upload_file(audio_path, api_key)
    tid = aai_request_transcription(upload_url, api_key)
    js = aai_poll_transcript(tid, api_key)
    text = js.get("text") or ""
    (work_dir / "transcript.txt").write_text(text, encoding="utf-8")
    print("📝  wrote transcript.txt", flush=True)
    print(f"⏱️  Completed transcription in {round(time.time() - t0, 1)}s", flush=True)
    return text

# ───────────────────────── LLM judging (unchanged) ─────────────────────────

def gpt_judge(prompt: str, work_dir: pathlib.Path, provider: str, model_name: str) -> dict:
    t0 = time.time()

    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise SystemExit("❌ OPENROUTER_API_KEY missing. Provide it in the GUI or env.")
        client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
        model = model_name  # e.g., "openai/gpt-4o-2024-11-20"
        provider_label = f"OpenRouter:{model}"
    else:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise SystemExit("❌ OPENAI_API_KEY missing. Provide it in the GUI or env.")
        client = OpenAI(api_key=key)  # OpenAI default base_url
        model = model_name           # e.g., "gpt-4o"
        provider_label = f"OpenAI:{model}"

    print(f"🤖  Calling {provider_label} …", flush=True)
    try:
        rsp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "You are a PF debate judge."},
                      {"role": "user", "content": prompt}],
            temperature=0, max_tokens=3500)
        out_text = rsp.choices[0].message.content or ""
        (work_dir / "judging_feedback.txt").write_text(out_text, encoding="utf-8")
        print("📄  wrote judging_feedback.txt", flush=True)

        usage = getattr(rsp, "usage", None)
        meta = {
            "provider": provider,
            "model": model_name,
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        }
        jf_json = {"provider": provider, "model": model_name, "feedback": out_text, "usage": meta, "error": None}
        (work_dir / "judge_feedback.json").write_text(json.dumps(jf_json, indent=2), encoding="utf-8")
        print("📊  wrote judge_feedback.json", flush=True)
        print(f"⏱️  Completed LLM analysis in {round(time.time() - t0, 1)}s", flush=True)
        return jf_json

    except Exception as e:
        msg = str(e)
        if "insufficient_quota" in msg or "payment" in msg.lower() or "402" in msg:
            hint = "Your account likely has no credits or is out of quota. Top up billing and retry."
        elif "Unauthorized" in msg or "401" in msg or "invalid_api_key" in msg.lower():
            hint = "API key invalid for the selected provider."
        else:
            hint = "LLM call failed."
        err_json = {"provider": provider, "model": model_name, "feedback": "", "usage": None,
                    "error": {"message": msg, "hint": hint}}
        (work_dir / "judge_feedback.json").write_text(json.dumps(err_json, indent=2), encoding="utf-8")
        print(f"❌ LLM error: {msg}\n   Hint: {hint}", flush=True)
        raise

# ───────────────────────── main ─────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Debate judging pipeline (AssemblyAI + LLM).")
    ap.add_argument("--audio", required=True, help="Path to .m4a/.wav (or any common audio file)")
    ap.add_argument("--topic", required=True, help="Debate topic")
    ap.add_argument("--first", required=True, choices=["Aff", "Neg"], help="Who speaks first")
    ap.add_argument("--style", required=True, choices=list(STYLE2_MODEL.keys()), help="Judging style")
    ap.add_argument("--aai-key", help="AssemblyAI API key (required unless --reuse-transcript).")
    ap.add_argument("--work-dir", default=".", help="Output directory")
    ap.add_argument("--provider", choices=["openrouter","openai"], default="openrouter",
                    help="LLM provider for judging")
    ap.add_argument("--model", default=None, help="LLM model name (provider-specific)")
    ap.add_argument("--no-gpt", action="store_true", help="Skip LLM judging (transcript-only)")
    ap.add_argument("--reuse-transcript", action="store_true",
                    help="Reuse existing transcript.txt in work dir (skip transcription)")
    args = ap.parse_args()

    work_dir = pathlib.Path(args.work_dir).expanduser().resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    # Guard against stale output (keep transcript if reuse flag is set)
    for p in ["judging_feedback.txt", "judge_feedback.json", "prompt_used.txt", "run.json"]:
        f = work_dir / p
        if f.exists():
            try: f.unlink()
            except Exception: pass

    style = args.style.lower()
    if style not in STYLE2_MODEL:
        sys.exit("❌ Style must be lay, flay, tech, or prog.")

    # Transcript availability / AAI key requirement
    transcript_path = work_dir / "transcript.txt"
    need_transcribe = True
    if args.reuse_transcript and transcript_path.exists() and transcript_path.stat().st_size > 0:
        need_transcribe = False
    aai_key = args.aai_key or os.getenv("ASSEMBLYAI_API_KEY")
    if need_transcribe and not aai_key:
        sys.exit("❌ AssemblyAI key required (pass --aai-key or set ASSEMBLYAI_API_KEY).")

    # Provider/model normalization
    model_name = _normalize_model(args.provider, args.model)

    # If we will call the LLM, validate that appropriate keys exist
    if not args.no_gpt:
        if args.provider == "openrouter" and not os.getenv("OPENROUTER_API_KEY"):
            sys.exit("❌ OPENROUTER_API_KEY required for provider=openrouter.")
        if args.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            sys.exit("❌ OPENAI_API_KEY required for provider=openai.")

    t0 = time.time()
    print("=== 🚀  Debate Judging Pipeline Start ===", flush=True)
    print(f"• Audio: {args.audio}", flush=True)
    print(f"• Topic: {args.topic}", flush=True)
    print(f"• First: {args.first}   • Style: {style}", flush=True)
    print(f"• LLM: {'(skipped)' if args.no_gpt else args.provider + ' / ' + model_name}", flush=True)
    print(f"• Work dir: {work_dir}", flush=True)

    try:
        # 1) Transcription (or reuse)
        if need_transcribe:
            audio_path = pathlib.Path(args.audio).expanduser().resolve()
            if not audio_path.exists():
                raise SystemExit(f"❌ Audio file not found: {audio_path}")
            transcript = aai_transcribe_to_file(audio_path, aai_key, work_dir)
        else:
            print("🔁  Reusing existing transcript.txt", flush=True)
            transcript = transcript_path.read_text(encoding="utf-8")

        # 2) LLM judging (optional)
        if not args.no_gpt:
            prompt = load_prompt(style, args.topic, args.first, transcript)

            # Special directive for GPT-5
            if _is_gpt5(model_name):
                prompt = prompt.rstrip() + "\n\nThink Deeply."
                print("🧩  Added GPT-5 directive: 'Think Deeply.'", flush=True)

            (work_dir / "prompt_used.txt").write_text(prompt, encoding="utf-8")
            print("🧾  wrote prompt_used.txt", flush=True)

            judge_json = gpt_judge(prompt, work_dir, args.provider, model_name)
            preview = judge_json.get("feedback", "")
            print("\n=== 🧠  AI Judge Feedback (preview) ===\n", flush=True)
            print((preview[:1200] + ("…" if len(preview) > 1200 else "")), flush=True)
        else:
            print("⚙️  --no-gpt set: skipping LLM judging. Transcript produced.", flush=True)

        _write_run_manifest(work_dir, {
            "audio": str(args.audio),
            "topic": args.topic,
            "first": args.first,
            "style": style,
            "provider": None if args.no_gpt else args.provider,
            "model": None if args.no_gpt else model_name,
            "no_gpt": bool(args.no_gpt),
            "transcript_chars": transcript_path.stat().st_size if transcript_path.exists() else 0,
        }, t0, status="ok")

        print(f"\n⏱  Total runtime: {round(time.time()-t0, 1)} s", flush=True)
        print("=== ✅  Done ===", flush=True)

    except SystemExit:
        # Already printed a clear message; still write manifest for GUI
        _write_run_manifest(work_dir, {
            "audio": str(args.audio),
            "topic": args.topic,
            "first": args.first,
            "style": style,
            "provider": None if args.no_gpt else args.provider,
            "model": None if args.no_gpt else model_name,
            "no_gpt": bool(args.no_gpt),
        }, t0, status="error")
        raise
    except Exception as e:
        print(f"❌ Unhandled error: {e}", flush=True)
        _write_run_manifest(work_dir, {
            "audio": str(args.audio),
            "topic": args.topic,
            "first": args.first,
            "style": style,
            "provider": None if args.no_gpt else args.provider,
            "model": None if args.no_gpt else model_name,
            "no_gpt": bool(args.no_gpt),
            "error": str(e),
        }, t0, status="error")
        raise

if __name__ == "__main__":
    main()
