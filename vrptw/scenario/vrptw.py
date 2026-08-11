from __future__ import annotations

from typing import TYPE_CHECKING

from or_scenario import Scenario
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dimension import *
from ..orm import *
from ..parameter import *

if TYPE_CHECKING:
    from ..schema import VrptwRequest


class VrptwScenario(Scenario):
    _instance: str
    _snapshot_id: int

    def __init__(self, request: VrptwRequest):
        super().__init__(request)
        self._instance = request.instance

    def load(self, session: Session | None = None) -> None:
        self._snapshot_id, self._version_id = session.execute(  # type: ignore[union-attr]
            select(DimVersion.snapshot_id, DimVersion.id).where(DimVersion.name == self._instance)  # type: ignore[attr-defined]
        ).one()

        self._load_vehicles(session)
        self._load_customers(session)

    def _load_customers(self, session: Session | None = None) -> None:
        """
        SELECT c.x, c.y, c.id, c.name, c.name_en
             , p.name_en AS parameter_name, f.quantity
        FROM dim_customer c
        INNER JOIN fact_customer f
            ON f.snapshot_id = self._snapshot_id
            AND f.customer_id = c.id
            AND f.parameter_id IN (Earliest.id, Latest.id, ServiceTime.id)
        INNER JOIN dim_parameter p
            ON p.id = f.parameter_id
        WHERE c.instance = self._instance
        """
        param_ids = (Demand.id, Earliest.id, Latest.id, ServiceTime.id)

        rows = session.execute(  # type: ignore[union-attr]
            select(
                DimCustomer.x,  # type: ignore[attr-defined]
                DimCustomer.y,  # type: ignore[attr-defined]
                DimCustomer.id,  # type: ignore[attr-defined]
                DimCustomer.name,  # type: ignore[attr-defined]
                DimCustomer.name_en,  # type: ignore[attr-defined]
                DimParameter.name_en.label("parameter_name"),  # type: ignore[attr-defined]
                FactCustomer.quantity,  # type: ignore[attr-defined]
            )
            .join(FactCustomer, FactCustomer.customer_id == DimCustomer.id)  # type: ignore[attr-defined]
            .join(DimParameter, DimParameter.id == FactCustomer.parameter_id)  # type: ignore[attr-defined]
            .where(
                FactCustomer.snapshot_id == self._snapshot_id,  # type: ignore[attr-defined]
                FactCustomer.parameter_id.in_(param_ids),  # type: ignore[attr-defined]
                DimCustomer.instance == self._instance,  # type: ignore[attr-defined]
            )
        ).all()

        for row in rows:
            c: int = row.id
            if c >= 40:
                continue
            self._data[Id][Customer,][c,] = row.id
            self._data[Name][Customer,][c,] = row.name
            self._data[Code][Customer,][c,] = row.name_en
            self._data[X][Customer,][c,] = row.x
            self._data[Y][Customer,][c,] = row.y
            match row.parameter_name:
                case Demand.name:
                    self._data[Demand][Customer,][c,] = row.quantity
                case Earliest.name:
                    self._data[Earliest][Customer,][c,] = row.quantity
                case Latest.name:
                    self._data[Latest][Customer,][c,] = row.quantity
                case ServiceTime.name:
                    self._data[ServiceTime][Customer,][c,] = row.quantity

    def _load_vehicles(self, session: Session | None = None) -> None:
        rows = session.execute(  # type: ignore[union-attr]
            select(DimVehicle.id, DimVehicle.name, DimVehicle.name_en, FactVehicle.quantity)  # type: ignore[attr-defined]
            .join(FactVehicle, FactVehicle.vehicle_id == DimVehicle.id)  # type: ignore[attr-defined]
            .where(
                FactVehicle.snapshot_id == self._snapshot_id,  # type: ignore[attr-defined]
                FactVehicle.parameter_id == Capacity.id,  # type: ignore[attr-defined]
                FactVehicle.quantity > 0,  # type: ignore[attr-defined]
            )
        ).all()

        for row in rows:
            v: int = row.id
            self._data[Id][Vehicle,][v,] = row.id
            self._data[Name][Vehicle,][v,] = row.name
            self._data[Code][Vehicle,][v,] = row.name_en
            self._data[Capacity][Vehicle,][v,] = row.quantity
