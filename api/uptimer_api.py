"""API for managing the services for the check if they reachable"""

from typing import List

import fastapi
import httpx
from fastapi import Depends
from models.service import DBService, PingService, Service
from models.service_error import ServiceNotFound
from services import uptimer_service

router = fastapi.APIRouter()


@router.get("/api/service/{name}/ping", response_model=PingService)
async def ping(service: Service = Depends()) -> PingService:
    """Ping a Service that is in the services.json

    Args:
        service (Service): Service with only a name

    Returns:
        PingService: Service with his responsetime
    """
    try:
        return await uptimer_service.PingService(service)
    except ServiceNotFound as error:
        return fastapi.responses.JSONResponse(content=error.json_data, status_code=error.status_code)
    except httpx.RequestError as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=408)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


@router.get("/api/services", response_model=List[DBService])
async def get_services() -> List[DBService]:
    """Get all saved Services

    Returns:
        List[DBService]: List of Services
    """
    return uptimer_service.get_services()


@router.post("/api/service/add", status_code=201, response_model=DBService)
async def add_service(service: DBService) -> DBService:
    """Add a service to the DB

    Args:
        service (DBService): Service to add

    Returns:
        DBService: return the Service if success
    """
    return uptimer_service.add_service(service)


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
