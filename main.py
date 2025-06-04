import os
import sys
import platform
import time
import random
import requests
import logging
import winreg
import ctypes
import tempfile
from pathlib import Path

import json
import subprocess
from PyQt6.QtGui import QAction, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QComboBox, QSlider,
                             QSpinBox, QTextEdit, QMessageBox, QProgressBar,
                             QToolBar, QFrame, QInputDialog, QDoubleSpinBox, QDialog,
                             QCheckBox, QTableWidgetItem, QTableWidget)
from PyQt6.QtCore import Qt, QProcess, QStandardPaths, QTimer, QSettings, QUrl, pyqtSignal, QRect
from PyQt6.QtNetwork import (QNetworkAccessManager, QNetworkRequest, QNetworkReply)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QSoundEffect

from styles import dark_stylesheet, light_stylesheet, blue_stylesheet, green_stylesheet, yellow_stylesheet, red_stylesheet

# Версия программы
__version__ = "v1.3"


def is_running_in_ide():
    """Проверяет, запущена ли программа в PyCharm или IDLE."""
    return any(ide in sys.argv[0].lower() for ide in ("pycharm", "idlelib"))

def log_error(message):
    """Записывает ошибки обновления в файл."""
    with open("update_log.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")


def check_for_updates(parent):
    """Проверяет и устанавливает обновления с прогресс-баром."""
    logger = setup_license_logging()
    logger.info("Проверка обновлений...")

    try:
        # Проверяем версию через GitHub API
        github_api_url = "https://api.github.com/repos/sharkye1/Szhimatar/releases/latest"
        network_manager = QNetworkAccessManager()
        api_reply = network_manager.get(QNetworkRequest(QUrl(github_api_url)))

        while not api_reply.isFinished():
            QApplication.processEvents()
            time.sleep(0.01)

        if api_reply.error() != QNetworkReply.NetworkError.NoError:
            raise Exception(api_reply.errorString())

        latest_release = json.loads(api_reply.readAll().data().decode('utf-8'))
        latest_version = latest_release.get("tag_name", "v1.0.0")
        logger.info(f"Актуальная версия: {latest_version}, текущая: {__version__}")

        if latest_version != __version__:
            logger.info("Найдено обновление, скачивание...")

            # Показываем прогресс-бар
            update_dialog = UpdateDialog(parent, parent.current_theme)
            update_dialog.show()
            QApplication.processEvents()

            # Определяем, что скачивать
            if getattr(sys, 'frozen', False):
                # Для .exe
                download_url = f"https://github.com/sharkye1/Szhimatar/releases/download/{latest_version}/Szhimatar.{latest_version.replace('v', '')}.exe"
                new_exe_name = f"Szhimatar.{latest_version.replace('v', '')}.exe"
            else:
                # Для .py
                download_url = f"https://github.com/sharkye1/Szhimatar/releases/download/{latest_version}/main.py"
                new_exe_name = None

            # Скачиваем файл
            download_reply = network_manager.get(QNetworkRequest(QUrl(download_url)))

            # Обновляем прогресс
            def update_progress(bytes_received, bytes_total):
                if bytes_total > 0:
                    progress = int((bytes_received / bytes_total) * 100)
                    update_dialog.set_progress(progress)
                    QApplication.processEvents()

            download_reply.downloadProgress.connect(update_progress)

            while not download_reply.isFinished():
                QApplication.processEvents()
                time.sleep(0.01)

            if download_reply.error() == QNetworkReply.NetworkError.NoError:
                program_dir = get_program_dir()
                if getattr(sys, 'frozen', False):
                    # Обработка обновления .exe
                    temp_dir = Path(tempfile.gettempdir())
                    temp_exe_path = temp_dir / new_exe_name
                    with open(temp_exe_path, "wb") as f:
                        f.write(download_reply.readAll().data())

                    # Создаем батник для замены .exe
                    current_exe = Path(sys.executable)
                    batch_content = f"""@echo off
timeout /t 2
move /Y "{temp_exe_path}" "{current_exe}"
start "" "{current_exe}"
"""
                    batch_path = program_dir / "update.bat"
                    with open(batch_path, "w", encoding="utf-8") as f:
                        f.write(batch_content)

                    logger.info(f"Обновление {latest_version} скачано, запускаем батник")
                    update_dialog.set_text("Обновление скачано, перезапуск...")
                    update_dialog.set_progress(100)
                    QApplication.processEvents()
                    time.sleep(1)

                    # Запускаем батник и выходим
                    subprocess.Popen(['cmd.exe', '/c', str(batch_path)])
                    parent.close()
                    QApplication.quit()
                    sys.exit(0)
                else:
                    # Обработка обновления .py
                    new_content = download_reply.readAll().data().decode('utf-8')
                    script_path = os.path.abspath(__file__)
                    backup_file = script_path.replace(".py", "_backup.py")

                    # Удаляем старую резервную копию
                    if os.path.exists(backup_file):
                        os.remove(backup_file)

                    # Создаём резервную копию
                    os.rename(script_path, backup_file)

                    # Записываем новый файл
                    with open(script_path, "w", encoding="utf-8", newline="\n") as f:
                        f.write(new_content)

                    logger.info(f"Обновление {latest_version} установлено")
                    update_dialog.set_text("Обновление установлено, перезапуск...")
                    update_dialog.set_progress(100)
                    QApplication.processEvents()
                    time.sleep(1)

                    # Перезапускаем
                    logger.info(f"Перезапуск: {sys.executable} {script_path}")
                    parent.close()
                    try:
                        subprocess.Popen([sys.executable, script_path])
                        logger.info("Перезапуск успешен")
                    except Exception as e:
                        logger.error(f"Ошибка перезапуска: {e}")
                    QApplication.quit()
                    sys.exit(0)
            else:
                error = download_reply.errorString()
                logger.error(f"Ошибка скачивания: {error}")
                update_dialog.close()
                QMessageBox.critical(parent, "Ошибка обновления",
                                    f"Не удалось скачать обновление: {error}\nСм. update_log.txt")
        else:
            logger.info("Программа на последней версии")
    except Exception as e:
        logger.error(f"Ошибка обновления: {e}")
        update_dialog.close()
        QMessageBox.critical(parent, "Ошибка обновления",
                            f"Не удалось проверить обновления: {e}\nСм. update_log.txt")

def setup_license_logging():
    """Настраивает логирование."""
    logger = logging.getLogger('Szhimatar')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        try:
            log_dir = get_program_dir()  # Используем папку программы
            log_file = log_dir / "update_log.txt"
            handler = logging.FileHandler(log_file, encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        except Exception as e:
            print(f"Ошибка настройки логирования: {e}")
            # Временный лог в консоль
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(console_handler)
    return logger


os.environ["QT_LOGGING_RULES"] = "*.debug=false"
os.environ["QT_LOGGING_RULES"] = "ffmpeg.*=false"
os.environ["QT_LOGGING_RULES"] = "qt.mediaplayer.*=false"
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.*=false"




class HistoryDialog(QDialog):
    def __init__(self, parent=None, theme='blue'):
        super().__init__(parent)
        self.setWindowTitle("История сжатия")
        prev = 100
        file_name = 170
        file_duration = 100
        filesize_before = 100
        filesize_after = 100
        date_of_compression = 150
        compression_options = 250
        total_window_width = prev + file_name + file_duration + filesize_before + filesize_after + date_of_compression + compression_options
        #self.setMinimumSize(total_window_width+100, 400)
        self.setMinimumSize(1056, 400)
        self.setModal(True)
        self.logger = setup_license_logging()
        self.logger.info("Инициализация окна истории сжатия")

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Превью", "Имя файла", "Длительность", "Размер до", "Размер после",
            "Дата сжатия", "Параметры"
        ])
        self.table.setRowCount(0)

        self.table.setColumnWidth(0, prev)  # Превью

        self.table.setColumnWidth(1, file_name)  # Имя файла

        self.table.setColumnWidth(2, file_duration)  # Длительность

        self.table.setColumnWidth(3, filesize_before)  # Размер до

        self.table.setColumnWidth(4, filesize_after)  # Размер после

        self.table.setColumnWidth(5, date_of_compression)  # Дата

        self.table.setColumnWidth(6, compression_options)  # Параметры
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.apply_theme(theme)
        self.load_history()

    def apply_theme(self, theme):
        """Применяет стиль тёмной, светлой, синей, зелёной, жёлтой или красной темы."""
        self.logger.info(f"Применение темы: {theme}")
        if theme == 'dark':
            self.setStyleSheet(dark_stylesheet)
        elif theme == 'light':
            self.setStyleSheet(light_stylesheet)
        elif theme == 'blue':
            self.setStyleSheet(blue_stylesheet)
        elif theme == 'green':
            self.setStyleSheet(green_stylesheet)
        elif theme == 'yellow':
            self.setStyleSheet(yellow_stylesheet)
        elif theme == 'red':
            self.setStyleSheet(red_stylesheet)
    def load_history(self):
        """Загружает историю из файла compression_history.json."""
        history_file = str(get_program_dir() / "compression_history.json")
        self.logger.info(f"Попытка загрузки истории из {history_file}")
        try:
            if not os.path.exists(history_file):
                self.logger.info("Файл истории не найден, создается пустой")
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                return

            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            self.table.setRowCount(len(history))
            for row, entry in enumerate(history):
                # Превью
                preview_item = QTableWidgetItem()
                preview_path = entry.get('preview_path')
                if preview_path and os.path.exists(preview_path):
                    pixmap = QPixmap(preview_path)
                    preview_item.setData(Qt.ItemDataRole.DecorationRole,
                                         pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
                else:
                    pixmap = QPixmap(100, 100)
                    pixmap.fill(QColor(128, 128, 128))  # Серый цвет для заглушки
                    preview_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
                self.table.setItem(row, 0, preview_item)
                self.table.setRowHeight(row, 100)

                # Имя файла
                self.table.setItem(row, 1, QTableWidgetItem(entry.get('filename', 'Неизвестно')))

                # Длительность
                duration = entry.get('duration', 0)
                duration_str = f"{int(duration // 3600):02d}:{int((duration % 3600) // 60):02d}:{int(duration % 60):02d}"
                self.table.setItem(row, 2, QTableWidgetItem(duration_str))

                # Размеры
                self.table.setItem(row, 3, QTableWidgetItem(self.format_size(entry.get('original_size', 0))))
                self.table.setItem(row, 4, QTableWidgetItem(self.format_size(entry.get('compressed_size', 0))))

                # Дата
                self.table.setItem(row, 5, QTableWidgetItem(entry.get('compression_date', 'Неизвестно')))

                # Параметры
                params = entry.get('parameters', {})
                params_str = (f"Кодек: {params.get('codec', '-')}, "
                              f"Битрейт: {params.get('bitrate', '-')}, "
                              f"FPS: {params.get('fps', '-')}, "
                              f"Аудио: {params.get('audio_codec', '-')}, "
                              f"А/битрейт: {params.get('audio_bitrate', '-')}")
                self.table.setItem(row, 6, QTableWidgetItem(params_str))

        except json.JSONDecodeError as e:
            self.logger.error(f"Файл истории поврежден: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Файл истории поврежден: {str(e)}")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки истории: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю: {str(e)}")

    def format_size(self, size):
        """Форматирует размер файла в удобочитаемый вид."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

class UpdateDialog(QDialog):
    """Окно с прогресс-баром для обновления."""
    def __init__(self, parent=None, theme='light'):
        super().__init__(parent)
        self.setWindowTitle("Обновление программы")
        self.setFixedSize(300, 100)
        self.setModal(True)

        layout = QVBoxLayout()
        self.label = QLabel("Установка обновления...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        # Применяем стиль
        self.apply_theme(theme)

    def apply_theme(self, theme):
        """Применяет стиль тёмной, светлой, синей, зелёной, жёлтой или красной темы."""
        if theme == 'dark':
            self.setStyleSheet(dark_stylesheet)
        elif theme == 'light':
            self.setStyleSheet(light_stylesheet)
        elif theme == 'blue':
            self.setStyleSheet(blue_stylesheet)
        elif theme == 'green':
            self.setStyleSheet(green_stylesheet)
        elif theme == 'yellow':
            self.setStyleSheet(yellow_stylesheet)
        elif theme == 'red':
            self.setStyleSheet(red_stylesheet)

    def set_progress(self, value):
        """Обновляет прогресс-бар."""
        self.progress_bar.setValue(value)

    def set_text(self, text):
        """Обновляет текст в окне."""
        self.label.setText(text)

class StatsDialog(QDialog):
    def __init__(self, parent=None, theme='blue'):
        super().__init__(parent)
        self.setWindowTitle("Статистика сжатия")
        self.setFixedSize(300, 200)
        self.setModal(True)
        self.logger = setup_license_logging()
        self.logger.info("Инициализация окна статистики")

        layout = QVBoxLayout()
        self.stats_label = QLabel("Загрузка статистики...")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)
        self.setLayout(layout)

        # Применяем тему
        self.apply_theme(theme)
        self.load_stats()

    def apply_theme(self, theme):
        """Применяет стиль тёмной, светлой, синей, зелёной, жёлтой или красной темы."""
        self.logger.info(f"Применение темы: {theme}")
        if theme == 'dark':
            self.setStyleSheet(dark_stylesheet)
            self.stats_label.setStyleSheet("color: #000000; background: transparent;")
        elif theme == 'light':
            self.setStyleSheet(light_stylesheet)
            self.stats_label.setStyleSheet("color: #000000; background: transparent;")
        elif theme == 'blue':
            self.setStyleSheet(blue_stylesheet)
            self.stats_label.setStyleSheet("color: #1e3a5f; background: transparent;")
        elif theme == 'green':
            self.setStyleSheet(green_stylesheet)
            self.stats_label.setStyleSheet("color: #1e4620; background: transparent;")
        elif theme == 'yellow':
            self.setStyleSheet(yellow_stylesheet)
            self.stats_label.setStyleSheet("color: #4a3c00; background: transparent;")
        elif theme == 'red':
            self.setStyleSheet(red_stylesheet)
            self.stats_label.setStyleSheet("color: #460000; background: transparent;")
        self.stats_label.setAutoFillBackground(False)  # Отключаем заливку фона

    def load_stats(self):
        """Загружает статистику из файла stats.json."""
        stats_file = str(get_program_dir() / "stats.json")
        self.logger.info(f"Попытка загрузки статистики из {stats_file}")
        try:
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                total_videos = stats.get('total_videos', 0)
                total_time = stats.get('total_time', 0)
                total_saved = stats.get('total_saved', 0)
                total_compression_time = stats.get('total_compression_time', 0)
                self.logger.info(f"Статистика загружена: видео={total_videos}, время={total_time}, "
                                 f"сэкономлено={total_saved}, время сжатия={total_compression_time}")
                self.stats_label.setText(
                    f"Всего сжато видео: {total_videos}\n"
                    f"Общее время сжатых видео: {self.format_time(total_time)}\n"
                    f"Экономия места: {self.format_size(total_saved)}\n"
                    f"Общее время сжатия: {self.format_time(total_compression_time)}"
                )
            else:
                self.logger.info("Файл статистики не найден, отображаем начальные значения")
                self.stats_label.setText(
                    "Всего сжато видео: 0\n"
                    "Общее время сжатых видео: 00:00:00\n"
                    "Экономия места: 0 B\n"
                    "Общее время сжатия: 00:00:00"
                )
        except Exception as e:
            self.logger.error(f"Ошибка загрузки статистики: {str(e)}")
            self.stats_label.setText("Ошибка загрузки статистики")

    def format_time(self, seconds):
        """Форматирует время в HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def format_size(self, size):
        """Форматирует размер файла в удобочитаемый вид (B, KB, MB, GB)."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"


class VideoCompressor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = setup_license_logging()
        self.presets_file = "presets.json"
        self.current_preset = None
        self.current_theme = 'light'
        self.start_time = None  # Время начала сжатия
        self.original_size = None  # Размер исходного файла

        self.current_files = []  # Список выбранных файлов
        self.processed_files = 0  # Счётчик обработанных файлов
        self.failed_files = []  # Список файлов с ошибками
        self.total_files = 0  # Общее количество файлов

        self.compression_stats = []
        self.is_multiple_files = False
        self.compression_stats = []  # Для хранения статистики при обработке нескольких файлов


        self.settings = QSettings("MyCompany", "VideoCompressor")
        self.output_folder = self.settings.value("output_folder", "")  # Загружаем сохранённую папку

        self.init_ui()
        self.load_presets()
        self.load_settings()
        self.background_image = QPixmap()
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.on_image_downloaded)
        self.image_urls = [
            "https://i.imgur.com/S721eIZ.png",
            "https://i.imgur.com/J2Ey9ce.png",
            "https://i.imgur.com/MswgFY3.png"
        ]
        self.cache_dir = os.path.join(os.path.dirname(__file__), "backs")
        os.makedirs(self.cache_dir, exist_ok=True)  # Создаем папку, если её нет

        self.music_dir = "nices"
        self.current_track_index = 0
        self.tracks = []
        self.music_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.music_player.setAudioOutput(self.audio_output)

        self.init_music()
        self.init_music_ui()

        self.download_background_image()
        self.background_opacity = 0.13
        # Проверяем аргументы командной строки
        if len(sys.argv) > 1:
            self.current_files = [f for f in sys.argv[1:] if f.lower().endswith('.mp4')]
            if self.current_files:
                self.is_multiple_files = True
                self.compress_multiple_videos()
        self.update_context_menu_action()
        # Проверка обновлений
        self.check_for_updates()



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
        return [f for f in os.listdir(self.cache_dir) if f.endswith(('.png', '.jpg', '.jpeg', 'gif'))]



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

    def init_music_ui(self):
        """Добавляет элементы управления музыкой в тулбар"""
        toolbar = self.findChild(QToolBar)

        # Кнопка паузы
        self.pause_action = QAction("⏯", self)
        self.pause_action.triggered.connect(self.toggle_music)
        toolbar.addAction(self.pause_action)

        # Кнопка следующего трека
        self.next_action = QAction("⏭", self)
        self.next_action.triggered.connect(self.next_track)
        toolbar.addAction(self.next_action)

    def init_music(self):
        """Инициализирует музыкальные треки"""
        # Убедимся, что папка существует
        if not os.path.exists(self.music_dir):
            #print(f"Папка {self.music_dir} не существует. Создаём...")
            os.makedirs(self.music_dir, exist_ok=True)

        track_url = "https://github.com/sharkye1/Szhimatar/raw/refs/heads/main/nain.mp3"
        track_path = self.download_music(track_url)

        # Формируем список треков
        self.tracks = [f for f in os.listdir(self.music_dir) if f.endswith('.mp3')]
        if track_path and os.path.exists(track_path):
            self.tracks.insert(0, os.path.basename(track_path))  # Используем только имя файла
            #print(f"Трек добавлен в список: {track_path}")

    def download_music(self, url):
        """Скачивает музыкальный трек с прямой ссылки"""
        try:
            filename = "nain.mp3"  # Имя файла
            filepath = os.path.join(self.music_dir, filename)

            if not os.path.exists(filepath):
                # Скачиваем файл напрямую
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    #print(f"Трек скачан: {filepath}")
                else:
                    print(f"Ошибка: сервер вернул код {response.status_code}")
                    return None
            return filepath
        except Exception as e:
            #print(f"Ошибка загрузки музыки: {e}")
            return None

    def play_music(self):
        """Начинает воспроизведение музыки"""
        if self.tracks:
            track = os.path.join(self.music_dir, self.tracks[self.current_track_index])
            #print(f"Попытка воспроизвести трек: {track}")
            self.music_player.setSource(QUrl.fromLocalFile(track))
            self.audio_output.setVolume(1.0)  # Максимальная громкость
            self.music_player.play()
            #print("Музыка должна играть...")
        #else:
            #print("Нет доступных треков для воспроизведения.")

    def toggle_music(self):
        """Пауза/воспроизведение"""
        if self.music_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.music_player.pause()
        else:
            self.music_player.play()

    def next_track(self):
        """Переключает на следующий трек"""
        if self.tracks:
            self.current_track_index = (self.current_track_index + 1) % len(self.tracks)
            self.play_music()

    def generate_preview(self, video_path):
        """Генерирует превью из середины видео и возвращает путь к файлу."""
        try:
            preview_dir = get_program_dir() / "previews"
            os.makedirs(preview_dir, exist_ok=True)
            preview_filename = f"{os.path.basename(video_path).replace('.mp4', '')}_preview.jpg"
            preview_path = preview_dir / preview_filename

            duration = self.get_video_duration()
            mid_time = duration / 2
            cmd = [
                'ffmpeg', '-y', '-i', video_path, '-ss', str(mid_time),
                '-frames:v', '1', '-q:v', '2', '-vf', 'scale=320:180',
                str(preview_path)
            ]
            self.logger.info(f"Генерация превью для {video_path}: {' '.join(cmd)}")
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(preview_path):
                self.logger.info(f"Превью создано: {preview_path}")
                return str(preview_path)
            else:
                self.logger.error(f"Превью не создано для {video_path}")
                return None
        except Exception as e:
            self.logger.error(f"Ошибка генерации превью для {video_path}: {str(e)}")
            return None

    def init_ui(self):
        self.setWindowTitle("Сжиматор на NVENC")
        self.setGeometry(100, 100, 800, 700)

        toolbar = QToolBar("Панель инструментов")

        '''class ToolBarArea(enum.Flag):
            LeftToolBarArea = ...  # type: Qt.ToolBarArea
            RightToolBarArea = ...  # type: Qt.ToolBarArea
            TopToolBarArea = ...  # type: Qt.ToolBarArea
            BottomToolBarArea = ...  # type: Qt.ToolBarArea
            AllToolBarAreas = ...  # type: Qt.ToolBarArea
            NoToolBarArea = ...  # type: Qt.ToolBarArea'''
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Для темы:
        self.theme_action = QAction("☀️Тема 🌙", self)
        self.theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.theme_action)
        # Для записей в реестре:
        self.context_menu_action = QAction("", self)
        self.context_menu_action.triggered.connect(self.toggle_context_menu)
        toolbar.addAction(self.context_menu_action)

        stats_action = QAction("📊 Статистика 📊", self)
        stats_action.triggered.connect(self.open_stats_dialog)
        toolbar.addAction(stats_action)

        history_action = QAction("📜 История сжатия 📜", self)
        history_action.triggered.connect(self.open_history_dialog)
        toolbar.addAction(history_action)

        self.file_label = QLabel("📷 Выбери видеофайл: 📷")
        self.file_btn = QPushButton("📂 Обзор в проводнике... 📂")
        self.file_btn.clicked.connect(self.select_file)

        # Обрезка видео с двумя ползунками
        '''self.trim_label = QLabel("✂️ Обрезка видео: ✂️")
        self.range_slider = RangeSlider()
        self.range_slider.setMinimum(0)
        self.range_slider.setMaximum(1000)
        self.range_slider.setMinimumValue(0)
        self.range_slider.setMaximumValue(1000)
        self.range_slider.valueChanged.connect(self.update_trim_times)'''

        # Выбор папки вывода
        self.output_folder_label = QLabel("🗂️ Папка для сохранения: 🗂️")
        self.output_folder_btn = QPushButton("📁 Выбрать папку... 📁")
        self.output_folder_btn.clicked.connect(self.select_output_folder)
        self.output_folder_display = QLabel(
            self.output_folder if self.output_folder else "По умолчанию (папка исходного файла)")
        self.output_folder_display.setStyleSheet("font-style: italic; color: #888;")

        # Добавляем галочку для сохранения в директории исходного файла
        self.save_in_source_dir_checkbox = QCheckBox("Сохранять в директории исходного файла")
        self.save_in_source_dir_checkbox.setChecked(True)  # По умолчанию выключена

        self.separator_output = self.create_separator()

        # Настройки сжатия
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1488x1337"])

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

        '''speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Скорость видео:"))
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_spin)'''

        # Сами пресеты
        self.presets_combo = QComboBox()
        self.presets_combo.currentIndexChanged.connect(self.apply_preset)
        self.save_preset_btn = QPushButton("💾 Сохранить пресет 💾")
        self.save_preset_btn.clicked.connect(self.save_preset)
        self.delete_preset_btn = QPushButton("🗑️ Удалить пресет 🗑️")
        self.delete_preset_btn.clicked.connect(self.delete_preset)

        # Горизонтальная компоновка для пресетов
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("📓 Пресеты: 📓"))
        presets_layout.addWidget(self.presets_combo)
        presets_layout.addWidget(self.save_preset_btn)
        presets_layout.addWidget(self.delete_preset_btn)

        # Элементы для отображения размера
        '''self.size_label = QLabel("Примерный размер выходного файла: ")
        self.size_value = QLabel("0.00 MB")
        self.size_value.setStyleSheet("font-weight: bold;")'''

        '''size_layout = QHBoxLayout()
        size_layout.addWidget(self.size_label)
        size_layout.addWidget(self.size_value)'''



        # Прогресс и логи
        self.progress_bar = QProgressBar()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # Кнопка запуска
        self.compress_btn = QPushButton("🔥❤️ Сжать видео ❤️🔥")
        self.compress_btn.clicked.connect(self.start_compression)

        self.separator1 = self.create_separator()
        self.separator2 = self.create_separator()
        self.separator3 = self.create_separator()

        # Компоновка

        layout = QVBoxLayout()
        layout.addWidget(self.file_label)
        layout.addWidget(self.file_btn)
        layout.addWidget(self.separator1)
        layout.addWidget(QLabel("🎬 Кодек: 🎬"))
        layout.addWidget(self.codec_combo)
        layout.addWidget(QLabel("📊 Битрейт (Мбит/с): 📊"))
        layout.addLayout(bitrate_layout)
        layout.addWidget(QLabel("FPS:"))
        layout.addLayout(fps_layout)
        #layout.addLayout(speed_layout)
        layout.addWidget(self.separator2)
        layout.addWidget(QLabel("🎵 Аудиокодек: 🎵"))
        layout.addWidget(self.audio_codec_combo)  # Добавляем выбор аудиокодека
        layout.addWidget(QLabel("🔊 Битрейт аудио (кбит/с): 🔊"))
        layout.addLayout(audio_bitrate_layout)  # Добавляем горизонтальную компоновку для битрейта аудио

        # Компоновка для обрезки

        '''trim_layout = QHBoxLayout()
        trim_layout.addWidget(self.trim_label)
        trim_layout.addWidget(self.start_time_display)
        trim_layout.addWidget(self.end_time_display)
        trim_layout.addWidget(self.start_frame_label)
        trim_layout.addWidget(self.end_frame_label)
        layout.addLayout(trim_layout)
        layout.addWidget(self.start_slider)
        layout.addWidget(self.end_slider)'''

        layout.addWidget(self.separator3)
        layout.addWidget(self.output_folder_label)
        layout.addWidget(self.output_folder_btn)
        layout.addWidget(self.output_folder_display)

        layout.addWidget(self.save_in_source_dir_checkbox)  # Добавляем галочку в интерфейс

        layout.addWidget(self.create_separator())
        #layout.addWidget(self.presets_combo)
        #layout.addLayout(preset_buttons_layout)
        layout.addLayout(presets_layout)
        layout.addWidget(self.progress_bar)
        #layout.addLayout(size_layout)
        layout.addWidget(self.log_area)
        layout.addWidget(self.compress_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.apply_theme(self.current_theme)

    def open_history_dialog(self):
        """Открывает диалоговое окно истории сжатия."""
        self.logger.info("Открытие окна истории сжатия")
        dialog = HistoryDialog(self, self.current_theme)
        dialog.exec()

    def open_stats_dialog(self):
        """Открывает диалоговое окно статистики."""
        self.logger = setup_license_logging()
        self.logger.info("Открытие окна статистики")
        dialog = StatsDialog(self, self.current_theme)
        dialog.exec()

    def update_stats(self, time_compressed, space_saved, compression_time):
        """Обновляет статистику в файле stats.json."""
        self.logger.info("Обновление статистики")
        stats_file = str(get_program_dir() / "stats.json")
        try:
            if not os.access(get_program_dir(), os.W_OK):
                self.logger.error(f"Нет прав на запись в директорию {get_program_dir()}")
                return

            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {'total_videos': 0, 'total_time': 0, 'total_saved': 0, 'total_compression_time': 0}
                self.logger.info(f"Создан новый файл статистики: {stats_file}")

            stats['total_videos'] += 1
            stats['total_time'] += time_compressed
            stats['total_saved'] += space_saved
            stats['total_compression_time'] += compression_time

            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=4)
            self.logger.info(f"Статистика обновлена: видео={stats['total_videos']}, "
                             f"время={stats['total_time']}, сэкономлено={stats['total_saved']}, "
                             f"время сжатия={stats['total_compression_time']}")
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении статистики: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить статистику: {str(e)}")

    def toggle_context_menu(self):
        """Добавляет или удаляет команду в контекстное меню."""
        logger = setup_license_logging()
        logger.info("Нажата кнопка управления контекстным меню")
        if check_context_menu():
            # Команда есть, удаляем
            logger.info("Попытка удаления команды")
            if is_admin():
                if remove_context_menu():
                    QMessageBox.information(self, "Успех", "Опция 'Сжать сжиматором' удалена из контекстного меню!")
                    self.update_context_menu_action()
                else:
                    logger.error("Не удалось удалить команду")
                    QMessageBox.critical(self, "Ошибка",
                                         "Не удалось удалить опцию. Убедитесь, что программа запущена от имени администратора, и проверьте update_log.txt.")
            else:
                logger.info("Требуются права администратора для удаления")
                msg = QMessageBox(self)
                msg.setWindowTitle("Требуются права администратора")
                msg.setText("Для удаления опции 'Сжать сжиматором' нужны права администратора.\n"
                            "Перезапустить программу с правами администратора?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    try:
                        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
                                                            f'"{os.path.abspath(__file__)}"', None, 1)
                        sys.exit(0)
                    except Exception as e:
                        logger.error(f"Ошибка запуска с правами администратора: {e}")
                        QMessageBox.critical(self, "Ошибка", f"Не удалось перезапустить программу: {e}")
        else:
            # Команды нет, добавляем
            logger.info("Попытка добавления команды")
            if is_admin():
                if add_context_menu():
                    QMessageBox.information(self, "Успех", "Опция 'Сжать сжиматором' добавлена в контекстное меню!")
                    self.update_context_menu_action()
                else:
                    logger.error("Не удалось добавить команду")
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить опцию. Проверьте update_log.txt.")
            else:
                logger.info("Требуются права администратора для добавления")
                msg = QMessageBox(self)
                msg.setWindowTitle("Требуются права администратора")
                msg.setText("Для добавления опции 'Сжать сжиматором' нужны права администратора.\n"
                            "Перезапустить программу с правами администратора?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if msg.exec() == QMessageBox.StandardButton.Yes:
                    try:
                        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
                                                            f'"{os.path.abspath(__file__)}"', None, 1)
                        sys.exit(0)
                    except Exception as e:
                        logger.error(f"Ошибка запуска с правами администратора: {e}")
                        QMessageBox.critical(self, "Ошибка", f"Не удалось перезапустить программу: {e}")

    def check_for_updates(self):
        """Вызывает проверку обновлений."""
        check_for_updates(self)

    def update_context_menu_action(self):
        """Обновляет текст кнопки в тулбаре."""
        if check_context_menu():
            self.context_menu_action.setText("Удалить из контекстного меню (бета)")
        else:
            self.context_menu_action.setText("Добавить в контекстное меню (бета)")

    def create_separator(self):
        """Создаёт горизонтальный разделитель."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator

    def toggle_theme(self):
        themes = ['dark', 'light', 'blue', 'green', 'yellow', 'red']  # Список доступных тем
        current_index = themes.index(self.current_theme)
        next_index = (current_index + 1) % len(themes)  # Переход к следующей теме
        self.current_theme = themes[next_index]
        self.apply_theme(self.current_theme)
        self.logger.info(f"Тема изменена на: {self.current_theme}")



    # Добавить новый метод для запуска сжатия:
    def start_compression(self):
        """Определяет, какой сценарий использовать (один файл или несколько)"""
        if self.current_files:
            self.is_multiple_files = True
            self.compress_multiple_videos()
        elif hasattr(self, 'current_file'):
            self.is_multiple_files = False
            self.compress_video()
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите файл(ы) для сжатия!")

    def select_file(self):
        """Выбирает один или несколько видеофайлов и обновляет интерфейс."""
        logger = setup_license_logging()
        logger.info("Запуск выбора файлов")

        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите видеофайл(ы)",
            self.last_dir,
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )

        if not files:
            logger.info("Файлы не выбраны")
            self.file_label.setText("📷 Выбери видеофайл: 📷")
            self.current_files = []
            return

        logger.info(f"Выбрано файлов: {len(files)}")
        self.current_files = files
        self.last_dir = os.path.dirname(files[0])
        logger.info(f"Обновлена последняя директория: {self.last_dir}")

        if len(files) == 1:
            self.current_file = files[0]
            self.file_label.setText(f"Выбран файл: {os.path.basename(files[0])}")
            logger.info(f"Выбран один файл: {files[0]}")
        else:
            self.file_label.setText(f"Выбрано файлов: {len(files)}")
            logger.info(f"Выбрано несколько файлов: {', '.join([os.path.basename(f) for f in files])}")

    def format_time(self, seconds):
        """Форматирует время в HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def get_frame_at_time(self, time_str):
        if not self.current_file:
            return QPixmap()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        cmd = [
            'ffmpeg',
            '-ss', time_str,
            '-i', self.current_file,
            '-frames:v', '1',
            '-q:v', '2',
            temp_file.name,
            '-y'  # Перезаписывать файл
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pixmap = QPixmap(temp_file.name)
        os.remove(temp_file.name)
        return pixmap

    def update_start_frame(self):
        time_str = self.start_time_edit.text()
        pixmap = self.get_frame_at_time(time_str)
        self.start_frame_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def update_end_frame(self):
        time_str = self.end_time_edit.text()
        pixmap = self.get_frame_at_time(time_str)
        self.end_frame_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def compress_video(self):
        logger = setup_license_logging()
        logger.info("Начало сжатия видео")

        if not hasattr(self, 'current_file'):
            logger.error("Файл для сжатия не выбран")
            QMessageBox.warning(self, "Ошибка", "Выберите файл для сжатия!")
            return

        try:
            # Получаем исходный размер файла
            original_size = os.path.getsize(self.current_file)
            logger.info(f"Исходный размер файла {self.current_file}: {self.format_size(original_size)}")

            self.original_size = original_size
            self.start_time = time.time()
            logger.info(f"Время начала сжатия: {self.start_time}")

            output_file = self.get_output_path()
            codec = "hevc_nvenc" if self.codec_combo.currentText().startswith("hevc") else "h264_nvenc"
            bitrate = f"{self.bitrate_spin.value()}M"
            fps = self.fps_spin.value()
            audio_codec = self.audio_codec_combo.currentText()
            audio_bitrate = f"{self.audio_bitrate_spin.value()}k"
            speed = self.speed_spin.value()
            input_file = f'"{self.current_file}"'
            output_file = output_file.replace('\\', '/')
            output_file = f'"{output_file}"'

            logger.info(f"Параметры сжатия: codec={codec}, bitrate={bitrate}, fps={fps}, "
                        f"audio_codec={audio_codec}, audio_bitrate={audio_bitrate}, speed={speed}")

            cmd = [
                'ffmpeg',
                '-y',
                '-hwaccel', 'cuda',
                '-i', input_file,
                '-c:v', codec,
                '-preset', 'p7',
                '-b:v', bitrate,
                '-maxrate', f"{self.bitrate_spin.value() + 1}M",
                '-bufsize', f"{self.bitrate_spin.value() * 2}M",
                '-r', str(fps),
                '-filter:v', f'setpts={1 / speed}*PTS',
                '-c:a', audio_codec,
                '-b:a', audio_bitrate,
                output_file
            ]



            logger.info(f"Команда FFmpeg: {' '.join(cmd)}")

            # Проверяем существование FFmpeg
            try:
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.info("FFmpeg доступен")
            except FileNotFoundError:
                logger.error("FFmpeg не найден в системе")
                QMessageBox.critical(self, "Ошибка", "FFmpeg не найден. Убедитесь, что он установлен.")
                return

            # Запускаем процесс
            self.process = QProcess()
            self.process.readyReadStandardError.connect(self.handle_log)
            self.process.finished.connect(self.on_finish)
            try:
                self.process.startCommand(' '.join(cmd))
                logger.info("Процесс FFmpeg запущен")
            except Exception as e:
                logger.error(f"Ошибка запуска процесса FFmpeg: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось запустить FFmpeg: {str(e)}")
                return

            # Проверяем, запустился ли процесс
            if self.process.state() != QProcess.ProcessState.Running:
                logger.error(f"Процесс не запустился. Код ошибки: {self.process.error()}")
                QMessageBox.critical(self, "Ошибка", "Не удалось запустить процесс сжатия.")
                return

            # Таймер для обновления прогресса
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_progress)
            self.timer.start(nkirill)
            logger.info("Таймер прогресса запущен")

        except Exception as e:
            logger.error(f"Ошибка в процессе сжатия: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сжатии: {str(e)}")
            self.progress_bar.setValue(0)
            if hasattr(self, 'timer'):
                self.timer.stop()

    def compress_multiple_videos(self):
        """Обрабатывает все выбранные файлы, показывая отчет только в конце."""
        if not self.current_files:
            QMessageBox.warning(self, "Ошибка", "Выберите файлы для сжатия!")
            return

        self.processed_files = 0
        self.failed_files = []
        self.total_files = len(self.current_files)
        self.compression_stats = []  # Очищаем статистику перед началом
        self.is_multiple_files = True  # Устанавливаем режим обработки нескольких файлов

        self.progress_bar.setMaximum(100)  # Устанавливаем максимум в 100%
        self.progress_bar.setValue(0)
        self.log_area.clear()

        progress_per_file = 100 / self.total_files  # Процент прогресса на один файл

        for index, file in enumerate(self.current_files):
            try:
                self.current_file = file
                self.file_label.setText(
                    f"Обработка файла {index + 1}/{self.total_files}: "
                    f"{os.path.basename(file)}"
                )
                QApplication.processEvents()  # Обновляем GUI

                # Запускаем сжатие текущего файла
                self.original_size = os.path.getsize(self.current_file)
                self.start_time = time.time()
                self.compress_video()

                # Ожидаем завершения процесса
                while self.process.state() == QProcess.ProcessState.Running:
                    QApplication.processEvents()
                    time.sleep(0.1)

                self.processed_files += 1
                self.progress_bar.setValue(int(self.processed_files * progress_per_file))

            except Exception as e:
                self.failed_files.append((file, str(e)))
                self.log_area.append(f"Ошибка при обработке {file}: {e}")

        # Формируем итоговый отчет
        '''report = (
            f"Обработка завершена!\n\n"
            f"Успешно: {self.processed_files}/{self.total_files}\n"
            f"Ошибки: {len(self.failed_files)}\n"
        )

        if self.failed_files:
            report += "\nФайлы с ошибками:\n" + "\n".join(
                [f"{os.path.basename(f[0])}: {f[1]}" for f in self.failed_files]
            )

        if self.compression_stats:
            report += "\n\nСтатистика сжатия:\n" + "\n".join(self.compression_stats)

        QMessageBox.information(self, "Отчёт", report)
        self.current_files = []  # Очищаем список файлов
        self.is_multiple_files = False  # Сбрасываем режим'''

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
        self.logger.info("Завершение сжатия видео")
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        self.progress_bar.setValue(100)

        try:
            output_file = self.get_output_path()
            self.logger.info(f"Проверка выходного файла: {output_file}")
            if not os.path.exists(output_file):
                self.logger.error(f"Выходной файл {output_file} не создан")
                self.progress_bar.setValue(0)
                if self.is_multiple_files:
                    self.failed_files.append((self.current_file, "Выходной файл не создан"))
                QMessageBox.critical(self, "Ошибка", f"Выходной файл {output_file} не создан")
                return

            end_time = time.time()
            elapsed_time = end_time - self.start_time
            self.logger.info(f"Время выполнения сжатия: {elapsed_time:.2f} секунд")

            compressed_size = os.path.getsize(output_file)
            self.logger.info(f"Размер сжатого файла: {self.format_size(compressed_size)}")

            compression_ratio = (1 - (compressed_size / self.original_size)) * 100
            space_saved = self.original_size - compressed_size
            self.logger.info(f"Экономия места: {self.format_size(space_saved)}")

            video_duration = self.get_video_duration()
            self.logger.info(f"Длительность видео: {video_duration} секунд")

            preview_path = self.generate_preview(self.current_file)
            self.logger.info(f"Путь к превью: {preview_path}")
            self.update_stats(video_duration, space_saved, elapsed_time)

            # Сохранение в историю
            history_file = str(get_program_dir() / "compression_history.json")
            self.logger.info(f"Попытка записи в историю: {history_file}")
            try:
                if not os.path.exists(history_file):
                    self.logger.info(f"Файл истории не существует, создается новый: {history_file}")
                    with open(history_file, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                    history = []
                else:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                    self.logger.info(f"История загружена, записей: {len(history)}")

                history_entry = {
                    'filename': os.path.basename(self.current_file),
                    'video_path': self.current_file,
                    'preview_path': preview_path,
                    'duration': video_duration,
                    'original_size': self.original_size,
                    'compressed_size': compressed_size,
                    'compression_date': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'parameters': {
                        'codec': self.codec_combo.currentText(),
                        'bitrate': f"{self.bitrate_spin.value()}M",
                        'fps': self.fps_spin.value(),
                        'audio_codec': self.audio_codec_combo.currentText(),
                        'audio_bitrate': f"{self.audio_bitrate_spin.value()}k"
                    }
                }
                history.append(history_entry)

                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=4)
                self.logger.info(f"Запись добавлена в историю: {os.path.basename(self.current_file)}")

            except json.JSONDecodeError as e:
                self.logger.error(f"Файл истории поврежден: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Файл истории поврежден: {str(e)}")
                return
            except PermissionError as e:
                self.logger.error(f"Ошибка доступа к файлу истории: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Нет прав для записи в файл истории: {str(e)}")
                return
            except Exception as e:
                self.logger.error(f"Ошибка записи в историю: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить историю: {str(e)}")
                return

            stats_message = (
                f"Файл: {os.path.basename(self.current_file)}\n"
                f"Исходный размер: {self.format_size(self.original_size)}\n"
                f"Сжатый размер: {self.format_size(compressed_size)}\n"
                f"Сжатие: {compression_ratio:.2f}%\n"
                f"Время выполнения: {elapsed_time:.2f} секунд\n"
            )

            if self.is_multiple_files:
                self.compression_stats.append(stats_message)
            else:
                self.progress_bar.setValue(0)
                QMessageBox.information(self, "Статистика сжатия", stats_message)

        except Exception as e:
            self.logger.error(f"Критическая ошибка в методе on_finish: {str(e)}")
            self.progress_bar.setValue(0)
            if self.is_multiple_files:
                self.failed_files.append((self.current_file, str(e)))
            QMessageBox.critical(self, "Ошибка", f"Критическая ошибка при завершении сжатия: {str(e)}")

    def get_output_path(self):
        """Возвращает путь для сохранения сжатого файла с учетом состояния галочки."""
        base, ext = os.path.splitext(os.path.basename(self.current_file))
        output_filename = f"{base}_compressed{ext}"

        if self.save_in_source_dir_checkbox.isChecked():
            # Сохраняем в директории исходного файла, если галочка активна
            return os.path.join(os.path.dirname(self.current_file), output_filename)
        else:
            # Иначе используем output_folder, если она задана, или директорию исходного файла
            if self.output_folder:
                return os.path.join(self.output_folder, output_filename)
            else:
                return os.path.join(os.path.dirname(self.current_file), output_filename)

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
        """Сохраняет настройки, включая состояние галочки."""
        settings = {
            'last_dir': self.last_dir,
            'theme': self.current_theme
        }
        with open('.env', 'w') as f:
            json.dump(settings, f)
        # Сохраняем состояние галочки
        self.settings.setValue("save_in_source_dir", self.save_in_source_dir_checkbox.isChecked())

    def load_settings(self):
        """Загружает настройки, включая состояние галочки."""
        try:
            with open('.env', 'r') as f:
                settings = json.load(f)
                self.last_dir = settings.get('last_dir', QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.HomeLocation))
                self.apply_theme(settings.get('theme', 'dark'))
        except FileNotFoundError:
            self.last_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
            self.apply_theme('dark')  # Изменено с 'light' на 'dark'
        self.save_in_source_dir_checkbox.setChecked(self.settings.value("save_in_source_dir", True, type=bool))


    def select_output_folder(self):
        """Позволяет пользователю выбрать папку для сохранения."""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения", self.output_folder)
        if folder:
            self.output_folder = folder
            self.output_folder_display.setText(self.output_folder)
            self.settings.setValue("output_folder", self.output_folder)  # Сохраняем выбранную папку

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
        """Применяет выбранную тему."""
        self.current_theme = theme
        if theme == 'dark':
            self.setStyleSheet(dark_stylesheet)
            self.theme_action.setText("🌙 Тёмная тема 🌙")
        elif theme == 'light':
            self.setStyleSheet(light_stylesheet)
            self.theme_action.setText("☀️ Светлая тема ☀️")
        elif theme == 'blue':
            self.setStyleSheet(blue_stylesheet)
            self.theme_action.setText("🔵 Синяя тема 🔵")
        elif theme == 'green':
            self.setStyleSheet(green_stylesheet)
            self.theme_action.setText("🟢 Зелёная тема 🟢")
        elif theme == 'yellow':
            self.setStyleSheet(yellow_stylesheet)
            self.theme_action.setText("🟡 Жёлтая тема 🟡")
        elif theme == 'red':
            self.setStyleSheet(red_stylesheet)
            self.theme_action.setText("🔴 Красная тема 🔴")
        self.logger.info(f"Применена тема: {theme}")
        # Обновление темы для диалоговых окон, если они открыты
        if hasattr(self, 'history_dialog') and self.history_dialog:
            self.history_dialog.apply_theme(theme)
        if hasattr(self, 'stats_dialog') and self.stats_dialog:
            self.stats_dialog.apply_theme(theme)
        if hasattr(self, 'update_dialog') and self.update_dialog:
            self.update_dialog.apply_theme(theme)
    """Конец метода VideoCompressor"""

def download_license_files():
    """Скачивает лицензионные соглашения, если их нет в папке."""
    logger = setup_license_logging()

    # Ссылки на raw-версии лицензионных соглашений
    license_urls = {
        "ЛИЦЕНЗИОННОЕ СОГЛАШЕНИЕ НА ИСПОЛЬЗОВАНИЕ ПРОГРАММЫ.docx": "https://github.com/sharkye1/Szhimatar/raw/refs/heads/main/%D0%9B%D0%98%D0%A6%D0%95%D0%9D%D0%97%D0%98%D0%9E%D0%9D%D0%9D%D0%9E%D0%95%20%D0%A1%D0%9E%D0%93%D0%9B%D0%90%D0%A8%D0%95%D0%9D%D0%98%D0%95%20%D0%9D%D0%90%20%D0%98%D0%A1%D0%9F%D0%9E%D0%9B%D0%AC%D0%97%D0%9E%D0%92%D0%90%D0%9D%D0%98%D0%95%20%D0%9F%D0%A0%D0%9E%D0%93%D0%A0%D0%90%D0%9C%D0%9C%D0%AB.docx",
        "LICENSE AGREEMENT FOR THE USE OF THE PROGRAM.docx": "https://github.com/sharkye1/Szhimatar/raw/refs/heads/main/LICENSE%20AGREEMENT%20FOR%20THE%20USE%20OF%20THE%20PROGRAM.docx"
    }

    # Путь к текущей директории (где находится main.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    for filename, url in license_urls.items():
        file_path = os.path.join(current_dir, filename)

        # Проверяем, существует ли файл
        if not os.path.exists(file_path):
            try:
                # Скачиваем файл
                response = requests.get(url)
                response.raise_for_status()  # Проверяем, что запрос успешен

                # Сохраняем файл в текущую директорию
                with open(file_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"Файл {filename} успешно скачан в {current_dir}")
            except requests.RequestException as e:
                logger.error(f"Ошибка при скачивании {filename}: {e}")



def check_context_menu():
    """Проверяет наличие команды в реестре."""
    logger = setup_license_logging()
    progid = get_mp4_progid()
    key_path = f"{progid}\\shell\\CompressWithSzhimatar"
    command_path = f"{key_path}\\command"
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path, 0, winreg.KEY_READ) as key:
            value = winreg.QueryValueEx(key, "")[0]
            if value != "Сжать сжиматором":
                logger.warning(f"Найден ключ {key_path}, но значение некорректно: {value}")
                return False
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, command_path, 0, winreg.KEY_READ) as key:
            command = winreg.QueryValueEx(key, "")[0]
            expected_start = sys.executable if getattr(sys, 'frozen', False) else f'"{sys.executable}"'
            if not command.startswith(expected_start):
                logger.warning(f"Найдена команда {command}, но она некорректна")
                return False
        logger.info(f"Команда 'Сжать сжиматором' найдена и корректна в {key_path}")
        return True
    except FileNotFoundError:
        logger.info(f"Команда 'Сжать сжиматором' не найдена в {key_path}")
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки реестра: {e}")
        return False


def get_mp4_progid():
    """Определяет ProgID для MP4."""
    logger = setup_license_logging()
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ".mp4", 0, winreg.KEY_READ) as key:
            progid = winreg.QueryValueEx(key, "")[0]
            if progid:
                try:
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid, 0, winreg.KEY_READ):
                        logger.info(f"Найден ProgID для MP4: {progid}")
                        return progid
                except FileNotFoundError:
                    logger.warning(f"Ветка {progid} не существует, используется mp4file")
                    return "mp4file"
            logger.warning("ProgID для MP4 пустой, используется mp4file")
            return "mp4file"
    except Exception as e:
        logger.error(f"Ошибка при определении ProgID для MP4: {e}")
        return "mp4file"


def add_context_menu():
    """Добавляет команду в контекстное меню."""
    logger = setup_license_logging()
    try:
        program_path = sys.executable if getattr(sys, 'frozen',
                                                 False) else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        logger.info(f"Путь к программе: {program_path}")

        progid = get_mp4_progid()
        key_path = f"{progid}\\shell\\CompressWithSzhimatar"

        with winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Сжать сжиматором")
            winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Player")
            logger.info(f"Создан ключ {key_path}")

        command_path = f"{key_path}\\command"
        with winreg.CreateKeyEx(winreg.HKEY_CLASSES_ROOT, command_path, 0,
                                winreg.KEY_SET_VALUE | winreg.KEY_WRITE) as key:
            command = f'{program_path} "%1"'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
            logger.info(f"Создана команда: {command}")

        if not check_context_menu():
            logger.error("Ошибка: запись в реестре создана, но не прошла проверку")
            return False

        os.system("taskkill /IM explorer.exe /F && start explorer.exe")
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления в реестр: {e}")
        return False
def remove_context_menu():
    """Удаляет команду 'Сжать сжиматором' из контекстного меню."""
    logger = setup_license_logging()
    logger.info("Попытка удаления команды из контекстного меню")
    try:
        progid = get_mp4_progid()
        logger.info(f"ProgID для MP4: {progid}")
        key_path = f"{progid}\\shell\\CompressWithSzhimatar"
        command_path = f"{key_path}\\command"
        logger.info(f"Проверка ключа: {key_path}")

        # Проверяем права администратора
        admin_status = is_admin()
        logger.info(f"Запуск с правами администратора: {admin_status}")

        # Проверяем наличие ключа
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path, 0, winreg.KEY_READ):
                logger.info(f"Ключ {key_path} существует")
        except FileNotFoundError:
            logger.info(f"Команда уже отсутствует в {key_path}")
            return True

        # Удаляем подключ command
        try:
            winreg.DeleteKeyEx(winreg.HKEY_CLASSES_ROOT, command_path, winreg.KEY_ALL_ACCESS, 0)
            logger.info(f"Подключ {command_path} удалён")
        except FileNotFoundError:
            logger.info(f"Подключ {command_path} не существует")
        except Exception as e:
            logger.error(f"Ошибка удаления подключа {command_path}: {e}")

        # Удаляем основной ключ
        winreg.DeleteKeyEx(winreg.HKEY_CLASSES_ROOT, key_path, winreg.KEY_ALL_ACCESS, 0)
        logger.info(f"Команда успешно удалена из {key_path}")

        # Перезапускаем проводник
        os.system("taskkill /IM explorer.exe /F && start explorer.exe")
        return True
    except FileNotFoundError:
        logger.info(f"Команда уже отсутствует в {key_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка удаления из реестра: {e}")
        return False

def get_app_data_path():
    """Возвращает путь к папке AppData\Roaming\Szhimatar."""
    return Path(os.getenv('APPDATA')) / "Szhimatar"

def get_program_dir():
    """Возвращает путь к папке программы."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(os.path.abspath(__file__)).parent

def is_admin():
    """Проверяет, запущена ли программа с правами администратора."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def prompt_add_context_menu(parent=None):
    """Предлагает добавить команду в контекстное меню."""
    logger = setup_license_logging()
    if not check_context_menu():
        if not is_admin():
            msg = QMessageBox(parent)
            msg.setWindowTitle("Требуются права администратора")
            msg.setText("Для добавления опции 'Сжать сжиматором' нужны права администратора.\n"
                        "Хотите перезапустить программу с правами администратора?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)

            if msg.exec() == QMessageBox.StandardButton.Yes:
                logger.info("Пользователь согласился на перезапуск с правами администратора")
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"',
                                                    None, 1)
                sys.exit(0)
            return

        msg = QMessageBox(parent)
        msg.setWindowTitle("Добавление функции")
        msg.setText("Хотите добавить опцию 'Сжать сжиматором' в контекстное меню для MP4-файлов?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            if add_context_menu():
                QMessageBox.information(parent, "Успех", "Опция 'Сжать сжиматором' добавлена!")
            else:
                QMessageBox.critical(parent, "Ошибка", "Не удалось добавить опцию. См. update_log.txt.")

if __name__ == "__main__":
    nkirill = 42
    download_license_files()
    app = QApplication(sys.argv)
    window = VideoCompressor()
    window.show()

    app.exec()
