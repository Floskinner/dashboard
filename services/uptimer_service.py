"""Backend manager for the Services"""
import json
from typing import List

import httpx
from httpx import Response
from models.service import DBService, PingService, Service
from models.service_error import ServiceBulkException, ServiceDuplicate, ServiceNotFound

from services import get_db_services, safe_db_services, services_path


async def ping_service(services: List[Service]) -> List[PingService]:
    """Ping the given Services to check if this is reachable. The Services has to be in the DB

    Args:
        services (List[Service]): Services to Ping (only Name required)

    Returns:
        List[PingService]: Return of the Services with responsetime
    """
    responses: List[PingService] = list()
    for service in services:
        service: DBService = get_service(service.name)
        async with httpx.AsyncClient() as client:
            resp: Response = await client.get(service.get("url"))
            resp.raise_for_status()
            responses.append(PingService(**service, response_time=resp.elapsed.total_seconds()))
    return responses


def add_services(services: List[DBService]) -> List[DBService]:
    """Add a Service to the DB. Stops adding on the first error of adding

    Args:
        services (DBService): Service with a requirements for the DB

    Raises:
        ServiceAddException: If one of the Services is already in the DB (same name)

    Returns:
        DBService: On succes return Serivce
    """
    added_services: List[DBService] = list()
    for service in services:
        try:
            all_services: List[DBService] = get_db_services(services_path)
            if service in all_services:
                # fmt:off
                raise ServiceDuplicate(
                    "Der Serivce ist bereits vorhaben",
                    409,
                    all_services[all_services.index(service)]
                )
                # fmt:on
            all_services.append(service)
            added_services.append(service)

        except json.decoder.JSONDecodeError:
            all_services: List[DBService] = list()
            all_services.append(service)
            added_services.append(service)

        except ServiceDuplicate as error:
            raise ServiceBulkException(
                "Can not add Services to DB", error.status_code, added_services, error
            ) from error
        finally:
            safe_db_services(all_services, services_path)

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
    raise ServiceNotFound("Der Service wurde nicht gefunden", 404, name)


def delete_services(services: List[DBService]) -> List[DBService]:
    """Delete the Services from the DB

    Args:
        services (List[DBService]): Services to delete

    Returns:
        List[DBService]: return the Service if success
    """
    deleted_services: List[DBService] = []
    try:
        for service in services:
            service = get_service(service.name)
            services = get_services()
            services.remove(service)
            safe_db_services(services, services_path)
            deleted_services.append(service)
    except ServiceNotFound as error:
        raise ServiceBulkException(
            "Can not delete Service. Service not found", error.status_code, deleted_services, service
        ) from error
    except Exception as error:
        raise ServiceBulkException(str(error), 500, deleted_services, service) from error
    return deleted_services
