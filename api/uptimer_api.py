"""API for managing the services for the check if they reachable"""

from typing import List

import fastapi
from models.service import ConfigService, PingService, Service
from models.service_error import BulkServiceError, PingError, ServiceDuplicate, ServiceError, ServiceNotFound
from services import uptimer_service

router = fastapi.APIRouter()


@router.post("/api/service/{name}/add", response_model=ConfigService)
async def add_service(name: str, url: str, ping: bool = False) -> ConfigService:
    """Add one service to the configuration. The name hase to be unique in the configuration

    Args:
        url (str): Ping the service on this url
        ping (bool, optional): Check the health of the service automatic. Defaults to False.
        name (Service): Name of the Service. Defaults to Depends().

    Returns:
        ConfigService: Created Service
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    service = ConfigService(name=name, url=url, ping=ping)
    return uptimer_service.add_service(service)


@router.post("/api/services/add", status_code=201, response_model=List[ConfigService])
async def add_services(services: List[ConfigService]) -> List[ConfigService]:
    """Adding one or more Services to the configuration

    Args:
        services (List[ConfigService]): Services to add

    Raises:
        BulkServiceError: Contains all failed services and succeeded services

    Returns:
        List[ConfigService]: All added services to the configuration
    """
    s_services: List[ConfigService] = []
    f_services: List[ServiceError] = []
    for service in services:
        try:
            s_services.append(uptimer_service.add_service(service))
        except ServiceDuplicate as error:
            f_services.append(error)
        except Exception as error:
            f_services.append(ServiceError(str(error), status_code=500, service=service))

    if len(f_services) > 0:
        raise BulkServiceError("Not all Service are added", 404, s_services, f_services)

    return s_services


@router.delete("/api/service/{name}/delete", status_code=200, response_model=ConfigService)
async def delete_service(name: str) -> ConfigService:
    """Delete one service from the service configuration

    Args:
        name (str): Name of the service

    Returns:
        ConfigService: Deleted Service
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    return uptimer_service.delete_service(Service(name=name))


@router.delete("/api/services/delete", status_code=200, response_model=List[ConfigService])
async def delete_services(services: List[Service]) -> ConfigService:
    """Delete one or more services from the service configuration

    Args:
        services (List[Service]): All services to delete

    Raises:
        BulkServiceError: Contains all failed services and succeeded services

    Returns:
        ConfigService: Deleted Services
    """
    s_services: List[ConfigService] = []
    f_services: List[ServiceError] = []
    for service in services:
        try:
            s_services.append(uptimer_service.delete_service(service))
        except ServiceNotFound as error:
            f_services.append(error)
        except Exception as error:
            f_services.append(ServiceError(str(error), status_code=500, service=service))

    if len(f_services) > 0:
        raise BulkServiceError("Not all Service are deleted", 404, s_services, f_services)

    return s_services


@router.get("/api/service/{name}/config", response_model=ConfigService)
async def get_service(name: str) -> ConfigService:
    """Get specific Config Service Configuration

    Returns:
        ConfigService: Service with config
    """
    return uptimer_service.get_service(name)


@router.get("/api/services/config", response_model=List[ConfigService])
async def get_services() -> List[ConfigService]:
    """Get all saved Services

    Returns:
        List[ConfigService]: List of Services
    """
    return uptimer_service.get_services()


@router.get("/api/service/{name}/ping", response_model=PingService)
async def ping_service(name: str) -> PingService:
    """Ping a service that is safed in the services config

    Args:
        name (str): Name of the Service

    Returns:
        PingService: Service with response_time
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    service = PingService(name=name)
    return await uptimer_service.ping_service(service)


# TODO: API documentation is not correct for the request body
@router.get("/api/services/ping", response_model=List[PingService])
async def ping_services(services: List[PingService]) -> List[PingService]:
    """Ping all given Services with only a name (check services config for url) or with given url

    Args:
        services (List[PingService]): Services to check. URL is optional and response_time not needed

    Raises:
        BulkServiceError: Contains all failed services and succeeded services

    Returns:
        List[PingService]: All Services with response_time
    """
    s_services: List[PingService] = []
    f_services: List[ServiceError] = []
    for service in services:
        try:
            s_services.append(await uptimer_service.ping_service(service))
        except ServiceNotFound as error:
            f_services.append(error)
        except PingError as error:
            f_services.append(error)
        except Exception as error:
            f_services.append(ServiceError(str(error), status_code=500, service=service))

    if len(f_services) > 0:
        raise BulkServiceError("Could not reach all services", 404, s_services, f_services)

    return s_services


@router.put("/api/service/{name}/update", response_model=ConfigService)
async def update_service(name: str, updated_service: ConfigService) -> ConfigService:
    """Update the configuration of one service. You also can change the name of the service with this update

    Args:
        name (str): name of the service to update
        updated_service (ConfigService): The new configuration

    Returns:
        ConfigService: the new settings for the service
    """
    old_service = Service(name=name)
    return uptimer_service.update_service(old_service, updated_service)
