#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd):
    """Run a shell command, raising an exception on failure."""
    print(f"\n▶ Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: run_pipeline.py TARGET_DIR [MAP_FILE] [--validate-column COLUMN]", file=sys.stderr)
        sys.exit(1)

    target_dir = Path(sys.argv[1]).resolve()
    map_file   = Path(sys.argv[2] if len(sys.argv) > 2 else "trim_map.txt").resolve()

    # Step 1: Convert & trim to WAV + generate manifest
    run_cmd(f"python convert_and_trim.py {target_dir} {map_file} --format wav")

    prefix  = target_dir.name
    wav_dir = target_dir / f"{prefix}_wav"
    if not wav_dir.is_dir():
        print(f"❌ Expected wav_dir at {wav_dir}, but it doesn’t exist.")
        sys.exit(1)

    # Prepare paths
    code = prefix[:5]
    csv_path = target_dir / f"{code}_transcripts.csv"
    xlsx_path = target_dir / f"{code}_transcripts.xlsx"

    # 3) Run Whisper on the same WAVs
    whisper_json = target_dir / "whisper_output.jsonl"
    run_cmd(f"python whisper_transcribe.py {wav_dir} --output_jsonl {whisper_json}")

    # Step 4: Build CSV/Excel from ASR JSON
    run_cmd(
        "python build_transcript.py "
        f"--whisper_jsonl {whisper_json} "
        f"--output_csv   {csv_path} "
        f"--output_xlsx  {xlsx_path}"
    )

    # 5) Validate responses
    validate_col = "transcript_whisper"
    validated_csv = target_dir / f"transcripts_validated.csv"
    run_cmd(
        f"python validate_responses.py "
        f"{csv_path} "
        f"--column {validate_col}"
    )

    print("\n✅ Full pipeline complete.")
    print(f"→ Combined transcripts: {csv_path}, {xlsx_path}")
    print(f"→ Validation results: {validated_csv}")

    print(f"\n✅ Pipeline complete. Outputs:\n  - {csv_path}\n  - {xlsx_path}")

if __name__ == "__main__":
    main()