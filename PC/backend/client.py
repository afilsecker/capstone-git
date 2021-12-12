from os import system
import os
import socket
from threading import Thread
from PyQt5.QtCore import QObject, pyqtSignal
import pickle
import json


class Client(QObject):

    # Para el inicio
    senal_intentos = pyqtSignal(int, int)
    senal_conexion_exitosa = pyqtSignal()
    senal_conexion_fallida = pyqtSignal()

    senal_perdida_conexion = pyqtSignal()

    senal_recibido_str = pyqtSignal(str)
    senal_recibido_list = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.obtener_parametros()

    def obtener_parametros(self):
        with open('parametros.json', 'r') as f:
            diccionario = json.load(f)
            self.__dict__.update(diccionario['backend']['cliente'])

    def connect_to_server(self):
        Thread(target=self.connect_to_server_thread, daemon=True).start()

    def connect_to_server_thread(self):
        conectado = False
        intento = 0
        segunda = True
        
        while not conectado:
            try:
                self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_client.connect((self.host, self.port))
                Thread(target=self.listen_thread, daemon=True).start()
                conectado = True
                self.senal_conexion_exitosa.emit()

            except ConnectionError:
                if segunda:
                    self.port += 1
                    segunda = False
                else:
                    segunda = True
                    intento += 1
                    self.port -= 1
                    if intento <= self.intentos_conexion:
                        self.senal_intentos.emit(intento, self.intentos_conexion)

                    if intento == self.intentos_conexion:
                        self.senal_conexion_fallida.emit()
                        break
                self.socket_client.close()

    def send(self, value):
        msg = pickle.dumps(value)
        largo = len(msg)
        largo_bytes = pickle.dumps(largo)
        largo_largo = len(largo_bytes)
        largo_largo_bytes = largo_largo.to_bytes(self.largo_largo_msg, byteorder='big')
        self.socket_client.sendall(largo_largo_bytes + largo_bytes + msg)

    def listen_thread(self):
        try:
            while True:
                largo_largo_bytes = self.socket_client.recv(self.largo_largo_msg)
                if len(largo_largo_bytes) != self.largo_largo_msg:
                    faltante = self.socket_client.recv(self.largo_largo_msg - len(largo_largo_bytes))
                    largo_largo_bytes += faltante

                largo_largo = int.from_bytes(largo_largo_bytes, byteorder='big')
                largo_bytes = self.socket_client.recv(largo_largo)
                if len(largo_bytes) != largo_largo:
                    faltante = self.socket_client.recv(largo_largo - len(largo_bytes))
                    largo_bytes = largo_bytes + faltante
                    
                largo = pickle.loads(largo_bytes)
                response = bytearray()
                while len(response) < largo:
                    faltante = largo - len(response)
                    if faltante > 4096:
                        packet = self.socket_client.recv(4096)

                    else:
                        packet = self.socket_client.recv(faltante)

                    response.extend(packet)
                    if len(packet) == 0:
                        break

                if len(response) > 0:
                    recibido = pickle.loads(response)
                    self.handler(recibido)
                    response = bytearray()

        except ConnectionResetError or ConnectionAbortedError:
            self.senal_perdida_conexion.emit()
            self.socket_client.close()
            self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.obtener_parametros()

        except ValueError:
            print("un paquete esta malo")

        except EOFError as error:
            print(error)
            self.senal_perdida_conexion.emit()
            self.socket_client.close()
            self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def handler(self, recibido):
        if isinstance(recibido, str):
            self.senal_recibido_str.emit(recibido)

        elif isinstance(recibido, list):
            self.senal_recibido_list.emit(recibido)

        else:
            raise TypeError(recibido)


if __name__ == "__main__":
    Client()
