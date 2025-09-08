#!/usr/bin/env python3
# AnalyzeDebate.py – argparse version with OpenRouter/OpenAI, JSON outputs, reuse-transcript,
# clear HF gating errors, and GPT-5 “Think Deeply” suffix support

import os, sys, time, subprocess, tempfile, argparse, pathlib, json
import importlib, importlib.metadata
import torch
import whisperx
from openai import OpenAI

# ─── tweakables ─────────────────────────────────────────────────────
DEVICE         = "cpu"                # "mps" / "cuda" if GPU available
MIN_SPEECH_SEC = 1.0                  # drop speech islands < 1 s
PAD_SEC        = 0.05                 # ± 50 ms padding
STYLE2_MODEL   = {"lay": "small", "flay": "small", "tech": "small", "prog": "small"}
PROMPT_FILE    = {"lay":  "lay_judge_prompt.txt",
                  "flay": "lay_judge_prompt.txt",
                  "tech": "tech_judge_prompt.txt",
                  "prog": "prog_judge_prompt.txt"}

# Align default with GUI’s OpenRouter catalog; OpenAI default can stay generic
DEFAULT_OR_MODEL  = "openai/gpt-4o-2024-11-20"   # for provider=openrouter
DEFAULT_OAI_MODEL = "gpt-4o"                     # for provider=openai
# ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

# ───────────────────────── helpers ─────────────────────────

def _ver(pkg: str) -> str:
    try:
        return importlib.metadata.version(pkg)
    except Exception:
        try:
            mod = importlib.import_module(pkg)
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
            "torch": _ver("torch"),
            "whisperx": _ver("whisperx"),
        },
        "git": _git_state(),
    }
    (work_dir / "run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("🧾  wrote run.json", flush=True)

def ffprobe_sec(path: str) -> float:
    try:
        return float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=nw=1:nk=1", path], text=True))
    except Exception:
        return 0.0

def hhmmss(sec: float) -> str:
    m, s = divmod(int(sec), 60); h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}"

def ensure_wav(src: str):
    root, ext = os.path.splitext(src)
    if ext.lower() in {".wav", ".wave"}:
        return src, False
    tmp = f"{root}_tmp16k.wav"
    subprocess.check_call([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", src, "-ar", "16000", "-ac", "1", "-y", tmp])
    return tmp, True

def vad_trim(raw_path: str, hf_token: str) -> str:
    from pyannote.audio import Pipeline
    from pyannote.core import Timeline

    t0 = time.time()
    wav_for_vad, tmp_flag = ensure_wav(raw_path)
    print("🔍  Running pyannote VAD …", flush=True)
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/voice-activity-detection",
            use_auth_token=hf_token).to(torch.device(DEVICE))
    except Exception as e:
        msg = str(e)
        tip = (
            "Your Hugging Face token likely lacks access to the **gated** pyannote models.\n"
            "Grant access here (both are required):\n"
            " • https://huggingface.co/pyannote/voice-activity-detection\n"
            " • https://huggingface.co/pyannote/speaker-diarization-3.0\n"
            "Then set HUGGINGFACE_TOKEN and retry."
        )
        sys.exit(f"❌ Failed to load pyannote VAD: {msg}\n{tip}")

    tl = pipeline({"audio": wav_for_vad}).get_timeline().support()
    speech_only = Timeline(segments=[s for s in tl if s.duration >= MIN_SPEECH_SEC])

    padded = Timeline()
    for seg in speech_only:
        start_seg = max(0.0, seg.start - PAD_SEC)
        end_seg = seg.end + PAD_SEC
        padded.add(seg.__class__(start_seg, end_seg))
    padded = padded.support()

    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as f:
        for seg in padded:
            f.write(f"file '{os.path.abspath(wav_for_vad)}'\n")
            f.write(f"inpoint {seg.start:.3f}\n")
            f.write(f"outpoint {seg.end:.3f}\n")
        concat_list = f.name

    out_wav = f"{os.path.splitext(raw_path)[0]}_speech.wav"
    subprocess.check_call([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", "-y", out_wav])
    os.unlink(concat_list)
    if tmp_flag:
        try: os.remove(wav_for_vad)
        except Exception: pass

    try:
        d_raw, d_trim = ffprobe_sec(raw_path), ffprobe_sec(out_wav)
        if d_raw > 0 and d_trim > 0:
            print(f"✅ saved {os.path.basename(out_wav)}   "
                  f"{hhmmss(d_raw)} → {hhmmss(d_trim)}  "
                  f"(shrink {100*(1-d_trim/d_raw):.1f} %)", flush=True)
    except Exception:
        print("⚠️  Unable to compute shrink stats (ffprobe not found?).", flush=True)

    print(f"⏱️  Completed silence trim in {round(time.time() - t0, 1)}s", flush=True)
    return out_wav

def transcribe(wav: str, size: str, work_dir: pathlib.Path) -> str:
    t0 = time.time()
    print(f"🧠  WhisperX ({size}) …", flush=True)
    model = whisperx.load_model(size, device=DEVICE, compute_type="float32")
    audio = whisperx.load_audio(wav)
    res = model.transcribe(audio)
    # Defensive: fall back to 'en' if language wasn’t returned
    lang = res.get("language") or "en"
    aligner, meta = whisperx.load_align_model(language_code=lang, device=DEVICE)
    aligned = whisperx.align(res["segments"], aligner, meta, audio, device=DEVICE)
    txt = " ".join(s["text"].strip() for s in aligned["segments"])
    (work_dir / "transcript.txt").write_text(txt, encoding="utf-8")
    print("📝  wrote transcript.txt", flush=True)
    print(f"⏱️  Completed transcription in {round(time.time() - t0, 1)}s", flush=True)
    return txt

def load_prompt(style: str, topic: str, first: str, transcript: str) -> str:
    prompt_path = SCRIPT_DIR / PROMPT_FILE[style]
    if not prompt_path.exists():
        sys.exit(f"❌ prompt file missing: {prompt_path}")
    template = prompt_path.read_text(encoding="utf-8")
    return (template
            .replace("[insert topic here]", topic)
            .replace("[insert team name here]", first)
            .replace("[insert transcript here]", transcript))

def _normalize_model(provider: str, model_arg: str) -> str:
    """
    Accepts 'openai/gpt-4o' for OpenRouter or 'gpt-4o' for OpenAI.
    Normalizes to the provider's expected form.
    """
    m = (model_arg or "").strip()
    if provider == "openrouter":
        # Allow bare OpenAI-style names by prefixing 'openai/'
        if "/" not in m:
            return f"openai/{m}"
        return m
    else:
        # OpenAI expects bare id; strip known vendor prefix if present
        if "/" in m and m.split("/", 1)[0] in {"openai"}:
            return m.split("/", 1)[1]
        return m

def _is_gpt5(normalized_model: str) -> bool:
    # Handles 'gpt-5' or 'openai/gpt-5' (and future suffixes like 'openai/gpt-5-something')
    tail = normalized_model.split("/", 1)[-1]
    return tail.startswith("gpt-5")

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
    ap = argparse.ArgumentParser(description="Debate judging pipeline (WhisperX + LLM).")
    ap.add_argument("--audio", required=True, help="Path to raw .m4a/.wav")
    ap.add_argument("--topic", required=True, help="Debate topic")
    ap.add_argument("--first", required=True, choices=["Aff", "Neg"], help="Who speaks first")
    ap.add_argument("--style", required=True, choices=list(STYLE2_MODEL.keys()), help="Judging style")
    ap.add_argument("--hf-token", help="HuggingFace token for pyannote VAD (required unless --reuse-transcript).")
    ap.add_argument("--work-dir", default=".", help="Output directory")
    ap.add_argument("--whisper-size", default=None,
                    help="Override WhisperX size (tiny/base/small/medium/large-v2). Defaults via style map.")
    ap.add_argument("--provider", choices=["openrouter","openai"], default="openrouter",
                    help="LLM provider")
    ap.add_argument("--model", default=None,
                    help="LLM model name (provider-specific).")
    ap.add_argument("--no-gpt", action="store_true",
                    help="Skip LLM judging (transcript-only).")
    ap.add_argument("--reuse-transcript", action="store_true",
                    help="Reuse existing transcript.txt in work dir (skip VAD/transcribe).")
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

    whisper_size = (args.whisper_size or STYLE2_MODEL[style]).strip()

    # Transcript availability / HF token requirement
    transcript_path = work_dir / "transcript.txt"
    need_transcribe = True
    if args.reuse_transcript and transcript_path.exists() and transcript_path.stat().st_size > 0:
        need_transcribe = False
    if need_transcribe and not args.hf_token:
        sys.exit("❌ --hf-token is required (or use --reuse-transcript with an existing transcript.txt).")

    # Provider/model normalization
    if args.model:
        model_name = _normalize_model(args.provider, args.model)
    else:
        model_name = _normalize_model(args.provider, DEFAULT_OR_MODEL if args.provider=="openrouter" else DEFAULT_OAI_MODEL)

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
    print(f"• First: {args.first}   • Style: {style}   • WhisperX: {whisper_size}", flush=True)
    print(f"• LLM: {'(skipped)' if args.no_gpt else args.provider + ' / ' + model_name}", flush=True)
    print(f"• Work dir: {work_dir}", flush=True)

    try:
        if need_transcribe:
            speech_wav = vad_trim(args.audio, args.hf_token)
            transcript = transcribe(speech_wav, whisper_size, work_dir)
        else:
            print("🔁  Reusing existing transcript.txt", flush=True)
            transcript = transcript_path.read_text(encoding="utf-8")

        if not args.no_gpt:
            # Build prompt
            prompt = load_prompt(style, args.topic, args.first, transcript)

            # Special directive for GPT-5
            if _is_gpt5(model_name):
                prompt = prompt.rstrip() + "\n\nThink Deeply."
                print("🧩  Added GPT-5 directive: 'Think Deeply.'", flush=True)

            # Save the final prompt actually used
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
            "whisper_size": whisper_size,
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
            "whisper_size": whisper_size,
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
            "whisper_size": whisper_size,
            "provider": None if args.no_gpt else args.provider,
            "model": None if args.no_gpt else model_name,
            "no_gpt": bool(args.no_gpt),
            "error": str(e),
        }, t0, status="error")
        raise

if __name__ == "__main__":
    main()
