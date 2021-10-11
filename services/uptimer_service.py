"""Backend manager for the Services"""
import json
from typing import List

import httpx
from httpx import Response
from models.service import DBService, PingService, Service
from models.service_error import ServiceAddException, ServiceDuplicate, ServiceNotFound

from services import get_json_data, services_path, set_json_data


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
        # fmt:off
        new_service = {
            "name": service.name,
            "url": service.url,
            "ping": service.ping
        }
        # fmt:on

        try:
            all_services: List[DBService] = get_json_data(services_path)
            if service in all_services:
                # fmt:off
                raise ServiceDuplicate(
                    "Der Serivce ist bereits vorhaben",
                    409,
                    all_services[all_services.index(service)]
                )
                # fmt:on
            all_services.append(new_service)
            added_services.append(service)

        except json.decoder.JSONDecodeError:
            all_services: List[DBService] = list()
            all_services.append(new_service)
            added_services.append(service)

        except ServiceDuplicate as error:
            raise ServiceAddException("Can not add Services to DB", error.status_code, added_services, error) from error
        finally:
            set_json_data(all_services, services_path)

    return added_services


def get_services() -> List[DBService]:
    """Get all saved services from the JSON file

    Returns:
        List[DBService]: List of all services
    """
    return get_json_data(services_path)


def get_service(name: str) -> DBService:
    """Get a Service from the DB

    Args:
        name (str): Name of the Service

    Raises:
        ServiceNotFound: If the Service can not be found

    Returns:
        DBService: Return found Service with all informations
    """
    services: List[DBService] = get_json_data(services_path)
    for service in services:
        if service.get("name").lower() == name.lower():
            return service
    raise ServiceNotFound("Der Service wurde nicht gefunden", 404, name)


def delete_service(service: Service) -> DBService:
    """Delete the Serive from the DB

    Args:
        service (Service): Service to delete

    Returns:
        DBService: return the Service if success
    """
    service = get_service(service.name)
    services = get_services()
    services.remove(service)
    set_json_data(services, services_path)
    return service
