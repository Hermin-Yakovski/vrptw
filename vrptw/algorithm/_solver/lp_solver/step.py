from __future__ import annotations

from typing import TYPE_CHECKING

from or_algo.lp import (
    CreateConstr,
    # Symbol,
    # Var,
    # Constr,
    # LpStep,
    CreateVar,
    VarKey,
)
from or_register import Register

from ....dimension import *
from ....parameter import *
from .symbol import *

if TYPE_CHECKING:
    from or_register import RegisterKey
    from ortools.linear_solver import pywraplp  # type: ignore[import-untyped]


class CreateVarTravel(CreateVar):
    def __init__(self) -> None:
        super().__init__(VarTravel)

    def run(
        self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]
    ) -> None:
        for (i,) in data[Id][Customer,].keys():
            for (j,) in data[Id][Customer,].keys():
                if i == j:
                    continue
                name = f"{self._symbol}{(Customer, Customer)}{(i, j)}"
                var[VarTravel][
                    Customer,
                    Customer,
                ][
                    i,
                    j,
                ] = model.IntVar(0, 1, name=name)
                manhattan_distance = abs(data[X][Customer,][i,] - data[X][Customer,][j,]) + abs(  # type: ignore[operator]
                    data[Y][Customer,][i,] - data[Y][Customer,][j,]  # type: ignore[operator]
                )
                model.Objective().SetCoefficient(
                    var[VarTravel][
                        Customer,
                        Customer,
                    ][
                        i,
                        j,
                    ],
                    -1.0 * manhattan_distance,
                )


class CreateVarArrival(CreateVar):
    def __init__(self) -> None:
        super().__init__(VarArrival)

    def run(
        self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]
    ) -> None:
        for (i,) in data[Id][Customer,].keys():
            name = f"{self._symbol}{(Customer,)}{(i,)}"
            var[self._symbol][Customer,][i,] = model.NumVar(
                data[Earliest][Customer,][i,], data[Latest][Customer,][i,], name=name
            )
            model.Objective().SetCoefficient(var[self._symbol][Customer,][i,], -0)


class CreateVarLoaded(CreateVar):
    _capacity: float

    def __init__(self, capacity: float) -> None:
        super().__init__(VarLoaded)
        import math

        self._capacity = math.inf if capacity is None else capacity

    def run(
        self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]
    ) -> None:
        for (i,) in data[Id][Customer,].keys():
            name = f"{self._symbol}{(Customer,)}{(i,)}"
            var[self._symbol][Customer,][i,] = model.NumVar(0, self._capacity, name=name)
            model.Objective().SetCoefficient(var[self._symbol][Customer,][i,], -0)


class CreateConstrArcInOut(CreateConstr):
    def __init__(self) -> None:
        super().__init__(ConstrArcInOut)

    def run(
        self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]
    ) -> None:
        for (c,) in data[Id][Customer,].keys():
            name = f"{self._symbol}{(Customer,)}{(c,)}_equal"
            model.Add(
                var[VarTravel][
                    Customer,
                    Customer,
                ][
                    :,
                    c,
                ].sum(model=model, var=var)
                == var[VarTravel][
                    Customer,
                    Customer,
                ][
                    c,
                    :,
                ].sum(model=model, var=var),
                name=name,
            )

            if c:  # customers
                name = f"{self._symbol}{(Customer,)}{(c,)}_customer"
                model.Add(
                    var[VarTravel][
                        Customer,
                        Customer,
                    ][
                        :,
                        c,
                    ].sum(model=model, var=var)
                    == 1,
                    name=name,
                )
            else:  # depot
                name = f"{self._symbol}{(Customer,)}{(c,)}_depot"
                model.Add(
                    var[VarTravel][
                        Customer,
                        Customer,
                    ][
                        :,
                        c,
                    ].sum(model=model, var=var)
                    >= 1,
                    name=name,
                )


class CreateConstrCalculateCapacity(CreateConstr):
    _big_m = 500

    def __init__(self) -> None:
        super().__init__(ConstrCalculateCapacity)

    def run(
        self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]
    ) -> None:
        var[VarLoaded][Customer,][0,].SetBounds(0, 0)  # loaded of depot

        for i, j in var[VarTravel][
            Customer,
            Customer,
        ].keys():
            if not j:
                # todo: mark depot
                continue
            name = f"{self._symbol}{(Customer, Customer)}{(i, j)}"
            model.Add(
                var[VarLoaded][Customer,][j,]
                >= var[VarLoaded][Customer,][i,]  # type: ignore[operator]
                + data[Demand][Customer,][j,]
                + self._big_m
                * (
                    var[VarTravel][  # type: ignore[operator]
                        Customer,
                        Customer,
                    ][
                        i,
                        j,
                    ]
                    - 1
                ),
                name=name,
            )


class CreateConstrCalculateArrival(CreateConstr):
    _big_m = 2000

    def __init__(self) -> None:
        super().__init__(ConstrCalculateArrival)

    def run(
        self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]
    ) -> None:
        var[VarArrival][Customer,][0,].SetBounds(0, 0)  # arrival of depot

        for i, j in var[VarTravel][
            Customer,
            Customer,
        ].keys():
            if not j:
                # todo: mark depot
                continue

            name = f"{self._symbol}{(Customer, Customer)}{(i, j)}"
            model.Add(
                var[VarArrival][Customer,][j,]
                >= var[VarArrival][Customer,][i,]  # type: ignore[operator]
                + data[ServiceTime][Customer,][i,]
                + abs(data[X][Customer,][i,] - data[X][Customer,][j,])  # type: ignore[operator]
                + abs(data[Y][Customer,][i,] - data[Y][Customer,][j,])  # type: ignore[operator]
                + self._big_m
                * (
                    var[VarTravel][  # type: ignore[operator]
                        Customer,
                        Customer,
                    ][
                        i,
                        j,
                    ]
                    - 1
                ),
                name=name,
            )
