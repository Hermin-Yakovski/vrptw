from datetime import datetime

from or_scenario import BaseRequest, BaseResponse
from pydantic import Field



class TranRequest(BaseRequest):
    """Request for the tran API."""
    date: datetime = Field(default=datetime.today(), description='做（次日）计划时的日期')
    horizon: int = Field(default=10, description='日期跨度')


class TranResponse(BaseResponse):
    """Response for the tran API."""
    pass


__all__ = [
    'TranRequest',
    'TranResponse',
]
