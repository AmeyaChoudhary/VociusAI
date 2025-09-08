"""
FullAnalyzer: A unified entrypoint for debate and speech analysis.

This script orchestrates two independent analysis pipelines – Debate Judging Feedback
and Speech Delivery Feedback – against a single input audio recording.  It prompts
the user for the necessary contextual information, duplicates the recording so
that each pipeline can operate on its own copy, and then executes both analyses
in parallel.  Results are written to the same output files (`judging_feedback.txt`
and `analyze_speech.txt`) as produced by the original scripts.

Notes:

* The original `AnalyzeDebate.py` and `AnalyzeSpeech.py` scripts must be present in
  the same directory as this file.  Their internal logic is untouched and
  preserved; this wrapper simply invokes them.
* Each script performs its own silence trimming and resampling.  To avoid
  interfering with that behaviour, the input audio is copied twice prior to
  analysis.
* All prompts required by the underlying scripts are surfaced here.  If the
  underlying scripts are extended with additional interactive prompts, you may
  need to extend the `debate_inputs` or `speech_inputs` lists accordingly.
* Concurrency is implemented using `concurrent.futures.ThreadPoolExecutor`.  If
  concurrent execution causes issues on your system (for example, due to GPU
  resource contention), set `USE_CONCURRENCY` to ``False`` below to fall back
  to serial execution.

Example usage:

    python FullAnalyzer.py /path/to/debate_recording.m4a

The program will then ask for the debate topic, who speaks first, judging style
and any other required information, copy the recording twice, and run both
analysis pipelines.  Once complete, `judging_feedback.txt` and
`analyze_speech.txt` will appear in the working directory.
"""

import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys


# Toggle this constant to ``False`` to force the analyses to run one after the
# other.  Parallel execution can drastically reduce overall runtime on
# multi‑core machines but may contend for resources (e.g. GPU memory) on
# machines with limited resources.
USE_CONCURRENCY: bool = True


def duplicate_audio(input_path: str, suffix: str) -> str:
    """Copy an audio file and return the new path.

    The copy will be placed next to the original with the given suffix
    inserted before the file extension.  For example, if ``input_path`` is
    ``recording.m4a`` and ``suffix`` is ``_debate``, the resulting path will
    be ``recording_debate.m4a``.

    Args:
        input_path: The path to the original audio file.
        suffix:     A short string to append to the base filename.

    Returns:
        The path to the duplicated file.
    """
    base, ext = os.path.splitext(input_path)
    copy_path = f"{base}{suffix}{ext}"
    # Perform the copy.  Any existing file will be overwritten.
    shutil.copyfile(input_path, copy_path)
    return copy_path


def run_analyze_debate(audio_path: str, topic: str, speak_first: str, judging_style: str) -> None:
    """Invoke the original AnalyzeDebate.py script with pre‑supplied inputs.

    This function opens a subprocess running ``AnalyzeDebate.py`` and writes
    answers to its interactive prompts via standard input.  The order of inputs
    supplied here should match the order of ``input()`` calls within
    ``AnalyzeDebate.py``.  If that script is updated to prompt for additional
    values, extend the ``debate_inputs`` list accordingly.

    Args:
        audio_path:    Path to the audio file to analyze.
        topic:         The debate topic as entered by the user.
        speak_first:   Which side speaks first (e.g. "Aff" or "Neg").
        judging_style: The judging style (e.g. "lay", "flay", "tech", "prog").
    """
    # Build the list of responses expected by AnalyzeDebate.py.  If the
    # underlying script asks additional questions, you should append further
    # responses here so that ``communicate()`` sends them in the correct order.
    debate_inputs = [
        audio_path,
        topic,
        speak_first,
        judging_style,
    ]
    # Join the inputs with newlines.  The trailing newline ensures the final
    # prompt receives an empty line if no extra input is expected.
    input_str = "\n".join(debate_inputs) + "\n"
    # Run the script as a subprocess.  ``text=True`` ensures that the input
    # string is treated as a unicode string rather than bytes.
    process = subprocess.run(
        [sys.executable, "AnalyzeDebate.py"],
        input=input_str,
        text=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    # Optionally, check the return code and raise if unsuccessful.
    if process.returncode != 0:
        raise RuntimeError(f"AnalyzeDebate.py exited with code {process.returncode}")


def run_analyze_speech(audio_path: str, speak_first: str, judging_style: str) -> None:
    """Invoke the original AnalyzeSpeech.py script with pre‑supplied inputs.

    This function runs ``AnalyzeSpeech.py`` in a subprocess and pipes answers to
    its interactive prompts.  Adjust the ``speech_inputs`` list if the
    underlying script expects more (or fewer) values.

    Args:
        audio_path:    Path to the audio file for speech analysis.
        speak_first:   Which side speaks first.
        judging_style: The judging style.
    """
    # Build inputs expected by AnalyzeSpeech.py.  We assume the script asks for
    # the audio path followed by the speak order and judging style.  Update
    # this list if AnalyzeSpeech.py's prompts change.
    speech_inputs = [
        audio_path,
        speak_first,
        judging_style,
    ]
    input_str = "\n".join(speech_inputs) + "\n"
    process = subprocess.run(
        [sys.executable, "AnalyzeSpeech.py"],
        input=input_str,
        text=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if process.returncode != 0:
        raise RuntimeError(f"AnalyzeSpeech.py exited with code {process.returncode}")


def main(argv: list[str] | None = None) -> int:
    """Entry point for the FullAnalyzer program.

    Parses command‑line arguments, prompts for any missing values, copies the
    input audio file for each pipeline, and executes both analyses.  In case of
    errors in either pipeline, the exception will be propagated to the caller.

    Args:
        argv: Optional list of arguments to parse instead of ``sys.argv``.

    Returns:
        Exit code (0 on success, non‑zero on failure).
    """
    parser = argparse.ArgumentParser(
        description="Run both debate and speech analyses on a single audio file."
    )
    parser.add_argument(
        "audio_file",
        nargs="?",
        help="Path to the input .m4a or .wav file.",
    )
    parser.add_argument(
        "--topic",
        dest="topic",
        help="Debate topic (optional; will prompt if omitted)",
    )
    parser.add_argument(
        "--first",
        dest="speak_first",
        help="Who speaks first (Aff or Neg; optional; will prompt if omitted)",
    )
    parser.add_argument(
        "--style",
        dest="judging_style",
        help="Judging style (lay, flay, tech, prog; optional; will prompt if omitted)",
    )
    args = parser.parse_args(argv)
    # Determine the audio file path.
    audio_path = args.audio_file or input("Enter the path to the audio file (.m4a or .wav): ").strip()
    if not os.path.isfile(audio_path):
        print(f"Error: File not found: {audio_path}", file=sys.stderr)
        return 1
    # Prompt for the debate topic if not supplied.
    topic = args.topic or input("Enter the debate topic: ").strip()
    # Prompt for who speaks first.
    speak_first = args.speak_first or input("Who speaks first? (Aff/Neg): ").strip()
    # Prompt for the judging style.
    judging_style = args.judging_style or input(
        "Judging style (lay, flay, tech, prog): "
    ).strip()
    # Duplicate the audio file for each pipeline.
    debate_copy = duplicate_audio(audio_path, "_debate")
    speech_copy = duplicate_audio(audio_path, "_speech")
    print(f"Audio file copied to:\n  {debate_copy} (for debate analysis)\n  {speech_copy} (for speech analysis)")
    # Define tasks to run.  Each task is a tuple of (callable, args, kwargs).
    tasks = [
        (run_analyze_debate, (debate_copy, topic, speak_first, judging_style), {}),
        (run_analyze_speech, (speech_copy, speak_first, judging_style), {}),
    ]
    # Execute the analyses either concurrently or sequentially.
    try:
        if USE_CONCURRENCY:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(func, *func_args, **func_kwargs)
                    for func, func_args, func_kwargs in tasks
                ]
                # Wait for all tasks to complete and propagate exceptions.
                for future in futures:
                    future.result()
        else:
            # Serial execution.
            for func, func_args, func_kwargs in tasks:
                func(*func_args, **func_kwargs)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print("Both analyses completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
