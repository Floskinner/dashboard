"""Contains all Exceptions for the Services"""
from typing import List

from models.service import Service


class ServiceError(Exception):
    """Base Exception for the Service Exceptions"""

    def __init__(self, error_msg: str, status_code: int, service: Service):
        super().__init__(error_msg)
        self.error_msg = error_msg
        self.status_code = status_code
        self.service = service


class ServiceDuplicate(ServiceError):
    """Exception if you try to add a already existing Service"""


class ServiceNotFound(ServiceError):
    """Exception if the requested service does not exist in the DB"""


class PingError(ServiceError):
    """Exception if Status Code is invalid"""


class BulkServiceError(Exception):
    """Exception for Bulk requests"""

    def __init__(self, error_msg: str, status_code: int, success: List[Service], faild: List[ServiceError]):
        super().__init__(error_msg)
        self.error_msg = error_msg
        self.status_code = status_code
        self.success = success
        self.faild = faild
