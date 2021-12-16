from time import time, sleep
import json
from multiprocessing.connection import Connection
from camera import Camera
from threading import Event, Thread
import numpy as np


class Controlador():
    def __init__(self, controlador_pipe: Connection, lock, pipe_motores: Connection):
        with open('parametros.json', 'r') as f:
            diccionario = json.load(f)
            self.__dict__.update(diccionario['controlador'])

        self.lock = lock
        self.pipe_motores = pipe_motores
        self.e_a_antiguos_i = list()
        self.e_b_antiguos_i = list()
        self.e_a_antiguos_d = list()
        self.e_b_antiguos_d = list()
        self.lista_datos = list()
        self.e_a_anterior = 0
        self.e_b_anterior = 0
        self.graficar = False
        self.prueba_13_activada = False
        self.prueba_13_listo = False
        self.inicio_prueba_13 = False
        self.envio_datos = False
        self.controlar_activado = False
        self.controlador_pipe = controlador_pipe
        self.listo_event = Event()
        self.camera = Camera(self.listo_event)
        self.resolution = self.camera.resolution
        self.ref = [self.resolution[0] / 2, self.resolution[1] / 2]
        self.parametros_dict = dict()
        self.obtener_parametros()
        self.contador = 0
        self.lista_fps = []
        self.laser_fuera = False
        self.start_time = time()
        self.generar_diccionario_acciones()
        Thread(target=self.controlar, daemon=False, name='controlar').start()
        Thread(target=self.handle_capstone, daemon=False, name='handle_capstone').start()

    # Para controlar las acciones que vienen de capstone
    def handle_capstone(self):
        while True:
            recibido = self.controlador_pipe.recv()
            if isinstance(recibido, str):
                print(f"recibido: {recibido}")

            elif isinstance(recibido, list):
                if recibido[1] is not None:
                    self.action_dict[recibido[0]](**recibido[1])

                else:
                    self.action_dict[recibido[0]]()

    def generar_diccionario_acciones(self):
        self.action_dict = {
            "initial_data_request": self.send_initial_data,
            'prueba_procesamiento': self.prueba_procesamiento,
            'set_actualizacion_datos': self.set_actualizacion_datos,
            'set_controlar_activado': self.set_controlar_activado,
            'nuevos_parametros': self.actualizar_parametros,
            'cambio_referencia': self.cambio_referencia,
            'prueba_13': self.prueba_13,
            'detener': self.detener_prueba,
            'set_graficar': self.set_graficar
        }

    def send_initial_data(self):
        datos = dict()
        datos['resolution'] = self.resolution
        datos['parametros'] = self.parametros_dict
        value = ['initial_data', datos]
        send = ['send', {'value': value}]
        envio = ['send_to_server', {"value": send}]
        self.send(envio)

    def prueba_procesamiento(self):
        frame, punto_encontrado, puntos_encontrados = self.camera.prueba_procesamiento()
        value = ['prueba_procesamiento_response', {'image': frame,
                                                   'puntos': puntos_encontrados,
                                                   'punto_rojo': punto_encontrado}]
        send = ['send', {'value': value}]
        envio = ['send_to_server', {'value': send}]
        self.send(envio)

    def set_actualizacion_datos(self, state):
        self.envio_datos = state
        self.reset_values()
        self.start_time_grafs = time()

    def set_controlar_activado(self, state):
        self.controlar_activado = state
        if state:
            self.start_time_grafs = time()
        if not state:
            self.envio_calculo()

    def actualizar_parametros(self, parametros: dict):
        self.__dict__.update(parametros)
        with open('par_controlador.txt', 'w') as f:
            for parametro in self.__dict__.keys():
                if parametro in parametros.keys():
                    f.write(parametro)
                    f.write('=')
                    f.write(str(self.__dict__[parametro]))
                    f.write('\n')

    def cambio_referencia(self, ref):
        self.ref = ref

    def set_graficar(self, state):
        self.graficar = state

    # Para acciones hacia capstone
    def send(self, envio):
        with self.lock:
            self.controlador_pipe.send(envio)

    def send_server(self, value):
        send = ['send', {'value': value}]
        envio = ['send_to_server', {'value': send}]
        self.send(envio)

    def almacenar_calculo(self):
        datos = {
                'fps': self.fps,
                'x': self.x,
                'y': self.y,
                'e_a': self.e_a,
                'e_b': self.e_b,
                'e_abs': self.e_abs,
                'ref_x': self.ref_camera_x,
                'ref_y': self.ref_camera_y,
                'p_a': self.p_a,
                'p_b': self.p_b,
                'd_a': self.d_a,
                'd_b': self.d_b,
                'i_a': self.i_a,
                'i_b': self.i_b,
                'u_a': self.u_a,
                'u_b': self.u_b,
                'time': time() - self.start_time_grafs
            }
        self.lista_datos.append(datos)

    def envio_calculo(self):
        if self.graficar:
            for dato in self.lista_datos:
                value = ['control', {'datos': dato}]
                self.send_server(value)
        value = ['datos_done', None]
        self.send_server(value)
        self.lista_datos = list()

    def set_vels(self):
        if self.u_a is not None and self.u_b is not None:
            self.send_time = time()
            value = ['set_vels', {'vel_A': self.u_a, 'vel_B': self.u_b}]
            self.pipe_motores.send(value)

    def send_center(self):
        value = ['send_center', None]
        envio = ['send_to_motores', {'value': value}]
        self.send(envio)

    # Para el controlador
    def obtener_parametros(self):
        with open('par_controlador.txt', 'r') as f:
            for line in f.readlines():
                splited = line.split('=')
                self.__dict__[splited[0]] = float(splited[1][:-1])
                self.parametros_dict[splited[0]] = float(splited[1][:-1])

    def controlar(self):
        while True:
            self.listo_event.wait()
            self.capture_time = time()
            self.listo_event.clear()
            self.contador += 1
            self.fps = 1 / (time() - self.start_time)
            self.lista_fps.append(self.fps)
            if self.contador > 100:
                # print(f"fps: {np.mean(np.array(self.lista_fps)):.2f}")
                self.contador = 0
                self.lista_fps = []

            if self.inicio_prueba_13:
                sleep(0.1)
            self.calcular()
            self.start_time = time()
            if self.controlar_activado:
                self.almacenar_calculo()
                self.set_vels()

            if self.prueba_13_activada:
                self.almacenar_calculo()
                self.tiempo = time()
                self.set_vels()
                if self.prueba_13_listo:
                    self.prueba_13_activada = False
                    self.prueba_13_listo = False
                    self.u_a = 0
                    self.u_b = 0
                    self.set_vels()
                    value = ['prueba_13_listo', None]
                    self.send_server(value)
                    self.envio_calculo()

            if self.laser_fuera:
                self.send_center()
                self.laser_fuera = False

    def calcular(self):
        self.ref_camera_x = self.ref[0]
        self.ref_camera_y = self.ref[1]
        if self.camera.red_point[0] is not None and self.camera.red_point[1] is not None:
            self.laser_fuera = False
            self.x = self.camera.red_point[1]
            self.y = self.camera.red_point[0]
            self.e_b = self.ref_camera_x - self.x
            self.e_a = - self.ref_camera_y + self.y
            self.e_abs = np.sqrt(self.e_b ** 2 + self.e_a ** 2)
            self.p_a = self.e_a * self.kpa
            self.p_b = self.e_b * self.kpb
            if len(self.e_a_antiguos_d) > 0:
                self.d_a = self.kda * (self.e_a -
                                       sum(self.e_a_antiguos_d) / len(self.e_a_antiguos_d))
            else:
                self.d_a = 0
            if len(self.e_b_antiguos_d) > 0:
                self.d_b = self.kdb * (self.e_b -
                                       sum(self.e_b_antiguos_d) / len(self.e_b_antiguos_d))
            else:
                self.d_b = 0
            if len(self.e_a_antiguos_i) > 0:
                self.i_a = self.kia * (sum(self.e_a_antiguos_i) + self.e_a)
            else:
                self.i_a = 0
            if len(self.e_b_antiguos_i) > 0:
                self.i_b = self.kib * (sum(self.e_b_antiguos_i) + self.e_b)
            else:
                self.i_b = 0
            if abs(self.e_b) < self.reset_i_b:
                self.i_b = 0
                self.e_b_antiguos_i = list()
            if abs(self.e_a) < self.reset_i_a:
                self.i_a = 0
                self.e_a_antiguos_i = list()
            if abs(self.i_a) > self.max_i_a:
                self.i_a = self.max_i_a * np.sign(self.i_a)
            if abs(self.i_b) > self.max_i_b:
                self.i_b = self.max_i_b * np.sign(self.i_b)
            self.d_a = - self.d_a
            self.d_b = - self.d_b
            self.u_a = int(self.p_a + self.d_a + self.i_a)
            self.u_b = int(self.p_b + self.d_b + self.i_b)
            self.e_a_antiguos_i.append(self.e_a)
            if len(self.e_a_antiguos_i) > self.length_i_a:
                self.e_a_antiguos_i.pop(0)
            self.e_b_antiguos_i.append(self.e_b)
            if len(self.e_b_antiguos_i) > self.length_i_b:
                self.e_b_antiguos_i.pop(0)
            self.e_a_antiguos_d.append(self.e_a)
            if len(self.e_a_antiguos_d) > 4:
                self.e_a_antiguos_d.pop(0)
            self.e_b_antiguos_d.append(self.e_b)
            if len(self.e_b_antiguos_d) > 4:
                self.e_b_antiguos_d.pop(0)
            self.e_b_anterior = self.e_b
            self.e_a_anterior = self.e_a
            if abs(self.u_a) > 200:
                self.u_a = int(200 * np.sign(self.u_a))
            if abs(self.u_b) > self.max_u:
                self.u_b = int(self.max_u * np.sign(self.u_b))

            if self.prueba_13_activada:
                if self.e_abs < 5:
                    self.contador_listo += 1
                    self.u_a = 0
                    self.u_b = 0
                else:
                    self.contador_listo = 0
                if self.contador_listo == 3:
                    self.prueba_13_listo = True
                    self.u_a = 0
                    self.u_b = 0

                if self.inicio_prueba_13:
                    self.start_time_grafs = time()
                    self.inicio_prueba_13 = False

        else:
            self.reset_values()
            if not self.laser_fuera:
                self.laser_fuera = True

    def reset_values(self):
        self.x = None
        self.y = None
        self.e_a = None
        self.e_b = None
        self.e_abs = None
        self.p_a = None
        self.p_b = None
        self.d_a = None
        self.d_b = None
        self.i_a = None
        self.i_b = None
        self.u_a = None
        self.u_b = None
        self.e_b_antiguos_d = list()
        self.e_a_antiguos_d = list()
        self.e_b_antiguos_i = list()
        self.e_a_antiguos_i = list()

    def prueba_13(self):
        try:
            dir_x = self.resolution[0] / 2 - self.x
            dir_y = self.resolution[1] / 2 - self.y
            abs_dir = np.sqrt(dir_x ** 2 + dir_y ** 2)
            self.ref = [int(self.x + dir_x * 104 / abs_dir), int(self.y + dir_y * 104 / abs_dir)]
            print(dir_x, dir_y, self.x, self.y, abs_dir, self.ref)
            value = ['new_ref', {'ref': self.ref}]
            self.send_server(value)
            self.reset_values()
            self.contador_listo = 0
            self.inicio_prueba_13 = True
            self.prueba_13_activada = True
            self.prueba_13_listo = False
        except:
            self.prueba_13_listo = True

    def detener_prueba(self):
        self.prueba_13_listo = True


if __name__ == '__main__':
    Controlador("hola")
