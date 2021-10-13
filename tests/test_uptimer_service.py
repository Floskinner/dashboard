from datetime import timedelta
from typing import Dict, List

import pytest
from httpx import Response
from models.service import DBService, PingService, Service
from models.service_error import ServiceBulkException, ServiceNotFound
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from services import uptimer_service


@pytest.fixture(autouse=True)
def init_db_set_get(mocker: MockerFixture, fake_db_json: Dict):
    mocker.patch("services.get_json_data", return_value=fake_db_json)
    mocker.patch("services.set_json_data")


@pytest.fixture
def db_service_ok() -> DBService:
    data = {"name": "test", "url": "https://test.url", "ping": False}
    return DBService(**data)


@pytest.fixture
def db_service_fail() -> DBService:
    data = {"name": "fail", "url": "https://fail.url", "ping": False}
    return DBService(**data)


@pytest.fixture
def fake_db_json(db_service_ok: DBService) -> List[Dict]:
    db: List[Dict] = []
    for i in range(10):
        data = {"name": f"{db_service_ok.name}-{i}", "url": db_service_ok.url, "ping": db_service_ok.ping}
        db.append(data)
    return db


@pytest.fixture
def fake_db_obj(fake_db_json: List[Dict]) -> List[DBService]:
    return [DBService(**service) for service in fake_db_json]


# fmt:off
@pytest.mark.parametrize(
    "status_code, exception",
    [
        (100, False),
        (200, False),
        (300, False),
        (400, True),
        (500, True)
    ]
)
@pytest.mark.asyncio
@pytest.mark.xfail  # XXX: fails until BUG is fixed
# fmt:on
async def test_ping_services_db(
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    fake_db_obj: List[DBService],
    db_service_ok: DBService,
    db_service_fail: DBService,
    status_code: int,
    exception: bool,
):
    # Requests only with Service and name attribute
    service_requests = [Service(name=s.name) for s in fake_db_obj]

    # Mock httpx responses
    httpx_mock.add_response(status_code=status_code, url=db_service_ok.url)

    # BUG: do not return timedelta with 0 total_seconds()
    mocker.patch.object(target=Response, attribute="_elapsed", new=timedelta(), create=True)
    # mocker.patch("httpx.Response.elapsed", return_value=timedelta(), create=True)

    # Test status_code
    if exception:
        # Code >= 400
        with pytest.raises(ServiceBulkException):
            await uptimer_service.ping_services(service_requests)
    else:
        # Code < 400
        excpected_response = [PingService(**s.get_attributes(), response_time=0) for s in fake_db_obj]
        response = await uptimer_service.ping_services(service_requests)
        assert response == excpected_response

    # No service found
    with pytest.raises(ServiceBulkException):
        await uptimer_service.ping_services([service_requests[0], db_service_fail])


# fmt:off
@pytest.mark.parametrize(
    "status_code, exception",
    [
        (100, False),
        (200, False),
        (300, False),
        (400, True),
        (500, True)
    ]
)
@pytest.mark.asyncio
@pytest.mark.xfail  # XXX: fails until BUG is fixed
# fmt:on
async def test_ping_services_new(
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    fake_db_obj: List[DBService],
    db_service_ok: DBService,
    db_service_fail: DBService,
    status_code: int,
    exception: bool,
):
    # Request with data that is not in der DB but with url
    service_request = [DBService(name="custom", url="https://dummy.test")]

    # Mock httpx responses
    httpx_mock.add_response(status_code=status_code, url=service_request[0].url)

    # BUG: do not return timedelta with 0 total_seconds()
    mocker.patch.object(target=Response, attribute="_elapsed", new=timedelta(), create=True)
    # mocker.patch("httpx.Response.elapsed", return_value=timedelta(), create=True)

    # Test status_code
    if exception:
        # Code >= 400
        with pytest.raises(ServiceBulkException):
            await uptimer_service.ping_services(service_request)
    else:
        # Code < 400
        excpected_response = [PingService(**s.get_attributes(), response_time=0) for s in service_request]
        response = await uptimer_service.ping_services(service_request)
        assert response == excpected_response


def test_delete(db_service_fail: DBService, fake_db_obj: List[DBService]):

    # Delete all services
    assert fake_db_obj == uptimer_service.delete_services(fake_db_obj)

    # Delete Services with Service object
    services_to_delete = [Service(name=s.name) for s in fake_db_obj]
    assert fake_db_obj == uptimer_service.delete_services(services_to_delete)

    # Raise because no service found
    services_to_delete = [db_service_fail]
    with pytest.raises(ServiceBulkException):
        uptimer_service.delete_services(services_to_delete)

    # Raise because the same service got deleted twice
    services_to_delete = [fake_db_obj[0], fake_db_obj[0]]
    with pytest.raises(ServiceBulkException):
        uptimer_service.delete_services(services_to_delete)


def test_get_service(db_service_fail: DBService, fake_db_obj: List[DBService]):
    # Get all Services
    assert fake_db_obj == uptimer_service.get_services()

    # Get one Service
    assert fake_db_obj[0] == uptimer_service.get_service(fake_db_obj[0].name)

    # Service not found
    with pytest.raises(ServiceNotFound):
        uptimer_service.get_service(db_service_fail.name)
