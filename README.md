# vrptw

Vehicle Routing Problem with Time Windows, implemented on the [or-scenario](https://test.pypi.org/project/or-scenario/) framework.

## Requirements

- Python >= 3.11
- CMake >= 3.20 (for the C++ greedy solver)

## Installation

```bash
uv sync
```

## Database setup

Create the SQLite database (default: `database/vrptw.db`):

```bash
python scripts/create_db.py
```

## Convert Solomon benchmarks

Convert a Solomon VRPTW benchmark JSON to CSV:

```bash
python scripts/solomon_to_csv.py                              # converts c101.json
python scripts/solomon_to_csv.py path/to/instance.json        # converts specified file
```

## Usage

```python
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from vrptw.algorithm import UnifiedCapacityAlgorithm
from vrptw.scenario import VrptwScenario
from vrptw.schema import VrptwRequest

# 1. Create a request for a Solomon benchmark instance
request = VrptwRequest(instance='C101')

# 2. Connect to the database
engine = sqlalchemy.create_engine("sqlite:///database/vrptw.db")

# 3. Load the scenario
scenario = VrptwScenario(request)
SessionLocal = sessionmaker(bind=engine)
with SessionLocal() as session:
    scenario.load(session=session)
    session.commit()

# 4. Set the algorithm and solver
scenario.set_algorithm(UnifiedCapacityAlgorithm, capacity=100, solver='exact')

# 5. Run the algorithm
scenario.exec_algorithm()
```

### Solvers

| `solver` value   | Description                              |
|-------------------|------------------------------------------|
| `'exact'`         | LP-based exact solver                    |
| `'greedy'`        | Python greedy construction heuristic     |
| `'greedy_cpp'`    | C++ greedy construction heuristic        |

## Docker Deployment

Run the solver in a Docker container (useful for systems with older glibc, e.g., CentOS 7):

```bash
docker build -t vrptw .
cp ./database/vrptw.db /data/jar
docker run --rm -v /data/jar:/data vrptw --instance=C101 --capacity=200 --solver=exact
```

Results are saved as `.xlsx` in the mounted directory.

## Testing

```bash
pytest
```