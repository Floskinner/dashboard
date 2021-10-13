"""Backend manager for the Services"""
import json
from typing import List, Union

import httpx
from httpx import Response
from models.service import DBService, PingService, Service
from models.service_error import PingError, ServiceBulkException, ServiceDuplicate, ServiceError, ServiceNotFound

from services import get_db_services, safe_db_services, services_path


async def ping_services(services: List[Union[Service, DBService]]) -> List[PingService]:
    """Ping the given Services to check if this is reachable. If the Service got a URL it has not to be in the DB

    Args:
        services (List[Service|DBService]): Services to Ping (only Name required)

    Returns:
        List[PingService]: Return of the Services with responsetime
    """
    responses: List[PingService] = []
    failed_services: List[ServiceError] = []
    for service in services:
        try:
            if not hasattr(service, "url"):
                service: DBService = get_service(service.name)

            async with httpx.AsyncClient() as client:
                resp: Response = await client.get(service.url)
                resp.raise_for_status()
                responses.append(PingService(**service.get_attributes(), response_time=resp.elapsed.total_seconds()))
        except ServiceError as error:
            failed_services.append(error)
        except httpx.HTTPStatusError as error:
            failed_services.append(PingError(str(error), resp.status_code, service))
        except httpx.RequestError as error:
            failed_services.append(ServiceError(str(error), 408))

    if len(failed_services) > 0:
        raise ServiceBulkException("Some Services got a Issue", 400, responses, failed_services)
    return responses


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
    service = get_service(service.name)
    db_services = get_services()
    db_services.remove(service)
    safe_db_services(db_services, services_path)
    return service
