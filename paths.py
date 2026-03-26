from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

WELLS_ROOT = Path(r"G:\Sub_Appl_Data\WellDB\NO\wells")


def scan_well_dir(well_dir: Path) -> list[str]:
    """Scan a single well directory for '09.Well_Test_Data' subdirectories."""
    found = []
    if not well_dir.is_dir():
        return found
    for sub_dir in sorted(well_dir.iterdir()):
        if not sub_dir.is_dir():
            continue
        test_data = sub_dir / "09.Well_Test_Data"
        if not test_data.is_dir():
            continue
        for file_path in sorted(test_data.iterdir()):
            if not file_path.is_file():
                continue
            if file_path.exists() and file_path.suffix.lower() == ".pdf":
                found.append(str(file_path))
                print(f"Found: {file_path}")
    return found


if __name__ == "__main__":
    well_dirs = sorted(p for p in WELLS_ROOT.iterdir() if p.is_dir())

    found_paths = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(scan_well_dir, d): d for d in well_dirs}
        for future in as_completed(futures):
            found_paths.extend(future.result())

    # Sort for deterministic output (as_completed doesn't preserve order)
    found_paths.sort()

    output_file = Path("well_test_data_paths.json")
    output_file.write_text(json.dumps(found_paths, indent=2))
    print(f"\nWrote {len(found_paths)} paths to {output_file}")