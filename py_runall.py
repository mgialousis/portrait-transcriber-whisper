import subprocess
from pathlib import Path

def run_pipeline_on_folder(folder: Path):
    print(f"\n=== Running pipeline on: {folder} ===")
    try:
        subprocess.run(
            ["python", "run_pipeline.py", str(folder)],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Pipeline failed for {folder}: {e}")

def main():
    base_dir = Path("/Users/miltos/Desktop/ftp_portrait/PORTRAIT")
    exclude_dir = base_dir / "backup_original"
    include_dir = [ base_dir / "NR21X", base_dir / "12TCV", base_dir / "21WYJ", base_dir / "F2Z1W", base_dir / "C2NN1"]

    subfolders = [f for f in base_dir.iterdir() if f.is_dir() and f in include_dir]

    for folder in sorted(subfolders):
        run_pipeline_on_folder(folder)

if __name__ == "__main__":
    main()