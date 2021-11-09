"""Contain all Exception for Docker Exceptions"""


class DockerError(Exception):
    """Base class for the Docker Exceptions"""

    def __init__(self, error_msg: str):
        super().__init__(error_msg)
        self.error_msg = error_msg


class ContainerNotFound(DockerError):
    """Exception that is used for docker container that are not found on the system"""

    def __init__(self, error_msg: str, container_name: str):
        super().__init__(error_msg)
        self.container_name = container_name
