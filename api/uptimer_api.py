"""API for managing the services for the check if they reachable"""

from typing import List

import fastapi
import httpx
from fastapi import Depends
from models.service import DBService, PingService, Service
from models.service_error import ServiceAddException, ServiceNotFound
from services import uptimer_service

router = fastapi.APIRouter()


@router.get("/api/services/ping", response_model=List[PingService])
async def ping_services(services: List[Service]) -> List[PingService]:
    """Ping Services that is in the services.json

    Args:
        services (List[Service]): Services with only a name

    Returns:
        List[PingService]: Services with his responsetime
    """
    try:
        return await uptimer_service.ping_service(services)
    except ServiceNotFound as error:
        return fastapi.responses.JSONResponse(content=error.json_data, status_code=error.status_code)
    except httpx.RequestError as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=408)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


@router.get("/api/service/{name}/ping", response_model=PingService)
async def ping_service(service: Service = Depends()) -> PingService:
    """Ping only one Service that is in the services.json

    Args:
        service (Service): Service to Ping

    Returns:
        PingService: Service with responsetime
    """
    response = await ping_services([service])
    if isinstance(response, list):
        return response[0]
    return response


@router.get("/api/services", response_model=List[DBService])
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
    except ServiceAddException as error:
        return fastapi.responses.JSONResponse(content=error.json_data, status_code=error.status_code)


@router.delete("/api/service/delete", status_code=200, response_model=DBService)
async def delete_service(service: Service) -> DBService:
    """Delete Service from DB

    Args:
        service (Service): Service to delete

    Returns:
        DBService: return the Service if success
    """
    try:
        return uptimer_service.delete_service(service)
    except ServiceNotFound as error:
        return fastapi.responses.JSONResponse(content=error.json_data, status_code=error.status_code)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)
