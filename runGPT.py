#!/usr/bin/env python3
"""
AnalyzeTranscript.py – feedback from existing transcript.txt
-------------------------------------------------------------
Skips speech detection & transcription. Uses existing `transcript.txt`
and generates GPT-4o judging feedback using prompt templates.

Requires one of:
- lay_judge_prompt.txt
- tech_judge_prompt.txt
- prog_judge_prompt.txt

Environment:
  export OPENAI_API_KEY=sk-...
"""

import os
import sys
import time
from openai import OpenAI

# Mapping from style → model prompt file
PROMPT_FILE = {
    "lay":  "lay_judge_prompt.txt",
    "flay": "lay_judge_prompt.txt",
    "tech": "tech_judge_prompt.txt",
    "prog": "prog_judge_prompt.txt"
}

# Load API key
api_key = os.getenv("OPENAI_API_KEY") or sys.exit("❌ Set OPENAI_API_KEY in your environment.")
client = OpenAI(api_key=api_key)

# === Step 1: User Input ===
topic = input("🗣  Debate topic: ").strip()
first = input("🏁  First team (Aff/Neg): ").strip()
style = input("🎿  Style (lay/flay/tech/prog): ").strip().lower()

if style not in PROMPT_FILE:
    sys.exit("❌ Style must be lay, flay, tech, or prog.")

# === Step 2: Load Prompt Template ===
prompt_path = PROMPT_FILE[style]
if not os.path.exists(prompt_path):
    sys.exit(f"❌ Missing prompt file: {prompt_path}")

template = open(prompt_path, encoding="utf-8").read()

# === Step 3: Load Transcript ===
if not os.path.exists("transcript.txt"):
    sys.exit("❌ transcript.txt not found.")

with open("transcript.txt", "r", encoding="utf-8") as f:
    transcript = f.read().strip()

# === Step 4: Prepare GPT prompt ===
filled_prompt = (template
    .replace("[insert topic here]", topic)
    .replace("[insert team name here]", first)
    .replace("[insert transcript here]", transcript))

# === Step 5: Send to GPT ===
print("🧠 GPT-4o analyzing transcript.txt …")
start = time.time()
rsp = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a PF debate judge."},
        {"role": "user", "content": filled_prompt}
    ],
    temperature=0,
    max_tokens=3500
)
output = rsp.choices[0].message.content.strip()

# === Step 6: Save output ===
with open("judging_feedback.txt", "w", encoding="utf-8") as f:
    f.write(output)

print("\n📄 wrote judging_feedback.txt")
print(f"⏱️  Completed GPT analysis in {round(time.time() - start, 1)}s")
print("\n=== 🧠  AI Judge Feedback ===\n")
print(output)