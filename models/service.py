"""Contains the BaseModel for the Service"""

from typing import Optional

from pydantic import BaseModel


class Service(BaseModel):
    """BaseModel with only a name

    Args:
        name (str): Name of the Service
    """

    name: str


class ConfigService(Service):
    """This Object can be written to the DB

    Args:
        url (str): URL String
        ping (bool): Activate automated ping. Default set to True
    """

    url: str
    ping: Optional[bool] = True


class PingService(Service):
    """Return Object if you pinged a Service"""

    url: str = None
    response_time: float = None
