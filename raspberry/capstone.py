from time import sleep

from threading import Thread
from multiprocessing import Process, Pipe, Lock
from multiprocessing.connection import Connection
from controlador import Controlador
from server import Server
from perturbador import Perturbador
from motores import Motores


class Capstone:
    """This class controls the system"""

    def __init__(self):
        controlador_pipe, self.controlador_pipe = Pipe()
        server_pipe, self.server_pipe = Pipe()
        perturbador_pipe, self.perturbador_pipe = Pipe()
        motores_pipe, self.motores_pipe = Pipe()
        from_controlador_pipe, to_motores_pipe = Pipe()
        self.lock_send = Lock()
        self.generar_diccionario_acciones()
        Thread(target=self.handle, daemon=False, name="handler controlador",
               args=(self.controlador_pipe, self.action_dict,)).start()
        Thread(target=self.handle, daemon=False, name="handler server",
               args=(self.server_pipe, self.action_dict,)).start()
        Thread(target=self.handle, daemon=False, name="handler perturbador",
               args=(self.perturbador_pipe, self.action_dict,)).start()
        Thread(target=self.handle, daemon=True, name='handler motores',
               args=(self.motores_pipe, self.action_dict,)).start()

        Process(target=self.controlador_process, daemon=False,
                args=(controlador_pipe, self.lock_send, from_controlador_pipe),
                name="proceso controlador").start()
        sleep(0.1)
        Process(target=self.server_process, daemon=False,
                args=(server_pipe, self.lock_send),
                name="proceso server").start()
        sleep(0.1)
        Process(target=self.perturbador_process, daemon=False,
                args=(perturbador_pipe, self.lock_send),
                name="proceso perturbador").start()
        sleep(0.1)
        Process(target=self.motores_process, daemon=True,
                args=(motores_pipe, self.lock_send, to_motores_pipe),
                name="proceso motores").start()

    def generar_diccionario_acciones(self):
        self.action_dict = {
            "send_to_server": self.send_to_server,
            'send_to_perturbador': self.send_to_perturbador,
            'send_to_controlador': self.send_to_controlador,
            'send_to_motores': self.send_to_motores
        }

    def send_to_controlador(self, value):
        self.controlador_pipe.send(value)

    def send_to_server(self, value):
        self.server_pipe.send(value)

    def send_to_perturbador(self, value):
        self.perturbador_pipe.send(value)

    def send_to_motores(self, value):
        self.motores_pipe.send(value)

    # Cosas Evidentes
    def handle(self, pipe: Connection, action_dict: dict):
        while True:
            recibido = pipe.recv()
            if isinstance(recibido, str):
                print(f"recibido: {recibido}")

            elif isinstance(recibido, list):
                if recibido[1] is not None:
                    action_dict[recibido[0]](**recibido[1])

                else:
                    action_dict[recibido[0]]()

    def controlador_process(self, controlador_pipe: Connection, lock, pipe_motores):
        self.controlador = Controlador(controlador_pipe, lock, pipe_motores)

    def server_process(self, server_pipe: Connection, lock):
        self.server = Server(server_pipe, lock)

    def perturbador_process(self, perturbador_pipe: Connection, lock):
        self.perturbador = Perturbador(perturbador_pipe, lock)

    def motores_process(self, motores_pipe: Connection, lock, pipe_controlador):
        self.motores = Motores(motores_pipe, lock, pipe_controlador)

    def dummy(self):
        print("dummy function called")


if __name__ == '__main__':
    Capstone()
    while True:
        pass
