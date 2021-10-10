from typing import List

import fastapi
import httpx
from fastapi import Depends
from models.service import JSON_Service, Ping_Service, Service
from models.service_error import ServiceNotFound
from services import uptimer_service

router = fastapi.APIRouter()


@router.get("/api/service/{name}/ping", response_model=Ping_Service)
async def ping(service: Service = Depends()) -> Ping_Service:
    try:
        return await uptimer_service.ping_service(service)
    except ServiceNotFound as error:
        return fastapi.responses.JSONResponse(content=error.json_data, status_code=error.status_code)
    except httpx.RequestError as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=408)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


@router.get("/api/services", response_model=List[JSON_Service])
async def get_services() -> List[Service]:
    return uptimer_service.get_services()


@router.post("/api/service/add", status_code=201, response_model=JSON_Service)
async def add_service(service: JSON_Service) -> JSON_Service:
    return uptimer_service.add_service(service)
