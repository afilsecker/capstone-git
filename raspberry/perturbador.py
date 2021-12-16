import json
from serial import Serial
from collections import deque
from multiprocessing.connection import Connection
from threading import Thread
import time


class Perturbador:
    def __init__(self, perturbador_pipe: Connection, lock):
        self.lock = lock
        self.perturbador_pipe = perturbador_pipe
        print("inicializando perturbador")
        with open('parametros.json', 'r') as f:
            diccionario = json.load(f)
            self.__dict__.update(diccionario['perturbador'])

        self.generar_diccionario_acciones()
        Thread(target=self.handle_capstone, name='handle_capstone').start()
        self.start_serial()

    def generar_diccionario_acciones(self):
        self.action_dict = {
            "send": self.send,
            'reset': self.reset
        }

    def handle_capstone(self):
        while True:
            recibido = self.perturbador_pipe.recv()
            if isinstance(recibido, str):
                print(f"recibido: {recibido}")

            elif isinstance(recibido, list):
                if recibido[1] is not None:
                    self.action_dict[recibido[0]](**recibido[1])

                else:
                    self.action_dict[recibido[0]]()

    def start_serial(self):
        self.serial = Serial(self.ruta, self.baudrate, timeout=self.timeout)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        self.closed = False
        Thread(target=self.listen, daemon=False, name="listen serial").start()

    def reset(self):
        self.closed = True
        self.serial.close()
        self.server_buffer = deque()
        self.start_serial()

    def listen(self):
        while not self.closed:
            try:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode(self.encoding).rstrip()
                    value = ["perturbador", {"recibido": line}]
                    send = ['send', {'value': value}]
                    envio = ['send_to_server', {'value': send}]
                    self.send_capstone(envio)
                time.sleep(0.1)
            except OSError:
                pass

    def send_capstone(self, envio):
        with self.lock:
            self.perturbador_pipe.send(envio)

    def send(self, msg: str):
        print(msg)
        self.serial.write((msg + '\n').encode(self.encoding))
