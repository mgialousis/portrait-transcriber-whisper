#!/usr/bin/env python3
import argparse
import sys
import subprocess
import json
from pathlib import Path

def load_trim_map(map_path: Path) -> dict:
    """
    Reads a two-column mapping file (key and seconds) and returns
    a dict[str, float].
    """
    trim_map = {}
    with map_path.open(encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            raw_key, raw_sec = parts[0], parts[1]
            key = raw_key.strip('"').strip()
            try:
                sec = float(raw_sec)
            except ValueError:
                print(f"⚠️  Skipping invalid time '{raw_sec}' for key '{key}'", file=sys.stderr)
                continue
            trim_map[key] = sec
            print(f"  {key} → {sec}")
    return trim_map

def main():
    parser = argparse.ArgumentParser(
        description="Convert .webm files to trimmed, 16 kHz mono .mp3 or .wav according to a mapping file."
    )
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Directory containing .webm files"
    )
    parser.add_argument(
        "map_filename",
        nargs="?",
        default="trim_map.txt",
        help="Name (or path) of the trim-map file (default: trim_map.txt)"
    )
    args = parser.parse_args()

    # ─── 1. Validate target directory
    target_dir = args.target_dir
    if not target_dir.is_dir():
        print(f"❌ Directory not found: {target_dir}", file=sys.stderr)
        sys.exit(1)

    # ─── 2. Locate mapping file
    map_path = Path(args.map_filename)
    if not map_path.is_file():
        alt = target_dir / args.map_filename
        if alt.is_file():
            map_path = alt
        else:
            print(
                f"❌ Mapping file not found. Tried '{args.map_filename}' and '{alt}'",
                file=sys.stderr
            )
            sys.exit(1)

    print(f"✅ Using mapping file: {map_path}")
    print()
    print(f"✅ Loaded keys from {map_path.name}:")
    trim_map = load_trim_map(map_path)
    print()

    # ─── 3. Prepare output directory
    prefix = target_dir.name
    out_dir = target_dir / f"{prefix}_wav"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ─── 4. Process each .webm
    for webm_file in sorted(target_dir.glob("*.webm"), key=lambda p: p.name):
        print(f"🔍 Checking file: {webm_file.name}")
        trim_seconds = 0.0
        for key, sec in trim_map.items():
            if key in webm_file.name:
                trim_seconds = sec
                print(f"  ✅ Match '{key}' → Trim {trim_seconds}s")
                break

        stem = webm_file.stem
        temp_wav = out_dir / f"{stem}_full.wav"
        final_out = out_dir / f"{stem}.wav"

        # ─── Step 1: Convert .webm → 16 kHz mono WAV (full length)
        print(f"  🎧 Step 1: Converting → {temp_wav.name} (16 kHz mono, full length)")
        cmd_convert = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(webm_file),
            "-ar", "16000",  # 16 kHz sample rate
            "-ac", "1",  # mono
            #"-c:a", "pcm_s16le",  # 16‐bit PCM WAV
            str(temp_wav)
        ]
        try:
            subprocess.run(cmd_convert, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ ffmpeg conversion failed on {webm_file.name}: {e}", file=sys.stderr)
            continue

        # ─── Step 2: Trim the intermediate WAV to final WAV
        if trim_seconds > 0:
            print(f"  🎧 Step 2: Trimming first {trim_seconds}s from {temp_wav.name} → {final_out.name}")
            cmd_trim = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-ss", str(trim_seconds),
                "-i", str(temp_wav),
                "-c", "copy",      # copy PCM chunks into final WAV
                str(final_out)
            ]
        else:
            # No trimming requested; rename the full WAV to final
            temp_wav.rename(final_out)
            print(f"  ℹ️  No trim; renamed {temp_wav.name} → {final_out.name}")
            cmd_trim = None

        if cmd_trim:
            try:
                subprocess.run(cmd_trim, check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ ffmpeg trimming failed on {temp_wav.name}: {e}", file=sys.stderr)
                continue

        # ─── Remove the intermediate WAV
        try:
            temp_wav.unlink()
            print(f"  🗑 Removed intermediate file: {temp_wav.name}")
        except OSError:
            pass

        print()

    print("✅ All done.")

if __name__ == "__main__":
    main()