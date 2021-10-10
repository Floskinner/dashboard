from models.service import Service


class ServiceError(Exception):
    """Exception for duplicate Service"""

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
