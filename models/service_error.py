"""Contains all Exceptions for the Services"""
from models.service import Service


class ServiceError(Exception):
    """Base Exception for the Service Exceptions"""

    def __init__(self, error_msg: str, status_code: int):
        super().__init__(error_msg)
        self.error_msg = error_msg
        self.status_code = status_code
        # fmt:off
        self.json_data = {
            "error": self.error_msg,
            "status": self.status_code
        }
        # fmt:on


class ServiceDuplicate(ServiceError):
    """Exception if you try to add a already existing Service"""

    def __init__(self, error_msg: str, status_code: int, service: Service):
        super().__init__(error_msg, status_code)
        self.service = service
        # fmt:off
        self.json_data = {
            "error": self.error_msg,
            "status": self.status_code,
            "service": self.service
        }
        # fmt:on


class ServiceNotFound(ServiceError):
    """Exception if the requested service does not exist in the DB"""

    def __init__(self, error_msg: str, status_code: int, service: Service):
        super().__init__(error_msg, status_code)
        self.service = service
        # fmt:off
        self.json_data = {
            "error": self.error_msg,
            "status": self.status_code,
            "service": self.service
        }
        # fmt:on
