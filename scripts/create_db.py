"""Create a SQLite database with all VRPTW ORM tables.

Usage:
    python scripts/create_db.py                        # creates database/vrptw.db
    python scripts/create_db.py path/to/out.db         # creates at specified path
"""

import sys
from pathlib import Path

# Add project root to sys.path so `vrptw` is importable
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sqlalchemy import create_engine, inspect

# Import ORM models — this registers all tables on DeclarativeBase.metadata
from omni_orm.base import DeclarativeBase
from vrptw.orm import (
    DimCustomer,
    DimParameter,
    DimSnapshot,
    DimVehicle,
    DimVersion,
    FactCustomer,
    FactVehicle,
    SolCustomerVehicle,
)


def create_database(db_path: Path) -> None:
    """Create a SQLite database with all VRPTW tables."""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    DeclarativeBase.metadata.create_all(engine)

    # Print summary
    tables = inspect(engine).get_table_names()
    print(f"Created {db_path} with {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        db_dir = Path(__file__).resolve().parent.parent / "database"
        db_dir.mkdir(exist_ok=True)
        path = db_dir / "vrptw.db"

    create_database(path)