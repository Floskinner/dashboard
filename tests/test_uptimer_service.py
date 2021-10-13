from datetime import timedelta
from typing import Dict, List
import pytest
from httpx import Response
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
# fmt:on
@pytest.mark.asyncio
@pytest.mark.xfail  # XXX: fails until BUG is fixed
async def test_ping_services(
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
    mocker.patch.object(target=Response, attribute="elapsed", new=timedelta())
    # mocker.patch("httpx.Response.elapsed", return_value=timedelta(), create=True)

    # Test status_code
    if exception:
        # Code >= 400
        with pytest.raises(ServiceBulkException):
            await uptimer_service.ping_service(service_requests)
    else:
        # Code < 400
        excpected_response = [PingService(**s.get_attributes(), response_time=0) for s in fake_db_obj]
        response = await uptimer_service.ping_service(service_requests)
        assert response == excpected_response

    # No service found
    with pytest.raises(ServiceBulkException):
        await uptimer_service.ping_service([service_requests[0], db_service_fail])


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
