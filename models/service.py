from typing import Optional
from pydantic import BaseModel


class Service(BaseModel):
    name: str


class JSON_Service(Service):
    url: str
    ping: Optional[bool] = True


class Ping_Service(Service):
    url: str
    response_time: float
