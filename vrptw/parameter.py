from typing import List

from register import Parameter
from register import Code, Id, Name

from .dimension import *


# parameters of vehicles
Capacity = Parameter(10, 'Capacity', '车辆容量', float)

# parameters of customers
X = Parameter(20, 'X', '客户坐标X', int)
Y = Parameter(30, 'Y', '客户坐标Y', int)
Demand = Parameter(40, 'Demand', '客户需求量', float)
## time-window-related parameters
Earliest = Parameter(50, 'Earliest', '最早到达时间', int)
Latest = Parameter(60, 'Latest', '最晚到达时间', int)
ServiceTime = Parameter(70, 'ServiceTime', '服务时间', int)


# relations
RouteId = Parameter(1000, 'RouteId', '线路编号', Route)    # Vehicle -> Route, 1:1 mapping
VehicleId = Parameter(1010, 'VehicleId', '车辆编号', Vehicle)  # Route -> Vehicle, 1:1 mapping
SegmentList = Parameter(1020, 'SegmentList', '线路路段有序集', List[Segment])  # Route/Vehicle -> list of Segment
CustomerList = Parameter(1030, 'CustomerList', '客户有序集', List[Customer])  # Route/Vehicle -> list of Customer


__all__ =[
    'Code', 'Id', 'Name',

    'Capacity',

    'X', 'Y', 'Demand',
    'Earliest', 'Latest', 'ServiceTime',

    'RouteId', 'VehicleId', 'SegmentList',
]
