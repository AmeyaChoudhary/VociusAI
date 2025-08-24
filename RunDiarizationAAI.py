#!/usr/bin/env python3
"""
RunDiarizationAAI.py
────────────────────
Helper for AnalyzeSpeechV2.py.

• Converts any input to 16 kHz mono WAV.
• Uploads the WAV as a raw binary stream (AssemblyAI’s preferred method).
• Waits until diarization is finished.
• Writes a minimal “segments-only” JSON compatible with AnalyzeSpeechV2.

Usage
-----
python RunDiarizationAAI.py audio.m4a \
       --out diarization.json \
       --aai-key YOUR_ASSEMBLYAI_KEY \
       [--max-speakers 4]
"""

from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

AAI_UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
AAI_TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"
SAMPLE_RATE = 16_000  # Hz


# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────
def ensure_16k_wav(src: Path) -> Path:
    """Return a 16 kHz mono WAV version of *src* (in-place if already suitable)."""
    wav_path = src.with_suffix(".wav") if src.suffix.lower() != ".wav" else src
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-ar",
        str(SAMPLE_RATE),
        "-ac",
        "1",
        "-y",
        str(wav_path),
    ]
    subprocess.run(cmd, check=True)
    return wav_path


def upload_audio(wav_path: Path, api_key: str) -> str:
    """Upload WAV as raw bytes, return AssemblyAI upload URL."""
    with wav_path.open("rb") as f:
        r = requests.post(
            AAI_UPLOAD_URL,
            headers={
                "authorization": api_key,
                "content-type": "application/octet-stream",
            },
            data=f,
            timeout=120,
        )
    r.raise_for_status()
    return r.json()["upload_url"]


def start_transcript(audio_url: str, api_key: str, speakers: int) -> str:
    payload = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "speakers_expected": speakers,
    }
    r = requests.post(
        AAI_TRANSCRIPT_URL, json=payload, headers={"authorization": api_key}, timeout=30
    )
    r.raise_for_status()
    return r.json()["id"]


def wait_for_done(job_id: str, api_key: str) -> dict:
    url = f"{AAI_TRANSCRIPT_URL}/{job_id}"
    while True:
        r = requests.get(url, headers={"authorization": api_key}, timeout=30)
        r.raise_for_status()
        js = r.json()
        if js["status"] in ("completed", "error"):
            return js
        time.sleep(4)


def normalise_speaker(raw) -> str:
    """Return SPEAKER_XX style label, regardless of int/str input."""
    if isinstance(raw, int):
        return f"SPEAKER_{raw:02d}"
    s = str(raw).strip()
    if s.upper().startswith("SPEAKER_"):
        return s.upper()
    return f"SPEAKER_{s.zfill(2)}" if s.isdigit() else s


# ────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────
def main() -> None:
    pa = argparse.ArgumentParser()
    pa.add_argument("audio", help="Input audio file (.m4a/.wav/.mp3 …)")
    pa.add_argument("--out", required=True, help="Path to write diarization JSON")
    pa.add_argument("--aai-key", required=True, help="AssemblyAI API key")
    pa.add_argument("--max-speakers", type=int, default=4)
    args = pa.parse_args()

    src = Path(args.audio).expanduser().resolve()
    wav = ensure_16k_wav(src)

    print(f"🆙  Uploading {wav.name} to AssemblyAI…", flush=True)
    audio_url = upload_audio(wav, args.aai_key)

    print("🚀  Starting diarization job…", flush=True)
    job_id = start_transcript(audio_url, args.aai_key, args.max_speakers)

    print("⏳  Waiting for AssemblyAI to finish (this can take a few mins)…", flush=True)
    result = wait_for_done(job_id, args.aai_key)
    if result["status"] != "completed":
        sys.exit(f"AssemblyAI error: {result.get('error')}")

    # Build segments-only JSON expected by AnalyzeSpeechV2
    segments = []
    for utt in result.get("utterances", []):
        segments.append(
            {
                "speaker": normalise_speaker(utt["speaker"]),
                "start": utt["start"] / 1000.0,
                "end": utt["end"] / 1000.0,
            }
        )

    out_path = Path(args.out).expanduser().resolve()
    out_path.write_text(json.dumps({"segments": segments}, indent=2))
    print(f"✅  Wrote diarization JSON → {out_path}")


if __name__ == "__main__":
    main()
