import sys
import json
import os

import requests
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QDialog, QVBoxLayout, QLabel, QLineEdit, \
    QPushButton, QMessageBox, QFileDialog, QCheckBox
from PyQt5.QtGui import QIcon
from watchdog.observers import Observer
from folder_watcher import FolderChangeHandler

# Global variable to hold the configuration
CONFIG = {}

observer = None
is_listening = False


class SettingsDialog(QDialog):
    def __init__(self, parent=None, tray_icon=None):
        super(SettingsDialog, self).__init__(parent)
        self.setFixedSize(400, 200)
        self.hide()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.setWindowTitle("Settings")

        layout = QVBoxLayout(self)
        self.hide()

        # API URL field
        self.api_url_label = QLabel("API URL:", self)
        self.api_url_input = QLineEdit(self)
        self.api_url_input.setText(CONFIG.get('api_url', ''))
        layout.addWidget(self.api_url_label)
        layout.addWidget(self.api_url_input)
        # connect to text changed signal
        self.api_url_input.textChanged.connect(lambda: self.save_button.setEnabled(True))

        # Path button
        self.path_label = QLabel("Folder to watch path: " + CONFIG.get('path', 'None'), self)
        layout.addWidget(self.path_label)
        self.path_button = QPushButton("Change Path", self)
        self.path_button.clicked.connect(self.select_path)
        layout.addWidget(self.path_button)

        # Save button
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)
        self.save_button.setEnabled(False)

        if tray_icon:
            self.tray_icon = tray_icon
            self.hide()
            QTimer.singleShot(100, lambda: self.show_near_tray(tray_icon))
            QTimer.singleShot(200, lambda: self.show())

    def show_near_tray(self, tray_icon):
        screen = QApplication.primaryScreen()
        screen_geom = screen.geometry()
        tray_geom = tray_icon.geometry()

        # This is a rough approximation and may need adjusting
        x = tray_geom.x() + tray_geom.width() / 2 - self.width() / 2
        y = tray_geom.y() + tray_geom.height()

        # Ensure the dialog is positioned within the screen bounds
        if x + self.width() > screen_geom.width():
            x = screen_geom.width() - self.width()
        if y + self.height() > screen_geom.height():
            y = screen_geom.height() - self.height()

        # cast to int
        self.move(int(x), int(y))

    def select_path(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            CONFIG['path'] = folder_path

        self.path_label.setText("Path: " + CONFIG.get('path', 'None'))

        # enable save button
        self.save_button.setEnabled(True)

    def closeEvent(self, event):
        # Override close event
        self.hide()
        event.ignore()

    def save_settings(self):
        # check if api url is valid
        if not self.api_url_input.text().startswith("http") or not self.api_url_input.text().startswith("https"):
            print("INVALID BECAUSE: not http or https")
            QMessageBox.warning(self, "Invalid API URL", "The API URL is invalid.")
            return

        # check if api url is 200
        try:
            response = requests.get(self.api_url_input.text())
            # if response.status_code != 200
            #     print("INVALID BECAUSE: not 200")
            #     QMessageBox.warning(self, "Invalid API URL", "The API URL is invalid.")
            #     return
        except Exception as e:
            print("INVALID BECAUSE: exception")
            QMessageBox.warning(self, "Invalid API URL", "The API URL is invalid.")
            return

        CONFIG['api_url'] = self.api_url_input.text()
        save_config(CONFIG)
        QMessageBox.information(self, "Settings Saved", "The settings have been saved successfully.")
        self.save_button.setEnabled(False)

        # if listener_action is disabled, emable it
        if not listener_action.isEnabled():
            listener_action.setEnabled(True)
            listener_action.setText("Enable Listener")


# Function to read config file
def get_base_folder():
    """Get the path for the base folder based on the operating system."""
    if os.name == 'nt':  # Windows
        return os.path.join(os.getenv('APPDATA'), 'Quick Embed')
    elif os.name == 'posix':  # macOS and Linux
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Quick Embed')
    else:
        raise OSError("Unsupported operating system")


# Function to read config file
def read_config():
    global CONFIG
    config_path = os.path.join(get_base_folder(), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            CONFIG = json.load(file)
    else:
        CONFIG = {
            "api_url": "https://drive-api.soos.dev"
        }


# Function to save config file
def save_config(config):
    global CONFIG
    CONFIG = config
    config_folder = get_base_folder()
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    config_path = os.path.join(config_folder, 'config.json')
    with open(config_path, 'w') as file:
        json.dump(CONFIG, file)


# Function to start/stop listener
def toggle_listener():
    global observer, is_listening, CONFIG
    if is_listening:
        observer.stop()
        observer.join()
        is_listening = False
        listener_action.setText("Start Listener")
    else:
        observer = Observer()
        event_handler = FolderChangeHandler(CONFIG.get('api_url'))
        observer.schedule(event_handler, CONFIG.get('path'), recursive=True)
        observer.start()
        is_listening = True
        listener_action.setText("Stop Listener")


# Function to open settings dialog
def open_settings(tray_icon):
    global settings_dialog
    if 'settings_dialog' not in globals():
        settings_dialog = SettingsDialog(tray_icon=tray_icon)
    settings_dialog.show_near_tray(tray_icon)
    settings_dialog.show()


def main():
    global listener_action, CONFIG
    read_config()

    app = QApplication(sys.argv)
    if not CONFIG.get('path') or not CONFIG.get('api_url'):
        print("No path or API URL set. Opening settings dialog.")
        # make folder if not exists
        if not os.path.exists(get_base_folder()):
            os.makedirs(get_base_folder())
            print("Created folder at " + get_base_folder())
        icon_url = "https://fastupload.io/secure/file/obj3jbOp23DxJ"
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ' \
                     'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        icon = requests.get(icon_url, headers={'User-Agent': user_agent})
        with open(os.path.join(get_base_folder(), 'icon.png'), 'wb') as file:
            file.write(icon.content)
    trayIcon = QSystemTrayIcon(QIcon(get_base_folder() + "/icon.png"), app)

    # Create a menu
    menu = QMenu()

    # Create listener toggle action
    listener_action = QAction("Start Listener", app)
    listener_action.triggered.connect(toggle_listener)

    # Check if configured
    if not CONFIG.get('path') or not CONFIG.get('api_url'):
        listener_action.setEnabled(False)
    menu.addAction(listener_action)

    # Create settings/configure action
    settings_action = QAction("Settings" if CONFIG.get('path') else "Configure", app)
    settings_action.triggered.connect(lambda: open_settings(trayIcon))

    menu.addAction(settings_action)

    # Add an exit action
    exitAction = QAction("Quit", app)
    exitAction.triggered.connect(app.quit)
    menu.addAction(exitAction)

    trayIcon.setContextMenu(menu)
    trayIcon.show()

    # show dialog if the app has no config file

    if not CONFIG.get('path') or not CONFIG.get('api_url'):
        print("SHOWING")
        # open message box for instructions
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Welcome to Quick Embed!")
        msg.setInformativeText("To get started, click Configure in the system tray/menu bar and configure the app.\n\n"
                               "On macos, it is normally at the top of the screen."
                               " On Windows, it is normally at the bottom right of the screen.")
        msg.setWindowTitle("Welcome to Quick Embed!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    # launch listener if configured
    if CONFIG.get('path') and CONFIG.get('api_url'):
        toggle_listener()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
