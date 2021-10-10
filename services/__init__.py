"""Backend Services for the API"""
import json
from pathlib import Path
from typing import Any


services_path = Path("data/services.json").absolute()
services_path.touch(mode=644)


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
    """Safe the Data to a File with pretty-print. The existing Data in the File get overwritten

    Args:
        data (Any): Data that accept the json.dump
        path (Path): Full Path to the File
    """
    with open(path, mode="w", encoding="utf8") as file:
        json.dump(data, file, indent="\t")
