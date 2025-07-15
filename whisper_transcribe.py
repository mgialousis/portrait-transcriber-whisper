#!/usr/bin/env python3
import argparse
import json
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from pathlib import Path
from pydub import AudioSegment
import io, math
import soundfile as sf
import warnings
warnings.filterwarnings(
    "ignore",
    message=".*The input name `inputs` is deprecated.*"
)

MAX_CHUNK_S = 28  # Whisper’s ~30 s limit

def parse_args():
    p = argparse.ArgumentParser(
        description="Run Whisper on a set of WAV files and emit a JSONL of transcripts."
    )
    p.add_argument(
        "audio_dir", type=Path,
        help="Directory containing .wav files to transcribe with Whisper"
    )
    p.add_argument(
        "--output_jsonl",
        type=Path,
        default=Path("whisper_output.jsonl"),
        help="Path to write Whisper JSONL output"
    )
    return p.parse_args()

def build_whisper_pipeline(model_id="openai/whisper-large-v3"):
    device = 0 if torch.cuda.is_available() else -1
    dtype  = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    ).to(f"cuda:{device}" if device >= 0 else "cpu")

    """
    model.generation_config.language = "<|es|>"
    model.generation_config.task = "transcribe"
    model.config.forced_decoder_ids = None
    """
    proc = AutoProcessor.from_pretrained(model_id)
    return pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=proc.tokenizer,
        feature_extractor=proc.feature_extractor,
        device=device,
        torch_dtype=dtype,
        generate_kwargs={"language": "spanish", "task": "transcribe"},
    )

def transcribe_file(pipe, wav_path: Path) -> dict:
    """Split `wav_path` into MAX_CHUNK_S-second pieces, transcribe each, and return the full transcript."""
    audio = AudioSegment.from_file(wav_path, format="wav")

    total_ms = len(audio)
    chunk_ms = MAX_CHUNK_S * 1000

    # keep reducing chunk_ms by 2000 ms until either:
    #  1) total_ms < chunk_ms → stop
    #  2) the remainder (total_ms % chunk_ms) exceeds 4000 → stop
    while chunk_ms <= total_ms and (total_ms % chunk_ms) <= 4000:
        chunk_ms -= 2000

    num_chunks = math.ceil(total_ms / chunk_ms)

    texts = []
    for i in range(num_chunks):
        start = i * chunk_ms
        end = min((i + 1) * chunk_ms, total_ms)
        chunk = audio[start:end]
        # Export to an in-memory WAV and read back as numpy + sample rate
        buf = io.BytesIO()
        chunk.export(buf, format="wav")
        buf.seek(0)
        # read audio into numpy array
        data, sr = sf.read(buf)

        # now call the ASR pipeline with (array, sampling_rate)
        res = pipe(data)

        texts.append(res.get("text", "").strip())

    transcript = " ".join(texts)
    audio_duration = math.floor(total_ms / 1000) # Convert milliseconds to seconds

    return {
        "transcript": transcript,
        "duration": audio_duration
    }

def main():
    args = parse_args()
    pipe = build_whisper_pipeline()

    with args.output_jsonl.open("w", encoding="utf-8") as out:
        for wav in sorted(args.audio_dir.glob("*.wav"), key=lambda p: p.name):
            if wav.name.startswith("."):
                continue
            print(f"🔊 Whisper → {wav.name}", end="… ")
            result = transcribe_file(pipe, wav)
            result["audio_filepath"] = str(wav.resolve())
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            print("done")

    print(f"✅ Whisper output written to {args.output_jsonl}")

if __name__ == "__main__":
    main()