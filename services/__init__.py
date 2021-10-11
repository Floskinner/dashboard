"""Backend Services for the API"""
import json
from pathlib import Path
from typing import Any, List

from models.service import DBService

services_path = Path("data/services.json").absolute()
services_path.touch(mode=644)


def get_db_services(path: Path) -> List[DBService]:
    """Get the DBServices Classes from the DB

    Args:
        path (Path): Path to the JSON-DB

    Returns:
        List[DBService]: All DBServices
    """
    return [DBService(**service) for service in get_json_data(path)]


def safe_db_services(services: List[DBService], path: Path) -> None:
    """Safe all DBServices to the JSON DB

    Args:
        services (List[DBService]): Services to safe
        path (Path): Path to the JSON-DB
    """
    json_data = [service.get_attributes() for service in services]
    set_json_data(json_data, path)


def get_json_data(path: Path) -> Any:
    """Get the Data from a JSON-File

    Args:
        path (Path): Path to the file

    Returns:
        Any: Data of the json.load
    """
    with open(path, mode="r", encoding="utf8") as file:
        return json.load(file)


def set_json_data(data: Any, path: Path) -> None:
    """Safe the Data to a File with pretty-print.

    Args:
        data (Any): Data that accept the json.dump
        path (Path): Full Path to the File
    """
    with open(path, mode="w", encoding="utf8") as file:
        json.dump(data, file, indent="\t")
