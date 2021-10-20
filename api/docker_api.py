"""API for managing docker containers"""

from typing import List
import fastapi
from models.docker_container import DockerContainer

from services import docker_service

router = fastapi.APIRouter()


@router.get("/api/docker/container", response_model=List[DockerContainer])
def get_container() -> List[DockerContainer]:
    """Get a List of all Docker Container on the Server

    Returns:
        List[DockerContainer]: List of own DockerContainer class
    """
    return docker_service.get_containers()
