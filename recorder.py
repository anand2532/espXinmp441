#!/usr/bin/env python3
import argparse
import sys
import time
import wave

import serial
from serial.tools import list_ports

SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2

ESP_USB_IDS = {
    (0x10C4, 0xEA60),  # CP210x
    (0x1A86, 0x7523),  # CH340
    (0x1A86, 0x55D4),  # CH9102
    (0x303A, 0x1001),  # ESP32-S2/S3 USB CDC
}


def find_esp_port():
    for port in list_ports.comports():
        if port.vid is not None and (port.vid, port.pid) in ESP_USB_IDS:
            return port.device
        desc = (port.description or "").lower()
        if any(name in desc for name in ("cp210", "ch340", "ch910", "usb serial", "uart")):
            return port.device
    return None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Record raw PCM audio from ESP32 + INMP441 over USB serial."
    )
    parser.add_argument(
        "--port",
        help="Serial port (e.g. /dev/ttyUSB0). Auto-detected if omitted.",
    )
    parser.add_argument("--baud", type=int, default=460800, help="Serial baud rate.")
    parser.add_argument(
        "--duration", type=float, default=5.0, help="Recording duration in seconds."
    )
    parser.add_argument(
        "--output", default="recording.wav", help="Output WAV file path."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Extra seconds to wait beyond expected duration.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    port = args.port or find_esp_port()
    if not port:
        print("Error: no serial port found. Pass --port explicitly.", file=sys.stderr)
        sys.exit(1)

    expected_bytes = int(SAMPLE_RATE * BYTES_PER_SAMPLE * args.duration)
    deadline = time.time() + args.duration + args.timeout

    print(f"Opening {port} at {args.baud} baud...")
    ser = serial.Serial(port, args.baud, timeout=1)

    time.sleep(2)
    ser.reset_input_buffer()

    print(f"Recording {args.duration:.1f}s ({expected_bytes} bytes expected)...")

    audio = bytearray()
    while len(audio) < expected_bytes and time.time() < deadline:
        chunk = ser.read(min(4096, expected_bytes - len(audio)))
        if chunk:
            audio.extend(chunk)

    ser.close()

    implied_duration = len(audio) / (SAMPLE_RATE * BYTES_PER_SAMPLE)
    print(f"Received {len(audio)} bytes ({implied_duration:.2f}s of audio)")

    if len(audio) < expected_bytes:
        print(
            f"Warning: got {len(audio)} bytes, expected {expected_bytes}. "
            "Check baud rate and close other serial monitors.",
            file=sys.stderr,
        )

    with wave.open(args.output, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(BYTES_PER_SAMPLE)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio)

    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
