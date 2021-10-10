"""Contains the BaseModel for the Service"""

from typing import Optional
from pydantic import BaseModel


class Service(BaseModel):
    """BaseModel with only a name"""
    name: str


class DBService(Service):
    """This Object can be written to the DB"""
    url: str
    ping: Optional[bool] = True


class PingService(Service):
    """Return Object if you pinged a Service"""
    url: str
    response_time: float
