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