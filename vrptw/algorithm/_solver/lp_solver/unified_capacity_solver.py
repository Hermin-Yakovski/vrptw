from typing import TYPE_CHECKING

from or_algo.lp import LpSolver

from ....dimension import *
from .step import *
from .symbol import *

if TYPE_CHECKING:
    from or_register import Register, RegisterKey


class UnifiedCapacitySolver(LpSolver):
    def __init__(self, *args, capacity: float, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.append(CreateVarTravel,)
        self.append(CreateVarArrival,)
        self.append(CreateVarLoaded, capacity=capacity)

        self.append(CreateConstrArcInOut, )
        self.append(CreateConstrCalculateCapacity,)
        self.append(CreateConstrCalculateArrival,)

        self.publish(VarTravel, (Customer, Customer,))
        self.publish(VarArrival, (Customer,))
        self.publish(VarLoaded, (Customer,), zeros=True)
