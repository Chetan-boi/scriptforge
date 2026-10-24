from pathlib import Path
from typing import Any
import tomllib

CONFIG_FILE = Path("config.toml")

def load_config() -> dict[str, Any]:
    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)

