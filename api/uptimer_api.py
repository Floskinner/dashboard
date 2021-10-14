"""API for managing the services for the check if they reachable"""

from typing import List

import fastapi
from fastapi.encoders import jsonable_encoder
from models.service import DBService, PingService, Service
from models.service_error import PingError, ServiceDuplicate, ServiceError, ServiceNotFound
from services import uptimer_service

router = fastapi.APIRouter()


@router.get("/api/service/{name}/ping", response_model=PingService)
async def ping_service(name: str) -> PingService:
    """Ping a service that is safed in the services config

    Args:
        name (str): Name of the Service

    Returns:
        PingService: Service with response_time
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    try:
        service = PingService(name=name)
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
            f_services.append(ServiceError(str(error), status_code=500, service=service))

    if len(f_services) > 0:
        # fmt:off
        content = {
            "error": "Not all Service are added",
            "success": jsonable_encoder(s_services),
            "faild": jsonable_encoder(f_services)
        }
        # fmt:on
        return fastapi.responses.JSONResponse(content=jsonable_encoder(content), status_code=404)

    return s_services


@router.get("/api/service/{name}/config", response_model=DBService)
async def get_service(name: str) -> DBService:
    """Get specific DB Service Configuration

    Returns:
        DBService: Service with config
    """
    try:
        return uptimer_service.get_service(name)
    except ServiceNotFound as error:
        return fastapi.responses.JSONResponse(content=jsonable_encoder(error), status_code=error.status_code)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


@router.get("/api/services/config", response_model=List[DBService])
async def get_services() -> List[DBService]:
    """Get all saved Services

    Returns:
        List[DBService]: List of Services
    """
    try:
        return uptimer_service.get_services()
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


@router.post("/api/service/{name}/add", response_model=DBService)
async def add_service(name: str, url: str, ping: bool = False) -> DBService:
    """Add one service to the configuration. The name hase to be unique in the configuration

    Args:
        url (str): Ping the service on this url
        ping (bool, optional): Check the health of the service automatic. Defaults to False.
        name (Service): Name of the Service. Defaults to Depends().

    Returns:
        DBService: Created Service
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    service = DBService(name=name, url=url, ping=ping)
    try:
        return uptimer_service.add_service(service)
    except ServiceDuplicate as error:
        return fastapi.responses.JSONResponse(content=jsonable_encoder(error), status_code=error.status_code)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


@router.post("/api/services/add", status_code=201, response_model=List[DBService])
async def add_services(services: List[DBService]) -> List[DBService]:
    """Adding one or more Services to the configuration

    Args:
        services (List[DBService]): Services to add

    Returns:
        List[DBService]: All added services to the configuration
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    s_services: List[DBService] = []
    f_services: List[ServiceError] = []
    for service in services:
        try:
            s_services.append(uptimer_service.add_service(service))
        except ServiceDuplicate as error:
            f_services.append(error)
        except Exception as error:
            f_services.append(ServiceError(str(error), status_code=500, service=service))

    if len(f_services) > 0:
        # fmt:off
        content = {
            "error": "Not all Service are added",
            "success": jsonable_encoder(s_services),
            "faild": jsonable_encoder(f_services)
        }
        # fmt:on
        return fastapi.responses.JSONResponse(content=content, status_code=404)

    return s_services


@router.delete("/api/service/{name}/delete", status_code=200, response_model=DBService)
async def delete_service(name: str) -> DBService:
    """Delete one service from the service configuration

    Args:
        name (str): Name of the service

    Returns:
        DBService: Deleted Service
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    try:
        return uptimer_service.delete_service(Service(name=name))
    except ServiceNotFound as error:
        return fastapi.responses.JSONResponse(content=jsonable_encoder(error), status_code=error.status_code)
    except Exception as error:
        return fastapi.responses.JSONResponse(content={"error": str(error)}, status_code=500)


@router.delete("/api/services/delete", status_code=200, response_model=List[DBService])
async def delete_services(services: List[Service]) -> DBService:
    """Delete one or more services from the service configuration

    Args:
        services (List[Service]): All services to delete

    Returns:
        DBService: Deleted Services
        fastapi.responses.JSONResponse: If some Exception are made with detailed information
    """
    s_services: List[DBService] = []
    f_services: List[ServiceError] = []
    for service in services:
        try:
            s_services.append(uptimer_service.delete_service(service))
        except ServiceNotFound as error:
            f_services.append(error)
        except Exception as error:
            f_services.append(ServiceError(str(error), status_code=500, service=service))

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
