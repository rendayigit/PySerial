# PySerial Helper

Small serial helper for VS Code with both interactive and scripted workflows.

## Files

- `py_serial.py`: main script with the serial helpers.
- `defined_messages.py`: predefined helper functions such as `send_idle()`, `start()`, and `stop()` for repeated manual use.
- `defined_messages.json`: fixed name-to-message map used by `py_serial.send_defined()`.
- `sample_scenario.py`: simple example that sends `AA BB`, checks the received bytes, then sends `CC` or `DD`.
- `config.json`: serial settings, receive timing, and logging only.
- `.vscode/tasks.json`: install, interactive, predefined-message, and example-run tasks.
- `.vscode/settings.json`: Task Buttons configuration for the main tasks.
- `.vscode/extensions.json`: recommended VS Code extensions for the project.
- `logs/`: created automatically for timestamped log files.

## Install

```bash
python -m pip install -r requirements.txt
```

## Configure

Edit `config.json`.

### `serial`

These values are passed to `serial.Serial(...)`:

- `port`
- `baudrate`
- `bytesize`
- `parity`
- `stopbits`
- `timeout`
- `write_timeout`
- `xonxoff`
- `rtscts`
- `dsrdtr`
- `inter_byte_timeout`
- `exclusive`

### `app`

- `receive_timeout_seconds`: wait this long for the first received byte.
- `receive_inter_byte_timeout_seconds`: after the first byte arrives, stop reading when this gap passes with no new byte.
- `log_directory`: folder for log files.

`config.json` does not contain message payloads. Keep bus settings here, and put example messages or scripted decisions in `sample_scenario.py`. The config file location is fixed in `py_serial.py`, so users do not need to pass a config path around.

Predefined named messages are stored in `defined_messages.json`, and `py_serial.send_defined("name")` looks them up automatically.

## Run In VS Code

Run the task `Python: Interactive py_serial`.

That opens a Python REPL with `py_serial.py` already loaded, so you can call the functions directly.

Run the task `Python: Interactive defined_messages`.

That opens a Python REPL with `defined_messages.py` already loaded, so you can call `connect()`, `disconnect()`, `show_config()`, `send_idle()`, `start()`, or `stop()` without typing the message bytes each time.

Run the tasks `Python: Send idle`, `Python: Start`, or `Python: Stop`.

Those tasks call the predefined functions directly and print the received message to the terminal.

Run the task `Python: Run sample scenario`.

That executes `sample_scenario.py`, which shows a simple fixed example on top of `py_serial.py`.

Task Buttons users can use the buttons from `.vscode/settings.json` to run install, interactive, predefined-message, or example tasks directly from the UI.

VS Code will also recommend the extensions from `.vscode/extensions.json` when the project is opened.

## Functions

```python
show_config()
connect()
send_once("AA BB")
send_defined("idle")
receive_once()
send_and_receive("AA BB")
disconnect()
```

This mode is intended for manual runtime decisions from the opened Python terminal.

If you want to keep the same serial connection open across several manual calls, use `connect()` first and `disconnect()` when you are done.

## Defined Messages

`defined_messages.py` is a lightweight helper layer on top of `py_serial.py`.

It reuses the original `connect()`, `disconnect()`, `show_config()`, and `send_defined()` from `py_serial.py` directly, and only adds the named helper wrappers.

It defines these functions:

```python
connect()
disconnect()
show_config()
send_defined("idle")
send_idle()
start()
stop()
```

Each function transmits once, receives once, prints the received message to the terminal, and returns the received hex array.

The actual bytes are defined in `defined_messages.json`:

```json
{
  "idle": "00",
  "start": "01",
  "stop": "02"
}
```

Change those entries to match your protocol.

## Scripted Example

`sample_scenario.py` demonstrates this simple flow on a persistent serial session:

1. Send `AA BB`.
2. Receive one response.
3. Take the third-last and second-last bytes from the response.
4. Combine those two bytes and decode them as a big-endian IEEE 754 half float.
5. If that float is `1.0`, send `CC`. Otherwise send `DD`.
6. Receive once more after the follow-up send.

Example entry point:

```bash
python sample_scenario.py
```

If you want a different fixed scenario, copy `sample_scenario.py` and change the messages or response check directly in code.

## Message Formats

- Transmit input: `"AA BB CC DD"`
- Receive return value: `["AA", "BB", "CC", "DD"]`

## Logging

- Logs are written only to files, not to the terminal.
- Each log file is named with the date and time when it is first created.
- Timestamps are precise to the millisecond.
- Newest log entry is written at the top.
- Direction labels are included: `TX`, `RX`, or `RX TIME`.

## Notes

- `send_and_receive()` sends once, then reads once on the same port.
- `send_defined()` sends once and receives once by looking up a message name in `defined_messages.json`.
- `SerialSession` keeps the port open for repeated calls when you want a persistent manual session.
- On receive timeout with no data, the receive functions return `[]`.
- `send_once()` and `send_and_receive()` require an explicit message argument.
- `defined_messages.py` gives you named helper functions so you do not have to type the hex bytes manually every time.
- `sample_scenario.py` is an example layer on top of `py_serial.py`; it does not replace the interactive workflow.
- Change `config.json` whenever you want different serial settings or timeouts.
