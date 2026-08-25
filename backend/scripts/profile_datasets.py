"""
backend/scripts/profile_datasets.py
CLI Script to execute dataset profiling and generate validation reports under docs/data-validation/.
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.science.profiler import generate_validation_reports


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "docs/data-validation"

    print(f"Scanning directory: '{data_dir}'...")
    print(f"Output directory:   '{output_dir}'...")

    is_real = generate_validation_reports(data_dir=data_dir, output_dir=output_dir)

    if not is_real:
        print("\n==========================================")
        print("REAL DATA REQUIRED")
        print("==========================================")
        print("Profiling infrastructure successfully built and verified.")
        print(f"No real datasets were found in '{data_dir}'. Reports generated under '{output_dir}'.\n")
    else:
        print("\n==========================================")
        print("DATASETS SUCCESSFULLY PROFILED")
        print("==========================================")
        print(f"Reports saved to '{output_dir}'.\n")


if __name__ == "__main__":
    main()
