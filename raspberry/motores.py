import json
from serial import Serial
from multiprocessing import Process, Pipe
from collections import deque
from multiprocessing.connection import Connection
from multiprocessing import Lock
from threading import Thread
from time import sleep, time
import random


class Motores:
    def __init__(self, motores_pipe: Connection, lock, controlador_pipe: Connection):
        self.lock = lock
        self.lock_serial = Lock()
        self.controlador_pipe = controlador_pipe
        self.motores_pipe = motores_pipe
        self.in_calibrate = False
        with open('parametros.json', 'r') as f:
            diccionario = json.load(f)
            self.__dict__.update(diccionario['motores'])

        self.listen_interval = 0.05
        self.generar_diccionario_acciones()
        self.generar_diccionario_acciones_motores()
        Thread(target=self.handle_capstone, name='handle_capstone').start()
        Thread(target=self.handle_controlador).start()
        self.start_serial()
        self.send_hard_reset()

    # Cosas de serial
    def start_serial(self):
        self.serial = Serial(port=self.ruta, baudrate=115200)
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
                    c = self.serial.read()
                    c = int.from_bytes(c, byteorder='big')
                    self.motores_action_dict[c]()
            except KeyError:
                print(f"Opcion {c} no válida")

            sleep(0.005)

    # Para acciones que vienen del arduino
    def generar_diccionario_acciones_motores(self):
        self.motores_action_dict = {
            0: self.calibrate_complete,
            1: self.center_reach,
            2: self.top_limit_reached,
            3: self.top_limit_cleared,
            4: self.bottom_limit_reached,
            5: self.bottom_limit_cleared,
            6: self.right_limit_reached,
            7: self.right_limit_cleared,
            8: self.left_limit_reached,
            9: self.left_limit_cleared,
            10: self.sleep_mode_entered,
            11: self.clear_sleep_mode,
            12: self.warning_awake,
            13: self.hard_reseted
        }

    def calibrate_complete(self):
        print("calibration completed")
        self.send_server(['calibrate_complete', None])

    def center_reach(self):
        print("center reached")

    def top_limit_reached(self):
        print("top limit reached")

    def top_limit_cleared(self):
        print("top limit cleared")

    def bottom_limit_reached(self):
        print("bottom limit reached")

    def bottom_limit_cleared(self):
        print("bottom limit cleared")

    def right_limit_reached(self):
        print("right limit reached")

    def right_limit_cleared(self):
        print("right limit cleared")

    def left_limit_reached(self):
        print("left limit reached")

    def left_limit_cleared(self):
        print("left limit cleared")

    def sleep_mode_entered(self):
        print("sleep mode entered")

    def clear_sleep_mode(self):
        print("clear sleep mode")

    def warning_awake(self):
        print("warning awake")

    def hard_reseted(self):
        print("hard_reseted")
        self.send_server(['hard_reseted', None])

    # Para acciones de controlador
    def handle_controlador(self):
        while True:
            recibido = self.controlador_pipe.recv()
            self.set_vels(**recibido[1])

    # Para acciones que vienen de Capstone
    def handle_capstone(self):
        while True:
            recibido = self.motores_pipe.recv()
            if isinstance(recibido, str):
                print(f"recibido: {recibido}")

            elif isinstance(recibido, list):
                if recibido[1] is not None:
                    self.action_dict[recibido[0]](**recibido[1])

                else:
                    self.action_dict[recibido[0]]()

    def generar_diccionario_acciones(self):
        self.action_dict = {
            'set_vels': self.set_vels,
            'send_calibrate': self.send_calibrate,
            'reset': self.reset,
            'send_sleep': self.send_sleep,
            'send_awake': self.send_awake,
            'send_center': self.send_center
        }

    def set_vels(self, vel_A: int, vel_B: int):
        self.start_time = time()
        initial_bit = pow(2, 7)
        if vel_A >= 0:
            initial_bit += pow(2, 0)
        if vel_B >= 0:
            initial_bit += pow(2, 1)
        initial_bit = int.to_bytes(initial_bit, 1, 'big')
        self.serial.write(initial_bit)
        vel_A_bit = int.to_bytes(abs(vel_A), 1, 'big')
        self.serial.write(vel_A_bit)
        vel_B_bit = int.to_bytes(abs(vel_B), 1, 'big')
        self.serial.write(vel_B_bit)
        # print('send_time = {:<6.2f} ms'.format((time() - self.start_time) * 1000))

    def send_calibrate(self):
        self.in_calibrate = True
        bit = pow(2, 6)
        bit = int.to_bytes(bit, 1, 'big')
        self.serial.write(bit)

    def send_sleep(self):
        bit = pow(2, 5)
        bit = int.to_bytes(bit, 1, 'big')
        self.serial.write(bit)

    def send_awake(self):
        bit = pow(2, 4)
        bit = int.to_bytes(bit, 1, 'big')
        self.serial.write(bit)

    def send_center(self):
        bit = pow(2, 3)
        bit = int.to_bytes(bit, 1, 'big')
        self.serial.write(bit)

    def send_hard_reset(self):
        bit = sum(pow(2, exp) for exp in range(8))
        bit = int.to_bytes(bit, 1, 'big')
        self.serial.write(bit)

    # Para acciones hacia Capstone
    def send_capstone(self, envio):
        with self.lock:
            self.motores_pipe.send(envio)

    def send_server(self, value):
        send = ['send', {'value': value}]
        envio = ['send_to_server', {'value': send}]
        self.send_capstone(envio)


def motores_process(motores_pipe, lock_send):
    Motores(motores_pipe, lock_send)


if __name__ == '__main__':
    conn1, conn2 = Pipe()
    lock = Lock()
    Process(target=motores_process, daemon=False, args=(conn1, lock),
            name="proceso motores").start()
    vel_A = 0
    vel_B = -255
    sleep(2)
    while True:
        try:
            a = int(input('1 para calibrar, 2 para velocidad random: '))
            if a == 1:
                conn2.send(['send_calibrate', None])
                print("calibrate")
            elif a == 2:
                vel_A = random.randint(-254, 254)
                vel_B = random.randint(-254, 254)
                print(f"vel_A = {vel_A}, vel_B = {vel_B}")
                conn2.send(['set_vels', {'vel_A': vel_A, 'vel_B': vel_B}])
            elif a == 0:
                vel_A = 0
                vel_B = 0
                print(f"vel_A = {vel_A}, vel_B = {vel_B}")
                conn2.send(['set_vels', {'vel_A': vel_A, 'vel_B': vel_B}])
            elif a == 3:
                vel_A = int(input("vel_A: "))
                vel_B = 0
                print(f"vel_A = {vel_A}, vel_B = {vel_B}")
                conn2.send(['set_vels', {'vel_A': vel_A, 'vel_B': vel_B}])
            elif a == 4:
                vel_A = 0
                vel_B = 0
                mult = 1
                for i in range(100, 254):
                    vel_A = i * mult
                    vel_B = i * - mult
                    mult = - mult
                    print(f"vel_A = {vel_A}, vel_B = {vel_B}")
                    conn2.send(['set_vels', {'vel_A': vel_A, 'vel_B': vel_B}])
                    sleep(0.5)
            elif a == 5:
                vel_A_anterior = 0
                vel_B_anterior = 0
                for _ in range(100):
                    vel_A = random.randint(-254, 254)
                    vel_B = random.randint(-254, 254)
                    while abs(vel_A - vel_A_anterior) > 150:
                        vel_A = random.randint(-254, 254)
                    while abs(vel_B - vel_B_anterior) > 200:
                        vel_B = random.randint(-254, 254)
                    print(f"vel_A = {vel_A}, vel_B = {vel_B}")
                    conn2.send(['set_vels', {'vel_A': vel_A, 'vel_B': vel_B}])
                    sleep(0.1)
                    vel_A_anterior = vel_A
                    vel_B_anterior = vel_B
            elif a == 6:
                conn2.send(['send_sleep', None])
            elif a == 7:
                conn2.send(['send_awake', None])
            elif a == 8:
                conn2.send(['send_center', None])
            elif a == 9:
                print("custom vels:")
                vel_A = int(input('vel_A: '))
                vel_B = int(input('vel_B: '))
                conn2.send(['set_vels', {'vel_A': vel_A, 'vel_B': vel_B}])

        except Exception:
            pass
