from datetime import timedelta
from typing import Dict, List

import pytest
from httpx import Response
from models.service import ConfigService, PingService, Service
from models.service_error import PingError, ServiceDuplicate, ServiceNotFound
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from services import uptimer_service


@pytest.fixture(autouse=True)
def init_conf_mock(mocker: MockerFixture, fake_config_json: Dict):
    mocker.patch("services.get_json_data", return_value=fake_config_json)
    mocker.patch("services.set_json_data")


@pytest.fixture
def config_service_ok() -> ConfigService:
    data = {"name": "test", "url": "https://test.url", "ping": False}
    return ConfigService(**data)


@pytest.fixture
def config_service_fail() -> ConfigService:
    data = {"name": "fail", "url": "https://fail.url", "ping": False}
    return ConfigService(**data)


@pytest.fixture
def fake_config_json(config_service_ok: ConfigService) -> List[Dict]:
    db: List[Dict] = []
    for i in range(10):
        data = {"name": f"{config_service_ok.name}-{i}", "url": config_service_ok.url, "ping": config_service_ok.ping}
        db.append(data)
    return db


@pytest.fixture
def fake_config_obj(fake_config_json: List[Dict]) -> List[ConfigService]:
    return [ConfigService(**service) for service in fake_config_json]


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
async def test_ping_services(
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    fake_config_obj: List[ConfigService],
    config_service_ok: ConfigService,
    config_service_fail: ConfigService,
    status_code: int,
    exception: bool,
):
    # Mock httpx responses
    httpx_mock.add_response(status_code=status_code, url=config_service_ok.url)
    httpx_mock.add_response(status_code=status_code, url="https://custom.url")

    # BUG: do not return timedelta with 0 total_seconds()
    mocker.patch.object(target=Response, attribute="_elapsed", new=timedelta(), create=True)
    # mocker.patch("httpx.Response.elapsed", return_value=timedelta(), create=True)

    # Setup for normal request for services in config
    service_request = PingService(name=fake_config_obj[0].name)
    expected_response = PingService(**dict(fake_config_obj[0]))
    expected_response.response_time = 0.0

    # Test status_code
    if exception:
        # Code >= 400
        with pytest.raises(PingError):
            await uptimer_service.ping_service(service_request)
    else:
        # Code < 400
        response = await uptimer_service.ping_service(service_request)
        assert response == expected_response

    # Setup for request with included url
    service_request.name = "custom"
    service_request.url = "https://custom.url"
    expected_response = service_request.copy()
    expected_response.response_time = 0.0

    # Test status_code
    if exception:
        # Code >= 400
        with pytest.raises(PingError):
            await uptimer_service.ping_service(service_request)
    else:
        # Code < 400
        response = await uptimer_service.ping_service(service_request)
        assert response == expected_response

    # Service not found
    with pytest.raises(ServiceNotFound):
        await uptimer_service.ping_service(PingService(name=config_service_fail.name))


def test_delete(config_service_fail: ConfigService, fake_config_obj: List[ConfigService]):

    services_to_delete = fake_config_obj[0]

    # Delete service
    assert services_to_delete == uptimer_service.delete_service(services_to_delete)

    # Delete Service with Service object
    assert services_to_delete == uptimer_service.delete_service(Service(name=services_to_delete.name))

    # Raise because no service found
    with pytest.raises(ServiceNotFound):
        uptimer_service.delete_service(config_service_fail)


def test_get_service(config_service_fail: ConfigService, fake_config_obj: List[ConfigService]):
    # Get all Services
    assert fake_config_obj == uptimer_service.get_services()

    # Get one Service
    assert fake_config_obj[0] == uptimer_service.get_service(fake_config_obj[0].name)

    # Service not found
    with pytest.raises(ServiceNotFound):
        uptimer_service.get_service(config_service_fail.name)


def test_add_service(fake_config_obj: List[ConfigService]):
    new_service = ConfigService(name="foo", url="https://foo.url", ping="False")

    assert new_service == uptimer_service.add_service(new_service)

    with pytest.raises(ServiceDuplicate):
        uptimer_service.add_service(fake_config_obj[0])
