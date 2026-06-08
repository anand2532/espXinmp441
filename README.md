# ESP32 + INMP441 Audio Recorder

## Overview
This project uses an ESP32 and an INMP441 I2S MEMS microphone to capture audio and transfer the recorded data to a computer over Serial communication. A Python script running on the computer receives the audio samples and converts them into a WAV file for playback and analysis.

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
| L/R | GND (Left Channel) or 3.3V (Right Channel) |

## Features
- Audio capture using ESP32 I2S peripheral
- 16 kHz sampling rate
- 16-bit PCM audio output
- Serial transfer of raw audio data
- WAV file generation on the host computer using Python

## Software
### ESP32 Firmware
- PlatformIO
- Arduino Framework
- ESP32 I2S Driver

### PC Side
- Python 3
- pyserial
- wave

## Usage
1. Connect the INMP441 microphone to the ESP32.
2. Upload the firmware to the ESP32.
3. Run the Python receiver script on the computer.
4. Record audio through the microphone.
5. The Python script saves the received audio as recording.wav.

## Output
The generated WAV file can be played using any standard audio player.

## Author
Shaurye Singhal# espXinmp441
