"""Convert Solomon VRPTW benchmark JSON to CSV.

Usage:
    python scripts/solomon_to_csv.py                              # converts c101.json
    python scripts/solomon_to_csv.py path/to/instance.json       # converts specified file
"""

import csv
import json
import sys
from pathlib import Path

_BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "solomon-vrptw-benchmarks-main"
_CSV_DIR = Path(__file__).resolve().parent.parent / "data"

_COLUMNS = ["id", "x", "y", "demand", "earliest", "latest", "cost"]


def convert(json_path: Path, csv_path: Path) -> None:
    """Convert a Solomon benchmark JSON file to a CSV of customers."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    instance = data["instance"]
    vehicle_nr = data["vehicle-nr"]
    capacity = data["capacity"]
    customers = data["customers"]

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_COLUMNS)
        writer.writeheader()
        for customer in customers:
            writer.writerow({col: customer[col] for col in _COLUMNS})

    print(f"Instance: {instance}")
    print(f"  vehicles: {vehicle_nr}, capacity: {capacity}")
    print(f"  {len(customers)} customers -> {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
    else:
        src = _BENCHMARK_DIR / "c" / "1" / "c101.json"

    dst = _CSV_DIR / f"{src.stem}.csv"
    convert(src, dst)