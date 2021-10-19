"""Main for the Dashboard"""
import fastapi
import uvicorn
from fastapi.encoders import jsonable_encoder

from api import uptimer_api
from models.service_error import BulkServiceError, ServiceError
from models.validation_error import InvalidURL

api = fastapi.FastAPI()


def configure():
    """Do initial config on start"""
    configure_routing()


def configure_routing():
    """Add all Router for FastAPI"""
    api.include_router(uptimer_api.router)


@api.exception_handler(BulkServiceError)
async def bulk_service_exception_handler(request, exc: BulkServiceError):
    """Exception Handler for the fastAPI if BulkServiceError is raised

    Args:
        request: Request for the api
        exc (BulkServiceError): Raised Exception

    Returns:
        fastapi.responses.JSONResponse: Return Exception as JSON-Formattet to the client
    """
    return fastapi.responses.JSONResponse(content=jsonable_encoder(exc), status_code=exc.status_code)


@api.exception_handler(ServiceError)
async def service_exception_handler(request, exc: ServiceError):
    """Exception Handler for the fastAPI if ServiceError is raised

    Args:
        request: Request for the api
        exc (ServiceError): Raised Exception

    Returns:
        fastapi.responses.JSONResponse: Return Exception as JSON-Formattet to the client
    """
    return fastapi.responses.JSONResponse(content=jsonable_encoder(exc), status_code=exc.status_code)


@api.exception_handler(InvalidURL)
async def validation_exception_handler(request, exc: InvalidURL):
    """Exception Handler for the fastAPI if InvalidURL is raised

    Args:
        request: Request for the api
        exc (InvalidURL): Raised Exception

    Returns:
        fastapi.responses.JSONResponse: Return Exception as JSON-Formattet to the client
    """
    return fastapi.responses.JSONResponse(content=jsonable_encoder(exc), status_code=422)


@api.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Exception Handler for all Exceptions made and unhandeld

    Args:
        request: Request for the api
        exc (ServiceError): Raised Exception

    Returns:
        fastapi.responses.JSONResponse: Return Exception as JSON-Formattet to the client
    """
    # TODO: Logging the Errors
    print(str(exc))
    content = {"error_msg": "Some internal Server Errors"}
    return fastapi.responses.JSONResponse(content=content, status_code=500)


if __name__ == "__main__":
    configure()
    uvicorn.run(api, port=8000, host="127.0.0.1")
else:
    configure()
