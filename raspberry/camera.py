import cv2
import json
from threading import Thread, Event, Lock
from collections import deque
import numpy as np


class Camera:
    def __init__(self, listo_event: Event):
        self.listo_event = listo_event
        with open('parametros.json', 'r') as archivo:
            diccionario = json.load(archivo)
            self.__dict__.update(diccionario["camera"])

        self.stream = cv2.VideoCapture(self.src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.stream.set(cv2.CAP_PROP_FPS, self.fps)
        self.stream.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness)
        self.stream.set(cv2.CAP_PROP_SATURATION, self.saturation)
        self.stopped = False
        self.imagen_capturada = Event()
        self.capturar = Event()
        self.punto_encontrado = Event()
        self.frames = deque()
        self.frames_lock = Lock()
        self.capturar.set()
        self.start()

    def start(self):
        Thread(target=self.update, name='update_camera').start()
        Thread(target=self.find_laser_thread, name='find_laser').start()

    def update(self):
        while True:
            if self.stopped:
                return

            self.capturar.wait()
            self.capturar.clear()
            _, frame = self.stream.read()
            with self.frames_lock:
                self.frames.append(frame)
            self.imagen_capturada.set()

    def find_laser_thread(self):
        while True:
            if self.stopped:
                return

            self.imagen_capturada.wait()
            self.imagen_capturada.clear()

            if len(self.frames) == 1:
                self.capturar.set()

            with self.frames_lock:
                frame = self.frames.popleft()
                self.find_laser(frame)
                if self.red_point[0] is not None and self.red_point[1] is not None:
                    self.punto_encontrado.set()

            self.listo_event.set()
            self.capturar.set()

    def find_laser(self, frame):
        red_chanell = frame[:, :, 2]
        red_points = (red_chanell > self.umbral).nonzero()
        if red_points[0].any() and red_points[1].any():
            self.red_point = [float, float]
            self.red_point[0] = np.mean(red_points[0])
            self.red_point[1] = np.mean(red_points[1])
            return self.red_point, red_points

        else:
            self.red_point = [None, None]
            return self.red_point, None

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True

    def prueba_procesamiento(self):
        with self.frames_lock:
            _, frame = self.stream.read()
            punto_encontrado, puntos_encontrados = self.find_laser(frame)
            return frame, punto_encontrado, puntos_encontrados


if __name__ == '__main__':
    Camera("hola")
