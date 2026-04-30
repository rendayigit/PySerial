from __future__ import annotations

from typing import Any

import py_serial

# Replace these three message constants with the command bytes for your device.
IDLE_MESSAGE = "00"
START_MESSAGE = "01"
STOP_MESSAGE = "02"
CONFIG = py_serial.load_config()


def connect(config: dict[str, Any] | None = None) -> py_serial.SerialSession:
    return py_serial.connect(config or CONFIG)


def disconnect() -> None:
    py_serial.disconnect()


def show_config() -> dict[str, Any]:
    return py_serial.show_config(CONFIG)


def _print_received_message(label: str, response: list[str]) -> None:
    if response:
        print(f"{label} RX: {' '.join(response)}")
        return

    print(f"{label} RX: <timeout>")


def _send_defined_message(
    message: str,
    label: str,
    config: dict[str, Any] | None = None,
    session: py_serial.SerialSession | None = None,
) -> list[str]:
    response = py_serial.send_and_receive(
        message,
        config=config or CONFIG,
        session=session,
    )
    _print_received_message(label, response)
    return response


def send_idle(
    config: dict[str, Any] | None = None,
    session: py_serial.SerialSession | None = None,
) -> list[str]:
    return _send_defined_message(IDLE_MESSAGE, "IDLE", config, session)


def start(
    config: dict[str, Any] | None = None,
    session: py_serial.SerialSession | None = None,
) -> list[str]:
    return _send_defined_message(START_MESSAGE, "START", config, session)


def stop(
    config: dict[str, Any] | None = None,
    session: py_serial.SerialSession | None = None,
) -> list[str]:
    return _send_defined_message(STOP_MESSAGE, "STOP", config, session)


if __name__ == "__main__":
    print(
        "Interactive helpers loaded: \n- show_config\n- connect\n- "
        "disconnect\n- send_idle\n- start\n- stop"
    )
