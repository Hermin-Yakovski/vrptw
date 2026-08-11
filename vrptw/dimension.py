from or_register import Dimension, Index, Metric

Customer = Dimension("Customer", "客户", "C")
Route = Dimension("Route", "路线", "R")
Segment = Dimension("Segment", "路段", "S")
Vehicle = Dimension("Vehicle", "车辆", "V")


__all__ = [
    "Customer",
    "Index",
    "Metric",
    "Route",
    "Segment",
    "Vehicle",
]
