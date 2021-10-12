from typing import List
import pytest
from pytest_mock import MockerFixture
from pytest_httpx import HTTPXMock
from models.service import DBService, PingService
from models.service_error import ServiceBulkException
from services import uptimer_service


@pytest.fixture
def db_service() -> DBService:
    data = {"name": "test", "url": "https://test.url", "ping": False}
    return DBService(**data)


@pytest.mark.parametrize(
    "number_of_requests",
    [
        (1),
        (10),
    ],
)
@pytest.mark.asyncio
async def test_ping_ok(mocker: MockerFixture, httpx_mock: HTTPXMock, number_of_requests: int, db_service: DBService):
    httpx_mock.add_response(status_code=200, url=db_service.url)
    mocker.patch("services.uptimer_service.get_service", return_value=db_service)

    requested_services = [db_service for i in range(number_of_requests)]
    excpected_response = [
        PingService(**db_service.get_attributes(), response_time=0) for i in range(number_of_requests)
    ]

    response = await uptimer_service.ping_service(requested_services)
    assert response == excpected_response


@pytest.mark.parametrize(
    "number_of_requests",
    [
        (1),
        (10),
    ],
)
@pytest.mark.asyncio
async def test_ping_fail(mocker: MockerFixture, httpx_mock: HTTPXMock, number_of_requests: int, db_service: DBService):
    requested_services = [db_service for i in range(number_of_requests)]

    # Raise because no service Found
    with pytest.raises(ServiceBulkException):
        await uptimer_service.ping_service(requested_services)

    # Raise because Service can not be resolved
    mocker.patch("services.uptimer_service.get_service", return_value=db_service)
    with pytest.raises(ServiceBulkException):
        await uptimer_service.ping_service(requested_services)

    # Raise because Service got no 2XX status code
    httpx_mock.add_response(status_code=404, url=db_service.url)
    with pytest.raises(ServiceBulkException):
        await uptimer_service.ping_service(requested_services)
