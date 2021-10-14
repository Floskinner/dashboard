"""Backend manager for the Services"""
import json
from typing import List

import httpx
from httpx import Response
from models.service import DBService, PingService, Service
from models.service_error import PingError, ServiceBulkException, ServiceDuplicate, ServiceError, ServiceNotFound

from services import get_db_services, safe_db_services, services_path


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
        db_service: DBService = get_service(service.name)
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


def add_services(services: List[DBService]) -> List[DBService]:
    """Add a Service to the DB.

    Args:
        services (DBService): Service with a requirements for the DB

    Raises:
        ServiceBulkException: If something bad happend

    Returns:
        DBService: On succes return Serivce
    """
    added_services: List[DBService] = []
    failed_services: List[ServiceError] = []
    for service in services:
        try:
            all_services: List[DBService] = get_db_services(services_path)
            if service in all_services:
                raise ServiceDuplicate(
                    "Der Serivce ist bereits vorhaben", 409, all_services[all_services.index(service)]
                )
            all_services.append(service)
            added_services.append(service)

        except json.decoder.JSONDecodeError:
            all_services: List[DBService] = []
            all_services.append(service)
            added_services.append(service)

        except ServiceDuplicate as error:
            failed_services.append(error)

        finally:
            safe_db_services(all_services, services_path)

    if len(failed_services) > 0:
        raise ServiceBulkException("Can not add all Services to DB", 400, added_services, failed_services)

    return added_services


def get_services() -> List[DBService]:
    """Get all saved services from the JSON file

    Returns:
        List[DBService]: List of all services
    """
    return get_db_services(services_path)


def get_service(name: str) -> DBService:
    """Get a Service from the DB

    Args:
        name (str): Name of the Service

    Raises:
        ServiceNotFound: If the Service can not be found

    Returns:
        DBService: Return found Service with all informations
    """
    services: List[DBService] = get_db_services(services_path)

    for service in services:
        if service.name.lower() == name.lower():
            return service
    raise ServiceNotFound("Der Service wurde nicht in der DB gefunden", 404, name)


def delete_service(service: Service) -> DBService:
    """Delete one Service from the services configuration

    Args:
        service (Service): Service to delete from the config

    Returns:
        DBService: Return Service if success
    """
    service = get_service(service.name)
    db_services = get_services()
    db_services.remove(service)
    safe_db_services(db_services, services_path)
    return service
