import sys
from pathlib import Path
import json
import whisperx
import torch

import sys
import build_transcript
import validate_responses
import convert_and_trim


def convert_and_trim_folder(target_dir: Path, map_file: Path):
    sys.argv = ["convert_and_trim.py", str(target_dir), str(map_file)]
    convert_and_trim.main()

def whisperx_transcribe(wav_dir: Path, output_jsonl: Path, language="es"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model = whisperx.load_model("large-v3", device, compute_type="float16" if device == "cuda" else "float32", language=language)
    except:
        model = whisperx.load_model("large-v3", device, compute_type="int8" if device == "cuda" else "float32", language=language)
    wav_files = sorted([str(w) for w in wav_dir.glob("*.wav") if not w.name.startswith(".")])
    print(f"🔊 WhisperX transcribing {len(wav_files)} files…")
    with output_jsonl.open("w", encoding="utf-8") as out:
        for wav_path in wav_files:
            result = model.transcribe(wav_path, language=language)
            print(wav_path)
            print(result)
            out.write(json.dumps({
                "audio_filepath": wav_path,
                "transcript": " ".join([segment['text'].strip() for segment in result['segments']]),
                "duration": int(sum([segment['end']-segment['start'] for segment in result['segments']]))
            }, ensure_ascii=False) + "\n")
    print(f"✅ WhisperX output written to {output_jsonl}")

def build_transcript_files(whisper_json, csv_path, xlsx_path):
    sys.argv = [
        "build_transcript.py",
        "--whisper_jsonl", str(whisper_json),
        "--output_csv", str(csv_path),
        "--output_xlsx", str(xlsx_path)
    ]
    build_transcript.main()

def validate_transcripts(csv_path, column="transcript_whisper"):
    sys.argv = [
        "validate_responses.py",
        str(csv_path),
        "--column", column
    ]
    validate_responses.main()

def main():
    base_dir = Path(r"D:/Usuarios/aaltfer/Desktop/MILTOS_Portrait/data")
    include_dir = [base_dir / "021KK"]  # Change as needed
    map_file = Path("trim_map.txt")     # Or skip if not trimming

    for folder in include_dir:
        print(f"\n=== Running efficient pipeline on: {folder} ===")
        prefix = folder.name
        wav_dir = folder / f"{prefix}_wav"

        # Step 1: Convert & trim (optional, comment out if not needed)
        convert_and_trim_folder(folder, map_file)

        # Step 2: Batch transcribe with WhisperX
        whisper_json = folder / "whisper_output.jsonl"
        whisperx_transcribe(wav_dir, whisper_json)

        # Step 3: Build CSV/Excel from ASR JSON
        code = prefix[:5]
        csv_path = folder / f"{code}_transcripts.csv"
        xlsx_path = folder / f"{code}_transcripts.xlsx"
        build_transcript_files(whisper_json, csv_path, xlsx_path)

        # Step 4: Validate responses
        validate_transcripts(csv_path)

        print(f"\n✅ Efficient pipeline complete for {folder}")
        print(f"→ Combined transcripts: {csv_path}, {xlsx_path}")

if __name__ == "__main__":
    main()