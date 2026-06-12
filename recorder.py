#!/usr/bin/env python3
import argparse
import sys
import time
import wave
import platform

import serial
from serial.tools import list_ports

SAMPLE_RATE = 16000
BYTES_PER_SAMPLE_RECEIVED = 1 # We receive 8-bit mu-law over cable
BYTES_PER_SAMPLE_SAVED = 2    # We save pristine 16-bit standard PCM
CHANNELS = 2  # STEREO

ESP_USB_IDS = {
    (0x10C4, 0xEA60),  # CP210x
    (0x1A86, 0x7523),  # CH340
    (0x1A86, 0x55D4),  # CH9102
    (0x303A, 0x1001),  # ESP32-S2/S3 USB CDC
}

# --- Generate the mu-law Decoding Lookup Table ---
# This instantly maps an 8-bit squished byte back to its 16-bit original value
ULAW_TABLE = [0] * 256
for i in range(256):
    u_val = ~i & 0xFF
    sign = (u_val & 0x80)
    exponent = (u_val >> 4) & 0x07
    mantissa = u_val & 0x0F
    sample = ((mantissa << 3) + 132) << exponent
    sample -= 132
    ULAW_TABLE[i] = -sample if sign else sample


def find_esp_port():
    for port in list_ports.comports():
        if port.vid is not None and (port.vid, port.pid) in ESP_USB_IDS:
            return port.device
        desc = (port.description or "").lower()
        if any(name in desc for name in ("cp210", "ch340", "ch910", "usb serial", "uart")):
            return port.device
    return None

def parse_args():
    parser = argparse.ArgumentParser(description="Record Stereo mu-law audio from ESP32.")
    parser.add_argument("--port", help="Serial port. Auto-detected if omitted.")
    parser.add_argument("--baud", type=int, default=460800, help="Safe Mac baud rate.")
    parser.add_argument("--duration", type=float, default=5.0, help="Recording duration.")
    parser.add_argument("--output", default="stereo_compressed_recording.wav", help="Output WAV path.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Extra wait time.")
    return parser.parse_args()

def main():
    args = parse_args()

    port = args.port or find_esp_port()
    if not port:
        print("Error: no serial port found. Pass --port explicitly.", file=sys.stderr)
        sys.exit(1)

    # Note: We expect 1 byte per sample over the cable now!
    expected_bytes = int(SAMPLE_RATE * BYTES_PER_SAMPLE_RECEIVED * CHANNELS * args.duration)
    deadline = time.time() + args.duration + args.timeout 
    print(f"Opening {port} at {args.baud} baud for compressed STEREO recording...")
    
    try:
        ser = serial.Serial(port, args.baud, timeout=1)
    except Exception as e:
        print(f"Failed to open port {port}: {e}")
        sys.exit(1)

    time.sleep(2)
    ser.reset_input_buffer()
    print("Discarding 3 seconds of startup static...")
    
    # CHANGED: Multiplied by 3.0 instead of 1.0
    discard_bytes = int(SAMPLE_RATE * BYTES_PER_SAMPLE_RECEIVED * CHANNELS * 3.0) 
    
    discarded = 0
    while discarded < discard_bytes:
        chunk = ser.read(min(4096, discard_bytes - discarded))
        discarded += len(chunk)

    print(f"Recording {args.duration:.1f}s ({expected_bytes} bytes expected)...")

    audio = bytearray() 
    while len(audio) < expected_bytes and time.time() < deadline:
        chunk = ser.read(min(4096, expected_bytes - len(audio)))
        if chunk:
            audio.extend(chunk)

    ser.close()

    implied_duration = len(audio) / (SAMPLE_RATE * BYTES_PER_SAMPLE_RECEIVED * CHANNELS)
    print(f"Received {len(audio)} bytes ({implied_duration:.2f}s of audio)")

    if len(audio) == 0:
        print("Error: Received 0 bytes.", file=sys.stderr)
        sys.exit(1)

    # 1. Byte alignment for compressed data: 1 frame = 2 bytes (1 L, 1 R)
    remainder = len(audio) % 2
    if remainder != 0:
        audio = audio[:-remainder]

    # 2. Decode the mu-law audio back to high-quality 16-bit PCM
    print("Decoding log-compressed audio to 16-bit PCM...")
    pcm_audio = bytearray()
    for byte in audio:
        pcm_val = ULAW_TABLE[byte]
        # Pack the integer into 2 bytes (16-bit little-endian)
        pcm_audio.extend(pcm_val.to_bytes(2, byteorder='little', signed=True))

    # 3. Save as standard, uncompressed 16-bit WAV file
    with wave.open(args.output, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BYTES_PER_SAMPLE_SAVED) # Set to 2 bytes!
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_audio)
        
    print(f"Saved uncompressed Stereo audio to: {args.output}")

if __name__ == "__main__":
    main()