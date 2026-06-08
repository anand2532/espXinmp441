import serial
import wave
import time

PORT = "/dev/cu.usbserial-10"
BAUD = 115200

print("Opening serial...")
ser = serial.Serial(PORT, BAUD)

time.sleep(3)          # wait for ESP32 reboot
ser.reset_input_buffer()

print("Recording 5 seconds...")

audio = bytearray()

start = time.time()

while time.time() - start < 5:
    audio.extend(ser.read(4096))

print("Received", len(audio), "bytes")

with wave.open("recording.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(audio)

print("Saved recording.wav")

ser.close()