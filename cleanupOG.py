#!/usr/bin/env python3
from pathlib import Path
import argparse
import subprocess
import numpy as np
import soundfile as sf
import librosa

SAMPLE_RATE = 16000

def ensure_16k_mono_wav(src: Path) -> Path:
    """Convert any audio file → 16 kHz mono WAV (only when needed)."""
    if src.suffix.lower() in {".wav", ".wave"}:
        # still normalize sr/channels to be safe
        out = src.with_name(f"{src.stem}_16k.wav")
    else:
        out = src.with_name(f"{src.stem}_16k.wav")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", str(src), "-ar", str(SAMPLE_RATE), "-ac", "1", "-y", str(out)
    ], check=True)
    return out

def trim_silence_auto(path: Path, out_path: Path,
                      frame_ms: int = 25,
                      hop_ms: int = 10,
                      rel_drop_db: float = 35.0,
                      min_pause: float = 0.20) -> Path:
    """
    OG energy-based, percentile-referenced trimmer.

    • Computes frame RMS (in dB), finds a dynamic threshold:
        threshold = 95th_percentile(db) - rel_drop_db
    • Keeps frames above threshold.
    • Merges across pauses shorter than `min_pause` seconds.
    • Adds implicit end-padding via (+win) when mapping frames→samples.
    """
    y, sr = librosa.load(str(path), sr=SAMPLE_RATE, mono=True)
    hop = int(sr * hop_ms / 1000.0)
    win = int(sr * frame_ms / 1000.0)

    # Frame-wise RMS → dB
    rms = librosa.feature.rms(y=y, frame_length=win, hop_length=hop)[0]
    db = 20.0 * np.log10(rms + 1e-10)

    # Dynamic threshold anchored at 95th percentile (robust vs loud peaks)
    speech_floor = np.percentile(db, 95) - rel_drop_db
    mask = db > speech_floor

    # If nothing trimmed, return original
    if mask.sum() == len(mask):
        return path

    # Collect contiguous runs of "speech" frames
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return path
    segments = []
    start = idx[0]
    for i in range(1, len(idx)):
        if idx[i] != idx[i - 1] + 1:
            segments.append((start, idx[i - 1]))
            start = idx[i]
    segments.append((start, idx[-1]))

    # Merge across very short pauses, and map frames→samples
    chunks = []
    last_end = None
    pause_samples = int(min_pause * sr)
    for fs, fe in segments:
        s = fs * hop
        e = min(len(y), fe * hop + win)  # include window tail
        if last_end is None or s - last_end > pause_samples:
            chunks.append(y[s:e])
        else:
            # bridge the short pause by including it
            chunks[-1] = np.concatenate([chunks[-1], y[last_end:s], y[s:e]])
        last_end = e

    y_out = np.concatenate(chunks) if chunks else y
    sf.write(str(out_path), y_out, sr)
    return out_path

def main():
    ap = argparse.ArgumentParser(description="OG percentile-based silence trimmer (AnalyzeSpeech original).")
    ap.add_argument("input", type=str, help="Input audio (.m4a/.wav)")
    ap.add_argument("output", type=str, help="Output WAV path")
    ap.add_argument("--rel-drop-db", type=float, default=35.0, help="Higher = gentler; lower = harsher")
    ap.add_argument("--min-pause", type=float, default=0.20, help="Merge across pauses < this (seconds)")
    ap.add_argument("--frame-ms", type=int, default=25, help="RMS frame length (ms)")
    ap.add_argument("--hop-ms", type=int, default=10, help="RMS hop length (ms)")
    args = ap.parse_args()

    in_path = ensure_16k_mono_wav(Path(args.input))
    out_path = Path(args.output)

    # show before/after durations for quick sanity check
    try:
        y0, sr0 = sf.read(str(in_path))
        dur0 = len(y0) / sr0
    except Exception:
        dur0 = None

    trimmed = trim_silence_auto(
        in_path, out_path,
        frame_ms=args.frame_ms,
        hop_ms=args.hop_ms,
        rel_drop_db=args.rel_drop_db,
        min_pause=args.min_pause
    )

    try:
        y1, sr1 = sf.read(str(trimmed))
        dur1 = len(y1) / sr1
    except Exception:
        dur1 = None

    if dur0 is not None and dur1 is not None:
        print(f"✅ Trimmed audio saved to {trimmed}  (before: {dur0:.1f}s → after: {dur1:.1f}s)")
    else:
        print(f"✅ Trimmed audio saved to {trimmed}")

if __name__ == "__main__":
    main()