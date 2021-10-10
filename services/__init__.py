import json
from pathlib import Path
from typing import List

from models.service import JSON_Service

services_path = Path("data/services.json").absolute()
services_path.touch(mode=644)


def get_json_data(path: Path) -> List[JSON_Service]:
    with open(path, mode="r", encoding="utf8") as f:
        return json.load(f)


def set_json_data(data: List[JSON_Service], path: Path) -> None:
    with open(path, mode="w", encoding="utf8") as f:
        json.dump(data, f)
