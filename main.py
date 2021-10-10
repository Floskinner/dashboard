"""Main for the Dashboard"""
import fastapi
import uvicorn

from api import uptimer_api

api = fastapi.FastAPI()


def configure():
    """Do initial config on start"""
    configure_routing()


def configure_routing():
    """Add all Router for FastAPI"""
    api.include_router(uptimer_api.router)


if __name__ == "__main__":
    configure()
    uvicorn.run(api, port=8000, host="127.0.0.1")
else:
    configure()
