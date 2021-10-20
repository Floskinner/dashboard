"""Contains the BaseModel for the Docker Container"""
from pydantic import BaseModel


class DockerContainer(BaseModel):
    """BaseModel for the return of the API call"""
    id: str
    name: str
    status: str
