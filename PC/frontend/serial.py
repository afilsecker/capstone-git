from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from frontend.pyqtdesigner.serial_ui import Ui_serial

class Serial(QWidget):

    senal_send = pyqtSignal(str)
    senal_reset = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ui = Ui_serial()
        self.ui.setupUi(self)
        self.ui.boton_send.clicked.connect(self.send)
        self.ui.input.returnPressed.connect(self.send)
        self.ui.boton_reset.clicked.connect(self.reset)

    def send(self):
        input = self.ui.input.text()
        if len(input) > 0:
            self.ui.input.clear()
            texto_enviado = "\nEnviado: "
            self.ui.texto.append(texto_enviado + input + '\n')
            self.senal_send.emit(input)

    def recieve(self, recieved: str):
        self.ui.texto.append(recieved)

    def reset(self):
        self.senal_reset.emit()
        self.ui.texto.clear()
        self.ui.input.clear()
