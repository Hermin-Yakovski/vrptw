from typing import List

# todo: fix or_register interface
from or_register.key import NumKey, StrKey, DimensionKey, DimensionCollectionKey
from or_register.parameter import Code, Id, Name

from .dimension import *


# parameters of vehicles
Capacity = NumKey(110, 'Capacity', '车辆容量')

# parameters of customers
X = NumKey(120, 'X', '客户坐标X')
Y = NumKey(130, 'Y', '客户坐标Y')
Demand = NumKey(140, 'Demand', '客户需求量')
## time-window-related parameters
Earliest = NumKey(150, 'Earliest', '最早到达时间')
Latest = NumKey(160, 'Latest', '最晚到达时间')
ServiceTime = NumKey(170, 'ServiceTime', '服务时间')

# decisive parameters
Sequence = NumKey(10, 'Sequence', '访问顺序' , int)    # sequence of customer i in route j

# relations
RouteId = DimensionKey(1000,  Route)    # Vehicle -> Route, 1:1 mapping
VehicleId = DimensionKey(1010,  Vehicle)    # Route -> Vehicle, 1:1 mapping
SegmentList = DimensionCollectionKey(1020, Segment)    # Route/Vehicle -> list of Segment
CustomerList = DimensionCollectionKey(1030, Customer)    # Route/Vehicle -> list of Customer

__all__ =[
    'Code', 'Id', 'Name',

    'Capacity',

    'X', 'Y', 'Demand',
    'Earliest', 'Latest', 'ServiceTime',

    'RouteId', 'VehicleId', 'SegmentList',
]
