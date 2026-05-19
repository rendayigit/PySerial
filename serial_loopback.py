import serial

# Loopback Settings
PORT = "/dev/ttyUSB1"
BAUDRATE = 115200


def run_loopback():
    try:
        # timeout=None allows pure OS-level blocking for maximum speed
        with serial.Serial(PORT, BAUDRATE, timeout=None, exclusive=True) as ser:
            print(f"Loopback started on {PORT} at {BAUDRATE} baud.")
            print("Press Ctrl+C to stop.")

            while True:
                # 1. Block and wait for the starting byte
                byte = ser.read(1)

                if byte == b"\xc0":
                    # 2. We found the start! Now efficiently read everything up to the ending 'C0'
                    rest_of_data = ser.read_until(b"\xc0")

                    # 3. Combine the start byte with the rest of the data
                    full_packet = byte + rest_of_data

                    # 4. Reverse the packet and send it back
                    ser.write(full_packet[::-1])
                    ser.flush()

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("\nLoopback stopped.")


if __name__ == "__main__":
    run_loopback()
