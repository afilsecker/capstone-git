from collections import deque
import socket
from threading import Thread
import json
import pickle
from multiprocessing.connection import Connection


class Server:
    def __init__(self, server_pipe: Connection, lock):
        print("Inicializando servidor...")
        self.buffer = deque()
        self.lock = lock
        self.server_pipe = server_pipe
        self.generar_diccionario_acciones()
        Thread(target=self.handle_capstone, daemon=True, name='handle_capstone').start()
        with open('parametros.json', 'r') as f:
            diccionario = json.load(f)
            self.__dict__.update(diccionario['server'])

        self.bind_and_listen()

    def generar_diccionario_acciones(self):
        self.action_dict = {
            "send": self.append_buffer,
            "close": self.close
        }

    def append_buffer(self, value):
        self.buffer.append(value)

    def close(self):
        print("hola")
        self.socket_server.close()

    # El handler del capstone
    def handle_capstone(self):
        while True:
            recibido = self.server_pipe.recv()

            if isinstance(recibido, str):
                print(f"recibido: {recibido}")

            elif isinstance(recibido, list):
                if recibido[1] is not None:
                    self.action_dict[recibido[0]](**recibido[1])

                else:
                    self.action_dict[recibido[0]]()

    # Cosas de Server
    def bind_and_listen(self):
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_connected = False
        self.online = False

        while not self.online:
            try:
                self.socket_server.bind((self.host, self.port))
                self.online = True
            except OSError as error:
                print(error)
                self.port += 1

        self.socket_server.listen()
        print(f"Servidor escuchando en {self.host}:{self.port}...")
        Thread(target=self.accept_connections_thread, daemon=False,
               name='accept_connections').start()

    def accept_connections_thread(self):
        while True:
            client_socket, _ = self.socket_server.accept()
            print("alguien se metio")
            if not self.client_connected:
                self.client_socket = client_socket
                Thread(target=self.listen_client_thread, daemon=True, args=(client_socket,),
                       name="listen_client").start()
                Thread(target=self.flush_buffer, daemon=True, name='flush_buffer').start()
                self.client_connected = True

            else:
                self.send("el servidor esta lleno", client_socket)
                print("pero no lo dejamos entrar")

    def send(self, value, sock: socket.socket):
        msg = pickle.dumps(value)
        largo = len(msg)
        largo_bytes = pickle.dumps(largo)
        largo_largo = len(largo_bytes)
        largo_largo_bytes = largo_largo.to_bytes(self.largo_largo_msg, byteorder='big')
        try:
            sock.sendall(largo_largo_bytes + largo_bytes + msg)
        except BrokenPipeError as error:
            print(error)
            pass
        except ConnectionResetError:
            print("se salio el cliente")
            self.client_connected = False

    def send_client(self, value):
        self.send(value, self.client_socket)

    def flush_buffer(self):
        while True:
            if self.client_connected:
                if len(self.buffer) > 0:
                    envio = self.buffer.popleft()
                    self.send_client(envio)

    def listen_client_thread(self, socket):
        try:
            while True:
                largo_largo_bytes = socket.recv(self.largo_largo_msg)
                if len(largo_largo_bytes) == 0:
                    raise ConnectionResetError

                largo_largo = int.from_bytes(largo_largo_bytes, byteorder='big')
                largo_bytes = socket.recv(largo_largo)
                largo = pickle.loads(largo_bytes)
                response = bytearray()
                while len(response) < largo:
                    faltante = largo - len(response)
                    if faltante > 4096:
                        packet = socket.recv(4096)

                    else:
                        packet = socket.recv(faltante)

                    response.extend(packet)

                if len(response) > 0:
                    recibido = pickle.loads(response)
                    self.send_capstone(recibido)

        except ConnectionResetError:
            print("se salio el cliente")
            self.client_connected = False
            envio = ['send_to_motores', {'value': ['send_sleep', None]}]
            self.send_capstone(envio)

    def send_capstone(self, envio):
        with self.lock:
            self.server_pipe.send(envio)


if __name__ == "__main__":
    Server()
