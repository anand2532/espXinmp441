# ESP32 + INMP441 Audio Recorder

## Overview
This project uses an ESP32 and an INMP441 I2S MEMS microphone to capture audio and transfer the recorded data to a computer over USB serial. A Python script running on the computer receives the audio samples and converts them into a WAV file for playback and analysis.

## Hardware Used
- ESP32 Development Board
- INMP441 I2S Microphone
- USB Cable
- Computer (for audio capture and WAV generation)

## Connections

| INMP441 | ESP32 |
|----------|--------|
| VCC | 3.3V |
| GND | GND |
| WS | GPIO 25 |
| SCK | GPIO 26 |
| SD | GPIO 39 |
| L/R | GND (Left Channel) |

Wire **L/R to GND** (do not leave it floating). The firmware reads both I2S slots and uses whichever channel carries mic data — this works around a common ESP32/ESP-IDF left-right channel swap with the INMP441.

## Features
- Audio capture using ESP32 I2S peripheral
- 16 kHz sampling rate
- 16-bit PCM audio output
- 921600 baud serial transfer of raw audio data
- WAV file generation on the host computer using Python

## Software
### ESP32 Firmware
- PlatformIO
- Arduino Framework
- ESP32 I2S Driver (`driver/i2s.h`)

### PC Side
- Python 3
- pyserial
- wave (stdlib)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Connect the INMP441 microphone to the ESP32 (see wiring table above).
2. Upload the firmware:
   ```bash
   pio run -t upload
   ```
3. Find the serial port:
   ```bash
   ls /dev/ttyUSB* /dev/ttyACM*
   ```
4. **Close any serial monitor** (PlatformIO monitor, `screen`, etc.) before recording — only one process can use the port.
5. Run the Python receiver:
   ```bash
   python recorder.py --port /dev/ttyUSB0 --duration 5
   ```
   Or let it auto-detect the port:
   ```bash
   python recorder.py --duration 5
   ```
6. The script saves the received audio as `recording.wav` (or the path given with `--output`).

### Serial baud rate
Both firmware and Python must use **921600 baud**. At 16 kHz mono 16-bit PCM, audio needs ~32 KB/s; 115200 baud is too slow and produces garbled or time-stretched recordings.

## Output
The generated WAV file can be played using any standard audio player. For a 5-second recording, expect roughly 160,000 bytes of PCM data (plus 44-byte WAV header).

## Troubleshooting
- **Silent recording (all zeros):** Confirm L/R is tied to GND (not floating), VCC is 3.3V, and WS/SCK/SD match the wiring table. Re-flash after firmware updates. Check levels with:
  ```bash
  python3 -c "import wave,struct; d=wave.open('recording.wav').readframes(80000); s=struct.unpack('<'+'h'*(len(d)//2),d); print(min(s),max(s))"
  ```
  Non-zero `max` means audio is present.
- **Garbled/slow audio:** Verify both sides use 921600 baud and no other app is reading the serial port.
- **Noisy/static:** Try changing `SAMPLE_SHIFT` in `src/main.cpp` from `14` to `16`, or swap WS and SCK wiring if clocks are crossed.

## Author
Shaurye Singhal
