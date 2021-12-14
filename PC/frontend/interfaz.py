from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTime, QTimer, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import random
import numpy as np

from frontend.pyqtdesigner.interfaz_ui import Ui_interfaz


class Interfaz(QMainWindow):

    # Señales para serial
    senal_abrir_serial = pyqtSignal()

    senal_prueba_procesamiento = pyqtSignal()
    senal_actualizar_controlador = pyqtSignal(dict)
    senal_graficos_keys = pyqtSignal(list)
    senal_calibrar = pyqtSignal()
    senal_centrar = pyqtSignal()
    senal_random = pyqtSignal()
    senal_cambio_referencia = pyqtSignal(list)
    
    senal_set_actualizacion_datos = pyqtSignal(bool)
    senal_set_controlar_activado = pyqtSignal(bool)
    senal_set_sleep = pyqtSignal(bool)

    def __init__(self):
        super(Interfaz, self).__init__()
        self.ui = Ui_interfaz()
        self.ui.setupUi(self)
        self.fps_list = list()
        self.keys_parametros = list()
        self.parametros = dict()
        for key in self.ui.__dict__:
            if key[:5] == 'edit_':
                if key[5:] != 'save':
                    self.keys_parametros.append(key[5:])

        self.begin_grafs = False

        self.set_text_edit()
        self.set_perturbador()
        self.set_botones()
        self.set_checkboxes()
        self.set_spinboxes()
        self.set_grafs()

    # set's de init
    def set_text_edit(self):
        for edit in [self.ui.__dict__[f'edit_{key}'] for key in self.keys_parametros]:
            edit.returnPressed.connect(self.boton_actualizar_controlador)

    def set_perturbador(self):
        self.ui.bttn_serial.clicked.connect(self.senal_abrir_serial.emit)

    def set_botones(self):
        self.ui.boton_prueba_procesamiento.clicked.connect(self.senal_prueba_procesamiento.emit)
        self.ui.bttn_actualizar_controlador.clicked.connect(self.boton_actualizar_controlador)
        self.ui.boton_calibrar.clicked.connect(self.senal_calibrar.emit)
        self.ui.boton_centrar.clicked.connect(self.senal_centrar.emit)
        self.ui.boton_random.clicked.connect(self.senal_random.emit)
        self.lista_botones_acciones = ['calibrar', 'centrar', 'prueba_13', 'prueba_6Hz',
                                       'prueba_x', 'prueba_y', 'random', 'prueba_procesamiento']

    def set_checkboxes(self):
        self.ui.check_controlar.stateChanged.connect(self.check_controlar_apretado)
        self.ui.check_sleep.stateChanged.connect(self.check_sleep_apretado)
        self.lista_check_boxes = ['datos', 'controlar', 'sleep']

    def set_spinboxes(self):
        self.ui.spin_ref_x.valueChanged.connect(self.referencia_cambiada)
        self.ui.spin_ref_y.valueChanged.connect(self.referencia_cambiada)

    def set_grafs(self):
        grafs_list = [
            [self.ui.verticalLayout_e_abs],
            [self.ui.verticalLayout_e_a],
            [self.ui.verticalLayout_e_b],
            [self.ui.verticalLayout_u_a],
            [self.ui.verticalLayout_u_b],
            [self.ui.verticalLayout_p_a],
            [self.ui.verticalLayout_p_b],
            [self.ui.verticalLayout_d_a],
            [self.ui.verticalLayout_d_b],
            [self.ui.verticalLayout_i_a],
            [self.ui.verticalLayout_i_b]
        ]
        self.grafs = dict()
        self.vals = dict()
        self.grafs_keys = list()
        for graf in grafs_list:
            self.grafs[graf[0].objectName()[15:]] = Grafico()
            self.grafs_keys.append(graf[0].objectName()[15:])
            graf[0].addWidget(self.grafs[graf[0].objectName()[15:]])

    # Acciones producidas en frontend
    def boton_actualizar_controlador(self):
        distinto = False
        for key in self.keys_parametros:
            edit = self.ui.__dict__[f'edit_{key}']
            if edit.text() != self.parametros[key]:
                distinto = True

        if distinto:
            for key in self.keys_parametros:
                self.parametros[key] = self.ui.__dict__[f'edit_{key}'].text()

            self.senal_actualizar_controlador.emit(self.parametros)

    def check_controlar_apretado(self):
        val = self.ui.check_controlar.checkState()
        self.senal_set_controlar_activado.emit(val > 0)

    def check_sleep_apretado(self):
        val = self.ui.check_sleep.checkState()
        self.senal_set_sleep.emit(val > 0)

    def referencia_cambiada(self):
        ref_x = self.ui.spin_ref_x.value()
        ref_y = self.ui.spin_ref_y.value()
        self.senal_cambio_referencia.emit([ref_x, ref_y])

    # Acciones por backend triviales
    def inicializar(self, datos: dict):
        texto_resolucion = f'Resolucion Camara: {datos["resolucion"][0]}X{datos["resolucion"][1]}'
        self.ui.label_res.setText(texto_resolucion)
        self.ui.spin_ref_x.setMaximum(datos['resolucion'][0])
        self.ui.spin_ref_y.setMaximum(datos['resolucion'][1])
        self.ui.spin_ref_x.setValue(datos['resolucion'][0] / 2)
        self.ui.spin_ref_y.setValue(datos['resolucion'][1] / 2)
        self.show()

    def enviar_grafs_keys(self):
        self.senal_graficos_keys.emit(self.grafs_keys)

    # Acciones por backend para los estados
    def cambio_estado(self, estado):
        if estado == 'calibracion_requerida':
            texto = 'Calibracion Requerida'
            botones_activados = ['prueba_procesamiento', 'calibrar']
            checks_activados = []
            self.ui.check_sleep.setChecked(False)
            self.ui.check_controlar.setChecked(False)
        elif estado == 'calibrando':
            texto = 'Calibrando'
            botones_activados = ['prueba_procesamiento']
            checks_activados = []
            self.ui.check_sleep.setChecked(False)
        elif estado == 'base':
            texto = 'Listo'
            botones_activados = ['prueba_procesamiento','calibrar', 'centrar', 'random']
            checks_activados = self.lista_check_boxes
        elif estado == 'controlando':
            texto = 'Controlando'
            botones_activados = ['prueba_6Hz', 'prueba_13', 'prueba_x', 'prueba_y']
            checks_activados = self.lista_check_boxes
        elif estado == 'sleep':
            texto = 'Sleep'
            botones_activados = ['prueba_procesamiento', 'calibrar']
            checks_activados = ['datos']
            self.ui.check_controlar.setChecked(False)
        elif estado == 'esperando_datos':
            texto = 'esperando graficos...'
            botones_activados = []
            checks_activados = []

        else:
            raise ValueError

        self.ui.label_estado.setText(texto)
        self.set_botones_activados(botones_activados, checks_activados)

    def set_botones_activados(self, botones_activados, checks_activados):
        for boton in self.lista_botones_acciones:
            key = f'boton_{boton}'
            if key in self.ui.__dict__.keys():
                self.ui.__dict__[key].setEnabled(boton in botones_activados)

        for check in self.lista_check_boxes:
            key = f'check_{check}'
            if key in self.ui.__dict__.keys():
                self.ui.__dict__[key].setEnabled(check in checks_activados)

    # Acciones por backend para la gui del controlador
    def actualizar_archivos(self, files):
        self.ui.combo_box_loads.clear()
        for file in files:
            self.ui.combo_box_loads.addItem(file[:-4])

    # Acciones por backend para los graficos y weas
    def graficar(self, datos: dict):
        for key in datos:
            self.grafs[key].graficar(
                datos[key]['limits'],
                datos[key]['x_data'],
                datos[key]['y_data']
            )

    def actualizar_text_controlador(self, values: dict):
        for key in values.keys():
            if f'edit_{key}' in self.ui.__dict__:
                self.parametros[key] = str(values[key])
                self.ui.__dict__[f'edit_{key}'].setText(str(values[key]))

    def actualizar_control(self, datos: dict):
        for key in datos.keys():
            if f'val_{key}' in self.ui.__dict__:
                if datos[key] is not None:
                    self.ui.__dict__[f'val_{key}'].setText(f'{datos[key]:.2f}')
                else:
                    self.ui.__dict__[f'val_{key}'].setText(' ')


        self.ui.label_fps.setText(f'FPS: {self.contar_fps(datos["fps"]):.2f}')

    def contar_fps(self, fps):
        self.fps_list.append(fps)
        if len(self.fps_list) > 100:
            self.fps_list.pop(0)
        return np.mean(np.array(self.fps_list))


class Grafico(FigureCanvas):
    def __init__(self):
        self.figure = Figure()
        super(Grafico, self).__init__(self.figure)
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)


    def graficar(self, limits, x_data, y_data):
        self.ax.clear()
        self.ax.set_ylim(limits)
        self.ax.plot(x_data, y_data, 'r')
        self.draw()
