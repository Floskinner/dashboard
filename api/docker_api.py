"""API for managing docker containers"""

from typing import List
import fastapi
from models.docker_container import DockerContainer

from services import docker_service

router = fastapi.APIRouter()


@router.get("/api/docker/container", response_model=List[DockerContainer])
async def get_container() -> List[DockerContainer]:
    """Get a List of all Docker Container on the Server

    Returns:
        List[DockerContainer]: List of own DockerContainer class
    """
    return await docker_service.get_containers()


@router.get("/api/docker/{name}/stop", response_model=DockerContainer)
async def stop_container(name: str):
    """Stop the docker container that has the specific name

    Args:
        name (str): Name of the container

    Raises:
        ContainerNotFound: The container with this name does not exists

    Returns:
        DockerContainer: The stopped docker container
    """
    return await docker_service.stop_container(name)


@router.get("/api/docker/{name}/start", response_model=DockerContainer)
async def start_container(name: str):
    """Start the docker container that has the specific name.
    There is no validation for active running of the container after starting

    Args:
        name (str): Name of the container

    Raises:
        error: The container with this name does not exists

    Returns:
        DockerContainer: The started docker container
    """
    return await docker_service.start_container(name)
