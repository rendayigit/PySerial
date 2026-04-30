from __future__ import annotations

import math
import struct
from typing import Any, Callable

import py_serial

FIRST_MESSAGE = "AA BB"
TRUE_MESSAGE = "CC"
FALSE_MESSAGE = "DD"


def get_decision_bytes(response: list[str]) -> list[str]:
    if len(response) < 3:
        return []

    return response[-3:-1]


def decode_decision_float(response: list[str]) -> float | None:
    decision_bytes = get_decision_bytes(response)
    if len(decision_bytes) != 2:
        return None

    raw_bytes = bytes(int(part, 16) for part in decision_bytes)
    return struct.unpack(">e", raw_bytes)[0]


def choose_follow_up_message(response: list[str]) -> str:
    decision_value = decode_decision_float(response)
    if decision_value is not None and math.isclose(decision_value, 1.0):
        return TRUE_MESSAGE

    return FALSE_MESSAGE


def _run_example(send_and_receive_step: Callable[[str], list[str]]) -> dict[str, Any]:
    first_response = send_and_receive_step(FIRST_MESSAGE)
    decision_bytes = get_decision_bytes(first_response)
    decision_value = decode_decision_float(first_response)
    follow_up_message = choose_follow_up_message(first_response)
    second_response = send_and_receive_step(follow_up_message)

    return {
        "first_message": FIRST_MESSAGE,
        "first_response": first_response,
        "decision_bytes": decision_bytes,
        "decision_float": decision_value,
        "follow_up_message": follow_up_message,
        "second_response": second_response,
    }


def run_example(
    config: dict[str, Any] | None = None,
    send_and_receive_func: Callable[[str, dict[str, Any]], list[str]] | None = None,
) -> dict[str, Any]:
    current_config = config or py_serial.load_config()

    if send_and_receive_func is not None:
        return _run_example(
            lambda message: send_and_receive_func(message, current_config)
        )

    with py_serial.SerialSession(current_config) as session:
        return _run_example(session.send_and_receive)


def print_result(result: dict[str, Any]) -> None:
    print(f"First message:    {result['first_message']}")
    print(f"First response:   {result['first_response']}")
    print(f"Decision bytes:   {result['decision_bytes']}")
    print(f"Decision float:   {result['decision_float']}")
    print(f"Follow-up message:{result['follow_up_message']}")
    print(f"Second response:  {result['second_response']}")


if __name__ == "__main__":
    print_result(run_example())
