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
    base_dir = Path(r"D:\Usuarios\MGIALOU\Desktop\ToProcess")
    exclude_dir = base_dir / "backup_original"
    include_dir = [ base_dir / "2S1VM"]

    subfolders = [f for f in base_dir.iterdir() if f.is_dir() and f in include_dir]

    for folder in sorted(subfolders):
        run_pipeline_on_folder(folder)

if __name__ == "__main__":
    main()