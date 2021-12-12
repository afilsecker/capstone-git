from PyQt5.QtWidgets import QApplication
import sys

from frontend.serial import Serial

if __name__ == '__main__':
    app = QApplication(sys.argv)
    interfaz = Serial()
    interfaz.show()
    sys.exit(app.exec_())
