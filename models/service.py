"""Contains the BaseModel for the Service"""

from typing import Dict, Optional

from pydantic import BaseModel


class Service(BaseModel):
    """BaseModel with only a name

    Args:
        name (str): Name of the Service
    """

    name: str

    def get_attributes(self) -> Dict:
        """Return all attributes from the Class as a Dict

        Returns:
            Dict: Attributes of the class
        """
        attr = {}
        for attribute, value in self.__dict__.items():
            attr[attribute] = value
        return attr


class DBService(Service):
    """This Object can be written to the DB

    Args:
        url (str): URL String
        ping (bool): Activate automated ping. Default set to True
    """

    url: str
    ping: Optional[bool] = True


class PingService(Service):
    """Return Object if you pinged a Service"""

    url: str
    response_time: float
