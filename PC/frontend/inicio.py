import json

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from frontend.pyqtdesigner.inicio_ui import Ui_inicio


class Inicio(QWidget):

    senal_conectar_cliente = pyqtSignal()
    senal_continuar = pyqtSignal()

    def __init__(self):
        super().__init__()
        with open('parametros.json', 'r') as f:
            diccionario = json.load(f)
            self.port = diccionario['backend']['cliente']['port']
        self.inicio = Ui_inicio()
        self.inicio.setupUi(self)
        self.set_initial_values()
        self.show()

    def set_initial_values(self):
        self.inicio.boton_conectar.setDisabled(False)
        self.inicio.boton_conectar.clicked.connect(self.conectar_cliente)
        self.inicio.boton_salir.clicked.connect(self.close)
        self.inicio.boton_continuar.hide()
        self.inicio.texto_conexion.setText("Presiona para conectar")

    def conectar_cliente(self):
        """Ocurre cuando apretas el boton de conectar"""
        self.inicio.texto_conexion.setText("Intentando conectar")
        self.senal_conectar_cliente.emit()
        self.inicio.boton_conectar.setDisabled(True)

    def actualizar_intentos(self, intento: int, totales: int):
        """Ocurre cuando falla al intentar conectar con el cliente"""
        self.inicio.texto_conexion.setText(f'Intento de conexion {intento}/{totales} fallido')

    def error_connection(self):
        """Ocurre cuando se te acaban los intentos"""
        self.inicio.texto_conexion.setText("No se pudo conectar con el servidor")
        self.inicio.boton_conectar.setDisabled(False)

    def succes_connection(self):
        """Ocurre cuando se logro conectar el cliente"""
        self.inicio.texto_conexion.setText("¡Conectado!\nEsperando Datos")

    def continuar_listo(self):
        """Ocurre despues que nos llegan los datos de la raspberry para iniciar"""
        self.inicio.texto_conexion.setText('¡Listo!')
        self.inicio.boton_continuar.show()
        self.inicio.boton_continuar.clicked.connect(self.continuar)

    def continuar(self):
        """Ocurre cuando se apreta el boton de continuar"""
        self.set_initial_values()
        self.hide()
        self.senal_continuar.emit()

    def perdida_conexion(self):
        """Ocurre cuando se pierde la conexion"""
        self.inicio.texto_conexion.setText("Conexion Perdida")
        self.inicio.boton_conectar.setDisabled(False)
        self.inicio.boton_continuar.hide()

    
