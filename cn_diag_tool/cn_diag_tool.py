import datetime
import subprocess
import logging
import os
import sys
import time

import json

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMainWindow, QApplication, QProgressDialog, QVBoxLayout, QMessageBox, QLabel, QDialog, \
    QWidget, QTableWidgetItem

from cn_diag_tool_ui import Ui_MainWindow
from form_tab_widget import FormTabWidget
from cndt_config_dialog import Ui_Dialog
from Plc_connection_worker import PLCConnectionWorker
from cn_lib import scan_cn

from logger_widget import QTextEditLogger

import user_data

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


class LogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Viewer")
        self.logTextBox = QTextEditLogger(self)
        # log to text box
        self.logTextBox.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s'))
        logging.getLogger().addHandler(self.logTextBox)
        logging.getLogger().setLevel(logging.INFO)

        # Create a layout
        layout = QVBoxLayout()
        layout.addWidget(self.logTextBox.widget)
        self.setLayout(layout)
        self.hide()


class MyUpdateTimer(object):
    def __init__(self, value: int = 999):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_val: int):
        self._value = new_val

    def set_value(self, new_value):
        try:
            self._value = int(new_value)
        except Exception as e:
            log.error(f"Error update timer: {e}")


class HelperConfigDialog(QDialog, Ui_Dialog):
    def __init__(self, callback, timer_value, confirmation, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._callback = callback
        self.connectSignalsSlots()
        self.spinBox.setValue(timer_value)
        self.checkBox.setChecked(confirmation)
        # self.spinBox.value(timer_value)

    def connectSignalsSlots(self):
        self.spinBox.valueChanged.connect(self._callback)


class DiagWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, config_file_path, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.logger_window = LogWindow(self)
        self.connectSignalsSlots()
        self._config_file_path = config_file_path
        self._update_timer = MyUpdateTimer()
        self._confirm_on_tab_close = True
        self._prev_update_time = time.monotonic_ns()

        self._app: QtWidgets.QApplication = QtWidgets.QApplication.instance()
        # creating a label widget for status bar
        self.status_bar_label_1 = QLabel("Not connected yet")

        self.status_bar_label_1.setStyleSheet("border :1px solid blue;")
        # adding label to status bar
        self.statusBar().addPermanentWidget(self.status_bar_label_1)

        self._workers = {}

    def non_fatal(self, message):
        self.statusBar().showMessage(message, 10000)

    def save_config(self, filename=None):
        """Saves the application configuration to a JSON file."""

        filename = filename or self._config_file_path
        config = {}

        # confirmation on tab close
        config['Close_tab_confirm'] = self._confirm_on_tab_close

        # timer setting
        config['Timer'] = self._update_timer.value

        # CN Settings
        config['CN'] = {
            'path': self.lineEditConnectionPath.text(),
        }

        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=4)  # Use indent for readability
            log.info(f"Configuration saved to {filename}")
        except (IOError, OSError) as e:
            log.error(f"Error saving configuration: {e}")

    def load_config(self, filename=None):
        """Loads the application configuration from a JSON file."""

        filename = filename or self._config_file_path

        try:
            with open(filename, 'r') as f:
                config = json.load(f)
            # confirmation
            self._confirm_on_tab_close = config.get('Close_tab_confirm', True)
            # load_timer_settings
            self._update_timer.value = config.get('Timer', 999)

            # Load ControlNet Settings
            plc_settings = config.get('CN', {})  # Get CN settings with fallback
            plc_path = plc_settings.get('path', "")
            self.lineEditConnectionPath.setText(plc_path)

            log.info(f"Configuration loaded from {filename}")

        except FileNotFoundError:
            log.warning("Configuration file not found. Using defaults.")
        except json.JSONDecodeError as e:
            log.error(f"Error decoding JSON configuration: {e}")


    def _worker_not_connected(self):
        self.lineEditConnectionPath.setEnabled(True)
        self.pushButtonConnect.setEnabled(True)
        self.pushButtonAddTab.setEnabled(False)

    def _worker_connected(self):
        self.lineEditConnectionPath.setEnabled(False)
        self.pushButtonConnect.setEnabled(False)
        self.pushButtonAddTab.setEnabled(True)

    def on_connection_lost(self, text_error: str):
        log.error(f"Lost connection {text_error}")
        self._worker_not_connected()
        QMessageBox.warning(self, f"Connection to PLC lost", text_error)
        pass

    def connectSignalsSlots(self):
        self.pushButtonConnect.clicked.connect(self.onButtonConnect)
        # self.pushButtonAddTab.clicked.connect(self.onAddTab)
        self.actionLoad.triggered.connect(self.load_config)
        self.actionSave.triggered.connect(self.save_config)
        self.actionRead_Timer.triggered.connect(self.on_read_timer_conf)
        self.actionEnable_writing_to_PLC.triggered.connect(self.on_write_enable)
        self.actionOpen_config_folder.triggered.connect(self.on_open_folder)
        self.actionShow_log.triggered.connect(self.show_log)

    def show_log(self):
        self.logger_window.show()

    def on_write_enable(self, state):
        # print(f"Enable writing {state}")
        log.info(f"Write enabled = {state}")
        self._worker.enable_writing = state

    def on_open_folder(self):
        directory_path = user_data.get_user_data_path()
        log.info(f"Opening folder {directory_path}")
        if sys.platform == "win32":
            os.startfile(directory_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", directory_path])
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", directory_path])
        else:
            QMessageBox.warning(self, "Error", f"Unsupported platform: {sys.platform}")

    def on_read_timer_conf(self):
        old_value = self._update_timer.value
        dialog = HelperConfigDialog(parent=self,
                                    timer_value=self._update_timer.value,
                                    confirmation=self._confirm_on_tab_close,
                                    callback=self._update_timer.set_value)
        result = dialog.exec()
        if result:
            self._confirm_on_tab_close = dialog.checkBox.checkState().value == QtCore.Qt.CheckState.Checked.value
        else:
            self._update_timer.value = old_value

    def onButtonConnect(self):
        self.lineEditConnectionPath.setEnabled(False)
        self.pushButtonConnect.setEnabled(False)
        _path = self.lineEditConnectionPath.text()

        self._app.instance().setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))

        nodes, paths = scan_cn(_path)

        labels = [
            'Node',
            'Serial',
            'channel_A_frame_error',
            'channel_B_frame_error',
            'Active_Channel',
            'Redundancy_Warning',
            # 'good_frames_transmitted',
            # 'good_frames_received',
            'noise_hits',
            'noise_hits_per_sec',
            'good_frames_transmitted_per_sec',
            'good_frames_received_per_sec',
            'selected_channel_frame_error',
            'selected_channel_frame_error_per_sec',
            'non_concurrence_per_sec',
            'non_concurrence',
        ]
        self.tableWidget.setRowCount(len(nodes))
        self.tableWidget.setColumnCount(len(labels))
        self.tableWidget.setHorizontalHeaderLabels(labels)

        row = -1
        for cn_module_serial, cn_path in paths.items():
            row += 1
            node_num = int(cn_path.split('/')[-1])

            cn_node_worker = PLCConnectionWorker(node_num)
            cn_node_worker.path = cn_path
            cn_node_worker.signals.read_done.connect(self.update_diag_data)
            cn_node_worker.start()

            self._workers[node_num] = cn_node_worker

            cn_module_nodenum_Item = QTableWidgetItem(f'[{node_num:02}]')
            self.tableWidget.setItem(row, 0, cn_module_nodenum_Item)
            cn_module_serial_Item = QTableWidgetItem(str(cn_module_serial))
            self.tableWidget.setItem(row, 1, cn_module_serial_Item)

        self._app.instance().restoreOverrideCursor()
        return

    def worker_load(self, communication_time_ns):
        # print(plc_time)
        # now_time = time.perf_counter()
        communication_time_sec = communication_time_ns / 1_000_000_000
        loop_time = time.monotonic() - self._prev_update_time  # Calculate 1S cycle time. Should be about 1S
        if loop_time:
            wait_time_proportion = ((loop_time - communication_time_sec) / loop_time) * 100
        else:
            wait_time_proportion = 0.
        self._prev_update_time = time.monotonic()
        self.progressBar.setValue(int(100 - wait_time_proportion))
        # self.labelDuty.setText(str(communication_time_ns))


    def update_diag_data(self, node_num, diag_data: dict):
        """Updates diagnostic data in the table for the specified node using a dictionary (PyQt6).

        Args:
            node_num: The node number to update.
            diag_data: A dictionary where keys correspond to column header labels
                       and values are the data to be displayed.

        Returns:
            True if the node was found and updated, False otherwise.
        """

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if item and item.text() == f'[{node_num:02}]':
                for key, value in diag_data.items():
                    # Find the column index based on the header label (PyQt6 change).
                    try:
                        # In PyQt6, horizontalHeaderItem() returns a QTableWidgetItem or None
                        # We need to iterate through the header items.
                        for col in range(self.tableWidget.columnCount()):
                            header_item = self.tableWidget.horizontalHeaderItem(col)
                            if header_item and header_item.text() == key:
                                break  # Found the column
                        else:  # Loop completed without finding the header
                            raise ValueError(f"Header '{key}' not found")
                    except ValueError as e:
                        # print(f"Warning: {e}")
                        continue

                    try:
                        str_value = str(value)
                    except (TypeError, ValueError) as e:
                        str_value = f"Error: {e}"

                    new_item = QTableWidgetItem(str_value)
                    self.tableWidget.setItem(row, col, new_item)


if __name__ == "__main__":
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    log.info('Start application')

    config_dir_path = user_data.get_user_data_path()
    config_file_path = config_dir_path / 'config.json'

    # Create the directory if it doesn't exist
    if not config_dir_path.exists():
        config_dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Config dir created {config_dir_path}")

    app = QApplication(sys.argv)

    win = DiagWindow(config_file_path)
    win.show()
    sys.exit(app.exec())
