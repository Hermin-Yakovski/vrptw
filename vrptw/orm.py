from or_scenario import orm
from or_scenario.orm import DimParameter, DimSnapshot, DimVersion

# dimension tables
DimVehicle = orm.generate_dimension_table("Vehicle")
DimCustomer = orm.generate_dimension_table(
    "Customer",
    x=orm.generate_extra_column("x", "integer", nullable=False),
    y=orm.generate_extra_column("y", "integer", nullable=False),
    instance=orm.generate_extra_column("instance", "text", nullable=False),
)

# fact tables
FactCustomer = orm.generate_fact_table("Customer")
FactVehicle = orm.generate_fact_table("Vehicle")

# sol tables
SolCustomerVehicle = orm.generate_sol_table("Customer", "Vehicle")


__all__ = [
    "DimCustomer",
    "DimParameter",
    "DimSnapshot",
    "DimVehicle",
    "DimVersion",
    "FactCustomer",
    "FactVehicle",
    "SolCustomerVehicle",
]
