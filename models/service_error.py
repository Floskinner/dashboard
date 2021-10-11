"""Contains all Exceptions for the Services"""
from typing import Dict, List

from models.service import DBService, Service


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

    def __init__(self, error_msg: str, status_code: int, service: DBService):
        super().__init__(error_msg, status_code)
        # fmt:off
        self.service = service.get_attributes()
        self.json_data = {
            "error": self.error_msg,
            "status": self.status_code,
            "service": self.service
        }
        # fmt:on


class ServiceAddException(ServiceError):
    """Exception for the bulk post request to add services"""

    def __init__(
        self,
        error_msg: str,
        status_code: int,
        success_services: List[Service],
        error_service: ServiceDuplicate,
    ):
        super().__init__(error_msg, status_code)
        self.status_code = status_code
        self.error_service = error_service.json_data

        self.success_services: List[Dict] = []
        for success_service in success_services:
            self.success_services.append(success_service.get_attributes())

        # fmt:off
        self.json_data = {
            "error": self.error_msg,
            "status": self.status_code,
            "added_services": self.success_services,
            "error_service": self.error_service
        }
        # fmt:on


class ServiceNotFound(ServiceError):
    """Exception if the requested service does not exist in the DB"""

    def __init__(self, error_msg: str, status_code: int, service: Service):
        super().__init__(error_msg, status_code)
        self.service = service.get_attributes()
        # fmt:off
        self.json_data = {
            "error": self.error_msg,
            "status": self.status_code,
            "service": self.service
        }
        # fmt:on
