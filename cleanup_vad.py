from pathlib import Path
import argparse
import subprocess
import numpy as np
import soundfile as sf
import librosa

SAMPLE_RATE = 16000
FRAME_LENGTH = 2048
HOP_LENGTH = 512
SILENCE_DB_THRESHOLD = -35  # dBFS threshold
MIN_SILENCE_SEC = 0.1


def ensure_16k_wav(path: Path) -> Path:
    out = path.with_suffix('.wav') if path.suffix != '.m4a' else path.with_name(f"{path.stem}_16k.wav")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", str(path),
        "-ar", str(SAMPLE_RATE),
        "-ac", "1",
        "-y", str(out)
    ], check=True)
    return out


def trim_all_silence(input_path: Path, output_path: Path,
                     silence_thresh_db: float = SILENCE_DB_THRESHOLD,
                     min_silence_sec: float = MIN_SILENCE_SEC):
    y, sr = librosa.load(str(input_path), sr=SAMPLE_RATE)

    # Find non-silent intervals
    intervals = librosa.effects.split(y, top_db=abs(silence_thresh_db),
                                      frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH)

    # Filter out tiny silent gaps
    min_samples = int(min_silence_sec * sr)
    merged = []
    for i, (start, end) in enumerate(intervals):
        if i > 0 and start - merged[-1][1] < min_samples:
            merged[-1][1] = end  # merge across short silence
        else:
            merged.append([start, end])

    if not merged:
        print("⚠️ No voiced segments found.")
        return input_path

    trimmed = np.concatenate([y[s:e] for s, e in merged])
    sf.write(str(output_path), trimmed, sr)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trim ALL silence aggressively, including mid-sentence pauses.")
    parser.add_argument("input", type=str, help="Input audio file (.m4a/.wav)")
    parser.add_argument("output", type=str, help="Output WAV path")
    args = parser.parse_args()

    raw_wav = ensure_16k_wav(Path(args.input))
    trimmed = trim_all_silence(raw_wav, Path(args.output))
    print(f"✅ Trimmed audio saved to {trimmed}")
