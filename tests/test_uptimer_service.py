from datetime import timedelta
from typing import Dict, List

import pytest
import services
from httpx import Response
from models.service import ConfigService, PingService, Service
from models.service_error import PingError, ServiceDuplicate, ServiceNotFound
from models.validation_error import InvalidURL
from py import path
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from services import get_json_data, uptimer_service


@pytest.fixture()
def conf_path(mocker: MockerFixture, fake_config_json: Dict, tmpdir: path.local):
    tmp_path = tmpdir.join("test_config.json")
    mocker.patch("services.services_path", new=tmp_path)
    mocker.patch("services.uptimer_service.services_path", new=tmp_path)
    services.set_json_data(fake_config_json, tmp_path)

    return tmp_path


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
    configs: List[Dict] = []
    for i in range(10):
        data = {"name": f"{config_service_ok.name}{i}", "url": config_service_ok.url, "ping": config_service_ok.ping}
        configs.append(data)
    return configs


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
    conf_path: path.local,  # Import to Mock the config
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

    # Test if the config file is untouched
    conf_services = [ConfigService(**service) for service in get_json_data(conf_path)]
    assert conf_services == fake_config_obj


def test_delete(fake_config_obj: List[ConfigService], conf_path: path.local):

    # Delete service 0
    assert fake_config_obj[0] == uptimer_service.delete_service(fake_config_obj[0])

    # Check if it is deleted
    conf_services = [ConfigService(**service) for service in get_json_data(conf_path)]
    assert any(s == fake_config_obj[0] for s in conf_services) is False

    # Delete Service 1 with Service object
    assert fake_config_obj[1] == uptimer_service.delete_service(Service(name=fake_config_obj[1].name))

    # Check if it is deleted
    conf_services = [ConfigService(**service) for service in get_json_data(conf_path)]
    assert any(s == fake_config_obj[1] for s in conf_services) is False

    # Raise because service got already deleted
    with pytest.raises(ServiceNotFound):
        uptimer_service.delete_service(fake_config_obj[0])


# conf_path unused but need to to call for fake config
def test_get_service(config_service_fail: ConfigService, fake_config_obj: List[ConfigService], conf_path: path.local):
    # Get all Services
    assert fake_config_obj == uptimer_service.get_services()

    # Get one Service
    assert fake_config_obj[0] == uptimer_service.get_service(fake_config_obj[0].name)

    # Service not found
    with pytest.raises(ServiceNotFound):
        uptimer_service.get_service(config_service_fail.name)


def test_add_service(fake_config_obj: List[ConfigService], conf_path: path.local):
    # Add service
    new_service = ConfigService(name="foo", url="https://foo.url", ping="False")
    assert new_service == uptimer_service.add_service(new_service)

    # Check if it is added
    conf_services = [ConfigService(**service) for service in get_json_data(conf_path)]
    assert any(s == new_service for s in conf_services) is True

    with pytest.raises(ServiceDuplicate):
        uptimer_service.add_service(fake_config_obj[0])

    # Check if it is just one time in the config
    conf_services = [ConfigService(**service) for service in get_json_data(conf_path)]
    counter = 0
    for conf_service in conf_services:
        if conf_service == fake_config_obj[0]:
            counter += 1

    assert counter == 1

    # Check if it can handle a empty config
    file = conf_path.open(mode="w")
    file.close()

    new_service = ConfigService(name="foo", url="https://foo.url", ping="False")
    assert new_service == uptimer_service.add_service(new_service)


def test_update_service(
    config_service_fail: ConfigService, fake_config_obj: List[ConfigService], conf_path: path.local
):
    # Update only url and ping
    u_service = fake_config_obj[0].copy()
    u_service.url = "https://updated.url"
    u_service.ping = True

    assert u_service == uptimer_service.update_service(fake_config_obj[0], u_service)

    # Check if data is changed
    conf_services = [ConfigService(**service) for service in get_json_data(conf_path)]
    assert any(s == u_service for s in conf_services) is True

    # Update also name of the service
    u_service = fake_config_obj[1].copy()
    u_service.name = "updated_name"
    u_service.url = "https://updated1.url"
    u_service.ping = True

    assert u_service == uptimer_service.update_service(fake_config_obj[1], u_service)

    # Check if data is changed
    conf_services = [ConfigService(**service) for service in get_json_data(conf_path)]
    assert any(s == u_service for s in conf_services) is True

    # Update shoud fail because service does not exist to update
    u_service = config_service_fail.copy()
    u_service.url = "https://updated2.url"

    with pytest.raises(ServiceNotFound):
        assert uptimer_service.update_service(config_service_fail, u_service)

    # Fail because rename to a existing service
    u_service = fake_config_obj[2].copy()
    u_service.name = fake_config_obj[3].name
    u_service.url = "https://updated1.url"
    u_service.ping = True

    with pytest.raises(ServiceDuplicate):
        uptimer_service.update_service(fake_config_obj[2], u_service)


# fmt:off
@pytest.mark.parametrize(
    "url, exception",
    [
        ("https://valid.url", False),
        ("https://still.valid.url", False),
        ("http://valid.url", False),
        ("https://valid.url/", False),
        ("https://valid.url:1337", False),
        ("http://valid.url:1337", False),
        ("https://valid.url:1337/valid", False),
        ("http://still.valid.url:1337/valid", False),
        ("http://still.valid.url:1337/valid/nice", False),
        ("htt://invalid.url", True),
        ("http://invalid", True),
        ("http://invalid.", True),
        ("http://invalid:1337", True),
        ("http://invalid.url::1337", True),
        ("invalid.url", True)
    ]
)
# fmt:on
def test_url_validation(url: str, exception: bool):
    data = {"name": "foo", "url": url}
    if exception:
        with pytest.raises(InvalidURL):
            ConfigService(**data)
    else:
        try:
            ConfigService(**data)
        except InvalidURL:
            pytest.fail("Should no exception")
