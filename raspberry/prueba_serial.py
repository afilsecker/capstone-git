import serial
import threading
import time

s = serial.Serial(port="/dev/ttyS0", baudrate=9600)


def listen():
    while True:
        if s.in_waiting > 0:
            c = s.read()
            c = int.from_bytes(c, byteorder='big')
            print(f"c, {c}")
        time.sleep(0.05)


threading.Thread(target=listen).start()

a = 0

while True:
    pass
