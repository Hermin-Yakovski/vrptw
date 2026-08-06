from or_algo.lp import ConstrKey, VarKey
from or_register import NumKey

from ....parameter import *    # from tran.parameter import *


VarTravel = VarKey(20, 'Travel', '使用路段', sign='a', vtype=bool)
VarArrival = VarKey(30, 'Arrival', '到达时间', sign='t', vtype=int)
VarLoaded = VarKey(40, 'Loaded', '到达时载重', sign='l', vtype=float)

ConstrArcInOut = ConstrKey(10010, 'ConstrArcInOut', '客户出度入度', sign='constr10')
ConstrCalculateCapacity = ConstrKey(10020, 'ConstrCalculateCapacity', '计算载重', sign='constr20')
ConstrCalculateArrival = ConstrKey(10030, 'ConstrCalculateArrival', '计算到达时间', sign='constr30')
#
# VarActivate = Var(Activate, 't')
# VarTransit = Var(Transit, 'x')

# ConstrActivateRelation = Constr('ConstrActivateRelation', '激活变量间的关系', 'ConstrActivateRelation')
# ConstrActivateLineUnique = Constr('ConstrActivateLineUnique', '激活线路唯一', 'ConstrActivateLineUnique')
# ConstrCalculateTransit = Constr('ConstrCalculateTransit', '计算途径件量', 'ConstrCalculateTransit')


__all__ = [
    'VarTravel',
    'VarArrival',
    'VarLoaded',

    'ConstrArcInOut',
    'ConstrCalculateCapacity',
    'ConstrCalculateArrival',

    # 'ConstrActivateRelation',
    # 'ConstrActivateLineUnique',
    # 'ConstrCalculateTransit',
]
