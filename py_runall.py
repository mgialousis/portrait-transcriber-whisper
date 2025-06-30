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
    include_dir = [ base_dir / "2PA1L", base_dir / "2HGA1", base_dir / "XZ21K", base_dir / "21YYD",
base_dir / "1H2GG", base_dir / "Z2ZF1", base_dir / "V2DL1", base_dir / "UQ2M1",
base_dir / "F21XO", base_dir / "YN21I", base_dir / "VD2X1", base_dir / "CY2H1",
base_dir / "YSW21" ]

    subfolders = [f for f in base_dir.iterdir() if f.is_dir() and f in include_dir]

    for folder in sorted(subfolders):
        run_pipeline_on_folder(folder)

if __name__ == "__main__":
    main()
