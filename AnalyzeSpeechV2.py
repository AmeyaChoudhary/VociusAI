#!/usr/bin/env python3
"""
AnalyzeSpeechV2.py  —  v5 (AAI diarization fallback, GUI-safe)
=============================================================

Delivery analysis for Public-Forum debates from **audio only**.

Changes from v4
---------------
• --diarization-json is **optional**. If the flag is missing we run
  AssemblyAI diarization automatically, then continue.
• New --aai-key flag so a GUI can pass the user’s AssemblyAI key.
• Metric logic, heuristics, and report format are otherwise identical.

Dependencies
------------
• ffmpeg in PATH
• Python pkgs: numpy, librosa, (optional) parselmouth
"""

from __future__ import annotations
import argparse, json, math, subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np, librosa
try:
    import parselmouth      # optional
except Exception:
    parselmouth = None

SAMPLE_RATE   = 16_000
FRAME_LENGTH  = 2048
HOP_LENGTH    = 512


# ───────────────────────────────────────────────────────────────────────────────
# Helper — run diarization when JSON not supplied, testing comment
# ───────────────────────────────────────────────────────────────────────────────
def run_diarization(audio: Path, work_dir: Path,
                    aai_key: str, max_speakers: int) -> Path:
    """
    Calls an external AssemblyAI diarization helper and returns the JSON path.
    Adjust the command below if your helper script differs.
    """
    diar_path = work_dir / "diarization.json"
    cmd = [
        "python", "-u", "RunDiarizationAAI.py",       # ← change if needed
        str(audio),
        "--out", str(diar_path),
        "--max-speakers", str(max_speakers)
    ]
    if aai_key:
        cmd += ["--aai-key", aai_key]
    subprocess.check_call(cmd)
    if not diar_path.exists():
        raise RuntimeError("Diarization failed — JSON not created.")
    return diar_path


# ───────────────────────────────────────────────────────────────────────────────
# Data structures
# ───────────────────────────────────────────────────────────────────────────────
@dataclass
class Segment:
    start: float
    end:   float
    def duration(self) -> float: return max(0.0, self.end - self.start)


# ───────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ───────────────────────────────────────────────────────────────────────────────
def log(msg: str) -> None: print(msg, flush=True)

def ensure_16k_wav(src: Path) -> Path:
    """Convert to 16 kHz mono WAV without altering duration."""
    out = src.with_suffix(".wav") if src.suffix.lower() != ".wav" else src
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error",
         "-i", str(src), "-ar", str(SAMPLE_RATE), "-ac", "1", "-y", str(out)],
        check=True
    )
    return out

def load_audio(wav: Path) -> Tuple[np.ndarray, int]:
    y, sr = librosa.load(str(wav), sr=SAMPLE_RATE, mono=True)
    return np.clip(y, -1.0, 1.0), sr

def fmt_hms(t: float) -> str:
    t = max(0, int(round(t)))
    h, m, s = t//3600, (t%3600)//60, t%60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def fmt_ranges(r: List[Segment]) -> str:
    return ", ".join(f"{fmt_hms(s.start)}–{fmt_hms(s.end)}" for s in r)


# ───────────────────────────────────────────────────────────────────────────────
# Parse Assembly-AI JSON
# ───────────────────────────────────────────────────────────────────────────────
def parse_aai_json(path: Path) -> Dict[str, List[Segment]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    speakers: Dict[str, List[Segment]] = defaultdict(list)

    def norm(tag) -> str:
        if isinstance(tag, int): return f"SPEAKER_{tag:02d}"
        return str(tag or "SPEAKER_00")

    if isinstance(data, dict) and isinstance(data.get("utterances"), list):
        for u in data["utterances"]:
            spk = norm(u.get("speaker"))
            start, end = u.get("start", 0), u.get("end", 0)
            if end > 1000: start, end = float(start)/1000, float(end)/1000
            if end > start: speakers[spk].append(Segment(float(start), float(end)))

    elif isinstance(data, dict) and isinstance(data.get("segments"), list):
        for s in data["segments"]:
            spk   = norm(s.get("speaker") or s.get("speaker_label"))
            start = float(s.get("start", 0)); end = float(s.get("end", 0))
            if end > start: speakers[spk].append(Segment(start, end))
    else:
        raise ValueError("Unrecognized diarization JSON structure.")

    for k in speakers: speakers[k].sort(key=lambda s: s.start)
    return speakers


# ───────────────────────────────────────────────────────────────────────────────
# Metrics helpers
# ───────────────────────────────────────────────────────────────────────────────
def samples_for_segments(y: np.ndarray, sr: int, segs: List[Segment]) -> np.ndarray:
    parts, n = [], len(y)
    for s in segs:
        i0, i1 = max(0, int(s.start*sr)), min(n, int(s.end*sr))
        if i1 > i0: parts.append(y[i0:i1])
    return np.concatenate(parts) if parts else np.zeros(1, dtype=np.float32)

def loudness_dbfs(y: np.ndarray) -> Tuple[float, float]:
    if y.size == 0: return float("-inf"), 0.0
    rms = librosa.feature.rms(y=y, frame_length=FRAME_LENGTH,
                              hop_length=HOP_LENGTH, center=True)[0]
    db  = 20*np.log10(np.maximum(rms, 1e-9))
    return float(np.mean(db)), float(np.max(db)-np.min(db)) if db.size else 0.0

def pitch_var(y: np.ndarray, sr: int) -> float:
    if parselmouth is None or y.size == 0: return float("nan")
    snd = parselmouth.Sound(y, sampling_frequency=sr)
    vals = snd.to_pitch(0.01, 75, 500).selected_array['frequency']
    vals = vals[np.isfinite(vals) & (vals > 0)]
    return float(np.var(vals)) if vals.size else float("nan")

def centroid_var(y: np.ndarray, sr: int) -> float:
    if y.size == 0: return float("nan")
    cent = librosa.feature.spectral_centroid(y=y, sr=sr,
                                             hop_length=HOP_LENGTH, n_fft=FRAME_LENGTH)
    v = cent.flatten(); v = v[np.isfinite(v)]
    return float(np.var(v)) if v.size else float("nan")

def avg_pause(segs: List[Segment]) -> float:
    if len(segs) < 2: return 0.0
    gaps = [b.start-a.end for a,b in zip(segs[:-1], segs[1:]) if b.start > a.end]
    return float(np.mean(gaps)) if gaps else 0.0


# ───────────────────────────────────────────────────────────────────────────────
# Speaker/segment helpers
# ───────────────────────────────────────────────────────────────────────────────
def total_time(segs: List[Segment]) -> float: return sum(s.duration() for s in segs)

def top_speakers(spk: Dict[str, List[Segment]], k:int) -> List[str]:
    return sorted(spk, key=lambda s: total_time(spk[s]), reverse=True)[:k]

def pick_segments(segs: List[Segment], max_n:int, min_sec:float) -> List[Segment]:
    chosen = [s for s in sorted(segs, key=lambda s: s.duration(), reverse=True)
              if s.duration() >= min_sec][:max_n]
    return chosen if chosen else segs[:1]

def by_first_seen(spk: Dict[str, List[Segment]], sel: List[str]) -> List[str]:
    return [s for _,s in sorted((spk[s][0].start, s) for s in sel)]

def pf_roles(sel: List[str], first:str, second:str) -> Dict[str,str]:
    tags=[f"{first} 1st Speaker",f"{second} 1st Speaker",
          f"{first} 2nd Speaker", f"{second} 2nd Speaker"]
    return {s: tags[i] if i<len(tags) else s for i,s in enumerate(sel)}


# ───────────────────────────────────────────────────────────────────────────────
# Delivery labels
# ───────────────────────────────────────────────────────────────────────────────
def delivery_labels(avg_db: float, pvar: float, pause: float) -> Tuple[str,str]:
    tone = ("monotone" if np.isfinite(pvar) and pvar<3500
            else "somewhat varied" if np.isfinite(pvar) and pvar<7000
            else "varied")
    energy = ("quiet" if np.isfinite(avg_db) and avg_db<-30
              else "passionate" if np.isfinite(avg_db) and avg_db>-22
              else "balanced")
    speed = ("very fast" if pause<=.12 else "fast" if pause<=.25
             else "moderate" if pause<=.45 else "slow")
    label = f"{tone}, {energy}, {speed}"
    tip = ("Vary your tone to keep judges engaged."      if tone=="monotone" else
           "Project more so key lines land."            if energy=="quiet"  else
           "Add small pauses after warrants/tags."      if speed in ("fast","very fast")
           else "Solid delivery — maintain variation.")
    return label, tip


# ───────────────────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(
    description="Speech-delivery metrics (AAI only).",
    add_help=True
    )
    ap.add_argument("audio")
    ap.add_argument("--work-dir", default="out")
    ap.add_argument("--first", default="Aff")
    ap.add_argument("--second", default="Neg")
    ap.add_argument("--diarization-json")
    ap.add_argument("--aai-key", default="")
    ap.add_argument("--max-speakers", type=int, default=4)
    ap.add_argument("--segments-per-speaker", type=int, default=2)
    ap.add_argument("--min-seg-sec", type=float, default=60.0)
    ap.add_argument("--alt-single-min-seg-sec", type=float, default=90.0)
    args, _ = ap.parse_known_args()
    audio_path = Path(args.audio).expanduser().resolve()
    work_dir   = Path(args.work_dir).expanduser().resolve(); work_dir.mkdir(parents=True, exist_ok=True)
    report_out = work_dir / "analyze_speech.txt"

    log(f"📁  Audio: {audio_path.name}")
    log(f"Teams: {args.first} vs {args.second}")

    # STEP 1 — audio prep
    log("🔧  STEP 1  Preparing audio…")
    wav_path = ensure_16k_wav(audio_path)

    # STEP 2 — diarization
    if args.diarization_json:
        diar_json = Path(args.diarization_json).expanduser().resolve()
        if not diar_json.exists():
            raise SystemExit(f"--diarization-json {diar_json} not found.")
        log("🔍  STEP 2  Using supplied diarization JSON…")
    else:
        log("🔍  STEP 2  Running AssemblyAI diarization…")
        diar_json = run_diarization(audio_path, work_dir,
                                    args.aai_key, args.max_speakers)

    speakers = parse_aai_json(diar_json)
    if not speakers: raise SystemExit("No speech segments in diarization JSON.")

    selected  = by_first_seen(speakers, top_speakers(speakers, args.max_speakers))
    roles     = pf_roles(selected, args.first, args.second)
    y, sr     = load_audio(wav_path)

    # STEP 3 — metrics & report
    lines: List[str] = []

    for sp in selected:
        sp_segs = speakers[sp]
        focus   = pick_segments(sp_segs, args.segments_per_speaker, args.min_seg_sec)
        samps   = samples_for_segments(y, sr, focus)

        avg_db,rng_db = loudness_dbfs(samps)
        pv            = pitch_var(samps, sr)
        cv            = centroid_var(samps, sr)
        pause         = avg_pause(sp_segs)

        label, tip    = delivery_labels(avg_db, pv, pause)
        role          = roles.get(sp, sp)

        lines.append(f"== {role} Speeches: ({fmt_ranges(focus)}) ==")
        loud_str = f"{avg_db:+.1f} dBFS (range {rng_db:.1f})" if np.isfinite(avg_db) else "n/a"
        lines.extend([
            f" • Delivery: {label}",
            f" • Loudness: {loud_str}",
            f" • Pitch var: {pv:.1f}"      if np.isfinite(pv) else " • Pitch var: n/a",
            f" • Centroid var: {cv:.1f}"   if np.isfinite(cv) else " • Centroid var: n/a",
            f" • Avg pause: {pause:.2f} s",
            f" • Tip: {tip}",
            ""
        ])

    report_out.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("\n".join(lines), "\n")
    log(f"✅  Wrote {report_out}")

# ───────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
