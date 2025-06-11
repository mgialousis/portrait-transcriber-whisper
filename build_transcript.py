#!/usr/bin/env python3
import argparse
import json
import os
import re
import pandas as pd
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(
        description="Merge Whisper JSONL into CSV/Excel table"
    )
    p.add_argument("-w", "--whisper_jsonl",  type=Path, required=True,
                   help="Whisper JSONL (transcript_whisper key)")
    p.add_argument("-c", "--output_csv",     type=Path, required=True,
                   help="Output CSV path")
    p.add_argument("-x", "--output_xlsx",    type=Path, required=True,
                   help="Output Excel path")
    return p.parse_args()

def load_jsonl(path: Path, key: str):
    """Return dict[audio_filepath] → value for the given key."""
    d = {}
    for line in path.open("r", encoding="utf-8"):
        obj = json.loads(line)
        fp = obj.get("audio_filepath")
        d[fp] = obj.get(key, "")
    return d

def main():
    args = parse_args()

    # Load both transcripts
    whisper_transcript = load_jsonl(args.whisper_jsonl, "transcript")
    whisper_duration = load_jsonl(args.whisper_jsonl, "duration")

    # regex for username/questionnaire/question
    pattern = re.compile(r"""
        ^(?P<username>[^_]+)
        _(?P<questionnaire>[^_]+_[^_]+)
        _(?P<question>q\d+)
    """, re.VERBOSE)

    records = []
    for fp in sorted(whisper_transcript.keys()):
        fname = os.path.basename(fp)
        m = pattern.match(fname)
        if m:
            uname = m.group("username")
            qn = m.group("questionnaire")
            q = m.group("question")
        else:
            uname = qn = q = ""

        records.append({
            "audio_filepath":     fp,
            "username":           uname,
            "questionnaire":      qn,
            "question":           q,
            "duration":           whisper_duration.get(fp, ""),
            "transcript_whisper": whisper_transcript.get(fp, ""),
        })

    df = pd.DataFrame(records)

    # -- SORT: first by questionnaire, then by question number extracted from 'qNN' --
    # Extract numeric part (e.g. 'q16' → 16)
    df['qnum'] = (
        df['question']
          .str.extract(r'q(\d+)', expand=False)
          .astype(int)
    )
    # Sort so that e.g. 'GR_Survey' < 'PE_Inventory', and then by qnum
    df = df.sort_values(['questionnaire', 'qnum'])
    # Clean up helper column
    df = df.drop(columns=['qnum'])

    # ensure dirs
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    df.to_excel(args.output_xlsx, index=False)

    print(f"✅ Wrote {len(df)} rows to {args.output_csv} and {args.output_xlsx}")

    # Identify all duplicate rows based on 'questionnaire' and 'question'
    duplicates = df[df.duplicated(subset=["questionnaire", "question"], keep=False)]

    # Write the duplicates to a CSV file for manual review
    duplicates.to_csv(args.output_csv.with_name("duplicate_questions.csv"), index=False)
    print("Duplicate questions written to: manually_check_duplicate_questions.csv")

    print(f"✅ Wrote {len(df)} rows to no_duplicates: {args.output_csv} and {args.output_xlsx}")

if __name__ == "__main__":
    main()