import os
import subprocess
import sys
from pathlib import Path

# Configuration
REPORTS_DIR = "C:/Users/advik/Desktop/Getfranchise/output/legacy-flat-food-reports/food franchises flat txt/"
FACTORY_SCRIPT = "C:/Users/advik/Desktop/Getfranchise/Factory/run_factory.py"
ROOT_DIR = "C:/Users/advik/Desktop/Getfranchise/Factory"

# Set env var for the factory
os.environ["FACTORY_REPORTS_DIR"] = REPORTS_DIR

def main():
    if not os.path.exists(REPORTS_DIR):
        print(f"Error: Reports directory not found: {REPORTS_DIR}")
        sys.exit(1)

    # Get 57 reports
    files = [f[:-4] for f in os.listdir(REPORTS_DIR) if f.endswith('.txt')]
    targets = files[:57]
    print(f"Targeting {len(targets)} franchises...")

    success_count = 0
    failures = []

    for i, franchise in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] Processing: {franchise}...", end=" ", flush=True)
        try:
            # Run the factory script
            result = subprocess.run(
                [sys.executable, FACTORY_SCRIPT, franchise],
                cwd=ROOT_DIR,
                env=os.environ.copy(),
                capture_output=True,
                text=True,
                check=True
            )
            print("DONE")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print("FAILED")
            failures.append((franchise, e.stderr.strip()))
        except Exception as e:
            print("ERROR")
            failures.append((franchise, str(e)))

    print("\n--- Final Report ---")
    print(f"Successfully processed: {success_count}")
    print(f"Failed: {len(failures)}")
    
    if failures:
        print("\nFailures detail:")
        for f, err in failures:
            print(f"{f}: {err}")

if __name__ == "__main__":
    main()
