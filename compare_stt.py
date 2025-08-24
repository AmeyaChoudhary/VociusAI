#!/usr/bin/env python3
"""
compare_stt.py
Run the same audio through Deepgram (nova-3) and AssemblyAI (universal),
request speaker diarization, then produce normalized outputs that keep the
top 4 speakers by total talk time.

Outputs (in ./runs/stt_compare_YYYYmmdd_HHMMSS):
  - deepgram_raw.json, deepgram_transcript.txt, deepgram_utterances.json, deepgram_speakerized.txt
  - assemblyai_raw.json, assemblyai_transcript.txt, assemblyai_utterances.json, assemblyai_speakerized.txt
  - summary.txt

Usage:
  export DEEPGRAM_API_KEY=...
  export ASSEMBLYAI_API_KEY=...
  python compare_stt.py /path/to/audio.(wav|mp3|m4a) [--speakers-expected N]

Notes:
- Deepgram model defaults to nova-3 (override via env: DG_MODEL).
- AssemblyAI model uses "universal" (their general model per API reference).
- No artificial wall/idle timeouts; large files are fine (polling for AAI).
"""

import os
import sys
import time
import json
import math
import mimetypes
import pathlib
import argparse
from datetime import datetime
from collections import defaultdict, Counter

import requests

# ------------------------------ Helpers -------------------------------- #

def hms(seconds: float) -> str:
    s = int(round(seconds))
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

def guess_mimetype(path: str) -> str:
    mt = mimetypes.guess_type(path)[0]
    return mt or "application/octet-stream"

def total_duration(utts, provider):
    # Deepgram uses seconds; AssemblyAI uses ms. Normalize to seconds.
    total = 0.0
    for u in utts:
        start, end = u.get("start"), u.get("end")
        if start is None or end is None: 
            continue
        if provider == "assemblyai":
            start, end = start / 1000.0, end / 1000.0
        total += max(0.0, end - start)
    return total

def duration_by_speaker(utts, provider):
    d = defaultdict(float)
    for u in utts:
        spk = u.get("speaker") or u.get("speaker_id") or u.get("speaker_label") or "UNK"
        start, end = u.get("start"), u.get("end")
        if start is None or end is None:
            continue
        if provider == "assemblyai":
            start, end = start / 1000.0, end / 1000.0
        d[str(spk)] += max(0.0, end - start)
    return dict(d)

def pick_top_speakers(utts, provider, topn=4):
    d = duration_by_speaker(utts, provider)
    if not d:
        return set()
    return set([spk for spk, _dur in sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:topn]])

def normalize_utterances(provider, raw):
    """
    Return a list of utterances:
    { "speaker": str, "text": str, "start": float|ms, "end": float|ms }
    provider: "deepgram" or "assemblyai"
    """
    out = []
    if provider == "deepgram":
        # Deepgram: results.utterances is a list with fields: speaker (int), transcript, start, end
        results = raw.get("results", {})
        utts = results.get("utterances") or []
        # Some responses put utterances at top level "utterances"
        if not utts and "utterances" in raw:
            utts = raw["utterances"]
        for u in utts:
            out.append({
                "speaker": str(u.get("speaker", "0")),
                "text": u.get("transcript", "").strip(),
                "start": float(u.get("start", 0.0)),
                "end": float(u.get("end", 0.0)),
            })
        # Fallback if no utterances: single block from overall transcript
        if not out:
            try:
                chan = results["channels"][0]["alternatives"][0]
                txt = chan.get("transcript", "").strip()
            except Exception:
                txt = raw.get("transcript", "").strip()
            if txt:
                out = [{"speaker": "0", "text": txt, "start": 0.0, "end": 0.0}]
        return out

    if provider == "assemblyai":
        # AssemblyAI: transcript has "utterances" if speaker_labels=True
        utts = raw.get("utterances") or []
        for u in utts:
            out.append({
                "speaker": str(u.get("speaker") or u.get("speaker_label") or "A"),
                "text": (u.get("text") or "").strip(),
                "start": int(u.get("start", 0)),  # ms
                "end": int(u.get("end", 0)),      # ms
            })
        if not out:
            # Fallback to full text
            txt = (raw.get("text") or "").strip()
            if txt:
                out = [{"speaker": "A", "text": txt, "start": 0, "end": 0}]
        return out

    return out

def render_speakerized(utts, provider, keep_top=set()):
    """
    Pretty-print with timestamps and up to 4 main speakers.
    Others collapse under 'Other'.
    """
    lines = []
    # Map speakers to friendly labels in descending talk-time order
    durs = duration_by_speaker(utts, provider)
    ordered = [spk for spk, _ in sorted(durs.items(), key=lambda kv: kv[1], reverse=True)]
    label_map = {}
    for i, spk in enumerate(ordered, 1):
        if keep_top and spk not in keep_top:
            label_map[spk] = "Other"
        else:
            label_map[spk] = f"Speaker {i}"

    for u in utts:
        spk = label_map.get(str(u.get("speaker")), "Other")
        if provider == "assemblyai":
            start, end = u["start"]/1000.0, u["end"]/1000.0
        else:
            start, end = u["start"], u["end"]
        tspan = f"[{hms(start)}–{hms(end)}]" if end > start > 0 else ""
        text = u.get("text", "").strip()
        if text:
            lines.append(f"{spk} {tspan}: {text}")
    return "\n".join(lines)

def word_count_from_text(t: str) -> int:
    return len([w for w in t.strip().split() if w])

# ------------------------ Deepgram (nova-3) --------------------------- #

def deepgram_transcribe(path: str, model: str = None):
    """
    POST /v1/listen with file bytes, requesting diarization & utterances.
    Docs (model & diarization):
      - https://developers.deepgram.com/docs/models-and-languages/
      - https://developers.deepgram.com/docs/speaker-diarization/
      - https://developers.deepgram.com/docs/utterances/
    """
    key = os.getenv("DEEPGRAM_API_KEY")
    if not key:
        raise SystemExit("Missing DEEPGRAM_API_KEY")

    model = model or os.getenv("DG_MODEL", "nova-3")  # allow override
    url = "https://api.deepgram.com/v1/listen"
    params = {
        "model": model,
        "smart_format": "true",
        "punctuate": "true",
        "diarize": "true",
        "utterances": "true",
        # You can add "paragraphs": "true" if you want paragraph grouping:
        # "paragraphs": "true",
    }
    mime = guess_mimetype(path)
    headers = {
        "Authorization": f"Token {key}",
        "Content-Type": mime,
        "Accept": "application/json"
    }

    with open(path, "rb") as f:
        data = f.read()

    rsp = requests.post(url, params=params, data=data, headers=headers, timeout=None)
    if rsp.status_code >= 400:
        raise RuntimeError(f"Deepgram error {rsp.status_code}: {rsp.text[:400]}")
    return rsp.json()

# ------------------------ AssemblyAI (universal) ---------------------- #

def aai_upload(filepath: str, key: str) -> str:
    """Upload local file to AssemblyAI and return the upload_url."""
    url = "https://api.assemblyai.com/v2/upload"
    headers = {"authorization": key}
    CHUNK = 5 * 1024 * 1024
    with open(filepath, "rb") as f:
        resp = requests.post(url, headers=headers, data=iter(lambda: f.read(CHUNK), b""), timeout=None)
    if resp.status_code >= 400:
        raise RuntimeError(f"AssemblyAI upload error {resp.status_code}: {resp.text[:400]}")
    return resp.json()["upload_url"]

def assemblyai_transcribe(path: str, speakers_expected: int = None):
    """
    Create a transcript with diarization.
    API reference (speech_model + diarization):
      - https://www.assemblyai.com/docs/api-reference/transcripts/create
    """
    key = os.getenv("ASSEMBLYAI_API_KEY")
    if not key:
        raise SystemExit("Missing ASSEMBLYAI_API_KEY")

    upload_url = aai_upload(path, key)

    create_url = "https://api.assemblyai.com/v2/transcript"
    payload = {
        "audio_url": upload_url,
        "speech_model": "universal",    # allowed: "best" | "slam-1" | "universal"
        "speaker_labels": True,         # enable diarization
        "punctuate": True,
        "format_text": True,
        "disfluencies": True,
        # "language_code": "en",  # optional
    }
    if speakers_expected and int(speakers_expected) > 0:
        payload["speakers_expected"] = int(speakers_expected)

    headers = {"authorization": key, "content-type": "application/json"}
    resp = requests.post(create_url, headers=headers, json=payload, timeout=None)
    if resp.status_code >= 400:
        raise RuntimeError(f"AssemblyAI create error {resp.status_code}: {resp.text[:400]}")

    tid = resp.json()["id"]
    # Poll
    get_url = f"https://api.assemblyai.com/v2/transcript/{tid}"
    while True:
        time.sleep(3.0)
        r = requests.get(get_url, headers=headers, timeout=None)
        if r.status_code >= 400:
            raise RuntimeError(f"AssemblyAI poll error {r.status_code}: {r.text[:400]}")
        j = r.json()
        status = j.get("status")
        if status == "completed":
            return j
        if status == "error":
            raise RuntimeError(f"AssemblyAI failed: {j.get('error')}")
        # else: queued / processing -> continue

# ------------------------------- Main --------------------------------- #

def save_json(path: pathlib.Path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", help="Path to .wav/.m4a/.mp3 etc.")
    ap.add_argument("--speakers-expected", type=int, default=None,
                    help="Hint for diarization (AssemblyAI only).")
    args = ap.parse_args()

    audio_path = pathlib.Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        print(f"❌ Audio not found: {audio_path}")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = pathlib.Path("runs") / f"stt_compare_{ts}"
    ensure_dir(outdir)

    print("=== Deepgram (nova-3) ===")
    try:
        dg_raw = deepgram_transcribe(str(audio_path))
        save_json(outdir / "deepgram_raw.json", dg_raw)

        # Extract plain transcript (best alternative)
        try:
            chan = dg_raw["results"]["channels"][0]["alternatives"][0]
            dg_text = chan.get("transcript", "") or dg_raw.get("transcript", "")
        except Exception:
            dg_text = dg_raw.get("transcript", "") or ""
        (outdir / "deepgram_transcript.txt").write_text(dg_text.strip(), encoding="utf-8")

        dg_utts = normalize_utterances("deepgram", dg_raw)
        save_json(outdir / "deepgram_utterances.json", dg_utts)
        dg_keep = pick_top_speakers(dg_utts, "deepgram", topn=4)
        dg_speakerized = render_speakerized(dg_utts, "deepgram", keep_top=dg_keep)
        (outdir / "deepgram_speakerized.txt").write_text(dg_speakerized, encoding="utf-8")
        print(f"✓ Deepgram done. Utterances: {len(dg_utts)}  |  Text words: {word_count_from_text(dg_text)}")
    except Exception as e:
        print(f"❌ Deepgram failed: {e}")
        dg_raw = {}
        dg_utts = []
        dg_text = ""

    print("\n=== AssemblyAI (universal) ===")
    try:
        aai_raw = assemblyai_transcribe(str(audio_path), speakers_expected=args.speakers_expected)
        save_json(outdir / "assemblyai_raw.json", aai_raw)

        aai_text = (aai_raw.get("text") or "").strip()
        (outdir / "assemblyai_transcript.txt").write_text(aai_text, encoding="utf-8")

        aai_utts = normalize_utterances("assemblyai", aai_raw)
        save_json(outdir / "assemblyai_utterances.json", aai_utts)
        aai_keep = pick_top_speakers(aai_utts, "assemblyai", topn=4)
        aai_speakerized = render_speakerized(aai_utts, "assemblyai", keep_top=aai_keep)
        (outdir / "assemblyai_speakerized.txt").write_text(aai_speakerized, encoding="utf-8")
        print(f"✓ AssemblyAI done. Utterances: {len(aai_utts)}  |  Text words: {word_count_from_text(aai_text)}")
    except Exception as e:
        print(f"❌ AssemblyAI failed: {e}")
        aai_raw = {}
        aai_utts = []
        aai_text = ""

    # Quick side-by-side summary
    dg_total = total_duration(dg_utts, "deepgram")
    aai_total = total_duration(aai_utts, "assemblyai")
    dg_spk = len(set(u.get("speaker") for u in dg_utts)) if dg_utts else 0
    aai_spk = len(set(u.get("speaker") for u in aai_utts)) if aai_utts else 0

    summary_lines = [
        "=== Summary ===",
        f"Audio: {audio_path.name}",
        "",
        "[Deepgram]",
        f"  Speakers detected: {dg_spk}",
        f"  Total speech (s): {dg_total:.1f} ({hms(dg_total)})",
        f"  Word count (approx): {word_count_from_text(dg_text)}",
        "",
        "[AssemblyAI]",
        f"  Speakers detected: {aai_spk}",
        f"  Total speech (s): {aai_total:.1f} ({hms(aai_total)})",
        f"  Word count (approx): {word_count_from_text(aai_text)}",
        "",
        "Files written:",
        f"  {outdir}/deepgram_transcript.txt",
        f"  {outdir}/deepgram_speakerized.txt",
        f"  {outdir}/assemblyai_transcript.txt",
        f"  {outdir}/assemblyai_speakerized.txt",
        f"  (raw JSON + utterances JSON in same folder)",
    ]
    (outdir / "summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")
    print("\n".join(summary_lines))

if __name__ == "__main__":
    main()
