import argparse
import pandas as pd
import re
from pathlib import Path

def is_trivial(text):
    """
    Returns True if text is empty or trivial (e.g., just yes/no or very short).
    """
    if not text or not isinstance(text, str) or not text.strip():
        return True
    # lowercase and strip punctuation
    t = re.sub(r"[^a-zA-Z]", "", text).lower()
    # check if only yes/no or monosyllabic
    if t in {"yes", "no", "y", "n"}:
        return True
    # too short (less than 10 words)
    if len(text.split()) < 10:
        return True
    return False

def validate(df, column):
    """
    Validate responses in the given column.
    Returns a list of booleans: True if valid, False if failed.
    """
    results = []
    for idx, resp in enumerate(df[column]):
        fail = is_trivial(resp)
        results.append(not fail)
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Validate transcripts: non-empty, non-trivial responses"
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to the transcripts CSV file"
    )
    parser.add_argument(
        "--column",
        type=str,
        default="transcript",
        help="Name of the transcript column to validate"
    )
    args = parser.parse_args()

    # Read the data
    df = pd.read_csv(args.input_csv)

    # Validate
    valid_mask = validate(df, args.column)
    # Convert the list to a Pandas Series if necessary.
    if not isinstance(valid_mask, pd.Series):
        valid_mask = pd.Series(valid_mask, index=df.index)

    df['valid_response'] = valid_mask

    # Summary
    total = len(df)
    failed = total - sum(valid_mask)
    print(f"Total responses: {total}")
    print(f"Failed (empty/trivial): {failed}")

    # Print each failed
    if failed > 0:
        print("\nFailed entries:")
        for i, ok in enumerate(valid_mask):
            if not ok:
                row = df.iloc[i]
                print(f"  Row {i+1}: {row['audio_filepath']} - '{row[args.column]}'")

    # Write annotated CSV
    out_csv = args.input_csv.with_name(args.input_csv.stem + "_validated.csv")
    df.to_csv(out_csv, index=False)
    print(f"Annotated CSV written to: {out_csv}")

    alarms_df = df[~valid_mask]
    alarms_df.to_csv(args.input_csv.with_name("alarms.csv"), index=False)
    print("Alarms CSV file written to: alarms.csv")

    # Optionally, could add color output with ANSI
    if failed == 0:
        print("\033[92mAll responses passed validation!\033[0m")
    else:
        print("\033[91mSome responses failed validation. See list above.\033[0m")

if __name__ == "__main__":
    main()