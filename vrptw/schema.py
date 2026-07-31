from datetime import datetime

from or_scenario import BaseRequest, BaseResponse
from pydantic import Field


class VrptwRequest(BaseRequest):
    """Request for the VRPTW API."""
    instance: str = Field(..., description='Instance name from the Solomon VRPTW benchmarks')


class VrptwResponse(BaseResponse):
    """Response for the VRPTW API."""
    pass


__all__ = [
    'VrptwRequest',
    'VrptwResponse',
]
