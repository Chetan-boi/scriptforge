import copy
from pathlib import Path
from typing import Any
import tomllib

DEFAULT_CONFIG: dict[str, Any] = {
    "page": {
        "size": "A4",
        "char_size": 14.0,
        "line_spacing": 24.0,
        "left_margin": 54.0,
        "right_margin": 20.0,
        "top_margin": 50.0,
        "bottom_margin": 40.0,
        "margin_indent": 8.0,
        "space_width_factor": 0.75,
        "show_rules": True,
        "show_margin": True,
        "rule_line_width": 0.6,
        "margin_line_width": 1.0,
    },
    "colors": {
        "rule_line": "#B0C4DE",
        "margin_line": "#E57373",
        "desk": "#E6EAF0",
        "paper": "#FCFCFD",
        "ink": "#1D2B4F",
    },
    "database": {
        "default_path": ".bin/default.db",
    },
}


def get_config_path(override_path: Path | str | None = None) -> Path:
    if override_path:
        return Path(override_path)
    cwd_cfg = Path("config.toml")
    if cwd_cfg.exists():
        return cwd_cfg
    root_cfg = Path(__file__).resolve().parent.parent.parent / "config.toml"
    if root_cfg.exists():
        return root_cfg
    return cwd_cfg


def _merge_defaults(custom: dict[str, Any], default: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(default)
    for k, v in custom.items():
        if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
            merged[k] = _merge_defaults(v, merged[k])
        else:
            merged[k] = v
    return merged


def load_config(config_path: Path | str | None = None) -> dict[str, Any]:
    path = get_config_path(config_path)
    if not path.exists():
        return copy.deepcopy(DEFAULT_CONFIG)
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return _merge_defaults(data, DEFAULT_CONFIG)
    except Exception:
        return copy.deepcopy(DEFAULT_CONFIG)


def _toml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    elif isinstance(v, (int, float)):
        return str(v)
    elif isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    return f'"{v}"'


def dump_toml(data: dict[str, Any]) -> str:
    lines = []
    # Top-level non-table items
    for k, v in data.items():
        if not isinstance(v, dict):
            lines.append(f"{k} = {_toml_value(v)}")

    # Table sections
    for section, table in data.items():
        if isinstance(table, dict):
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"[{section}]")
            for k, v in table.items():
                lines.append(f"{k} = {_toml_value(v)}")
    lines.append("")
    return "\n".join(lines)


def save_config(config_data: dict[str, Any], config_path: Path | str | None = None) -> Path:
    path = get_config_path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    toml_str = dump_toml(config_data)
    path.write_text(toml_str, encoding="utf-8")
    return path
