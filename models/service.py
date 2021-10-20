"""Contains the BaseModel for the Service"""

import re
from typing import Optional

from pydantic import BaseModel, validator

from models.validation_error import InvalidURL


class Service(BaseModel):
    """BaseModel with only a name

    Args:
        name (str): Name of the Service
    """

    name: str
    container_name: str = None


class ConfigService(Service):
    """This Object can be written to the config

    Args:
        url (str): URL String
        ping (bool): Activate automated ping. Default set to True
    """

    url: str
    ping: Optional[bool] = True

    @validator("url")
    def validate_service_url(cls, url) -> None:
        regex = re.compile(r"^(https?:\/\/(\w+\.)+\w+(:\d+)?(/\w*)*)$")
        if not regex.match(url):
            raise InvalidURL("The URL ist not correct http(s)://some.url:1337/", url)
        return url


class PingService(Service):
    """Return Object if you pinged a Service"""

    url: str = None
    response_time: float = None
