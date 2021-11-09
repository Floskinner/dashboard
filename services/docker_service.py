"""Backend manager for Docker calls"""

from typing import List

import docker
from docker.errors import NotFound
from docker.models.containers import Container
from models.docker_container import DockerContainer
from models.docker_container_error import ContainerNotFound

d_client = docker.from_env()


async def get_containers() -> List[DockerContainer]:
    """Get a list of all Docker Container on the Server

    Returns:
        List[DockerContainer]: List of all Container
    """
    d_container: List[Container] = d_client.containers.list(all=True)
    api_container = []
    for container in d_container:
        api_container.append(DockerContainer(id=container.id, name=container.name, status=container.status))
    return api_container


async def __get_d_container(name: str) -> Container:
    """Get specific docker container with his name

    Args:
        name (str): unique name of the container

    Raises:
        ContainerNotFound: If no container is found with the name

    Returns:
        Container: Docker Container that was found with the same name
    """
    try:
        return d_client.containers.get(name)
    except NotFound as error:
        raise ContainerNotFound("Container not found", name) from error


async def stop_container(name: str) -> DockerContainer:
    """Stop the docker container that has the specific name

    Args:
        name (str): Name of the container

    Raises:
        ContainerNotFound: The container with this name does not exists

    Returns:
        DockerContainer: The stopped docker container
    """
    try:
        container = await __get_d_container(name)
    except ContainerNotFound as error:
        raise error
    container.stop()
    return DockerContainer(id=container.id, name=container.name, status=container.status)


async def start_container(name: str) -> DockerContainer:
    """Start the docker container that has the specific name.
    There is no validation for active running of the container after starting

    Args:
        name (str): Name of the container

    Raises:
        error: The container with this name does not exists

    Returns:
        DockerContainer: The started docker container
    """
    try:
        container = await __get_d_container(name)
    except ContainerNotFound as error:
        raise error
    container.start()
    return DockerContainer(id=container.id, name=container.name, status=container.status)
