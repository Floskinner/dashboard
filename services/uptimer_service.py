"""Backend manager for the Services"""
from json.decoder import JSONDecodeError
from typing import List

import httpx
from httpx import Response
from models.service import ConfigService, PingService, Service
from models.service_error import PingError, ServiceDuplicate, ServiceNotFound

from services import get_conf_services, safe_conf_services, services_path


def add_service(service: ConfigService) -> ConfigService:
    """Add the service to the service configuration. Unique Name required

    Args:
        service (ConfigService): Service to add

    Raises:
        ServiceDuplicate: Service is already in the Config. Unique Name required

    Returns:
        ConfigService: Added service
    """
    try:
        get_service(service.name)
    except ServiceNotFound:
        conf_services = get_services()
        conf_services.append(service)
        safe_conf_services(conf_services, services_path)
        return service
    except JSONDecodeError:
        safe_conf_services([service], services_path)
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
    conf_services = get_services()
    conf_services.remove(service)
    safe_conf_services(conf_services, services_path)
    return service


def get_services() -> List[ConfigService]:
    """Get all saved services from the JSON file

    Returns:
        List[ConfigService]: List of all services
    """
    return get_conf_services(services_path)


def get_service(name: str) -> ConfigService:
    """Get a Service from the Config

    Args:
        name (str): Name of the Service

    Raises:
        ServiceNotFound: If the Service can not be found

    Returns:
        ConfigService: Return found Service with all informations
    """
    services: List[ConfigService] = get_conf_services(services_path)

    for service in services:
        if service.name.lower() == name.lower():
            return service
    raise ServiceNotFound("Der Service wurde nicht in der Configuration gefunden", 404, name)


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
        conf_service: ConfigService = get_service(service.name)
        service = PingService(**dict(conf_service))
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


def update_service(old_service: Service, updated_service: ConfigService) -> ConfigService:
    """Update the setting of one service. Also can change the name of the service if not already exist

    Args:
        old_service (Service): The that need to be updated
        updated_service (ConfigService): The new configuration for the service

    Raises:
        ServiceNotFound: If the Service to update is not in the configuration

    Returns:
        ConfigService: Updated settings
    """
    updated = False
    conf_services = get_services()
    old_service = get_service(old_service.name)

    if old_service.name != updated_service.name:
        add_service(updated_service)
        delete_service(old_service)
        return updated_service

    for index, conf_service in enumerate(conf_services):
        if conf_service == old_service:
            conf_services[index] = updated_service
            updated = True
            break
    safe_conf_services(conf_services, services_path)

    if not updated:
        raise ServiceNotFound("Service to update not found", 404, updated_service)

    return updated_service
