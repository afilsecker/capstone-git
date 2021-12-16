from PyQt5.QtCore import QObject, pyqtSignal
import sys
from matplotlib import pyplot as plt
import cv2
from os import listdir
from os.path import isfile, join
import numpy as np
import random
import time


class Logica(QObject):

    # Senales del para el cliente
    senal_send_str = pyqtSignal(str)
    senal_send_list = pyqtSignal(list)

    # Senales para inicio
    senal_listo_para_continuar = pyqtSignal()

    # Senales para interfaz
    senal_inicializar_interfaz = pyqtSignal(dict)
    senal_actualizar_control = pyqtSignal(dict)
    senal_actualizar_archivos = pyqtSignal(list)
    senal_actualizar_text_controlador = pyqtSignal(dict)
    senal_pedir_grafs_keys = pyqtSignal()
    senal_graficar = pyqtSignal(dict)
    senal_cambio_ref = pyqtSignal(list)
    senal_actualizar_controlador = pyqtSignal(dict)

    senal_cambio_estado = pyqtSignal(str)

    # Senales para el serial del perturbador
    senal_mensaje_perturbador_recibido = pyqtSignal(str)
    senal_enviar_mensaje_perturbador = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.connected = False
        self.en_interfaz = False
        self.aceptando_datos = False
        self.estado = 'calibracion_requerida'
        self.parametros = dict()
        self.limites_graficos = dict()
        self.lista_datos = list()
        self.graficar_activado = False
        self.generar_diccionario_acciones()

    # Para acciones que vienen del cliente
    def succes_connection(self):
        self.connected = True
        value = ['initial_data_request', None]
        envio = ['send_to_controlador', {'value': value}]
        self.senal_send_list.emit(envio)

    # Para acciones que vienen del servidor
    def handler(self, recibido):
        if isinstance(recibido, str):
            print(f"recibido: {recibido}")

        elif isinstance(recibido, list):
            if recibido[0] in self.acciones.keys():
                if recibido[1] is not None:
                    self.acciones[recibido[0]](**recibido[1])

                else:
                    self.acciones[recibido[0]]()

            else:
                print(recibido[0], "not part of diccionario acciones")

    def generar_diccionario_acciones(self):
        self.acciones = {
            'initial_data': self.acquire_initial_data,
            'perturbador': self.recibir_perturbador,
            'prueba_procesamiento_response': self.recibir_prueba_procesamiento,
            'control': self.recibir_control,
            'datos_done': self.graficar,
            'calibrate_complete': self.calibrate_complete,
            'hard_reseted': self.hard_reseted,
            'prueba_13_listo': self.prueba_13_listo,
            'new_ref': self.new_ref
        }

    def acquire_initial_data(self, **datos):
        self.resolution = datos['resolution']
        self.parametros = datos['parametros']
        self.senal_listo_para_continuar.emit()
        value = self.parametros.copy()
        value["name"] = 'inicial'
        self.senal_actualizar_text_controlador.emit(value)
        self.senal_pedir_grafs_keys.emit()
        self.escribir_parametros('inicial', self.parametros)
        self.obtener_paths_parametros()

    def recibir_perturbador(self, recibido: str):
        self.senal_mensaje_perturbador_recibido.emit(recibido)

    def perdida_conexion(self):
        self.connected = False
        print("Se perdio la conexion")
        if self.en_interfaz:
            sys.exit()

    def recibir_prueba_procesamiento(self, image, puntos, punto_rojo):
        if image is not None:
            plt.figure()
            plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            if puntos is not None:
                plt.scatter(puntos[1], puntos[0], c='blue')
            if punto_rojo[0] is not None:
                plt.scatter(punto_rojo[1], punto_rojo[0], c='red')
            plt.show()

    def recibir_control(self, datos):
        self.lista_datos.append(datos)

    def calibrate_complete(self):
        self.estado = 'base'
        self.senal_cambio_estado.emit(self.estado)

    def hard_reseted(self):
        self.estado = 'calibracion_requerida'
        self.senal_cambio_estado.emit(self.estado)

    def new_ref(self, ref):
        self.ref = ref
        self.senal_cambio_ref.emit(ref)

    # Acciones hacia perturbador
    def enviar_perturbador(self, msg):
        value = ['send', {'msg': msg}]
        envio = ['send_to_perturbador', {'value': value}]
        self.senal_send_list.emit(envio)

    def reset_perturbador(self):
        value = ['reset', None]
        send = ['send_to_perturbador', {'value': value}]
        self.senal_send_list.emit(send)

    # Acciones hacia controlador
    def pedir_prueba_procesamiento(self):
        value = ['prueba_procesamiento', None]
        envio = ['send_to_controlador', {'value': value}]
        self.senal_send_list.emit(envio)

    def set_actualizacion_datos(self, state):
        value = ['set_actualizacion_datos', {'state': state}]
        envio = ['send_to_controlador', {'value': value}]
        self.senal_send_list.emit(envio)
        self.aceptando_datos = state

    def set_controlar_activado(self, state):
        value = ['set_controlar_activado', {'state': state}]
        envio = ['send_to_controlador', {'value': value}]
        self.senal_send_list.emit(envio)
        if state:
            self.estado = 'controlando'
        else:
            self.estado = 'esperando_datos'
        self.senal_cambio_estado.emit(self.estado)
        time.sleep(0.05)

        if not state:
            value = ['set_vels', {'vel_A': 0, 'vel_B': 0}]
            envio = ['send_to_motores', {'value': value}]
            self.senal_send_list.emit(envio)
        
    def actualizar_controlador(self, parametros: dict):
        try:
            for key in parametros:
                self.parametros[key] = float(parametros[key])
            value = ['nuevos_parametros', {'parametros': self.parametros}]
            envio = ['send_to_controlador', {'value': value}]
            self.senal_send_list.emit(envio)

        except  ValueError:
            pass

    def enviar_prueba_13(self):
        value = ['prueba_13', None]
        envio = ['send_to_controlador', {'value': value}]
        self.senal_send_list.emit(envio)

    def detener_prueba(self):
        value = ['detener', None]
        envio = ['send_to_controlador', {'value': value}]
        self.senal_send_list.emit(envio)

    # Acciones hacia motores
    def enviar_calibrar(self):
        self.estado = 'calibrando'
        self.senal_cambio_estado.emit(self.estado)
        value = ['send_calibrate', None]
        envio = ['send_to_motores', {'value': value}]
        self.senal_send_list.emit(envio)

    def enviar_centrar(self):
        value = ['send_center', None]
        envio = ['send_to_motores', {'value': value}]
        self.senal_send_list.emit(envio)

    def enviar_random(self):
        vel_A = random.randint(-255, 255)
        vel_B = random.randint(-255, 255)
        value = ['set_vels', {'vel_A': vel_A, 'vel_B': vel_B}]
        envio = ['send_to_motores', {'value': value}]
        self.senal_send_list.emit(envio)

    def enviar_sleep(self, state):
        if state:
            self.estado = 'sleep'
        else:
            self.estado = 'calibracion_requerida'
        self.senal_cambio_estado.emit(self.estado)
        value = ['send_sleep', None]
        envio = ['send_to_motores', {'value': value}]
        self.senal_send_list.emit(envio)

    def cambio_referencia(self, referencia):
        self.ref = referencia
        value = ['cambio_referencia', {'ref': referencia}]
        envio = ['send_to_controlador', {'value': value}]
        self.senal_send_list.emit(envio)

    def prueba_13(self):
        self.estado = 'prueba_13'
        self.senal_cambio_estado.emit(self.estado)
        parametros = dict()
        with open('backend/parametros/parametros_13.txt', 'r') as f:
            for line in f.readlines():
                splited = line.split('=')
                parametros[splited[0]] = float(splited[1][:-1])
        self.actualizar_controlador(parametros)
        self.senal_actualizar_controlador.emit(parametros)
        self.enviar_prueba_13()

    def prueba_6(self, datos: dict):
        self.enviar_centrar()
        for key in datos.keys():
            if len(datos[key]) == 0:
                valor = 0
            else:
                valor = datos[key]
            msg = f'{key}{valor}'
            self.enviar_perturbador(msg)
        parametros = dict()
        with open('backend/parametros/parametros_6.txt', 'r') as f:
            for line in f.readlines():
                splited = line.split('=')
                parametros[splited[0]] = float(splited[1][:-1])
        self.actualizar_controlador(parametros)
        self.senal_actualizar_controlador.emit(parametros)

    def prueba_13_listo(self):
        self.estado = 'base'
        self.senal_cambio_estado.emit(self.estado)

    # Acciones de interfaz
    def obtener_graficos_keys(self, keys: list):
        self.graficos_keys = keys

    def set_graficar(self, state):
        self.graficar_activado = state
        value = ['set_graficar', {'state': state}]
        envio = ['send_to_controlador', {'value': value}]
        self.senal_send_list.emit(envio)

    # Acciones hacia interfaz
    def iniciar_interfaz(self):
        datos = {'resolucion': self.resolution}
        self.senal_inicializar_interfaz.emit(datos)
        self.estado = 'calibracion_requerida'
        self.senal_cambio_estado.emit(self.estado)
        self.en_interfaz = True

    def escribir_parametros(self, nombre: str, parametros: dict):
        with open(f'backend/parametros/{nombre}.txt', 'w') as f:
            for parametro in parametros.keys():
                f.write(f'{parametro}={parametros[parametro]}\n')

    def obtener_paths_parametros(self):
        path = 'backend/parametros/'
        files = [f for f in listdir(path) if isfile(join(path, f))]
        self.senal_actualizar_archivos.emit(files)

    def graficar(self):
        self.estado = 'base'
        self.senal_cambio_estado.emit(self.estado)
        corte = 1
        if self.graficar_activado:
            diccionario_datos = dict()
            for dato in self.lista_datos:
                for key in dato.keys():
                    if key not in diccionario_datos.keys():
                        diccionario_datos[key] = list()

                    diccionario_datos[key].append(dato[key])

            for key in diccionario_datos.keys():
                try:
                    if key == 'e_abs':
                        for i in range(len(diccionario_datos[key])):
                            e_abs = diccionario_datos[key][i]
                            if abs(e_abs - diccionario_datos[key][0]) > 2:
                                corte = i
                                break
                        if not corte:
                            corte = 1
                except TypeError:
                    corte = 1

            for i in range(len(diccionario_datos['time'])):
                diccionario_datos['time'][i] -= diccionario_datos['time'][corte - 1]

            for key in diccionario_datos.keys():
                diccionario_datos[key] = np.array(diccionario_datos[key][corte - 1:])

            datos_graficos = dict()

            for key in self.graficos_keys:
                datos_graficos[key] = dict()
                try:
                    self.limites_graficos[key] = [np.min(diccionario_datos[key]), np.max(diccionario_datos[key])]
                except TypeError:
                    self.limites_graficos[key] = [-200, 200]

                if self.limites_graficos[key][0] == self.limites_graficos[key][1]:
                    self.limites_graficos[key][0] -= 1
                    self.limites_graficos[key][1] += 1
                datos_graficos[key]['limits'] = self.limites_graficos[key]
                datos_graficos[key]['y_data'] = diccionario_datos[key]
                datos_graficos[key]['x_data'] = diccionario_datos['time']

            self.senal_graficar.emit(datos_graficos)
            self.lista_datos = list()
