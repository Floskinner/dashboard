"""Backend manager for Docker calls"""

from typing import List
import docker
from docker.models.containers import Container

from models.docker_container import DockerContainer

d_client = docker.from_env()


def get_containers() -> List[DockerContainer]:
    """Get a list of all Docker Container on the Server

    Returns:
        List[DockerContainer]: List of all Container
    """
    d_container: List[Container] = d_client.containers.list(all=True)
    api_container = []
    for container in d_container:
        api_container.append(DockerContainer(id=container.id, name=container.name, status=container.status))
    return api_container
