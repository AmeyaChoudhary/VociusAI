#!/usr/bin/env python3
"""
AnalyzeSpeech.py
=================
Debate speech analyser for Public Forum debates.

What's new:
- Hard-require --hf-token (no interactive prompts).
- Clear, early failure if the HuggingFace token lacks access to gated pyannote models,
  with helpful links.
- Writes delivery_metrics.json alongside analyze_speech.txt.

Requirements
------------
numpy, librosa, soundfile, praat-parselmouth, pyannote.audio, torch, ffmpeg.
Provide HuggingFace token via --hf-token (or HUGGINGFACE_TOKEN env).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

# Required packages
try:
    import librosa  # type: ignore
except ImportError as e:
    raise SystemExit(f"librosa is required but not installed: {e}")
try:
    import soundfile as sf  # type: ignore
except ImportError as e:
    raise SystemExit(f"soundfile is required but not installed: {e}")
try:
    import parselmouth  # type: ignore
except ImportError as e:
    raise SystemExit(f"praat-parselmouth is required but not installed: {e}")
try:
    import torch  # type: ignore
except ImportError as e:
    raise SystemExit(f"PyTorch is required but not installed: {e}")
try:
    from pyannote.audio import Pipeline  # type: ignore
except ImportError as e:
    raise SystemExit(
        "pyannote.audio is required but not installed: {}.\n"
        "Install with: pip install pyannote.audio".format(e)
    )

from concurrent.futures import ProcessPoolExecutor


# ----------------------------- Configuration ---------------------------------

DIARIZATION_MODEL = "pyannote/speaker-diarization-3.0"

# Durations (seconds)
MIN_TURN_LENGTH = 15.0
MIN_MERGED_LENGTH = 60.0

# Selection
NUM_TOP_SPEAKERS = 4
NUM_SEGMENTS_PER_SPEAKER = 2

# Audio
SAMPLE_RATE = 16_000

# Silence-removal parameters
FRAME_LENGTH = 2048
HOP_LENGTH = 512
SILENCE_DB_THRESHOLD = -35.0  # dB below peak; absolute is used (35)
MIN_SILENCE_SEC = 0.1         # merge gaps shorter than this


# --------------------------- Helper structures --------------------------------

@dataclass
class Segment:
    speaker: str
    start: float  # seconds
    end: float    # seconds

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> Dict[str, float | str]:
        return {"speaker": self.speaker, "start": self.start, "end": self.end}


@dataclass
class Metrics:
    speaker: str
    start: float
    end: float
    mean_db: float
    dynamic_range: float
    pitch_var: float
    centroid_var: float
    avg_pause: float
    expressiveness: str
    passion: str
    speed: str

    def to_dict(self) -> Dict[str, float | str]:
        return {
            "speaker": self.speaker,
            "start": self.start,
            "end": self.end,
            "mean_db": self.mean_db,
            "dynamic_range": self.dynamic_range,
            "pitch_var": self.pitch_var,
            "centroid_var": self.centroid_var,
            "avg_pause": self.avg_pause,
            "expressiveness": self.expressiveness,
            "passion": self.passion,
            "speed": self.speed,
        }


# ------------------------------- Utilities ------------------------------------

def hhmmss(seconds: float) -> str:
    seconds = int(round(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


def run_ffmpeg(cmd: List[str]) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(e.stderr.decode(errors="ignore"))
        raise


def ensure_16k_wav(path: Path) -> Path:
    """
    Always produce a 16 kHz, mono WAV.
    If input is .m4a, write `<stem>_16k.wav`; otherwise overwrite the .wav name.
    """
    out = path.with_suffix('.wav') if path.suffix.lower() != '.m4a' else path.with_name(f"{path.stem}_16k.wav")
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", str(path),
        "-ar", str(SAMPLE_RATE),
        "-ac", "1",
        "-y", str(out)
    ]
    run_ffmpeg(cmd)
    return out


def trim_all_silence(
    input_path: Path,
    output_path: Path,
    silence_thresh_db: float = SILENCE_DB_THRESHOLD,
    min_silence_sec: float = MIN_SILENCE_SEC
) -> Path:
    """
    Aggressively trim ALL silence, including short mid-sentence pauses.
    Merges gaps shorter than `min_silence_sec`. Returns the output path,
    or the original path if no voiced segments were found.
    """
    y, sr = librosa.load(str(input_path), sr=SAMPLE_RATE, mono=True)

    intervals = librosa.effects.split(
        y,
        top_db=abs(silence_thresh_db),
        frame_length=FRAME_LENGTH,
        hop_length=HOP_LENGTH
    )

    min_samples = int(min_silence_sec * sr)
    merged: List[List[int]] = []
    for i, (start, end) in enumerate(intervals):
        if i > 0 and start - merged[-1][1] < min_samples:
            merged[-1][1] = end
        else:
            merged.append([start, end])

    if not merged:
        print("⚠️ No voiced segments found.", flush=True)
        return input_path

    trimmed = np.concatenate([y[s:e] for s, e in merged])
    sf.write(str(output_path), trimmed, sr)
    return output_path


# --------------------------- pyannote loading ---------------------------------

def load_pipeline(token: str):
    """
    Loads the gated diarization model with a friendly error if token lacks access.
    """
    from functools import lru_cache

    @lru_cache(maxsize=1)
    def _load(token_: str):
        try:
            pipeline = Pipeline.from_pretrained(DIARIZATION_MODEL, use_auth_token=token_)
        except Exception as e:
            tip = (
                "Your Hugging Face token likely lacks access to the **gated** pyannote models.\n"
                "Grant access here (both recommended):\n"
                " • https://huggingface.co/pyannote/speaker-diarization-3.0\n"
                " • https://huggingface.co/pyannote/voice-activity-detection\n"
                "Then set HUGGINGFACE_TOKEN (or pass --hf-token) and retry."
            )
            raise SystemExit(f"❌ Failed to load {DIARIZATION_MODEL}: {e}\n{tip}")
        pipeline.to(torch.device("cpu"))
        return pipeline

    return _load(token)


def diarize_audio(wav_path: Path, hf_token: str) -> List[Segment]:
    pipeline = load_pipeline(hf_token)
    diarization = pipeline({"audio": str(wav_path)})
    segments: List[Segment] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(Segment(speaker=speaker, start=float(turn.start), end=float(turn.end)))
    return segments


def merge_adjacent_segments(segments: Iterable[Segment], max_gap: float = 0.1) -> List[Segment]:
    merged: List[Segment] = []
    for seg in segments:
        if not merged:
            merged.append(Segment(speaker=seg.speaker, start=seg.start, end=seg.end))
            continue
        last = merged[-1]
        if seg.speaker == last.speaker and seg.start - last.end <= max_gap:
            last.end = max(last.end, seg.end)
        else:
            merged.append(Segment(speaker=seg.speaker, start=seg.start, end=seg.end))
    return merged


def drop_short_segments(segments: Iterable[Segment], threshold: float) -> List[Segment]:
    return [s for s in segments if s.duration >= threshold]


def select_top_speakers(segments: Iterable[Segment], num_speakers: int = NUM_TOP_SPEAKERS) -> List[str]:
    totals: Dict[str, float] = defaultdict(float)
    for seg in segments:
        totals[seg.speaker] += seg.duration
    sorted_speakers = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return [sp for sp, _ in sorted_speakers[:num_speakers]]


def select_longest_segments(
    segments: Iterable[Segment],
    allowed_speakers: List[str],
    k: int = NUM_SEGMENTS_PER_SPEAKER
) -> List[Segment]:
    by_sp: Dict[str, List[Segment]] = defaultdict(list)
    for seg in segments:
        if seg.speaker in allowed_speakers:
            by_sp[seg.speaker].append(seg)
    selected: List[Segment] = []
    for sp, segs in by_sp.items():
        segs_sorted = sorted(segs, key=lambda s: s.duration, reverse=True)
        selected.extend(segs_sorted[:k])
    return sorted(selected, key=lambda s: s.start)


def extract_clips(src_wav: Path, segments: Iterable[Segment], output_dir: Path) -> List[Tuple[Path, Segment]]:
    clips: List[Tuple[Path, Segment]] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for seg in segments:
        sp_safe = seg.speaker.replace("/", "_").replace(" ", "_")
        start_ms = int(seg.start * 1000)
        end_ms = int(seg.end * 1000)
        clip_name = f"{sp_safe}_{start_ms}_{end_ms}.wav"
        clip_path = output_dir / clip_name
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(src_wav),
            "-ss", f"{seg.start}",
            "-to", f"{seg.end}",
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            "-y",
            str(clip_path),
        ]
        run_ffmpeg(cmd)
        clips.append((clip_path, seg))
    return clips


# ----------------------------- Acoustic analysis ------------------------------

def analyse_segment(job: Tuple[Path, Segment]) -> Metrics:
    clip_path, seg = job
    y, sr = librosa.load(str(clip_path), sr=SAMPLE_RATE, mono=True)
    total_duration = seg.duration

    frame_length = 2048
    hop_length = 512
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    db = 20.0 * np.log10(rms + 1e-6)
    mean_db = float(np.mean(db))

    if len(db) > 0:
        lo, hi = np.percentile(db, [10, 90])
        dynamic_range = float(hi - lo)
    else:
        dynamic_range = 0.0

    try:
        sound = parselmouth.Sound(str(clip_path))
        pitch = sound.to_pitch()
        f0 = pitch.selected_array['frequency']
        f0 = f0[f0 > 0]
        pitch_var = float(np.var(f0)) if f0.size > 0 else 0.0
    except Exception:
        pitch_var = 0.0

    centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    centroid_var = float(np.var(centroids)) if centroids.size > 0 else 0.0

    intervals = librosa.effects.split(y, top_db=25)
    speech_samples = sum((end - start) for start, end in intervals)
    speech_duration = speech_samples / sr
    num_pauses = max(len(intervals) - 1, 1)
    avg_pause = float(max(total_duration - speech_duration, 0.0) / num_pauses)
    speech_ratio = speech_duration / total_duration if total_duration > 0 else 0.0

    if centroid_var > 5e6:
        expressiveness = "expressive"
    elif centroid_var > 2e6:
        expressiveness = "neutral"
    else:
        expressiveness = "monotone"

    if dynamic_range > 10.0:
        passion = "passionate"
    elif dynamic_range > 4.0:
        passion = "balanced"
    else:
        passion = "subdued"

    if speech_ratio > 0.85:
        speed = "very fast"
    elif speech_ratio > 0.6:
        speed = "fast"
    elif speech_ratio > 0.4:
        speed = "moderate"
    else:
        speed = "slow"

    return Metrics(
        speaker=seg.speaker,
        start=seg.start,
        end=seg.end,
        mean_db=round(mean_db, 1),
        dynamic_range=round(dynamic_range, 1),
        pitch_var=round(pitch_var, 1),
        centroid_var=round(centroid_var, 0),
        avg_pause=round(avg_pause, 2),
        expressiveness=expressiveness,
        passion=passion,
        speed=speed,
    )


# ----------------------------- Feedback generation ----------------------------

def generate_tip(metrics: Metrics) -> str:
    tips: List[str] = []
    if metrics.expressiveness == "monotone":
        tips.append("Vary your tone between arguments to keep the judge engaged.")
    elif metrics.expressiveness == "neutral":
        tips.append("Use a bit more vocal variety to emphasise key points.")
    if metrics.passion == "subdued":
        tips.append("Project more confidence and energy to convey conviction.")
    if metrics.speed in {"very fast", "fast"}:
        tips.append("Slow down and insert short pauses after important claims.")
    elif metrics.speed == "slow":
        tips.append("Pick up the pace slightly to maintain momentum.")
    if metrics.avg_pause < 0.2:
        tips.append("Introduce brief pauses to separate ideas and aid clarity.")
    return tips[0] if tips else "Maintain your current delivery while emphasising key points."


# --------------------------- Orchestration pipeline ---------------------------

def process_debate(
    input_audio: Path,
    hf_token: str,
    team1_label: str,
    team2_label: str,
    first_team: str,
    work_dir: Path
) -> None:
    start_time = time.time()
    work_dir.mkdir(parents=True, exist_ok=True)

    # Remove stale report at start
    report_path = work_dir / "analyze_speech.txt"
    if report_path.exists():
        try: report_path.unlink()
        except Exception: pass

    # Step 1: Convert to 16 kHz mono WAV
    print("[1/7] Converting input to 16 kHz mono WAV…", flush=True)
    wav_path = ensure_16k_wav(input_audio)

    # Step 2: Trim silence (aggressive)
    print("[2/7] Trimming silence…", flush=True)
    trimmed_path = wav_path.with_name(f"{wav_path.stem}_trim.wav")
    trimmed_path = trim_all_silence(wav_path, trimmed_path)
    print(f"     Trimmed file saved as {Path(trimmed_path).name}", flush=True)

    # Step 3: Diarize (gated model)
    print("[3/7] Performing speaker diarization… this may take a while", flush=True)
    diar_segments = diarize_audio(trimmed_path, hf_token)
    diar_segments.sort(key=lambda s: s.start)

    segments_json = work_dir / "segments.json"
    with open(segments_json, "w") as f:
        json.dump([seg.to_dict() for seg in diar_segments], f, indent=2)
    print(f"     Raw segments saved to {segments_json.name}", flush=True)

    diar_segments = drop_short_segments(diar_segments, MIN_TURN_LENGTH)

    # Step 4: Merge adjacent segments and drop short ones
    merged_segments = merge_adjacent_segments(diar_segments)
    merged_segments = drop_short_segments(merged_segments, MIN_MERGED_LENGTH)
    merged_json = work_dir / "merged_segments.json"
    with open(merged_json, "w") as f:
        json.dump([seg.to_dict() for seg in merged_segments], f, indent=2)
    print(f"     Merged segments saved to {merged_json.name}", flush=True)

    if not merged_segments:
        print("No merged segments of sufficient length found. Exiting.", flush=True)
        with open(report_path, "w", encoding="utf-8") as report:
            report.write("No merged segments ≥60s found after diarization and trimming.\n"
                         "Try a longer recording or reduce MIN_MERGED_LENGTH.")
        return

    # Step 5: Select top speakers and longest segments
    top_speakers = select_top_speakers(merged_segments, NUM_TOP_SPEAKERS)
    selected_segments = select_longest_segments(merged_segments, top_speakers, NUM_SEGMENTS_PER_SPEAKER)
    selected_json = work_dir / "selected.json"
    with open(selected_json, "w") as f:
        json.dump([seg.to_dict() for seg in selected_segments], f, indent=2)
    print(f"     Selected segments saved to {selected_json.name}", flush=True)

    # Step 6: Role mapping by first appearance
    appearance: List[str] = []
    for seg in selected_segments:
        if seg.speaker not in appearance:
            appearance.append(seg.speaker)
        if len(appearance) >= 4:
            break
    if first_team.lower() == team1_label.lower():
        role_order = [f"{team1_label} 1st Speaker", f"{team2_label} 1st Speaker",
                      f"{team1_label} 2nd Speaker", f"{team2_label} 2nd Speaker"]
    else:
        role_order = [f"{team2_label} 1st Speaker", f"{team1_label} 1st Speaker",
                      f"{team2_label} 2nd Speaker", f"{team1_label} 2nd Speaker"]
    role_map: Dict[str, str] = {sp: role_order[i] for i, sp in enumerate(appearance) if i < len(role_order)}

    # Step 7: Extract clips and analyse
    clips_dir = work_dir / "clips"
    clip_jobs = extract_clips(trimmed_path, selected_segments, clips_dir)

    print("[4/7] Analysing selected segments…", flush=True)
    with ProcessPoolExecutor() as pool:
        metrics_list = list(pool.map(analyse_segment, clip_jobs))

    # Write delivery_metrics.json for the GUI
    metrics_path = work_dir / "delivery_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as jf:
        json.dump([m.to_dict() for m in metrics_list], jf, indent=2)
    print(f"     Metrics saved to {metrics_path.name}", flush=True)

    # Group by speaker and write human-readable report
    grouped: Dict[str, List[Metrics]] = defaultdict(list)
    for m in metrics_list:
        grouped[m.speaker].append(m)

    with open(report_path, "w", encoding="utf-8") as report:
        for sp, mlist in grouped.items():
            role = role_map.get(sp, sp)
            times = [f"{hhmmss(m.start)}–{hhmmss(m.end)}" for m in mlist]
            mean_db = np.mean([m.mean_db for m in mlist])
            dyn_range = np.mean([m.dynamic_range for m in mlist])
            pitch_var = np.mean([m.pitch_var for m in mlist])
            cent_var = np.mean([m.centroid_var for m in mlist])
            avg_pause = np.mean([m.avg_pause for m in mlist])
            longest = max(mlist, key=lambda m: m.end - m.start)
            express = longest.expressiveness
            passion = longest.passion
            speed = longest.speed
            tip = generate_tip(longest)
            header = f"== {role} Speeches: (" + ", ".join(times) + ") =="
            report.write(header + "\n")
            report.write(f" • Delivery: {express}, {passion}, {speed}\n")
            report.write(f" • Loudness: {mean_db:.1f} dBFS (range {dyn_range:.1f} dB)\n")
            report.write(f" • Pitch var: {pitch_var:.1f} | Centroid var: {cent_var:.1f}\n")
            report.write(f" • Average pause: {avg_pause:.2f} s\n")
            report.write(f" • Tip: {tip}\n\n")

    print(f"\nReport written to {report_path}", flush=True)
    elapsed = time.time() - start_time
    print(f"Finished processing in {elapsed:.1f} seconds.", flush=True)


# ---------------------------------- CLI --------------------------------------

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyse a Public Forum debate recording and generate delivery feedback.")
    parser.add_argument("audio", type=str, help="Path to debate recording (.m4a or .wav)")
    parser.add_argument("--team1", type=str, default="Aff", help="Label of the first team (default: Aff)")
    parser.add_argument("--team2", type=str, default="Neg", help="Label of the second team (default: Neg)")
    parser.add_argument("--first", type=str, choices=["Aff", "Neg"], required=True,
                        help="Which team speaks first (Aff or Neg).")
    parser.add_argument("--work-dir", type=str, default=".",
                        help="Directory to store intermediate and output files (default: current directory)")

    # GUI/automation friendly: no interactive prompts; token is required.
    parser.add_argument("--hf-token", type=str, required=True,
                        help="Hugging Face token (must have access to pyannote diarization).")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    input_audio = Path(args.audio).expanduser().resolve()
    if not input_audio.exists():
        raise SystemExit(f"Input file not found: {input_audio}")

    hf_token = args.hf_token or os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        raise SystemExit("❌ A HuggingFace token is required (--hf-token).")

    team1 = (args.team1 or "Aff").strip() or "Aff"
    team2 = (args.team2 or "Neg").strip() or "Neg"
    first_team = args.first

    work_dir = Path(args.work_dir).expanduser().resolve()

    process_debate(
        input_audio=input_audio,
        hf_token=hf_token,
        team1_label=team1,
        team2_label=team2,
        first_team=first_team,
        work_dir=work_dir
    )


if __name__ == "__main__":
    main()
