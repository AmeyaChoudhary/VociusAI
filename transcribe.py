import whisperx
# Choose device and model
device = "cpu" # use "cuda" if you have an NVIDIA GPU, or "mps" for Apple Silicon GPU
model = whisperx.load_model("small", device=device, compute_type="float32")
 # using large-v2 model for best accuracy
# Load the audio file
audio_file = "sampledebate1.m4a" # <-- replace with your filename or path
audio = whisperx.load_audio(audio_file)
# Transcribe the audio (segment-level transcription without word timestamps yet)
result = model.transcribe(audio)
print("Transcription done. Aligning words...")
# Perform word-level alignment using WhisperX alignment model
model_a, metadata = whisperx.load_align_model(language_code=result["language"],
device=device)


aligned_result = whisperx.align(result["segments"], model_a, metadata, audio,
device=device)
# Extract the full text from aligned segments
segments = aligned_result["segments"]
full_text = " ".join(segment["text"].strip() for segment in segments)
print("\nFull Transcript:\n")
print(full_text)

output_file = "transcript.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"\nTranscript written to {output_file}")
