from __future__ import annotations

from py_serial import connect, disconnect, send_defined, show_config

INTERACTIVE_HELPER_NAMES = [
    connect.__name__,
    disconnect.__name__,
    show_config.__name__,
    send_defined.__name__,
    "send_idle",
    "start",
    "stop",
]


def _print_received_message(label: str, response: list[str]) -> None:
    if response:
        print(f"{label} RX: {' '.join(response)}")
        return

    print(f"{label} RX: <timeout>")


def _send_defined_message(
    name: str,
) -> list[str]:
    response = send_defined(name)
    _print_received_message(name.upper(), response)
    return response


def send_idle() -> list[str]:
    return _send_defined_message("idle")


def start() -> list[str]:
    return _send_defined_message("start")


def stop() -> list[str]:
    return _send_defined_message("stop")


if __name__ == "__main__":
    print("Interactive helpers loaded: \n- " + "\n- ".join(INTERACTIVE_HELPER_NAMES))
