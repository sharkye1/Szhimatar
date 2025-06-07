dark_stylesheet = """
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QMessageBox {
    background-color: #2b2b2b;
    color: #ffffff;
}

QMessageBox QLabel {
    color: #ffffff;
}

QMessageBox QPushButton {
    background-color: #3c3f41;
    color: #ffffff;
    border: 1px solid #555;
    padding: 10px;
    border-radius: 4px;
}

QMessageBox QPushButton:hover {
    background-color: #4c4f51;
    border: 1px solid #666;
}

QPushButton {
    background-color: #3c3f41;
    border: 1px solid #555;
    padding: 5px;
    color: white;
    border-radius: 4px;
}

/* Состояние при наведении */
QPushButton:hover {
    background-color: #4c4f51;
    border: 1px solid #666;
    padding: 7px; 
    font-weight: bold; 
}

QComboBox, QSpinBox, QTextEdit {
    background-color: #3c3f41;
    color: white;
    border: 1px solid #555;
}

QLabel {
    color: #ffffff;
}

QProgressBar {
    background-color: #3c3f41;
    color: white;
    border: 1px solid #555;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4CAF50;
}
"""

light_stylesheet = """
QMainWindow {
    background-color: #f0f0f0;
    color: #000000;
}

QMessageBox {
    background-color: #f0f0f0;
    color: #000000;
}

QMessageBox QLabel {
    color: #000000;
}

QMessageBox QPushButton {
    background-color: #e0e0e0;
    color: #000000;
    border: 1px solid #555;
    padding: 10px;
    border-radius: 4px;
}

QMessageBox QPushButton:hover {
    background-color: #d0d0d0;
    border: 1px solid #666;
}

QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #555;
    padding: 5px;
    color: black;
    border-radius: 4px;
}

/* Состояние при наведении */
QPushButton:hover {
    background-color: #d0d0d0;
    border: 1px solid #666;
    padding: 7px; 
    font-weight: bold; 
}

QComboBox, QSpinBox, QTextEdit {
    background-color: #ffffff;
    color: black;
    border: 1px solid #555;
}

QLabel {
    color: #000000;
}

QProgressBar {
    background-color: #e0e0e0;
    color: black;
    border: 1px solid #555;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4CAF50;
}
"""

blue_stylesheet = """
QMainWindow {
    background-color: #1e3a5f;  /* Тёмно-синий фон */
    color: #ffffff;
}

QMessageBox {
    background-color: #1e3a5f;
    color: #ffffff;
}

QMessageBox QLabel {
    color: #ffffff;
}

QMessageBox QPushButton {
    background-color: #2a4d7a;  /* Более светлый синий для кнопок */
    color: #ffffff;
    border: 1px solid #4a6b9d;
    padding: 10px;
    border-radius: 4px;
}

QMessageBox QPushButton:hover {
    background-color: #3a5d8a;
    border: 1px solid #5a7bad;
}

QPushButton {
    background-color: #2a4d7a;
    border: 1px solid #4a6b9d;
    padding: 5px;
    color: white;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #3a5d8a;
    border: 1px solid #5a7bad;
    padding: 7px;
    font-weight: bold;
}

QComboBox, QSpinBox, QTextEdit {
    background-color: #2a4d7a;
    color: white;
    border: 1px solid #4a6b9d;
}

QLabel {
    color: #ffffff;
}

QProgressBar {
    background-color: #2a4d7a;
    color: white;
    border: 1px solid #4a6b9d;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #2196F3;  /* Ярко-синий для прогресс-бара */
}
"""

green_stylesheet = """
QMainWindow {
    background-color: #1e4620;
    color: #ffffff;
}

QMessageBox {
    background-color: #1e4620;
    color: #ffffff;
}

QMessageBox QLabel {
    color: #ffffff;
}

QMessageBox QPushButton {
    background-color: #2e6630;
    color: #ffffff;
    border: 1px solid #4a8b4c;
    padding: 10px;
    border-radius: 4px;
}

QMessageBox QPushButton:hover {
    background-color: #3e7640;
    border: 1px solid #5a9b5c;
}

QPushButton {
    background-color: #2e6630;
    border: 1px solid #4a8b4c;
    padding: 5px;
    color: white;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #3e7640;
    border: 1px solid #5a9b5c;
    padding: 7px;
    font-weight: bold;
}

QComboBox, QSpinBox, QTextEdit {
    background-color: #2e6630;
    color: white;
    border: 1px solid #4a8b4c;
}

QTableWidget {
    background-color: #2e6630;
    color: #ffffff;
}

QTableWidget::item {
    border: 1px solid #4a8b4c;
}

QHeaderView::section {
    background-color: #3e7640;
    color: #ffffff;
}

QLabel {
    color: #ffffff;
}

QProgressBar {
    background-color: #2e6630;
    color: white;
    border: 1px solid #4a8b4c;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4CAF50;
}
"""

yellow_stylesheet = """
QMainWindow {
    background-color: #4a3c00;
    color: #ffffff;
}

QMessageBox {
    background-color: #4a3c00;
    color: #ffffff;
}

QMessageBox QLabel {
    color: #ffffff;
}

QMessageBox QPushButton {
    background-color: #6a5c20;
    color: #ffffff;
    border: 1px solid #8a7b40;
    padding: 10px;
    border-radius: 4px;
}

QMessageBox QPushButton:hover {
    background-color: #7a6c30;
    border: 1px solid #9a8b50;
}

QPushButton {
    background-color: #6a5c20;
    border: 1px solid #8a7b40;
    padding: 5px;
    color: white;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #7a6c30;
    border: 1px solid #9a8b50;
    padding: 7px;
    font-weight: bold;
}

QComboBox, QSpinBox, QTextEdit {
    background-color: #6a5c20;
    color: white;
    border: 1px solid #8a7b40;
}

QTableWidget {
    background-color: #6a5c20;
    color: #ffffff;
}

QTableWidget::item {
    border: 1px solid #8a7b40;
}

QHeaderView::section {
    background-color: #7a6c30;
    color: #ffffff;
}

QLabel {
    color: #ffffff;
}

QProgressBar {
    background-color: #6a5c20;
    color: white;
    border: 1px solid #8a7b40;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #FFC107;
}
"""

red_stylesheet = """
QMainWindow {
    background-color: #460000;
    color: #ffffff;
}

QMessageBox {
    background-color: #460000;
    color: #ffffff;
}

QMessageBox QLabel {
    color: #ffffff;
}

QMessageBox QPushButton {
    background-color: #660000;
    color: #ffffff;
    border: 1px solid #8b2020;
    padding: 10px;
    border-radius: 4px;
}

QMessageBox QPushButton:hover {
    background-color: #760000;
    border: 1px solid #9b3030;
}

QPushButton {
    background-color: #660000;
    border: 1px solid #8b2020;
    padding: 5px;
    color: white;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #760000;
    border: 1px solid #9b3030;
    padding: 7px;
    font-weight: bold;
}

QComboBox, QSpinBox, QTextEdit {
    background-color: #660000;
    color: white;
    border: 1px solid #8b2020;
}

QTableWidget {
    background-color: #660000;
    color: #ffffff;
}

QTableWidget::item {
    border: 1px solid #8b2020;
}

QHeaderView::section {
    background-color: #760000;
    color: #ffffff;
}

QLabel {
    color: #ffffff;
}

QProgressBar {
    background-color: #660000;
    color: white;
    border: 1px solid #8b2020;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #F44336;
}
"""

midnight_soft_stylesheet = """
    QMainWindow, QDialog {
        background-color: #1e252f; /* Тёмно-синий фон, мягкий для глаз */
        color: #d0d7e1; /* Светло-серый текст для хорошей читаемости */
    }
    QWidget {
        background-color: #1e252f;
        color: #d0d7e1;
    }
    QPushButton {
        background-color: #3b4a66; /* Приглушённый синий для кнопок */
        color: #d0d7e1;
        border: 1px solid #4a5a7a;
        padding: 6px;
        border-radius: 5px;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #4a5a7a; /* Чуть светлее при наведении */
    }
    QPushButton:pressed {
        background-color: #2a3a56; /* Темнее при нажатии */
        border: 1px solid #2a3a56;
    }
    QComboBox {
        background-color: #2a3140; /* Тёмный фон для выпадающих списков */
        color: #d0d7e1;
        border: 1px solid #3b4a66;
        padding: 4px;
        border-radius: 4px;
    }
    QComboBox QAbstractItemView {
        background-color: #2a3140;
        color: #d0d7e1;
        selection-background-color: #3b4a66;
        selection-color: #ffffff;
        border: 1px solid #3b4a66;
    }
    QSlider::groove:horizontal {
        background: #3b4a66; /* Тёмная дорожка для слайдера */
        height: 6px;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #5c6d8f; /* Светлый синий для ручки слайдера */
        width: 14px;
        height: 14px;
        margin: -4px 0;
        border-radius: 7px;
        border: 1px solid #3b4a66;
    }
    QSpinBox, QDoubleSpinBox {
        background-color: #2a3140;
        color: #d0d7e1;
        border: 1px solid #3b4a66;
        padding: 4px;
        border-radius: 4px;
    }
    QTextEdit, QPlainTextEdit {
        background-color: #2a3140;
        color: #d0d7e1;
        border: 1px solid #3b4a66;
        border-radius: 4px;
        font-size: 12px;
    }
    QProgressBar {
        background-color: #2a3140;
        border: 1px solid #3b4a66;
        border-radius: 5px;
        text-align: center;
        color: #d0d7e1;
        font-size: 12px;
    }
    QProgressBar::chunk {
        background-color: #5c6d8f; /* Спокойный синий для прогресса */
        border-radius: 5px;
    }
    QLabel {
        color: #d0d7e1;
        font-size: 13px;
    }
    QTableWidget {
        background-color: #2a3140;
        color: #d0d7e1;
        border: 1px solid #3b4a66;
        gridline-color: #3b4a66;
    }
    QTableWidget::item {
        background-color: #2a3140;
        color: #d0d7e1;
        padding: 4px;
    }
    QTableWidget::item:selected {
        background-color: #3b4a66;
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #2a3140;
        color: #d0d7e1;
        border: 1px solid #3b4a66;
        padding: 5px;
        font-size: 12px;
    }
    QFrame[frameShape="4"], QFrame[frameShape="5"] { /* HLine, VLine */
        color: #3b4a66; /* Тёмные разделители */
    }
    QCheckBox {
        color: #d0d7e1;
        font-size: 13px;
    }
    QCheckBox::indicator {
        border: 1px solid #3b4a66;
        background-color: #2a3140;
        width: 16px;
        height: 16px;
        border-radius: 4px;
    }
    QCheckBox::indicator:checked {
        background-color: #5c6d8f;
        border: 1px solid #5c6d8f;
    }
    QToolBar {
        background-color: #1e252f;
        border: none;
        spacing: 8px;
    }
    QAction {
        color: #d0d7e1;
        font-size: 13px;
    }
    QAction:hover {
        background-color: #3b4a66;
        border-radius: 4px;
    }
"""
