"""Contains all Exceptions for the Services"""
from typing import Dict, List, Union

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


class ServiceBulkException(ServiceError):
    """Exception for the bulk requests"""

    def __init__(
        self,
        error_msg: str,
        status_code: int,
        success_services: List[Service],
        error: Union[ServiceDuplicate, Service],
    ):
        super().__init__(error_msg, status_code)
        self.status_code = status_code
        if isinstance(error, ServiceError):
            self.error = error.json_data
        else:
            self.error = error.get_attributes()

        self.success_services: List[Dict] = []
        for success_service in success_services:
            self.success_services.append(success_service.get_attributes())

        # fmt:off
        self.json_data = {
            "error": self.error_msg,
            "status": self.status_code,
            "success_services": self.success_services,
            "failed_service": self.error
        }
        # fmt:on


class ServiceNotFound(ServiceError):
    """Exception if the requested service does not exist in the DB"""

    def __init__(self, error_msg: str, status_code: int, service_name: str):
        super().__init__(error_msg, status_code)
        self.service_name = service_name
        # fmt:off
        self.json_data = {
            "error": self.error_msg,
            "status": self.status_code,
            "service": self.service_name
        }
        # fmt:on
