from datetime import timedelta
from typing import Dict, List
import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from models.service import DBService, PingService, Service
from models.service_error import ServiceBulkException
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


@pytest.mark.parametrize(
    "number_of_requests",
    [
        (1),
        (10),
    ],
)
@pytest.mark.asyncio
async def test_ping_ok(
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    number_of_requests: int,
    fake_db_obj: List[DBService],
    db_service_ok: DBService,
):
    httpx_mock.add_response(status_code=200, url=db_service_ok.url)
    mocker.patch("httpx.Response.elapsed", return_value=timedelta())

    requested_services = [fake_db_obj[i] for i in range(number_of_requests)]
    excpected_response = [
        PingService(**fake_db_obj[i].get_attributes(), response_time=0) for i in range(number_of_requests)
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
async def test_ping_fail(
    httpx_mock: HTTPXMock,
    number_of_requests: int,
    db_service_ok: DBService,
    fake_db_obj: List[DBService],
):
    requested_services = [fake_db_obj[i] for i in range(number_of_requests)]

    # Raise because no service Found
    with pytest.raises(ServiceBulkException):
        await uptimer_service.ping_service(requested_services)

    # Raise because Service can not be resolved
    with pytest.raises(ServiceBulkException):
        await uptimer_service.ping_service(requested_services)

    # Raise because Service got no 2XX status code
    httpx_mock.add_response(status_code=404, url=db_service_ok.url)
    with pytest.raises(ServiceBulkException):
        await uptimer_service.ping_service(requested_services)


@pytest.mark.parametrize(
    "number_of_requests",
    [
        (1),
        (10),
    ],
)
def test_delete(
    number_of_requests: int,
    db_service_fail: DBService,
    fake_db_obj: List[DBService],
):
    # Fake the DB with only db_service_ok data

    # Expected Result if success
    excepted_result = [fake_db_obj[i] for i in range(number_of_requests)]

    # Successfull delete Services with DBService objects
    services_to_delete = [fake_db_obj[i] for i in range(number_of_requests)]
    assert excepted_result == uptimer_service.delete_services(services_to_delete)

    # Successfull delete Services with Service objects
    services_to_delete = [Service(**fake_db_obj[i].get_attributes()) for i in range(number_of_requests)]
    assert excepted_result == uptimer_service.delete_services(services_to_delete)

    # Raise because no service found
    services_to_delete = [db_service_fail]
    with pytest.raises(ServiceBulkException):
        uptimer_service.delete_services(services_to_delete)

    # Raise because the same service got deleted twice
    services_to_delete = [fake_db_obj[0], fake_db_obj[0]]
    with pytest.raises(ServiceBulkException):
        uptimer_service.delete_services(services_to_delete)
