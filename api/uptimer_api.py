"""API for managing the services for the check if they reachable"""

from typing import List

import fastapi
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from models.service import DBService, PingService, Service
from models.service_error import PingError, ServiceBulkException, ServiceError, ServiceNotFound
from services import uptimer_service

router = fastapi.APIRouter()


@router.get("/api/service/{name}/ping", response_model=PingService)
async def ping_service(service: Service = Depends()) -> PingService:
    """Ping a service that is safed in the services config

    Args:
        service (Service): Service to ping

    Returns:
        PingService: Service with response_time
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    try:
        service = PingService(name=service.name)
        return await uptimer_service.ping_service(service)
    except ServiceNotFound as error:
        return fastapi.responses.JSONResponse(content=jsonable_encoder(error), status_code=error.status_code)
    except PingError as error:
        return fastapi.responses.JSONResponse(content=jsonable_encoder(error), status_code=error.status_code)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


# TODO: API documentation is not correct for the request body
@router.get("/api/services/ping", response_model=List[PingService])
async def ping_services(services: List[PingService]) -> List[PingService]:
    """Ping all given Services with only a name (check services config for url) or with given url

    Args:
        services (List[PingService]): Services to check. URL is optional and response_time not needed

    Returns:
        List[PingService]: All Services with response_time
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
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
            f_services.append(ServiceError(str(error), status_code=500))

    if len(f_services) > 0:
        content = ServiceBulkException("Not all Service are pingable", 400, s_services, f_services)
        return fastapi.responses.JSONResponse(content=jsonable_encoder(content), status_code=404)

    return s_services


@router.get("/api/service/{name}/config", response_model=DBService)
async def get_service(service: Service = Depends()) -> DBService:
    """Get specific DB Service Configuration

    Returns:
        DBService: Service with config
    """
    return uptimer_service.get_service(service.name)


@router.get("/api/services/config", response_model=List[DBService])
async def get_services() -> List[DBService]:
    """Get all saved Services

    Returns:
        List[DBService]: List of Services
    """
    return uptimer_service.get_services()


@router.post("/api/services/add", status_code=201, response_model=List[DBService])
async def add_service(services: List[DBService]) -> List[DBService]:
    """Add a services to the DB

    Args:
        services (List[DBService]): Service to add

    Returns:
        List[DBService]: return the Service if success
    """
    try:
        return uptimer_service.add_services(services)
    except ServiceBulkException as error:
        return fastapi.responses.JSONResponse(content=jsonable_encoder(error), status_code=error.status_code)


@router.delete("/api/service/{name}/delete", status_code=200, response_model=DBService)
async def delete_service(service: Service) -> DBService:
    try:
        return uptimer_service.delete_service(service)
    except ServiceNotFound as error:
        return fastapi.responses.JSONResponse(content=jsonable_encoder(error), status_code=error.status_code)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


@router.delete("/api/services/delete", status_code=200, response_model=List[DBService])
async def delete_services(services: List[Service]) -> DBService:
    s_services: List[DBService] = []
    f_services: List[ServiceError] = []
    for service in services:
        try:
            s_services.append(uptimer_service.delete_service(service))
        except ServiceNotFound as error:
            f_services.append(error)
        except Exception as error:
            f_services.append(ServiceError(str(error), status_code=500))

    if len(f_services) > 0:
        # fmt:off
        content = {
            "error": "Not all Service are deleted",
            "success": jsonable_encoder(s_services),
            "faild": jsonable_encoder(f_services)
        }
        # fmt:on
        return fastapi.responses.JSONResponse(content=content, status_code=404)

    return s_services
