"""This is the main program"""

import sys

from PyQt5.QtWidgets import QApplication

from frontend.inicio import Inicio
from frontend.interfaz import Interfaz
from frontend.serial import Serial

from backend.client import Client
from backend.logica import Logica

# Para poder debbuguear
def hook(type_error, traceback):
    print(type_error)
    print(traceback)


if __name__ == '__main__':
    sys.__excepthook__ = hook
    app = QApplication(sys.argv)

    logica = Logica()
    inicio = Inicio()
    client = Client()
    interfaz = Interfaz()
    serial_perturbador = Serial()

    # De inicio a cliente
    inicio.senal_conectar_cliente.connect(client.connect_to_server)

    # De cliente a inicio
    client.senal_intentos.connect(inicio.actualizar_intentos)
    client.senal_conexion_exitosa.connect(inicio.succes_connection)
    client.senal_conexion_fallida.connect(inicio.error_connection)
    client.senal_perdida_conexion.connect(inicio.perdida_conexion)

    # De inicio a logica
    inicio.senal_continuar.connect(logica.iniciar_interfaz)

    # De logica a inicio
    logica.senal_listo_para_continuar.connect(inicio.continuar_listo)

    # De cliente a logica
    client.senal_conexion_exitosa.connect(logica.succes_connection)
    client.senal_perdida_conexion.connect(logica.perdida_conexion)
    client.senal_recibido_list.connect(logica.handler)
    client.senal_recibido_str.connect(logica.handler)

    # De logica a cliente
    logica.senal_send_list.connect(client.send)
    logica.senal_send_str.connect(client.send)

    # De logica a serial
    logica.senal_mensaje_perturbador_recibido.connect(serial_perturbador.recieve)

    # De serial a logica
    serial_perturbador.senal_send.connect(logica.enviar_perturbador)
    serial_perturbador.senal_reset.connect(logica.reset_perturbador)

    # de interfaz a serial
    interfaz.senal_abrir_serial.connect(serial_perturbador.show)

    # De logica a interfaz
    logica.senal_inicializar_interfaz.connect(interfaz.inicializar)
    logica.senal_actualizar_control.connect(interfaz.actualizar_control)
    logica.senal_actualizar_archivos.connect(interfaz.actualizar_archivos)
    logica.senal_actualizar_text_controlador.connect(interfaz.actualizar_text_controlador)
    logica.senal_pedir_grafs_keys.connect(interfaz.enviar_grafs_keys)
    logica.senal_cambio_estado.connect(interfaz.cambio_estado)
    logica.senal_graficar.connect(interfaz.graficar)

    # De interfaz a logica
    interfaz.senal_prueba_procesamiento.connect(logica.pedir_prueba_procesamiento)
    interfaz.senal_actualizar_controlador.connect(logica.actualizar_controlador)
    interfaz.senal_graficos_keys.connect(logica.obtener_graficos_keys)
    interfaz.senal_calibrar.connect(logica.enviar_calibrar)
    interfaz.senal_centrar.connect(logica.enviar_centrar)
    interfaz.senal_random.connect(logica.enviar_random)
    interfaz.senal_set_actualizacion_datos.connect(logica.set_actualizacion_datos)
    interfaz.senal_set_controlar_activado.connect(logica.set_controlar_activado)
    interfaz.senal_set_sleep.connect(logica.enviar_sleep)
    interfaz.senal_cambio_referencia.connect(logica.cambio_referencia)

    # inicio de la aplicacion
    sys.exit(app.exec_())
