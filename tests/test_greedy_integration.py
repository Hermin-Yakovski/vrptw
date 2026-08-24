from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from vrptw.algorithm import UnifiedCapacityAlgorithm
from vrptw.dimension import Customer, Route
from vrptw.parameter import Id, Loaded, Travel
from vrptw.scenario import VrptwScenario
from vrptw.schema import VrptwRequest

project_root = Path(__file__).resolve().parent.parent
_db_path = project_root / "database" / "vrptw.db"
database = f"sqlite:///{_db_path}"


@pytest.fixture(scope="module")
def solved_scenario():
    """Load C101 instance and run the greedy algorithm pipeline."""
    if not _db_path.exists():
        pytest.skip("database/vrptw.db not found (integration test requires local database)")
    engine = sqlalchemy.create_engine(database)
    session_local = sessionmaker(bind=engine)

    request = VrptwRequest(instance="C101")
    scenario = VrptwScenario(request)

    with session_local() as session:
        scenario.load(session=session)
        session.commit()

    scenario.set_algorithm(UnifiedCapacityAlgorithm, capacity=200, solver='greedy')
    scenario.exec_algorithm()

    return scenario


def test_all_customers_served(solved_scenario):
    """Every loaded customer should appear in at least one route."""
    # _data is the or_scenario.Scenario register; no public accessor exists yet
    data = solved_scenario._data
    customer_ids = {c for (c,) in data[Id][(Customer,)].keys()}
    assert len(customer_ids) > 0, "No customers loaded"

    # Every customer (except depot) should have at least one incoming travel edge
    travel_keys = list(
        data[Travel][
            (
                Customer,
                Customer,
            )
        ].keys()
    )
    visited = set()
    for i, j in travel_keys:
        if data[Travel][
            (
                Customer,
                Customer,
            )
        ][
            (
                i,
                j,
            )
        ]:
            visited.add(j)

    # All non-depot customers must be visited
    non_depot = customer_ids - {0}
    assert non_depot.issubset(visited), f"Unserved customers: {non_depot - visited}"


def test_routes_extracted(solved_scenario):
    """RouteExtractor should produce at least one route after greedy solver."""
    data = solved_scenario._data  # see comment in test_all_customers_served
    route_ids = list(data[Id][(Route,)].keys())
    assert len(route_ids) > 0, "No routes extracted"


def test_capacity_not_exceeded(solved_scenario):
    """Each route's total demand should not exceed vehicle capacity (200)."""
    data = solved_scenario._data  # see comment in test_all_customers_served
    capacity = 200

    for (r,) in data[Id][(Route,)].keys():
        # Loaded tracks cumulative demand per customer on each route;
        # the maximum cumulative value equals the total route demand.
        route_demand = 0
        for c, r2 in data[Loaded][
            (
                Customer,
                Route,
            )
        ].keys():
            if r2 == r:
                route_demand = max(
                    route_demand,
                    data[Loaded][
                        (
                            Customer,
                            Route,
                        )
                    ][
                        (
                            c,
                            r,
                        )
                    ],
                )
        assert 0 < route_demand <= capacity, (
            f"Route {r} demand {route_demand} out of bounds (0, {capacity}]"
        )
