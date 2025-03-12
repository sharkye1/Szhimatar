import os
import sys
from concurrent.futures import ThreadPoolExecutor
import platform
import time
import random
import requests

import json
import subprocess
from PyQt6.QtGui import QAction, QPixmap, QPainter
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QComboBox, QSlider,
                             QSpinBox, QCheckBox, QTextEdit, QMessageBox, QProgressBar,
                             QToolBar, QFrame, QInputDialog, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QProcess, QStandardPaths, QTimer, QSettings, QUrl
from PyQt6.QtNetwork import (QNetworkAccessManager, QNetworkRequest, QNetworkReply)

from styles import dark_stylesheet, light_stylesheet


class VideoCompressor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.presets_file = "presets.json"
        self.current_preset = None
        self.current_theme = 'dark'
        self.start_time = None  # Время начала сжатия
        self.original_size = None  # Размер исходного файла

        self.settings = QSettings("MyCompany", "VideoCompressor")
        self.output_folder = self.settings.value("output_folder", "")  # Загружаем сохранённую папку

        self.init_ui()
        self.load_presets()
        self.load_settings()
        self.background_image = QPixmap()
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.on_image_downloaded)
        self.image_urls = [
            "https://i.imgur.com/S721eIZ.png",  # Замените на ваши ссылки
            "https://i.imgur.com/J2Ey9ce.png",
            "https://i.imgur.com/MswgFY3.png",
            "https://i.imgur.com/7RQtLnR.png",
            "https://i.imgur.com/IXNVtAa.png",

        ]
        self.cache_dir = os.path.join(os.path.dirname(__file__), "backs")
        os.makedirs(self.cache_dir, exist_ok=True)  # Создаем папку, если её нет

        self.download_background_image()

        self.background_opacity = 0.2

    def download_background_image(self):
        """Скачивает новое изображение или использует уже скачанное."""
        # Получаем список уже скачанных изображений
        downloaded_images = self.get_downloaded_images()

        # Находим нескачанные изображения
        not_downloaded_urls = [url for url in self.image_urls if self.get_image_filename(url) not in downloaded_images]

        if not_downloaded_urls:
            # Если есть нескачанные изображения, выбираем одно из них
            image_url = random.choice(not_downloaded_urls)
            #print(f"Загружаем новое изображение: {image_url}")
            request = QNetworkRequest(QUrl(image_url))
            self.network_manager.get(request)
        else:
            # Если все изображения скачаны, выбираем случайное из уже скачанных
            if downloaded_images:
                random_image = random.choice(downloaded_images)
                self.background_image.load(os.path.join(self.cache_dir, random_image))
                self.update()
                #print(f"Используем уже скачанное изображение: {random_image}")
            else:
                print("Нет доступных изображений.")

    def get_downloaded_images(self):
        """Возвращает список уже скачанных изображений."""
        return [f for f in os.listdir(self.cache_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

    def get_image_filename(self, url):
        """Генерирует имя файла на основе URL."""
        return url.split('/')[-1]  # Извлекаем имя файла из URL

    def on_image_downloaded(self, reply):
        """Обрабатывает скачанное изображение."""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            image_data = reply.readAll()
            if image_data.size() > 0:  # Проверяем, что данные не пустые
                #print("Изображение успешно скачано!")

                # Загружаем изображение в QPixmap
                self.background_image.loadFromData(image_data)
                self.update()  # Обновляем интерфейс

                # Сохраняем изображение в папку backs
                image_url = reply.url().toString()
                filename = self.get_image_filename(image_url)
                cache_path = os.path.join(self.cache_dir, filename)

                with open(cache_path, "wb") as f:
                    f.write(image_data)

                #print(f"Изображение сохранено в: {cache_path}")
            else:
                print("Ошибка: изображение не содержит данных.")
        else:
            print("Ошибка при загрузке изображения:", reply.errorString())

    def paintEvent(self, event):
        """Отрисовывает фоновое изображение."""
        painter = QPainter(self)
        if not self.background_image.isNull():
            scaled_pixmap = self.background_image.scaled(
                self.size(),
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatioByExpanding
            )
            painter.setOpacity(self.background_opacity)
            painter.drawPixmap(self.rect(), scaled_pixmap)




    def init_ui(self):
        self.setWindowTitle("Сжиматор на NVENC")
        self.setGeometry(100, 100, 700, 600)

        toolbar = QToolBar("Панель инструментов")
        self.addToolBar(toolbar)

        self.theme_action = QAction("Тема", self)
        self.theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.theme_action)

        self.file_label = QLabel("Выбери видеофайл:")
        self.file_btn = QPushButton("Обзор в проводнике...")
        self.file_btn.clicked.connect(self.select_file)

        # Выбор папки вывода
        self.output_folder_label = QLabel("Папка для сохранения:")
        self.output_folder_btn = QPushButton("Выбрать папку...")
        self.output_folder_btn.clicked.connect(self.select_output_folder)
        self.output_folder_display = QLabel(
            self.output_folder if self.output_folder else "По умолчанию (папка исходного файла)")
        self.output_folder_display.setStyleSheet("font-style: italic; color: #888;")

        self.separator_output = self.create_separator()

        # Настройки сжатия
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "160x120", "176x144", "240x160", "320x180", "320x240",
            "400x240", "480x272", "480x320", "640x360", "640x480",
            "720x480", "800x450", "800x600", "854x480", "960x540",
            "1024x576", "1024x768", "1152x648", "1280x720", "1280x800",
            "1280x960", "1366x768", "1440x900", "1600x900", "1920x1080"
        ])

        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(["aac", "libmp3lame", "copy"])  # Добавляем варианты кодеков
        self.audio_codec_combo.setCurrentText("aac")  # Устанавливаем AAC по умолчанию

        # Настройки аудио битрейта
        self.audio_bitrate_slider = QSlider(Qt.Orientation.Horizontal)
        self.audio_bitrate_slider.setRange(1, 320)
        self.audio_bitrate_spin = QSpinBox()
        self.audio_bitrate_spin.setRange(1, 320)
        self.audio_bitrate_spin.setFixedWidth(60)  # Фиксированная ширина
        self.audio_bitrate_slider.valueChanged.connect(self.audio_bitrate_spin.setValue)
        self.audio_bitrate_spin.valueChanged.connect(self.audio_bitrate_slider.setValue)

        audio_bitrate_layout = QHBoxLayout()
        audio_bitrate_layout.addWidget(self.audio_bitrate_slider)
        audio_bitrate_layout.addWidget(self.audio_bitrate_spin)

        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["hevc_nvenc (H.265)", "h264_nvenc (H.264)"])

        # Настройки видео битрейта
        self.bitrate_slider = QSlider(Qt.Orientation.Horizontal)
        self.bitrate_slider.setRange(1, 50)
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(1, 50)
        self.bitrate_slider.valueChanged.connect(self.bitrate_spin.setValue)
        self.bitrate_spin.valueChanged.connect(self.bitrate_slider.setValue)

        bitrate_layout = QHBoxLayout()
        bitrate_layout.addWidget(self.bitrate_slider)
        bitrate_layout.addWidget(self.bitrate_spin)

        # Настройка выбора фпса
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 60)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setFixedWidth(60)  # Фиксированная ширина
        self.fps_slider.valueChanged.connect(self.fps_spin.setValue)
        self.fps_spin.valueChanged.connect(self.fps_slider.setValue)

        fps_layout = QHBoxLayout()
        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_spin)

        # Настройки скорости видео
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(25, 200)  # От 0.5x до 2.0x
        self.speed_slider.setValue(100)  # По умолчанию 1.0x
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.25, 2.0)
        self.speed_spin.setSingleStep(0.01)
        self.speed_spin.setValue(1.0)  # По умолчанию 1.0x
        self.speed_spin.setFixedWidth(60)  # Фиксированная ширина
        self.speed_slider.valueChanged.connect(self.update_speed_spin)
        self.speed_spin.valueChanged.connect(self.update_speed_slider)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Скорость видео:"))
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_spin)

        # Сами пресеты
        self.presets_combo = QComboBox()
        self.presets_combo.currentIndexChanged.connect(self.apply_preset)
        self.save_preset_btn = QPushButton("Сохранить пресет")
        self.save_preset_btn.clicked.connect(self.save_preset)
        self.delete_preset_btn = QPushButton("Удалить пресет")
        self.delete_preset_btn.clicked.connect(self.delete_preset)

        # Горизонтальная компоновка для кнопок пресета
        preset_buttons_layout = QHBoxLayout()
        preset_buttons_layout.addWidget(self.save_preset_btn)
        preset_buttons_layout.addWidget(self.delete_preset_btn)

        # Элементы для отображения размера
        self.size_label = QLabel("Примерный размер выходного файла: ")
        self.size_value = QLabel("0.00 MB")
        self.size_value.setStyleSheet("font-weight: bold;")

        size_layout = QHBoxLayout()
        size_layout.addWidget(self.size_label)
        size_layout.addWidget(self.size_value)



        # Прогресс и логи
        self.progress_bar = QProgressBar()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # Кнопка запуска
        self.compress_btn = QPushButton("Сжать видео")
        self.compress_btn.clicked.connect(self.compress_video)

        self.separator1 = self.create_separator()
        self.separator2 = self.create_separator()
        self.separator3 = self.create_separator()

        # Компоновка

        layout = QVBoxLayout()
        layout.addWidget(self.file_label)
        layout.addWidget(self.file_btn)
        layout.addWidget(self.separator1)
        layout.addWidget(QLabel("Разрешение видео:"))
        layout.addWidget(self.resolution_combo)
        layout.addWidget(QLabel("Кодек:"))
        layout.addWidget(self.codec_combo)
        layout.addWidget(QLabel("Битрейт (Мбит/с):"))
        layout.addLayout(bitrate_layout)
        layout.addWidget(QLabel("FPS:"))
        layout.addLayout(fps_layout)
        layout.addLayout(speed_layout)
        layout.addWidget(self.separator2)
        layout.addWidget(QLabel("Аудиокодек:"))
        layout.addWidget(self.audio_codec_combo)  # Добавляем выбор аудиокодека
        layout.addWidget(QLabel("Битрейт аудио (кбит/с):"))
        layout.addLayout(audio_bitrate_layout)  # Добавляем горизонтальную компоновку для битрейта аудио
        layout.addWidget(self.separator3)
        layout.addWidget(self.output_folder_label)
        layout.addWidget(self.output_folder_btn)
        layout.addWidget(self.output_folder_display)
        layout.addWidget(self.create_separator())
        layout.addWidget(QLabel("Пресеты:"))
        layout.addWidget(self.presets_combo)
        layout.addLayout(preset_buttons_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(size_layout)
        layout.addWidget(self.log_area)
        layout.addWidget(self.compress_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.apply_theme(self.current_theme)

    def create_separator(self):
        """Создаёт горизонтальный разделитель."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator

    def toggle_theme(self):
        """Переключает тему между светлой и тёмной."""
        if self.current_theme == 'dark':
            self.current_theme = 'light'
        else:
            self.current_theme = 'dark'
        self.apply_theme(self.current_theme)

    def apply_theme(self, theme):
        """Применяет выбранную тему."""
        self.current_theme = theme
        if theme == 'dark':
            self.setStyleSheet(dark_stylesheet)
            self.theme_action.setText("Светлая тема")
        else:
            self.setStyleSheet(light_stylesheet)
            self.theme_action.setText("Тёмная тема")


    def select_file(self):
        """Выбирает файл и обновляет интерфейс."""
        file, _ = QFileDialog.getOpenFileName(
            self, "Выберите видеофайл",
            self.last_dir,
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file:
            self.current_file = file
            self.last_dir = os.path.dirname(file)
            self.file_label.setText(f"Выбран файл: {os.path.basename(file)}")

            # Получаем размер файла
            original_size = os.path.getsize(file)

            # Вычисляем 22% от исходного размера
            compressed_size = original_size * 0.22

            # Форматируем размер для отображения
            compressed_size_mb = compressed_size / (1024 * 1024)  # Переводим в мегабайты
            original_size_mb = original_size / (1024 * 1024)  # Переводим в мегабайты

            # Вычисляем процент сжатия
            percent_change = ((compressed_size_mb - original_size_mb) / original_size_mb) * 100

            # Обновляем отображение
            self.size_value.setText(f"{compressed_size_mb:.2f} MB ({percent_change:.2f}%)")



    def compress_video(self):
        print('Пошел компресс...')
        if not hasattr(self, 'current_file'):
            QMessageBox.warning(self, "Ошибка", "Выберите файл для сжатия!")
            return

        # Получаем исходный размер файла
        original_size = os.path.getsize(self.current_file)

        # Вычисляем 22% от исходного размера
        compressed_size = original_size * 0.22

        # Форматируем размер для отображения
        compressed_size_mb = compressed_size / (1024 * 1024)  # Переводим в мегабайты
        original_size_mb = original_size / (1024 * 1024)  # Переводим в мегабайты

        # Вычисляем процент сжатия
        percent_change = ((compressed_size_mb - original_size_mb) / original_size_mb) * 100

        # Обновляем отображение
        self.size_value.setText(f"{compressed_size_mb:.2f} MB ({percent_change:.2f}%)")

        self.original_size = os.path.getsize(self.current_file)
        self.start_time = time.time()

        output_file = self.get_output_path()
        codec = "hevc_nvenc" if self.codec_combo.currentText().startswith("hevc") else "h264_nvenc"
        bitrate = f"{self.bitrate_spin.value()}M"
        resolution = self.resolution_combo.currentText()
        fps = self.fps_spin.value()

        audio_codec = self.audio_codec_combo.currentText()
        audio_bitrate = f"{self.audio_bitrate_spin.value()}k"
        speed = self.speed_spin.value()
        # Обернем пути в кавычки для корректной обработки FFmpeg
        input_file = f'"{self.current_file}"'
        output_file = output_file.replace('\\', '/')
        output_file = f'"{output_file}"'
        print(output_file)

        cmd = [
            'ffmpeg',
            '-y',
            '-hwaccel', 'cuda',  # Использование CUDA для аппаратного ускорения
            '-i', input_file,
            '-c:v', codec,
            '-preset', 'p7',  # Максимальное качество
            '-b:v', bitrate,
            '-maxrate', f"{self.bitrate_spin.value() + 1}M",  # Максимальный битрейт
            '-bufsize', f"{self.bitrate_spin.value() * 2}M",  # Размер буфера
            '-r', str(fps),
            '-filter:v', f'setpts={1 / speed}*PTS',  # Изменение скорости видео
            '-c:a', audio_codec,  # Аудиокодек
            '-b:a', audio_bitrate,  # Битрейт аудио
            output_file
        ]

        self.process = QProcess()
        self.process.readyReadStandardError.connect(self.handle_log)
        self.process.finished.connect(self.on_finish)
        print(f"Дана команда {cmd}")
        self.process.startCommand(' '.join(cmd))

        # Таймер для обновления прогресса
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(nkirill)

    def update_speed_spin(self):
        """Обновляет значение скорости в QDoubleSpinBox при изменении ползунка."""
        speed_value = self.speed_slider.value() / 100.0
        self.speed_spin.setValue(speed_value)

    def update_speed_slider(self):
        """Обновляет значение ползунка при изменении QDoubleSpinBox."""
        speed_value = int(self.speed_spin.value() * 100)
        self.speed_slider.setValue(speed_value)

    def handle_log(self):
        process = self.sender()
        error = process.readAllStandardError().data().decode()
        self.log_area.append(error)

        if "error" in error.lower():
            QMessageBox.critical(self, "Ошибка FFmpeg", error)

    def update_progress(self):
        if hasattr(self, 'process') and self.process.state() == QProcess.ProcessState.Running:
            self.progress_bar.setValue(self.progress_bar.value() + 1)

    def on_finish(self):
        self.timer.stop()
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Готово", "Сжатие завершено!")

    def get_output_path(self):
        base, ext = os.path.splitext(self.current_file)
        return f"{base}_compressed{ext}"

    def update_output_size(self):
        # Примерный расчет размера выходного файла
        duration = self.get_video_duration()
        bitrate = self.bitrate_spin.value()
        audio_bitrate = 192  # Кбит/с
        size_mb = (bitrate + audio_bitrate / 1000) * duration / 8
        self.log_area.append(f"Примерный размер выходного файла: {size_mb:.2f} МБ")

    def get_video_duration(self):
        """Возвращает длительность видео, обрабатывает ошибки."""
        try:
            # Настройки для скрытия консоли
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', self.current_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            return float(result.stdout.strip())
        except Exception as e:
            print(f"Ошибка получения длительности: {e}")
            return 0.0

    def save_preset(self):
        print('сейв пресет зашел')
        """Сохраняет текущие настройки как пресет."""
        preset_name, ok = QInputDialog.getText(self, "Сохранение пресета", "Введите имя пресета:")
        if ok and preset_name:
            # Сохраняем текущие настройки
            self.presets[preset_name] = {
                "resolution": self.resolution_combo.currentText(),
                "codec": self.codec_combo.currentText(),
                "bitrate": self.bitrate_spin.value(),
                "fps": self.fps_spin.value(),
                "audio_codec": self.audio_codec_combo.currentText(),
                "audio_bitrate": self.audio_bitrate_spin.value(),
            }

            # Сохраняем пресеты в файл
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=4)

            # Обновляем выпадающий список пресетов
            self.presets_combo.clear()
            self.presets_combo.addItems(self.presets.keys())

            QMessageBox.information(self, "Успех", f"Пресет '{preset_name}' сохранён!")

    def delete_preset(self):
        """Удаляет выбранный пресет."""
        preset_name = self.presets_combo.currentText()
        if preset_name in self.presets:
            # Подтверждение удаления
            reply = QMessageBox.question(
                self,
                "Удаление пресета",
                f"Вы уверены, что хотите удалить пресет '{preset_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Удаляем пресет
                del self.presets[preset_name]

                # Сохраняем изменения в файл
                with open(self.presets_file, 'w', encoding='utf-8') as f:
                    json.dump(self.presets, f, indent=4)

                # Обновляем выпадающий список
                self.presets_combo.clear()
                self.presets_combo.addItems(self.presets.keys())

                QMessageBox.information(self, "Успех", f"Пресет '{preset_name}' удалён!")
        else:
            QMessageBox.warning(self, "Ошибка", "Пресет не выбран или не существует.")

    def load_presets(self):
        """Загружает пресеты из файла presets.json."""
        if not os.path.exists(self.presets_file):
            # Если файл не существует, создаём его с пустым JSON-объектом
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                self.presets = json.load(f)
                self.presets_combo.addItems(self.presets.keys())
        except json.JSONDecodeError:
            # Если файл повреждён, создаём новый
            self.presets = {}
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def apply_preset(self):
        """Применяет выбранный пресет."""
        preset_name = self.presets_combo.currentText()
        if preset_name in self.presets:
            preset = self.presets[preset_name]

            # Применяем настройки видео
            self.resolution_combo.setCurrentText(preset["resolution"])
            self.codec_combo.setCurrentText(preset["codec"])
            self.bitrate_spin.setValue(preset["bitrate"])
            self.fps_spin.setValue(preset["fps"])

            # Применяем настройки аудио
            self.audio_codec_combo.setCurrentText(preset["audio_codec"])
            self.audio_bitrate_spin.setValue(preset["audio_bitrate"])

    def save_settings(self):
        settings = {
            'last_dir': self.last_dir,
            'theme': self.current_theme
        }
        with open('.env', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open('.env', 'r') as f:
                settings = json.load(f)
                self.last_dir = settings.get('last_dir',
                                             QStandardPaths.writableLocation(
                                                 QStandardPaths.StandardLocation.HomeLocation))
                self.apply_theme(settings.get('theme', 'dark'))
        except FileNotFoundError:
            self.last_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
            self.apply_theme('dark')

    def select_output_folder(self):
        """Позволяет пользователю выбрать папку для сохранения."""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения", self.output_folder)
        if folder:
            self.output_folder = folder
            self.output_folder_display.setText(self.output_folder)
            self.settings.setValue("output_folder", self.output_folder)  # Сохраняем выбранную папку

    def get_output_path(self):
        """Возвращает путь для сохранения сжатого файла."""
        base, ext = os.path.splitext(os.path.basename(self.current_file))
        output_filename = f"{base}_compressed{ext}"

        # Если папка вывода не выбрана, сохраняем в папке исходного файла
        if not self.output_folder:
            return os.path.join(os.path.dirname(self.current_file), output_filename)

        # Иначе сохраняем в выбранной папке
        return os.path.join(self.output_folder, output_filename)

    def on_finish(self):
        """Вызывается после завершения сжатия."""
        self.timer.stop()
        self.progress_bar.setValue(100)

        self.progress_bar.setValue(0)
        # Вычисляем время выполнения
        end_time = time.time()
        elapsed_time = end_time - self.start_time

        # Получаем размер сжатого файла
        output_file = self.get_output_path()
        compressed_size = os.path.getsize(output_file)

        # Вычисляем процент сжатия
        compression_ratio = (1 - (compressed_size / self.original_size)) * 100

        # Формируем сообщение со статистикой
        stats_message = (
            f"Исходный размер: {self.format_size(self.original_size)}\n"
            f"Сжатый размер: {self.format_size(compressed_size)}\n"
            f"Сжатие: {compression_ratio:.2f}%\n"
            f"Время выполнения: {elapsed_time:.2f} секунд"
        )

        # Показываем статистику в диалоговом окне
        QMessageBox.information(self, "Статистика сжатия", stats_message)

    def get_original_audio_bitrate(self):
        """Возвращает битрейт аудио с обработкой ошибок."""
        try:
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'stream=bit_rate',
                 '-of', 'default=noprint_wrappers=1:nokey=1', '-select_streams', 'a:0', self.current_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            return int(result.stdout.strip() or 0) / 1000
        except Exception as e:
            print(f"Ошибка аудио битрейта: {e}")
            return 0



    def format_size(self, size):
        """Форматирует размер файла в удобочитаемый вид (KB, MB, GB)."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    def apply_theme(self, theme):
        self.current_theme = theme
        if theme == 'dark':
            self.setStyleSheet(dark_stylesheet)
        else:
            self.setStyleSheet(light_stylesheet)


if __name__ == "__main__":
    nkirill = 40
    app = QApplication([])
    window = VideoCompressor()
    window.show()
    app.exec()
