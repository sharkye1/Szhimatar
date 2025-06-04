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
