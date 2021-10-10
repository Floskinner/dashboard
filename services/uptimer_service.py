import json
from typing import List, Optional, Union

import httpx
from httpx import Response
from models.service import Ping_Service, Service, JSON_Service
from models.service_error import ServiceDuplicate, ServiceNotFound
from services import get_json_data, services_path, set_json_data


async def ping_service(service: Service):
    service: JSON_Service = get_service(service.name)
    async with httpx.AsyncClient() as client:
        resp: Response = await client.get(service.get("url"))
        resp.raise_for_status()
        return Ping_Service(**service, response_time=resp.elapsed.total_seconds())


def add_service(service: JSON_Service) -> Optional[JSON_Service]:
    # fmt:off
    new_service = {
        "name": service.name,
        "url": service.url,
        "ping": service.ping
    }
    # fmt:on

    try:
        all_services: List[JSON_Service] = get_json_data(services_path)
        if service in all_services:
            raise ServiceDuplicate("Der Serivce ist bereits vorhaben", 409, service)
        all_services.append(new_service)

    except json.decoder.JSONDecodeError:
        all_services: List[JSON_Service] = list()
        all_services.append(new_service)
    finally:
        set_json_data(all_services, services_path)

    return service


def get_services() -> List[JSON_Service]:
    """Get all saved services from the JSON file

    Returns:
        List[JSON_Service]: List of all services
    """
    return get_json_data(services_path)


def get_service(name: str) -> JSON_Service:
    services: List[JSON_Service] = get_json_data(services_path)
    for service in services:
        if service.get("name").lower() == name.lower():
            return service
    raise ServiceNotFound("Der Service wurde nicht gefunden", 404, name)
