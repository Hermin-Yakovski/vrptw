"""Docker entrypoint for VRPTW solver.

This script provides a CLI interface for running the VRPTW solver
in a Docker container. It reads the database from /data/vrptw.db
and outputs results as an .xlsx file to /data/.
"""

import argparse
import sys
from pathlib import Path

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from vrptw.algorithm import UnifiedCapacityAlgorithm
from vrptw.scenario import VrptwScenario
from vrptw.schema import VrptwRequest


def main():
    parser = argparse.ArgumentParser(
        description='VRPTW solver - solve vehicle routing problems with time windows'
    )
    parser.add_argument(
        '--instance',
        required=True,
        help='Instance name (e.g., C101, R101, RC101)'
    )
    parser.add_argument(
        '--capacity',
        type=int,
        default=100,
        help='Vehicle capacity (default: 100)'
    )
    parser.add_argument(
        '--solver',
        choices=['exact', 'greedy'],
        default='exact',
        help='Solver type (default: exact)'
    )

    args = parser.parse_args()

    # Fixed paths
    database_path = Path('/data/vrptw.db')
    output_dir = Path('/data')

    # Validate database exists
    if not database_path.exists():
        print(f"Error: Database not found at {database_path}", file=sys.stderr)
        sys.exit(1)

    # Create request
    request = VrptwRequest(instance=args.instance)

    # Connect to database
    database_url = f"sqlite:///{database_path}"
    engine = sqlalchemy.create_engine(database_url)

    # Create and load scenario
    scenario = VrptwScenario(request)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        scenario.load(session=session)
        session.commit()

    # Set algorithm
    scenario.set_algorithm(
        UnifiedCapacityAlgorithm,
        capacity=args.capacity,
        solver=args.solver
    )

    # Execute algorithm
    print(f"Solving instance {args.instance} with {args.solver} solver (capacity: {args.capacity})...")
    scenario.exec_algorithm()

    # Save results
    scenario.save_xlsx(output_dir)
    print(f"Results saved to {output_dir}")


if __name__ == '__main__':
    main()
