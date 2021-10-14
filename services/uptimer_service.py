"""Backend manager for the Services"""
from typing import List

import httpx
from httpx import Response
from models.service import ConfigService, PingService, Service
from models.service_error import PingError, ServiceDuplicate, ServiceNotFound

from services import get_db_services, safe_db_services, services_path


def add_service(service: ConfigService) -> ConfigService:
    """Add the service to the service configuration. Unique Name required

    Args:
        service (ConfigService): Service to add

    Raises:
        ServiceDuplicate: Service is already in the DB. Unique Name required

    Returns:
        ConfigService: Added service
    """
    try:
        get_service(service.name)
    except ServiceNotFound:
        db_services = get_services()
        db_services.append(service)
        safe_db_services(db_services, services_path)
        return service
    else:
        raise ServiceDuplicate("Service Name is already in the configuration", 409, service)


def delete_service(service: Service) -> ConfigService:
    """Delete one Service from the services configuration

    Args:
        service (Service): Service to delete from the config

    Returns:
        ConfigService: Return Service if success
    """
    service = get_service(service.name)
    db_services = get_services()
    db_services.remove(service)
    safe_db_services(db_services, services_path)
    return service


def get_services() -> List[ConfigService]:
    """Get all saved services from the JSON file

    Returns:
        List[ConfigService]: List of all services
    """
    return get_db_services(services_path)


def get_service(name: str) -> ConfigService:
    """Get a Service from the DB

    Args:
        name (str): Name of the Service

    Raises:
        ServiceNotFound: If the Service can not be found

    Returns:
        ConfigService: Return found Service with all informations
    """
    services: List[ConfigService] = get_db_services(services_path)

    for service in services:
        if service.name.lower() == name.lower():
            return service
    raise ServiceNotFound("Der Service wurde nicht in der DB gefunden", 404, name)


async def ping_service(service: PingService) -> PingService:
    """Ping the Service with the given url or search for the url in the service configuration

    Args:
        service (PingService): Services to check

    Raises:
        PingError: Error if status_code >= 400
        PingError: Error if the url is invalid

    Returns:
        PingService: Service with filled response_time
    """
    if service.url is None:
        db_service: ConfigService = get_service(service.name)
        service = PingService(**dict(db_service))
    try:
        async with httpx.AsyncClient() as client:
            resp: Response = await client.get(service.url)
            resp.raise_for_status()
            service.response_time = resp.elapsed.total_seconds()
            return service
    except httpx.HTTPStatusError as error:
        raise PingError(str(error), 404, service) from error
    except httpx.RequestError as error:
        raise PingError(str(error), 408, service) from error
