#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import time
import logging
import random
import math
import threading
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import RPi.GPIO as GPIO
import spidev as SPI
from .LCD_1inch28 import LCD_1inch28


class EqualizerBar:
    def __init__(self, bars, color_scheme_index=0):
        self.bars = bars
        self._values = [0] * bars

        # Определяем цветовые схемы
        self.color_schemes = self._get_color_schemes()
        self.color_scheme_index = color_scheme_index
        self.colors = self.color_schemes[self.color_scheme_index]

        # Параметры для движения круга по дуге
        self.circle_radius = 15  # Радиус круга
        self.arc_radius = 120  # Радиус дуги, по которой движется круг
        self.arc_center_x = 120  # Центр дуги по X (центр экрана)
        self.arc_center_y = 150  # Центр дуги по Y (ниже центра экрана)
        self.angle = 310  # Начальный угол в градусах (левая сторона)
        self.angle_speed = 1  # Скорость изменения угла в градусах за кадр
        self.moving_right = True  # Направление движения

    def _get_color_schemes(self):
        """Возвращает список различных цветовых схем"""
        return [
            # 0: Исходная схема (фиолетово-оранжевая)
            ["#2d004b", "#542788", "#8073ac", "#b2abd2", "#d8daeb", "#f7f7f7", "#fee0b6",
             "#fdb863", "#e08214", "#b35806", "#7f3b08"],

            # 1: Сине-зеленая (океан)
            ["#000C40", "#0A2472", "#0E6BA8", "#A6E1FA", "#B9F3FC", "#F6F6F6", "#C1F7DC",
             "#79F2C0", "#2EC4B6", "#198C8C", "#0A5C5C"],

            # 2: Красно-желтая (огонь)
            ["#2C0703", "#621708", "#941B0C", "#BC3908", "#F6AA1C", "#FFF8F0", "#FFE8D6",
             "#FFB4A2", "#E56B6F", "#B23A48", "#8C1C13"],

            # 3: Зеленая (лес)
            ["#00120B", "#0C3823", "#356859", "#6A994E", "#A7C957", "#F2E8CF", "#EDE0D4",
             "#DDB892", "#B08968", "#7F5539", "#4A2C1B"],

            # 4: Радужная
            ["#3A015C", "#4F0147", "#35012C", "#290025", "#11001C", "#FFFFFF", "#FFE5EC",
             "#FFC2D1", "#FFB7C5", "#FF8FAB", "#FB6F92"],

            # 5: Неоновая (киберпанк)
            ["#03071E", "#370617", "#6A040F", "#9D0208", "#D00000", "#FFBA08", "#FFD60A",
             "#00FF9D", "#00B4D8", "#0077B6", "#0096C7"],

            # 6: Пастельная
            ["#FAD2E1", "#E2ECE9", "#BEE1E6", "#F0EFEB", "#DFE7FD", "#FFFFFF", "#CDDAFD",
             "#A1C3FD", "#7796CB", "#576490", "#3A405A"],

            # 7: Монохромная синяя
            ["#03045E", "#023E8A", "#0077B6", "#0096C7", "#00B4D8", "#FFFFFF", "#90E0EF",
             "#48CAE4", "#00A8E8", "#0077B6", "#00509E"],

            # 8: Закатная (розово-оранжевая)
            ["#240046", "#3C096C", "#5A189A", "#7B2CBF", "#9D4EDD", "#FF9E00", "#FF9100",
             "#FF6D00", "#FF5400", "#FF2E00", "#FF0000"],

            # 9: Зимняя (холодная)
            ["#012A4A", "#013A63", "#01497C", "#014F86", "#2A6F97", "#FFFFFF", "#E9F5FB",
             "#C4E4F2", "#9CCFE7", "#6DAEDB", "#468FAF"]
        ]

    def set_color_scheme(self, scheme_index):
        """Устанавливает цветовую схему по индексу"""
        if 0 <= scheme_index < len(self.color_schemes):
            self.color_scheme_index = scheme_index
            self.colors = self.color_schemes[scheme_index]

    def next_color_scheme(self):
        """Переключает на следующую цветовую схему"""
        self.color_scheme_index = (self.color_scheme_index + 1) % len(self.color_schemes)
        self.colors = self.color_schemes[self.color_scheme_index]
        return self.color_scheme_index

    def setValues(self, values):
        self._values = values

    def values(self):
        return self._values

    def update_circle_position(self):
        """Обновляет позицию круга для движения по дуге"""
        # Обновляем угол
        if self.moving_right:
            self.angle += self.angle_speed
            # Если достигли правой стороны дуги, меняем направление
            if self.angle >= 310:
                self.moving_right = False
        else:
            self.angle -= self.angle_speed
            # Если достигли левой стороны дуги, меняем направление
            if self.angle <= 230:
                self.moving_right = True

        # Преобразуем угол в радианы
        angle_rad = math.radians(self.angle)

        # Рассчитываем позицию круга на дуге
        circle_x = self.arc_center_x + self.arc_radius * math.cos(angle_rad)
        circle_y = self.arc_center_y + self.arc_radius * math.sin(angle_rad)

        return circle_x, circle_y

    def draw(self, draw, width, height):
        # Clear the display
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

        bar_width = width // self.bars
        segment_height = 10  # Высота каждого маленького прямоугольника
        spacing = 2  # Отступ между столбиками

        for i in range(self.bars):
            # Рассчитываем сколько сегментов должно быть видно (0-100% -> 0-23 сегмента)
            max_segments = 12  # 230px / 10px = 23 сегмента (оставляем 10px сверху)
            num_segments = int((self._values[i] / 100.0) * max_segments)

            # Ограничиваем количество сегментов
            if num_segments < 0:
                num_segments = 0
            elif num_segments > max_segments:
                num_segments = max_segments

            # Рисуем сегменты снизу вверх
            for segment in range(num_segments):
                # Рассчитываем цвет для этого сегмента (чем выше - тем теплее цвет)
                color_idx = min(int((segment / max_segments) * (len(self.colors) - 1)), len(self.colors) - 1)
                color = self._hex_to_rgb(self.colors[color_idx])

                # Координаты сегмента
                x0 = i * bar_width + spacing
                y0 = height - (segment + 1) * segment_height  # сверху сегмента
                x1 = (i + 1) * bar_width - spacing - 1
                y1 = height - segment * segment_height - 4  # снизу сегмента

                # Рисуем маленький прямоугольник (сегмент)
                draw.rectangle([x0, y0, x1, y1], fill=color)

                # Добавляем небольшую обводку между сегментами для визуального разделения
                if segment < num_segments - 1:
                    draw.line([x0, y0, x1, y0], fill=(50, 50, 50), width=2)

        # Получаем обновленную позицию круга на дуге
        circle_x, circle_y = self.update_circle_position()

        # Координаты для круга
        circle_x0 = circle_x - self.circle_radius
        circle_y0 = circle_y - self.circle_radius
        circle_x1 = circle_x + self.circle_radius
        circle_y1 = circle_y + self.circle_radius

        # Рисуем белый круг
        draw.ellipse([circle_x0, circle_y0, circle_x1, circle_y1], fill=(255, 255, 255))

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


class EqualizerLCDWindow:
    def __init__(self, disp):
        # Store display
        self.disp = disp

        # Store display dimensions
        self.width = self.disp.width  # 240
        self.height = self.disp.height  # 240

        # Создаем один эквалайзер для обоих глаз (одинаковая картинка)
        self.equalizer = EqualizerBar(10, color_scheme_index=0)

        # Инициализация с случайными значениями
        self.equalizer.setValues([random.randint(20, 80) for _ in range(10)])

        # Для автоматической смены цветовых схем
        self.scheme_change_counter = 0
        self.scheme_change_interval = 50

        # Текущее состояние: один кадр показывается обоим глазам поочередно
        self.current_frame = None
        self.current_eye = "right"  # Какой глаз сейчас активен
        self.frame_shown_count = 0  # Сколько раз текущий кадр был показан
        self.eyes_per_frame = 2  # Каждый кадр показывается обоим глазам

        # Время показа каждого глаза
        self.eye_display_time = 0.1  # 100 мс на каждый глаз
        self.time_since_last_switch = 0

    def update_values(self):
        """Обновляет значения эквалайзера (только когда создается новый кадр)"""
        # Обновляем значения эквалайзера
        self.equalizer.setValues([
            min(100, v + random.randint(0, 30) if random.randint(0, 5) > 2 else max(0, v - random.randint(0, 20)))
            for v in self.equalizer.values()
        ])

        # Автоматически меняем цветовые схемы через определенные интервалы
        self.scheme_change_counter += 1
        if self.scheme_change_counter >= self.scheme_change_interval:
            self.equalizer.next_color_scheme()
            self.scheme_change_counter = 0

    def create_frame(self):
        """Создает новый кадр эквалайзера"""
        # Обновляем значения перед созданием кадра
        self.update_values()

        # Создаем новое изображение
        image = Image.new("RGB", (self.width, self.height), "BLACK")
        draw = ImageDraw.Draw(image)

        # Рисуем эквалайзер
        self.equalizer.draw(draw, self.width, self.height)

        return image

    def show_eye(self, eye_side, frame):
        """Показывает кадр на указанном глазу"""
        # Управляем GPIO для выбора глаза
        if eye_side == "left":
            GPIO.output(7, 1)  # Включаем левый глаз
            GPIO.output(24, 0)  # Выключаем правый глаз
        else:  # right
            GPIO.output(7, 0)  # Выключаем левый глаз
            GPIO.output(24, 1)  # Включаем правый глаз

        # Отображаем кадр на LCD
        self.disp.ShowImage(frame)

    def update_display(self, elapsed_time):
        """
        Обновляет отображение: один кадр показывается сначала на одном глазу, потом на другом

        Args:
            elapsed_time: Время с последнего обновления в секундах
        """
        self.time_since_last_switch += elapsed_time

        # Если пришло время переключить глаз
        if self.time_since_last_switch >= self.eye_display_time:
            self.time_since_last_switch = 0

            # Если это первый показ кадра или кадр уже показан обоим глазам
            if self.current_frame is None or self.frame_shown_count >= self.eyes_per_frame:
                # Создаем новый кадр
                self.current_frame = self.create_frame()
                self.frame_shown_count = 0
                self.current_eye = "right"  # Начинаем с правого глаза

            # Показываем текущий кадр на текущем глазу
            self.show_eye(self.current_eye, self.current_frame)

            # Увеличиваем счетчик показа кадра
            self.frame_shown_count += 1

            # Переключаем глаз для следующего показа
            if self.current_eye == "right":
                self.current_eye = "left"
            else:
                self.current_eye = "right"


class EqualizerAPI:
    def __init__(self, robot_eye_display):
        self._running = False
        self._thread = None
        self._lcd_window = None
        self.robot_display = robot_eye_display
        self.original_gpio_state = None

    def play(self):
        """Запускает визуализацию эквалайзера на LCD дисплее с поочередным включением глаз"""
        if self._running:
            return False

        self._running = True

        # Сохраняем оригинальное состояние GPIO
        self.original_gpio_state = (GPIO.input(7), GPIO.input(24))

        def run_visualization():
            try:
                # Initialize LCD window with existing display
                self._lcd_window = EqualizerLCDWindow(self.robot_display.disp)

                # Main loop
                last_update = time.time()
                update_interval = 0.05  # 20 раз в секунду для плавного переключения глаз

                while self._running:
                    current_time = time.time()
                    elapsed_time = current_time - last_update

                    if elapsed_time >= update_interval:
                        self._lcd_window.update_display(elapsed_time)
                        last_update = current_time

                    # Небольшая задержка для снижения нагрузки на CPU
                    time.sleep(0.001)

            except Exception as e:
                self.robot_display.log.error(f"Error in equalizer visualization: {e}")
            finally:
                # Cleanup - возвращаем оригинальное состояние GPIO
                if self.original_gpio_state:
                    GPIO.output(7, self.original_gpio_state[0])
                    GPIO.output(24, self.original_gpio_state[1])
                self._lcd_window = None
                self.original_gpio_state = None

        # Запускаем в отдельном потоке
        self._thread = threading.Thread(target=run_visualization, daemon=True)
        self._thread.start()
        self.robot_display.log.info("Equalizer visualization started with alternating eyes")
        return True

    def stop(self):
        """Останавливает визуализацию эквалайзера"""
        if not self._running:
            return False

        self._running = False

        # Ждем завершения потока
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
            self._thread = None

        # Возвращаем GPIO в исходное состояние
        GPIO.output(7, 0)
        GPIO.output(24, 0)

        self.robot_display.log.info("Equalizer visualization stopped")
        return True

    def is_playing(self):
        """Проверяет, запущена ли визуализация"""
        return self._running


class RobotEyeDisplay:
    def __init__(self):
        global thread_status
        thread_status = False
        """
        Initialize the RobotEyeDisplay class.

        This class controls the robotic eye display on a Raspberry Pi.
        """
        # GPIO Setup
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(7, GPIO.OUT)
        GPIO.setup(24, GPIO.OUT)
        GPIO.output(7, 0)
        GPIO.output(24, 0)

        # LCD Configuration
        self.RST = 27
        self.DC = 25
        self.BL = 18
        self.bus = 0
        self.device = 0
        self.log = logging.getLogger(__name__)
        self.disp = self.init_display()

        # Инициализируем Equalizer API
        self.equalizer_api = EqualizerAPI(self)

        # Чистый экран при старте
        image1 = Image.new("RGB", (self.disp.width, self.disp.height), color="Black")
        self.disp.ShowImage(image1)

    def init_display(self):
        """
        Initialize the LCD display using SPI.

        Returns:
            LCD_1inch28: Initialized LCD display object.
        """
        try:
            self.log.info("Initializing display...")
            disp = LCD_1inch28(spi=SPI.SpiDev(self.bus, self.device))
            disp.Init()
            disp.clear()
            GPIO.output(7, 0)
            GPIO.output(24, 0)
            self.log.info("Display initialized successfully.")
            return disp
        except Exception as e:
            self.log.error(f"Error initializing display: {e}")
            sys.exit(1)

    def load_frames(self, gif_path):
        """
        Load frames from a GIF.

        Args:
            gif_path (str): Path to the GIF file.

        Returns:
            list: List of frames from the GIF.
        """
        gif = Image.open(gif_path)
        frames = [frame.copy() for frame in ImageSequence.Iterator(gif)]
        return frames

    def display_frames(self, frames_R, frames_L):
        """
        Display frames on the robotic eyes.

        Args:
            frames_R (list): List of frames for the right eye.
            frames_L (list): List of frames for the left eye.
        """
        try:
            time.sleep(2.0)
            max_frames = max(len(frames_L), len(frames_R))

            for i in range(max_frames):
                if thread_status:
                    break
                if i < len(frames_L):
                    self.left_eye(frames_L[i])
                if i < len(frames_R):
                    self.right_eye(frames_R[i])

            time.sleep(3.0)
            GPIO.output(7, 0)
            GPIO.output(24, 0)

            self.log.info("Display closed.")
        except Exception as e:
            self.log.error(f"Error displaying frames: {e}")

    def right_eye(self, frame_R):
        """
        Display a frame on the right eye.

        Args:
            frame_R (PIL.Image.Image): Frame to display on the right eye.
        """
        frame_rgb_R = frame_R.convert('RGB')
        GPIO.output(7, 0)
        GPIO.output(24, 1)
        self.disp.ShowImage(frame_rgb_R)

    def left_eye(self, frame_L):
        """
        Display a frame on the left eye.

        Args:
            frame_L (PIL.Image.Image): Frame to display on the left eye.
        """
        GPIO.output(7, 1)
        GPIO.output(24, 0)
        frame_rgb_L = frame_L.convert('RGB')
        self.disp.ShowImage(frame_rgb_L)

    def run(self, gif_paths_R, gif_paths_L):
        """
        Run the robotic eye display animation.

        Args:
            gif_paths_R (list): List of paths to GIFs for the right eye.
            gif_paths_L (list): List of paths to GIFs for the left eye.
        """
        try:
            frames_R = [self.load_frames(gif_path) for gif_path in gif_paths_R]
            frames_L = [self.load_frames(gif_path) for gif_path in gif_paths_L]
            print(f'Number of frames in GIF: {len(frames_L)}, {len(frames_R)}')

            max_frames = max(len(frames_L), len(frames_R))

            for i in range(max_frames):
                if thread_status:
                    break
                if i < len(frames_R):
                    frames_R_set = frames_R[i]
                else:
                    frames_R_set = []

                if i < len(frames_L):
                    frames_L_set = frames_L[i]
                else:
                    frames_L_set = []

                self.display_frames(frames_R_set, frames_L_set)
        except KeyboardInterrupt:
            self.log.info("Keyboard interrupt detected. Exiting...")
        except Exception as e:
            self.log.error(f"An error occurred: {e}")

    # API методы для управления эквалайзером
    def play_equalizer(self):
        """Запустить визуализацию эквалайзера с поочередным включением глаз"""
        return self.equalizer_api.play()

    def stop_equalizer(self):
        """Остановить визуализацию эквалайзера"""
        return self.equalizer_api.stop()

    def is_equalizer_playing(self):
        """Проверить, запущен ли эквалайзер"""
        return self.equalizer_api.is_playing()


# Пример использования:
"""
if __name__ == "__main__":
    # Создаем экземпляр робота
    robot = RobotEyeDisplay()

    # Запускаем эквалайзер с поочередным включением глаз
    robot.play_equalizer()

    # Ждем 10 секунд
    time.sleep(10)

    # Останавливаем эквалайзер
    robot.stop_equalizer()

    # Или запускаем анимацию глаз
    # robot.run(['right_eye.gif'], ['left_eye.gif'])
"""
