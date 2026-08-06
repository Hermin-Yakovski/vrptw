from __future__ import annotations
from typing import TYPE_CHECKING

from or_algo.lp import (
    # Symbol,
    # Var,
    # Constr,
    # LpStep,
    CreateVar,
    CreateConstr,
    # CreateConstrCalculateMetric,
    # LpSolver,
    exception, VarKey,
)
from or_register import Register

from ....dimension import *
from ....parameter import *
from .symbol import *

if TYPE_CHECKING:
    from typing import Tuple

    from ortools.linear_solver import pywraplp
    from or_register import RegisterKey


class CreateVarTravel(CreateVar):

    def __init__(self):
        super().__init__(VarTravel)

    def run(self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]) -> None:
        for i, in data[Id][Customer,].keys():
            for j, in data[Id][Customer,].keys():
                if i == j:
                    continue
                name = '{}{}{}'.format(self._symbol, (Customer, Customer,), (i,j,))
                var[VarTravel][Customer, Customer,][i, j,] = model.IntVar(0, 1, name=name)
                manhattan_distance = abs(data[X][Customer,][i,] - data[X][Customer,][j,]) \
                    + abs(data[Y][Customer,][i,] - data[Y][Customer,][j,])
                model.Objective().SetCoefficient(
                    var[VarTravel][Customer, Customer,][i, j,], -1.0 * manhattan_distance)


class CreateVarArrival(CreateVar):

    def __init__(self):
        super().__init__(VarArrival)

    def run(self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]) -> None:
        for i, in data[Id][Customer,].keys():
            name = '{}{}{}'.format(self._symbol, (Customer,), (i,))
            var[self._symbol][Customer,][i,]  = model.NumVar(
                data[Earliest][Customer,][i,], data[Latest][Customer,][i,], name=name)
            model.Objective().SetCoefficient(var[self._symbol][Customer,][i,], -0)


class CreateVarLoaded(CreateVar):

    def __init__(self):
        super().__init__(VarLoaded)

    def run(self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]) -> None:
        for i, in data[Id][Customer,].keys():
            name = '{}{}{}'.format(self._symbol, (Customer,), (i,))
            var[self._symbol][Customer,][i,]  = model.NumVar(
                0, 100, name=name)
            model.Objective().SetCoefficient(var[self._symbol][Customer,][i,], -0)


class CreateConstrArcInOut(CreateConstr):
    def __init__(self):
        super().__init__(ConstrArcInOut)

    def run(self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]) -> None:
        for c, in data[Id][Customer,].keys():
            name = '{}{}{}_equal'.format(self._symbol, (Customer,), (c,))
            model.Add(
                var[VarTravel][Customer, Customer,][:, c,].sum()
                == var[VarTravel][Customer, Customer,][c, :,].sum(), name=name)

            if c:    # customers
                name = '{}{}{}_customer'.format(self._symbol, (Customer,), (c,))
                model.Add(var[VarTravel][Customer, Customer,][:, c,].sum() == 1, name=name)
            else:    # depot
                name = '{}{}{}_depot'.format(self._symbol, (Customer,), (c,))
                model.Add(var[VarTravel][Customer, Customer,][:, c, ].sum() >= 1, name=name)


class CreateConstrCalculateCapacity(CreateConstr):
    _big_m = 500

    def __init__(self):
        super().__init__(ConstrCalculateCapacity)

    def run(self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]) -> None:
        var[VarLoaded][Customer,][0,].SetBounds(0, 0)    # loaded of depot

        for i, j in var[VarTravel][Customer, Customer,].keys():
            if not j:
                # todo: mark depot
                continue
            name = '{}{}{}'.format(self._symbol, (Customer, Customer,), (i, j))
            model.Add(
                var[VarLoaded][Customer,][j,]
                >= var[VarLoaded][Customer,][i,] + data[Demand][Customer,][j,]
                + self._big_m * (var[VarTravel][Customer, Customer,][i, j,] - 1), name=name)


class CreateConstrCalculateArrival(CreateConstr):
    _big_m = 2000

    def __init__(self):
        super().__init__(ConstrCalculateArrival)

    def run(self, data: Register[RegisterKey], model: pywraplp.Solver, var: Register[VarKey]) -> None:
        var[VarArrival][Customer,][0,].SetBounds(0, 0)    # arrival of depot

        for i, j in var[VarTravel][Customer, Customer,].keys():
            if not j:
                # todo: mark depot
                continue

            name = '{}{}{}'.format(self._symbol, (Customer, Customer,), (i, j))
            model.Add(
                var[VarArrival][Customer,][j,]
                >= var[VarArrival][Customer,][i,]
                + data[ServiceTime][Customer,][i,]
                + abs(data[X][Customer,][i,] - data[X][Customer,][j,])
                + abs(data[Y][Customer,][i,] - data[Y][Customer,][j,])
                + self._big_m * (var[VarTravel][Customer, Customer,][i, j,] - 1), name=name)
