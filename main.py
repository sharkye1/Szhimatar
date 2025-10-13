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
import shutil

import threading
import math
import urllib.request
from datetime import datetime

import json
import subprocess
from PyQt6.QtGui import QAction, QPixmap, QPainter, QColor, QDesktopServices
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QComboBox, QSlider,
                             QSpinBox, QTextEdit, QMessageBox, QProgressBar,
                             QToolBar, QFrame, QInputDialog, QDoubleSpinBox, QDialog,
                             QCheckBox, QTableWidgetItem, QTableWidget, QGridLayout,
                                )
from PyQt6.QtCore import Qt, QProcess, QStandardPaths, QTimer, QSettings, QUrl
from PyQt6.QtNetwork import (QNetworkAccessManager, QNetworkRequest, QNetworkReply,
                                )
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from PyQt6.QtCore import QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve
from PyQt6.QtWidgets import QSplashScreen, QGraphicsOpacityEffect  # Не обязательно, но для сравнения
#from PyQt6.QtGui import QGraphicsOpacityEffect

from styles import dark_stylesheet, light_stylesheet, blue_stylesheet,\
    green_stylesheet, yellow_stylesheet, red_stylesheet, midnight_soft_stylesheet

# Версия программы
__version__ = "v1.5.0"



if getattr(sys, 'frozen', False):
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


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
            update_dialog.start_download()  # Запускаем отсчет времени
            QApplication.processEvents()

            if getattr(sys, 'frozen', False):
                # Для .exe
                download_url = f"https://github.com/sharkye1/Szhimatar/releases/download/{latest_version}/Szhimatar.{latest_version.replace('v', '')}.exe"
                new_exe_name = f"Szhimatar.{latest_version.replace('v', '')}.exe"
                download_reply = network_manager.get(QNetworkRequest(QUrl(download_url)))

                def update_progress(bytes_received, bytes_total):
                    if bytes_total > 0:
                        update_dialog.update_progress(bytes_received, bytes_total)
                        QApplication.processEvents()

                while not download_reply.isFinished():
                    QApplication.processEvents()
                    time.sleep(0.01)

                if download_reply.error() == QNetworkReply.NetworkError.NoError:
                    program_dir = get_program_dir()
                    temp_dir = Path(tempfile.gettempdir())
                    temp_exe_path = temp_dir / new_exe_name
                    with open(temp_exe_path, "wb") as f:
                        f.write(download_reply.readAll().data())

                    batch_content = f"""@echo off
timeout /t 2
move /Y "{temp_exe_path}" "{Path(sys.executable)}"
start "" "{Path(sys.executable)}"
"""
                    batch_path = program_dir / "update.bat"
                    with open(batch_path, "w", encoding="utf-8") as f:
                        f.write(batch_content)

                    logger.info(f"Обновление {latest_version} скачано, запускаем батник")
                    update_dialog.set_text("Обновление скачано, перезапуск...")
                    update_dialog.set_progress(100)
                    QApplication.processEvents()
                    time.sleep(1)

                    subprocess.Popen(['cmd.exe', '/c', str(batch_path)])
                    parent.close()
                    QApplication.quit()
                    sys.exit(0)
                else:
                    error = download_reply.errorString()
                    logger.error(f"Ошибка скачивания: {error}")
                    update_dialog.close()
                    QMessageBox.critical(parent, "Ошибка обновления",
                                        f"Не удалось скачать обновление: {error}\nСм. update_log.txt")
            else:
                # Для .py: загружаем main.py и styles.py
                files_to_update = ["main.py", "styles.py"]
                for file_name in files_to_update:
                    download_url = f"https://github.com/sharkye1/Szhimatar/releases/download/{latest_version}/{file_name}"
                    logger.info(f"Скачивание {file_name} с {download_url}")
                    download_reply = network_manager.get(QNetworkRequest(QUrl(download_url)))

                    def update_progress(bytes_received, bytes_total):
                        if bytes_total > 0:
                            progress = int((bytes_received / bytes_total) * 100)
                            update_dialog.set_progress(progress // len(files_to_update))
                            QApplication.processEvents()

                    download_reply.downloadProgress.connect(update_progress)

                    while not download_reply.isFinished():
                        QApplication.processEvents()
                        time.sleep(0.01)

                    if download_reply.error() == QNetworkReply.NetworkError.NoError:
                        new_content = download_reply.readAll().data().decode('utf-8')
                        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
                        backup_file = file_path.replace(".py", "_backup.py")

                        if os.path.exists(backup_file):
                            os.remove(backup_file)
                        if os.path.exists(file_path):
                            os.rename(file_path, backup_file)

                        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                            f.write(new_content)
                        logger.info(f"Файл {file_name} обновлён")
                    else:
                        error = download_reply.errorString()
                        logger.error(f"Ошибка скачивания {file_name}: {error}")
                        update_dialog.close()
                        QMessageBox.critical(parent, "Ошибка обновления",
                                            f"Не удалось скачать {file_name}: {error}\nСм. update_log.txt")
                        return

                update_dialog.set_text("Обновление установлено, перезапуск...")
                update_dialog.set_progress(100)
                QApplication.processEvents()
                time.sleep(1)

                script_path = os.path.abspath("main.py")
                logger.info(f"Перезапуск: {sys.executable} {script_path}")
                parent.close()
                subprocess.Popen([sys.executable, script_path])
                QApplication.quit()
                sys.exit(0)
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

# Настройка логирования для отладки
'''logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)'''

# Класс для заставки
class SplashWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Splash Screen")
        self.setStyleSheet("background-color: black;")  # Полностью чёрный фон
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)  # Полноэкранный режим
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)  # Скрытие панели задач

        # Главный layout для центрирования
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        self.setLayout(main_layout)

        # Внутренний layout для горизонтального центрирования
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(logo_layout)

        logo_size = int(1920)
        #logger.info(f"Установлен размер логотипа: {logo_size}x{logo_size}")

        # Путь к логотипу в директории программы
        self.logo_path = os.path.join(os.path.dirname(__file__), "logo1.png")
        #logger.info(f"Проверяем наличие логотипа: {self.logo_path}")

        # Проверяем и загружаем логотип, если его нет
        self.download_logo_if_missing()

        # Логотип
        self.logo = QLabel(self)
        pixmap = QPixmap(self.logo_path)
        if pixmap.isNull():
            #logger.error(f"Не удалось загрузить логотип: {self.logo_path}")
            pixmap = QPixmap(100, 100)  # Заглушка
            pixmap.fill(Qt.GlobalColor.red)  # Красный фон для отладки
        self.logo.setPixmap(pixmap.scaled(logo_size, logo_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedSize(logo_size, logo_size)  # Фиксированный размер
        self.logo.setGraphicsEffect(QGraphicsOpacityEffect(self.logo))
        self.logo.graphicsEffect().setOpacity(0.0)  # Начально скрыто
        logo_layout.addWidget(self.logo)

        # Анимации
        self.setup_animations()

    def download_logo_if_missing(self):
        """Скачивает логотип, если он отсутствует в директории программы."""
        if not os.path.exists(self.logo_path):
            logo_url = "https://raw.githubusercontent.com/sharkye1/Szhimatar/12e8581b407f33de2be7eb37558e0ef0b1931329/logo1.png"  # Замените на вашу реальную ссылку
            #logger.info(f"Логотип не найден, скачиваем с {logo_url}")
            try:
                response = requests.get(logo_url, timeout=10)
                response.raise_for_status()  # Проверяем успешность запроса
                with open(self.logo_path, "wb") as f:
                    f.write(response.content)
                #logger.info(f"Логотип успешно сохранён: {self.logo_path}")
            except Exception as e:
                pass
                #logger.error(f"Ошибка при скачивании логотипа: {str(e)}")
                # Продолжаем с заглушкой, если скачивание не удалось

    def setup_animations(self):
        # Fade-in для логотипа
        fade_in = QPropertyAnimation(self.logo.graphicsEffect(), b"opacity")
        fade_in.setDuration(1500)  # 1.5 секунды
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Fade-out для логотипа
        fade_out = QPropertyAnimation(self.logo.graphicsEffect(), b"opacity")
        fade_out.setDuration(1000)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Группа анимаций
        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(fade_in)
        self.animation_group.addPause(2000)  # Пауза 2 секунды
        self.animation_group.addAnimation(fade_out)

        # Закрываем splash
        self.animation_group.finished.connect(self.close)
        self.animation_group.start()
class DownloadFFmpegDialog(QDialog):
    def __init__(self, parent=None, theme='light'):
        super().__init__(parent)
        self.setWindowTitle("Установка FFmpeg")
        self.setFixedSize(500, 300)  # Увеличим для текста инструкции
        self.setModal(True)
        self.parent = parent

        layout = QVBoxLayout()

        # Информация
        info_label = QLabel("Для работы программы нужен FFmpeg. Мы откроем браузер для скачивания архива с официального сайта.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Инструкция
        self.instruction_label = QLabel(
            "Инструкция:\n"
            "1. Скачайте архив 'ffmpeg-release-full.7z' с сайта.\n"
            "2. Распакуйте архив в удобную папку (рекомендуем в папку программы).\n"
            "3. В настройках программы (⚙️) выберите путь к 'ffmpeg.exe' из распакованной папки (обычно в bin/).\n"
            "4. Если нужно, добавьте папку с FFmpeg в системный PATH для автоматического обнаружения.\n"
            "После этого программа будет готова к работе!"
        )
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.instruction_label.setWordWrap(True)
        layout.addWidget(self.instruction_label)

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.download_btn = QPushButton("📥 Открыть страницу скачивания")
        self.download_btn.clicked.connect(self.open_download_page)
        buttons_layout.addWidget(self.download_btn)

        self.cancel_btn = QPushButton("❌ Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        self.apply_theme(theme)

    def apply_theme(self, theme):
        """Применяет тему."""
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
        elif theme == 'midnight':
            self.setStyleSheet(midnight_soft_stylesheet)

    def open_download_page(self):
        """Открывает браузер на странице скачивания и закрывает диалог."""
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z"  # Прямая ссылка на файл (браузер начнёт скачивание)
        QDesktopServices.openUrl(QUrl(url))  # Открывает в браузере по умолчанию
        self.accept()  # Закрываем диалог после открытия


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
        elif theme == 'midnight_soft_stylesheet':
            self.setStyleSheet(midnight_soft_stylesheet)
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
        self.setFixedSize(400, 150)  # Увеличим высоту для новой информации
        self.setModal(True)

        self.start_time = None
        self.last_bytes_received = 0
        self.last_update_time = None

        layout = QVBoxLayout()

        # Основной текст
        self.label = QLabel("Установка обновления...")
        layout.addWidget(self.label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Информация о скорости и времени
        info_layout = QHBoxLayout()

        # Скорость скачивания
        self.speed_label = QLabel("Скорость: -")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_layout.addWidget(self.speed_label)

        # Оставшееся время
        self.time_label = QLabel("Осталось: -")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(self.time_label)

        layout.addLayout(info_layout)
        self.setLayout(layout)

        # Применяем стиль
        self.apply_theme(theme)

    def start_download(self):
        """Начинает отсчет времени для расчета скорости."""
        self.start_time = time.time()
        self.last_bytes_received = 0
        self.last_update_time = self.start_time

    def update_progress(self, bytes_received, bytes_total):
        """Обновляет прогресс с расчетом скорости и времени."""
        if bytes_total > 0:
            progress = int((bytes_received / bytes_total) * 100)
            self.progress_bar.setValue(progress)

            # Рассчитываем скорость и оставшееся время
            current_time = time.time()

            if self.start_time is None:
                self.start_download()

            # Рассчитываем текущую скорость
            time_diff = current_time - self.last_update_time
            if time_diff > 0.5:  # Обновляем не чаще чем раз в 0.5 секунды
                bytes_diff = bytes_received - self.last_bytes_received
                speed_kbps = (bytes_diff / time_diff) / 1024  # KB/s

                # Форматируем скорость
                if speed_kbps > 1024:
                    speed_str = f"{speed_kbps / 1024:.1f} MB/s"
                else:
                    speed_str = f"{speed_kbps:.1f} KB/s"

                self.speed_label.setText(f"Скорость: {speed_str}")

                # Рассчитываем оставшееся время
                if speed_kbps > 0:
                    bytes_remaining = bytes_total - bytes_received
                    seconds_remaining = bytes_remaining / (speed_kbps * 1024)

                    # Форматируем время
                    if seconds_remaining > 3600:
                        time_str = f"{int(seconds_remaining // 3600)}ч {int((seconds_remaining % 3600) // 60)}м"
                    elif seconds_remaining > 60:
                        time_str = f"{int(seconds_remaining // 60)}м {int(seconds_remaining % 60)}с"
                    else:
                        time_str = f"{int(seconds_remaining)}с"

                    self.time_label.setText(f"Осталось: {time_str}")
                else:
                    self.time_label.setText("Осталось: -")

                # Обновляем последние значения
                self.last_bytes_received = bytes_received
                self.last_update_time = current_time

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
        elif theme == 'midnight_soft_stylesheet':
            self.setStyleSheet(midnight_soft_stylesheet)

    def set_progress(self, value):
        """Обновляет прогресс-бар (для обратной совместимости)."""
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
        #self.logger.info(f"Применение темы: {theme}")
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
        elif theme == 'midnight_soft_stylesheet':
            self.setStyleSheet(midnight_soft_stylesheet)
            self.stats_label.setStyleSheet("color: #1e252f; background: transparent;")

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


class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme='light', version="v1.0.0"):
        super().__init__(parent)
        self.setWindowTitle("Настройки программы")
        self.setFixedSize(440, 700)
        self.setModal(True)
        self.logger = setup_license_logging()
        self.logger.info("Инициализация окна настроек")

        self.parent = parent
        self.version = version

        layout = QVBoxLayout()

        # Информация о версии
        version_label = QLabel(f"Версия программы: {version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(version_label)

        layout.addWidget(self.create_separator())

        # Смена темы
        theme_label = QLabel("🎨 Смена темы оформления:")
        layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная", "Синяя", "Зелёная", "Жёлтая", "Красная", "Приятная"])
        self.theme_combo.setCurrentText(self.get_theme_name(parent.current_theme))
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        layout.addWidget(self.theme_combo)

        layout.addWidget(self.create_separator())

        # Контекстное меню
        context_menu_label = QLabel("📋 Контекстное меню Windows:")
        layout.addWidget(context_menu_label)

        self.context_menu_btn = QPushButton()
        self.update_context_menu_button()
        self.context_menu_btn.clicked.connect(self.toggle_context_menu)
        layout.addWidget(self.context_menu_btn)

        layout.addWidget(self.create_separator())

        # Статистика
        stats_label = QLabel("📊 Статистика сжатия:")
        layout.addWidget(stats_label)

        stats_btn = QPushButton("📈 Показать статистику")
        stats_btn.clicked.connect(self.show_stats)
        layout.addWidget(stats_btn)

        layout.addWidget(self.create_separator())

        # История сжатия
        history_label = QLabel("📜 История сжатия:")
        layout.addWidget(history_label)

        history_btn = QPushButton("📖 Показать историю")
        history_btn.clicked.connect(self.show_history)
        layout.addWidget(history_btn)

        layout.addWidget(self.create_separator())

        # Проверка обновлений
        update_label = QLabel("🔄 Обновления программы:")
        layout.addWidget(update_label)

        update_btn = QPushButton("🔍 Проверить обновления")
        update_btn.clicked.connect(self.check_updates)
        layout.addWidget(update_btn)

        layout.addWidget(self.create_separator())

        #
        layout.addWidget(self.create_separator())
        # Секция для заставки
        splash_label = QLabel("🖼️ Заставка при запуске:")
        layout.addWidget(splash_label)
        self.show_splash_checkbox = QCheckBox("Показывать заставку при запуске")
        self.show_splash_checkbox.setChecked(
            self.parent.settings.value("show_splash", True, type=bool))  # Загружаем значение (по умолчанию True)
        self.show_splash_checkbox.stateChanged.connect(self.save_splash_setting)  # Сохраняем при изменении
        layout.addWidget(self.show_splash_checkbox)


        # Кнопка закрытия
        '''close_btn = QPushButton("✅ Закрыть настройки")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)'''

        self.setLayout(layout)
        self.apply_theme(parent.current_theme if parent else 'light')


        # Секция FFmpeg
        ffmpeg_label = QLabel("🎬 Настройки FFmpeg:")
        layout.addWidget(ffmpeg_label)

        # Текущий путь к FFmpeg
        self.ffmpeg_path_label = QLabel("Поиск FFmpeg... Нажмите '🔄 Обновить'")
        layout.addWidget(self.ffmpeg_path_label)

        # Замените QHBoxLayout на QGridLayout
        ffmpeg_buttons_grid = QGridLayout()
        ffmpeg_buttons_grid.setSpacing(5)  # Расстояние между кнопками

        # Кнопка обновления информации
        refresh_ffmpeg_btn = QPushButton("🔄 Обновить")
        refresh_ffmpeg_btn.clicked.connect(self.update_ffmpeg_info)
        ffmpeg_buttons_grid.addWidget(refresh_ffmpeg_btn, 0, 0)

        # Кнопка выбора кастомного пути
        custom_ffmpeg_btn = QPushButton("📁 Выбрать FFmpeg")
        custom_ffmpeg_btn.clicked.connect(self.select_custom_ffmpeg)
        ffmpeg_buttons_grid.addWidget(custom_ffmpeg_btn, 0, 1)

        # Кнопка сброса к стандартному пути
        reset_ffmpeg_btn = QPushButton("↩️ Сбросить")
        reset_ffmpeg_btn.clicked.connect(self.reset_ffmpeg_path)
        ffmpeg_buttons_grid.addWidget(reset_ffmpeg_btn, 1, 0)

        # Кнопка скачивания FFmpeg
        download_ffmpeg_btn = QPushButton("📥 Скачать FFmpeg (бета)")
        download_ffmpeg_btn.clicked.connect(self.download_ffmpeg)
        ffmpeg_buttons_grid.addWidget(download_ffmpeg_btn, 1, 1)

        # Устанавливаем растяжение колонок
        ffmpeg_buttons_grid.setColumnStretch(0, 1)
        ffmpeg_buttons_grid.setColumnStretch(1, 1)

        layout.addLayout(ffmpeg_buttons_grid)
        layout.addWidget(self.create_separator())

        # Красивая панель с информацией
        copyright_widget = QWidget()
        copyright_widget.setStyleSheet("background-color: #2a2a2a; border-radius: 5px;")
        copyright_layout = QHBoxLayout(copyright_widget)
        copyright_layout.setContentsMargins(10, 5, 10, 5)

        # Иконка
        icon_label = QLabel("🦈")  # Акула как ник sharkye1
        icon_label.setStyleSheet("font-size: 14px;")

        # Текст
        text_label = QLabel(
            '© 2024-2025 <a href="https://github.com/sharkye1" style="color: #6ab0de; text-decoration: none;">sharkye1</a>. Все права защищены.')
        text_label.setOpenExternalLinks(True)
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setStyleSheet("color: #ccc; font-size: 10px;")

        copyright_layout.addWidget(icon_label)
        copyright_layout.addStretch()
        copyright_layout.addWidget(text_label)
        copyright_layout.addStretch()

        layout.addWidget(copyright_widget)

    def save_splash_setting(self, state):
        self.parent.settings.setValue("show_splash", state == Qt.CheckState.Checked.value)

    def download_ffmpeg(self):
        """Запускает процесс установки FFmpeg."""
        dialog = DownloadFFmpegDialog(self, self.parent.current_theme)
        dialog.exec()  # Диалог покажет инструкцию и откроет браузер
        # После закрытия диалога обнови информацию о FFmpeg
        self.update_ffmpeg_info()

    def update_ffmpeg_info(self):
        """Обновляет информацию о FFmpeg."""
        try:
            ffmpeg_path = self.parent.get_ffmpeg_path()
            custom_path = self.parent.settings.value("custom_ffmpeg_path")

            if custom_path and os.path.exists(custom_path):
                status = "✅ Настроен вручную"
                path = custom_path
            elif ffmpeg_path:
                status = "✅ Найден автоматически"
                path = ffmpeg_path
            else:
                status = "❌ Не найден"
                path = "FFmpeg не установлен или не добавлен в PATH"

            # Получаем версию FFmpeg
            version = self.get_ffmpeg_version(ffmpeg_path if not custom_path else custom_path)

            self.ffmpeg_path_label.setText(
                f"Статус: {status}\n"
                f"Путь: {path}\n"
                f"Версия: {version}"
            )

        except Exception as e:
            self.logger.error(f"Ошибка обновления информации FFmpeg: {e}")
            self.ffmpeg_path_label.setText("Ошибка получения информации о FFmpeg")

    def get_ffmpeg_version(self, ffmpeg_path):
        """Получает версию FFmpeg."""
        try:
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                result = subprocess.run([ffmpeg_path, '-version'],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    first_line = result.stdout.split('\n')[0]
                    return first_line.strip()
            return "Неизвестно"
        except Exception:
            return "Неизвестно"

    def select_custom_ffmpeg(self):
        """Позволяет выбрать кастомный путь к FFmpeg."""
        if self.parent.set_custom_ffmpeg_path():
            self.update_ffmpeg_info()

    def reset_ffmpeg_path(self):
        """Сбрасывает кастомный путь к FFmpeg."""
        self.parent.settings.remove("custom_ffmpeg_path")
        QMessageBox.information(self, "Успех", "Путь к FFmpeg сброшен к стандартному")
        self.update_ffmpeg_info()

    def create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator

    def get_theme_name(self, theme_key):
        theme_names = {
            'light': 'Светлая',
            'dark': 'Тёмная',
            'blue': 'Синяя',
            'green': 'Зелёная',
            'yellow': 'Жёлтая',
            'red': 'Красная',
            'midnight': 'Приятная'
        }
        return theme_names.get(theme_key, 'Светлая')

    def get_theme_key(self, theme_name):
        theme_keys = {
            'Светлая': 'light',
            'Тёмная': 'dark',
            'Синяя': 'blue',
            'Зелёная': 'green',
            'Жёлтая': 'yellow',
            'Красная': 'red',
            'Приятная': 'midnight'
        }
        return theme_keys.get(theme_name, 'light')

    def change_theme(self):
        theme_name = self.theme_combo.currentText()
        theme_key = self.get_theme_key(theme_name)
        if self.parent:
            self.parent.current_theme = theme_key
            self.parent.apply_theme(theme_key)
            self.apply_theme(theme_key)

    def update_context_menu_button(self):
        if check_context_menu():
            self.context_menu_btn.setText("🗑️ Удалить из контекстного меню")
        else:
            self.context_menu_btn.setText("➕ Добавить в контекстное меню")

    def toggle_context_menu(self):
        if self.parent:
            self.parent.toggle_context_menu()
            self.update_context_menu_button()

    def show_stats(self):
        if self.parent:
            self.parent.open_stats_dialog()

    def show_history(self):
        if self.parent:
            self.parent.open_history_dialog()

    def check_updates(self):
        if self.parent:
            self.parent.check_for_updates()

    def apply_theme(self, theme):
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
        elif theme == 'midnight':
            self.setStyleSheet(midnight_soft_stylesheet)

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
        self.show_splash = self.settings.value("show_splash", True, type=bool)  # Добавьте атрибут класса
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
        # Проверка обновлений при запуске программы
        #self.check_for_updates()

    def get_ffmpeg_path(self):
        """Возвращает путь к ffmpeg или None если не найден."""
        try:
            # Сначала проверяем кастомный путь
            custom_path = self.settings.value("custom_ffmpeg_path")
            if custom_path and os.path.exists(custom_path):
                return custom_path

            # Проверяем стандартный путь в PATH
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                return ffmpeg_path

            # Проверяем возможные альтернативные пути
            possible_paths = [
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
                os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),
                os.path.join(get_program_dir(), "ffmpeg", "bin", "ffmpeg.exe")
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    return path

            return None
        except Exception as e:
            self.logger.error(f"Ошибка поиска FFmpeg: {e}")
            return None

    def set_custom_ffmpeg_path(self):
        """Позволяет пользователю выбрать кастомный путь к ffmpeg."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите исполняемый файл FFmpeg",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )

        if file_path and os.path.exists(file_path):
            # Проверяем, что это действительно ffmpeg
            try:
                result = subprocess.run([file_path, '-version'],
                                        capture_output=True, text=True, timeout=5)
                if 'ffmpeg version' in result.stdout:
                    # Сохраняем путь в настройках
                    self.settings.setValue("custom_ffmpeg_path", file_path)
                    QMessageBox.information(self, "Успех",
                                            f"FFmpeg успешно настроен:\n{file_path}")
                    return True
                else:
                    QMessageBox.warning(self, "Ошибка",
                                        "Выбранный файл не является FFmpeg")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка",
                                    f"Не удалось проверить FFmpeg: {e}")

        return False

    def get_ffmpeg_command(self):
        """Возвращает команду ffmpeg с учетом кастомного пути."""
        try:
            # Сначала проверяем кастомный путь из настроек
            custom_path = self.settings.value("custom_ffmpeg_path")
            if custom_path and os.path.exists(custom_path):
                self.logger.info(f"Используется кастомный FFmpeg: {custom_path}")
                return custom_path

            # Проверяем ffmpeg в различных местах
            possible_paths = [
                # В папке с программой
                os.path.join(get_program_dir(), "ffmpeg.exe"),
                os.path.join(get_program_dir(), "ffmpeg", "bin", "ffmpeg.exe"),
                os.path.join(get_program_dir(), "bin", "ffmpeg.exe"),

                # Стандартные пути установки
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",

                # В PATH
                shutil.which('ffmpeg') or ''
            ]

            for path in possible_paths:
                if path and os.path.exists(path):
                    self.logger.info(f"Найден FFmpeg: {path}")
                    return path

            self.logger.warning("FFmpeg не найден ни в одном из мест")
            return 'ffmpeg'  # Будет искать в PATH

        except Exception as e:
            self.logger.error(f"Ошибка получения пути FFmpeg: {e}")
            return 'ffmpeg'


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
                #print("Нет доступных изображений.")
                self.logger.info(f"Нет доступных изображений")

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
                self.logger.info('Ошибка: изображение не содержит данных.')
                #print("Ошибка: изображение не содержит данных.")
        else:
            self.logger.info(f"Ошибка при загрузке изображения: {reply.errorString()}")
            #print("Ошибка при загрузке изображения:", reply.errorString())

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
        #toolbar = self.findChild(QToolBar)

        # Кнопка паузы
        self.pause_action = QAction("⏯", self)
        self.pause_action.triggered.connect(self.toggle_music)
        #toolbar.addAction(self.pause_action)

        # Кнопка следующего трека
        self.next_action = QAction("⏭", self)
        self.next_action.triggered.connect(self.next_track)
        #toolbar.addAction(self.next_action)

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
                    #print(f"Ошибка: сервер вернул код {response.status_code}")
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

            ffmpeg_cmd = self.get_ffmpeg_command() # в 1.4.0 для 1.4.1
            cmd = [
                ffmpeg_cmd, '-y', '-i', video_path, '-ss', str(mid_time),
                '-frames:v', '1', '-q:v', '2', '-vf', 'scale=320:180',
                str(preview_path)
            ]
            self.logger.info(f"Генерация превью для {video_path}: {' '.join(cmd)}")
            self.run_subprocess(cmd, capture_output=False)
            if os.path.exists(preview_path):
                self.logger.info(f"Превью создано: {preview_path}")
                return str(preview_path)
            else:
                self.logger.error(f"Превью не создано для {video_path}")
                return None
        except Exception as e:
            self.logger.error(f"Ошибка генерации превью для {video_path}: {str(e)}")
            return None

    def open_settings(self):
        """Открывает диалоговое окно настроек."""
        self.logger.info("Открытие окна настроек")
        dialog = SettingsDialog(self, self.current_theme, __version__)
        dialog.exec()

    def init_ui(self):
        self.setWindowTitle("Сжиматор на NVENC")
        self.setGeometry(100, 100, 800, 700)

        # Создаем горизонтальный layout для кнопки
        top_layout = QHBoxLayout()
        # Создаем кнопку настроек
        settings_btn = QPushButton("⚙️ Настройки")
        settings_btn.clicked.connect(self.open_settings)
        settings_btn.setFixedSize(111, 30)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)  # Добавляем горизонтальный layout с кнопкой

        # Для темы:
        self.theme_action = QAction("☀️Тема 🌙", self)
        self.theme_action.triggered.connect(self.toggle_theme)
        #toolbar.addAction(self.theme_action)
        # Для записей в реестре:
        self.context_menu_action = QAction("", self)
        self.context_menu_action.triggered.connect(self.toggle_context_menu)
        #toolbar.addAction(self.context_menu_action)

        stats_action = QAction("📊 Статистика 📊", self)
        stats_action.triggered.connect(self.open_stats_dialog)
        #toolbar.addAction(stats_action)

        history_action = QAction("📜 История сжатия 📜", self)
        history_action.triggered.connect(self.open_history_dialog)
        #toolbar.addAction(history_action)

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

        # Настройка выбора фпс
        fps_layout = QHBoxLayout()

        # Галочка автоматического определения
        self.auto_fps_checkbox = QCheckBox("Определять автоматически")
        self.auto_fps_checkbox.setChecked(True)  # По умолчанию включено
        self.auto_fps_checkbox.stateChanged.connect(self.toggle_auto_fps)
        fps_layout.addWidget(self.auto_fps_checkbox)

        # Ползунок FPS
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 240)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setFixedWidth(60)
        self.fps_slider.valueChanged.connect(self.fps_spin.setValue)
        self.fps_spin.valueChanged.connect(self.fps_slider.setValue)

        #fps_layout.addWidget(QLabel("FPS:"))
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
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignRight)
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

    def toggle_auto_fps(self, state):
        """Включает/выключает автоматическое определение FPS."""
        if state == Qt.CheckState.Checked.value:
            self.fps_slider.setEnabled(False)
            self.fps_spin.setEnabled(False)
            # Автоматически определяем FPS при включении галочки
            self.auto_detect_fps()
        else:
            self.fps_slider.setEnabled(True)
            self.fps_spin.setEnabled(True)

    def auto_detect_fps(self):
        """Автоматически определяет FPS видео и устанавливает значение."""
        if not hasattr(self, 'current_file') or not self.current_file:
            return

        try:
            fps = self.get_video_fps()
            if fps:
                # Ограничиваем максимальным значением 120
                fps_value = min(round(fps), 120)
                self.fps_spin.setValue(fps_value)
                self.logger.info(f"Автоматически определен FPS: {fps} -> установлено: {fps_value}")
            else:
                self.logger.warning("Не удалось определить FPS автоматически")

        except Exception as e:
            self.logger.error(f"Ошибка автоматического определения FPS: {e}")

    def get_video_fps(self):
        """Возвращает FPS видео файла."""
        try:
            if not hasattr(self, 'current_file') or not self.current_file:
                return None

            # Используем ffprobe для получения информации о видео
            ffprobe_cmd = self.get_ffprobe_command()
            if not ffprobe_cmd:
                self.logger.error("ffprobe не найден для определения FPS")
                return None

            cmd = [
                ffprobe_cmd,
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=avg_frame_rate',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                self.current_file
            ]

            # Запускаем процесс
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10,
                                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0)

            if result.returncode == 0:
                fps_str = result.stdout.strip()
                # Обрабатываем разные форматы FPS (например, "30000/1001")
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    try:
                        return float(num) / float(den)
                    except (ValueError, ZeroDivisionError):
                        return float(fps_str)
                else:
                    return float(fps_str)

            return None

        except FileNotFoundError:
            self.logger.error("ffprobe не найден для определения FPS")
            return None
        except subprocess.TimeoutExpired:
            self.logger.warning("Таймаут определения FPS")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка определения FPS: {e}")
            return None


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
        themes = ['dark', 'light', 'blue', 'green', 'yellow', 'red', 'midnight']  # Список доступных тем
        current_index = themes.index(self.current_theme)
        next_index = (current_index + 1) % len(themes)  # Переход к следующей теме
        self.current_theme = themes[next_index]
        self.apply_theme(self.current_theme)
        #self.logger.info(f"Тема изменена на: {self.current_theme}")



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
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv)"
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

            # Автоматически определяем FPS если галочка активна
            if self.auto_fps_checkbox.isChecked():
                self.auto_detect_fps()
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

        ffmpeg_cmd = self.get_ffmpeg_command()

        cmd = [
            ffmpeg_cmd,
            '-ss', time_str,
            '-i', self.current_file,
            '-frames:v', '1',
            '-q:v', '2',
            temp_file.name,
            '-y'  # Перезаписывать файл
        ]
        self.run_subprocess(cmd, capture_output=False)
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

            # Автоматически определяем FPS если нужно
            if self.auto_fps_checkbox.isChecked():
                auto_fps = self.get_video_fps()
                if auto_fps:
                    fps_value = min(round(auto_fps), 120)
                    self.fps_spin.setValue(fps_value)
                    logger.info(f"Используется автоматический FPS: {fps_value}")

            # Получаем выбранный FPS
            fps = self.fps_spin.value()

            audio_codec = self.audio_codec_combo.currentText()
            audio_bitrate = f"{self.audio_bitrate_spin.value()}k"
            speed = self.speed_spin.value()
            input_file = f'"{self.current_file}"'
            output_file = output_file.replace('\\', '/')
            output_file = f'"{output_file}"'

            logger.info(f"Параметры сжатия: codec={codec}, bitrate={bitrate}, fps={fps}, "
                        f"audio_codec={audio_codec}, audio_bitrate={audio_bitrate}, speed={speed}")

            # Получаем команду FFmpeg с учетом кастомного пути
            ffmpeg_cmd = self.get_ffmpeg_command()
            logger.info(f"Используемый FFmpeg: {ffmpeg_cmd}")

            cmd = [
                ffmpeg_cmd,
                '-y',
                #'-hwaccel', 'cuda',
                '-hwaccel_output_format', 'cuda',
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
                subprocess.run([ffmpeg_cmd, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
                '''if platform.system() == 'Windows':
                    self.process.setCreateProcessArgumentsModifier(
                        lambda args: args.append(subprocess.CREATE_NO_WINDOW)
                    )'''
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

    def get_ffprobe_command(self):
        """Возвращает команду ffprobe с учетом кастомного пути."""
        try:
            # Сначала проверяем кастомный путь из настроек
            custom_path = self.settings.value("custom_ffmpeg_path")
            if custom_path and os.path.exists(custom_path):
                # Заменяем ffmpeg на ffprobe в пути
                ffprobe_path = custom_path.replace('ffmpeg', 'ffprobe')
                if os.path.exists(ffprobe_path):
                    return ffprobe_path
                # Если ffprobe не найден рядом с ffmpeg, используем из PATH
                return 'ffprobe'

            # Проверяем ffprobe в различных местах
            possible_paths = [
                os.path.join(get_program_dir(), "ffprobe.exe"),
                os.path.join(get_program_dir(), "ffmpeg", "bin", "ffprobe.exe"),
                os.path.join(get_program_dir(), "bin", "ffprobe.exe"),
                r"C:\ffmpeg\bin\ffprobe.exe",
                r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
                shutil.which('ffprobe') or ''
            ]

            for path in possible_paths:
                if path and os.path.exists(path):
                    return path

            return 'ffprobe'  # Будет искать в PATH

        except Exception as e:
            self.logger.error(f"Ошибка получения пути ffprobe: {e}")
            return 'ffprobe'

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
                # Автоматически определяем FPS для каждого файла если галочка активна
                if self.auto_fps_checkbox.isChecked():
                    self.auto_detect_fps()
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
            #self.logger.info(f"Время выполнения сжатия: {elapsed_time:.2f} секунд")

            compressed_size = os.path.getsize(output_file)
            #self.logger.info(f"Размер сжатого файла: {self.format_size(compressed_size)}")

            compression_ratio = (1 - (compressed_size / self.original_size)) * 100
            space_saved = self.original_size - compressed_size
            #self.logger.info(f"Экономия места: {self.format_size(space_saved)}")

            video_duration = self.get_video_duration()
            #self.logger.info(f"Длительность видео: {video_duration} секунд")

            preview_path = self.generate_preview(self.current_file)
            #self.logger.info(f"Путь к превью: {preview_path}")
            self.update_stats(video_duration, space_saved, elapsed_time)

            # Сохранение в историю
            history_file = str(get_program_dir() / "compression_history.json")
            #self.logger.info(f"Попытка записи в историю: {history_file}")
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

            ffprobe_cmd = self.get_ffprobe_command()

            result = subprocess.run(
                [ffprobe_cmd, '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', self.current_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            return float(result.stdout.strip())
        except Exception as e:
            #print(f"Ошибка получения длительности: {e}")
            return 0.0

    def save_preset(self):
        #print('сейв пресет зашел')
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
            self.apply_theme('midnight')  # Изменено с 'light' на 'dark'
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

            ffprobe_cmd = self.get_ffprobe_command()  # Добавьте эту строку в начало метода

            result = subprocess.run(
                [ffprobe_cmd, '-v', 'error', '-show_entries', 'stream=bit_rate',
                 '-of', 'default=noprint_wrappers=1:nokey=1', '-select_streams', 'a:0', self.current_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            return int(result.stdout.strip() or 0) / 1000
        except Exception as e:
            #print(f"Ошибка аудио битрейта: {e}")
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
        elif theme == 'midnight':
            self.setStyleSheet(midnight_soft_stylesheet)
            self.theme_action.setText("🟦 Приятная тема 🟦")
        #self.logger.info(f"Применена тема: {theme}")
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
    r"""Возвращает путь к папке AppData\Roaming\Szhimatar."""
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

    window = VideoCompressor()  # Создайте window раньше

    # Проверяем настройку
    show_splash = window.settings.value("show_splash", True, type=bool)
    if show_splash:
        splash = SplashWindow()
        splash.show()

        # Ждём завершения анимации splash (он сам закроется)
        while splash.isVisible():
            app.processEvents()  # Обработка событий, чтобы анимация работала
            #time.sleep(0.01)

    window.show()
    app.exec()
