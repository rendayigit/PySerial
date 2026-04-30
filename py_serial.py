from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import serial

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DEFINED_MESSAGES_PATH = BASE_DIR / "defined_messages.json"
STATE: dict[str, Any] = {"default_session": None, "log_file_path": None}
SERIAL_OPTION_KEYS = [
    "port",
    "baudrate",
    "bytesize",
    "parity",
    "stopbits",
    "timeout",
    "write_timeout",
    "xonxoff",
    "rtscts",
    "dsrdtr",
    "inter_byte_timeout",
    "exclusive",
]


def load_config() -> dict[str, Any]:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    if "serial" not in data or "app" not in data:
        raise ValueError("config.json must contain 'serial' and 'app' sections")

    serial_config = data["serial"]
    app_config = data["app"]

    if not serial_config.get("port"):
        raise ValueError("config.json serial.port must be set")

    if app_config.get("receive_timeout_seconds") is None:
        raise ValueError("config.json app.receive_timeout_seconds must be set")

    if app_config.get("receive_inter_byte_timeout_seconds") is None:
        raise ValueError(
            "config.json app.receive_inter_byte_timeout_seconds must be set"
        )

    return data


def parse_hex_message(message: str) -> bytes:
    parts = [part.strip().upper() for part in message.split() if part.strip()]
    if not parts:
        raise ValueError("message must contain at least one byte like 'AA BB'")

    invalid_parts = [part for part in parts if len(part) != 2]
    if invalid_parts:
        raise ValueError(f"invalid byte values: {invalid_parts}")

    try:
        return bytes(int(part, 16) for part in parts)
    except ValueError as error:
        raise ValueError("message must use uppercase or lowercase hex bytes") from error


def require_message(message: str | None) -> str:
    if message is None or not message.strip():
        raise ValueError("message is required; pass a hex string like 'AA BB'")

    return message


def load_defined_messages() -> dict[str, str]:
    data = json.loads(DEFINED_MESSAGES_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("defined_messages.json must contain a name-to-message object")

    normalized_messages: dict[str, str] = {}
    for raw_name, raw_message in data.items():
        if not isinstance(raw_name, str):
            raise ValueError("defined_messages.json keys must be strings")

        if not isinstance(raw_message, str):
            raise ValueError(
                f"defined message '{raw_name}' must be a hex string like 'AA BB'"
            )

        normalized_name = raw_name.strip().lower()
        if not normalized_name:
            raise ValueError("defined_messages.json cannot contain empty names")

        if normalized_name in normalized_messages:
            raise ValueError(
                f"defined_messages.json contains a duplicate name: '{raw_name}'"
            )

        normalized_messages[normalized_name] = bytes_to_hex_string(
            parse_hex_message(raw_message)
        )

    return normalized_messages


def bytes_to_hex_array(data: bytes) -> list[str]:
    return [f"{byte:02X}" for byte in data]


def bytes_to_hex_string(data: bytes) -> str:
    return " ".join(bytes_to_hex_array(data))


def serial_settings(config: dict[str, Any] | None = None) -> dict[str, Any]:
    current_config = config or load_config()
    return {
        key: current_config["serial"][key]
        for key in SERIAL_OPTION_KEYS
        if key in current_config["serial"]
    }


def open_port(config: dict[str, Any] | None = None) -> serial.Serial:
    return serial.Serial(**serial_settings(config))


def _log_path(config: dict[str, Any]) -> Path:
    log_directory = BASE_DIR / config["app"].get("log_directory", "logs")
    log_directory.mkdir(parents=True, exist_ok=True)

    if STATE["log_file_path"] is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        STATE["log_file_path"] = log_directory / f"{timestamp}.log"

    log_file_path = STATE["log_file_path"]
    if not isinstance(log_file_path, Path):
        raise RuntimeError("log file path was not initialized")

    return log_file_path


def log_message(
    direction: str, message: str, config: dict[str, Any] | None = None
) -> Path:
    current_config = config or load_config()
    log_file = _log_path(current_config)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    entry = f"{timestamp} | {direction:<7} | {message}\n"
    existing = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    log_file.write_text(entry + existing, encoding="utf-8")
    return log_file


def _send_to_port(port: serial.Serial, message: str, config: dict[str, Any]) -> str:
    payload = parse_hex_message(message)
    port.write(payload)
    port.flush()

    pretty_message = bytes_to_hex_string(payload)
    log_message("TX", pretty_message, config)
    return pretty_message


def _receive_from_port(port: serial.Serial, config: dict[str, Any]) -> list[str]:
    app_config = config["app"]
    port.timeout = app_config["receive_timeout_seconds"]
    first_byte = port.read(1)

    if not first_byte:
        log_message("RX TIME", "<timeout>", config)
        return []

    received = bytearray(first_byte)
    port.timeout = app_config["receive_inter_byte_timeout_seconds"]

    while True:
        chunk = port.read(1)
        if not chunk:
            break
        received.extend(chunk)

    message = bytes_to_hex_array(bytes(received))
    log_message("RX", " ".join(message), config)
    return message


class SerialSession:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_config()
        self.port: serial.Serial | None = None

    @property
    def is_open(self) -> bool:
        return self.port is not None and self.port.is_open

    def open(self) -> SerialSession:
        if not self.is_open:
            self.port = open_port(self.config)
        return self

    def close(self) -> None:
        if self.port is not None:
            self.port.close()
            self.port = None

    def send_once(self, message: str | None = None) -> str:
        self.open()
        if self.port is None:
            raise RuntimeError("serial port is not open")

        hex_message = require_message(message)
        return _send_to_port(self.port, hex_message, self.config)

    def receive_once(self) -> list[str]:
        self.open()
        if self.port is None:
            raise RuntimeError("serial port is not open")

        return _receive_from_port(self.port, self.config)

    def send_and_receive(self, message: str | None = None) -> list[str]:
        self.send_once(require_message(message))
        return self.receive_once()

    def __enter__(self) -> SerialSession:
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def get_default_session(config: dict[str, Any] | None = None) -> SerialSession:
    default_session = STATE.get("default_session")
    if isinstance(default_session, SerialSession):
        if config is not None:
            default_session.config = config
        return default_session

    session = SerialSession(config)
    STATE["default_session"] = session
    return session


def connect(config: dict[str, Any] | None = None) -> SerialSession:
    return get_default_session(config).open()


def disconnect() -> None:
    default_session = STATE.get("default_session")
    if isinstance(default_session, SerialSession):
        default_session.close()

    STATE["default_session"] = None


def _resolve_session(
    config: dict[str, Any] | None = None, session: SerialSession | None = None
) -> tuple[SerialSession, bool]:
    if session is not None:
        session.open()
        return session, False

    default_session = STATE.get("default_session")
    if isinstance(default_session, SerialSession):
        if config is not None:
            default_session.config = config
        default_session.open()
        return default_session, False

    temporary_session = SerialSession(config)
    temporary_session.open()
    return temporary_session, True


def send_once(
    message: str | None = None,
    config: dict[str, Any] | None = None,
    session: SerialSession | None = None,
) -> str:
    explicit_message = require_message(message)
    active_session, should_close = _resolve_session(config, session)
    try:
        return active_session.send_once(explicit_message)
    finally:
        if should_close:
            active_session.close()


def receive_once(
    config: dict[str, Any] | None = None,
    session: SerialSession | None = None,
) -> list[str]:
    active_session, should_close = _resolve_session(config, session)
    try:
        return active_session.receive_once()
    finally:
        if should_close:
            active_session.close()


def send_and_receive(
    message: str | None = None,
    config: dict[str, Any] | None = None,
    session: SerialSession | None = None,
) -> list[str]:
    explicit_message = require_message(message)
    active_session, should_close = _resolve_session(config, session)
    try:
        return active_session.send_and_receive(explicit_message)
    finally:
        if should_close:
            active_session.close()


def send_defined(
    name: str,
    config: dict[str, Any] | None = None,
    session: SerialSession | None = None,
) -> list[str]:
    lookup_name = require_message(name).strip().lower()
    defined_messages = load_defined_messages()

    if lookup_name not in defined_messages:
        available_names = ", ".join(sorted(defined_messages))
        raise ValueError(
            f"unknown defined message '{name}'. Available messages: {available_names}"
        )

    return send_and_receive(
        defined_messages[lookup_name],
        config=config,
        session=session,
    )


def show_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return config or load_config()


CONFIG = load_config()

if __name__ == "__main__":
    print(
        "Interactive helpers loaded: \n- load_config\n- show_config\n- connect\n- "
        "disconnect\n- get_default_session\n- load_defined_messages\n- "
        "send_once\n- receive_once\n- send_and_receive\n- send_defined\n- "
        "SerialSession"
    )
