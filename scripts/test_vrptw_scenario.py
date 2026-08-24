import sys
from pathlib import Path

from mypy.dmypy.client import request

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from vrptw.algorithm import UnifiedCapacityAlgorithm
from vrptw.scenario import VrptwScenario
from vrptw.schema import VrptwRequest


if __name__ == '__main__':
    request = VrptwRequest(instance='C101')

    database = f"sqlite:///{project_root / 'database' / 'vrptw.db'}"
    engine = sqlalchemy.create_engine(database)

    scenario = VrptwScenario(request)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        scenario.load(session=session)
        session.commit()

    # scenario.save_xlsx(project_root / 'data')
    #
    #
    # # algorithm
    # from math import inf
    # import cProfile
    # import pstats
    # import io

    scenario.set_algorithm(UnifiedCapacityAlgorithm, capacity=100, solver='exact')

    # profiler = cProfile.Profile()
    # profiler.enable()
    # scenario.exec_algorithm()
    # profiler.disable()
    #
    # stream = io.StringIO()
    # ps = pstats.Stats(profiler, stream=stream)
    # ps.sort_stats('cumulative')
    # ps.print_stats(30)
    # print(stream.getvalue())
    #
    # scenario.save_xlsx(project_root / 'data')
    #
    # sys.exit(0)