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
    QWidget

from helper_window_ui import Ui_MainWindow
from form_tab_widget import FormTabWidget
from config_helper_dialog_ui import Ui_Dialog
from Plc_connection_worker import PLCConnectionWorker

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


class HelperWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, data, config_file_path, parent=None):
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

        self._worker = PLCConnectionWorker()
        self._worker.signals.connected.connect(self.on_connection_check_connected)
        self._worker.signals.lost_connection.connect(self.on_connection_lost)
        self._worker.signals.non_fatal_error.connect(self.non_fatal)

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

        # PLC Settings
        config['PLC'] = {
            'path': self.lineEditConnectionPath.text(),
        }

        # Tab Settings
        config['TABS'] = []
        for i in range(self.tabWidget.count()):
            tab_name = self.tabWidget.tabText(i)
            widget: FormTabWidget = self.tabWidget.widget(i)

            # Get tag data from the widget
            tag_data = widget.get_table_data()

            config['TABS'].append({
                'name': tab_name,
                'data': tag_data,
            })

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

            # Load PLC Settings
            plc_settings = config.get('PLC', {})  # Get PLC settings with fallback
            plc_path = plc_settings.get('path', "")
            self.lineEditConnectionPath.setText(plc_path)

            # Load Tab Settings
            for tab_info in config.get('TABS', []):
                tab_name = tab_info.get('name', "Unnamed")
                tag_data = tab_info.get('data', {})

                # Create a new tab and populate data
                self.create_tab_from_data(tab_name, tag_data)
            log.info(f"Configuration loaded from {filename}")

        except FileNotFoundError:
            log.warning("Configuration file not found. Using defaults.")
        except json.JSONDecodeError as e:
            log.error(f"Error decoding JSON configuration: {e}")

    def tab_close(self, index):
        """Handles the tabCloseRequested signal of the QTabWidget."""

        # Get the widget for the tab to be closed
        widget = self.tabWidget.widget(index)
        widget_title = self.tabWidget.tabText(index)  # Get the tab title
        # Optional: Ask the user for confirmation before closing
        if self._confirm_on_tab_close:
            if QMessageBox.question(
                    self,
                    "Close Tab",
                    f"Are you sure you want to close tab {widget_title} ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No  # Set default button
            ) == QMessageBox.StandardButton.No:
                return  # Don't close the tab if the user clicked "No"

        # Remove the tab from the tab widget
        if widget is not None:
            widget.deleteLater()  # Ensure proper cleanup
        self.tabWidget.removeTab(index)

    def create_tab_from_data(self, tab_name, tag_data):
        """Creates a new tab and populates it with tag data."""

        form_tab_widget = FormTabWidget(worker=self._worker, timer=self._update_timer)
        self.tabWidget.addTab(form_tab_widget, tab_name)

        # Populate the table in the new tab
        for row_index, row_data in enumerate(tag_data):
            # 1. Ensure enough rows:
            while row_index >= form_tab_widget.model.rowCount(QtCore.QModelIndex()):
                form_tab_widget.model.add_new_row()
            # 2. Ensure enough columns:
            while len(row_data) > form_tab_widget.model.columnCount(QtCore.QModelIndex()):
                form_tab_widget.model.add_new_column()
            # 3. Populate each cell in the row
            for col_index, cell_value in enumerate(row_data):
                form_tab_widget.model.setData(
                    form_tab_widget.model.index(row_index, col_index),
                    cell_value,
                    Qt.ItemDataRole.EditRole
                )

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
        self.pushButtonAddTab.clicked.connect(self.onAddTab)
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

        self._worker.path = _path
        connected, descr = self._worker.connect()
        self._app.instance().restoreOverrideCursor()

        if connected:
            self._worker_connected()
            self._worker.signals.current_worker_load.connect(self.worker_load)
            self._worker.signals.plc_current_time.connect(self.plc_onboard_time)
            # self.writer_worker = PLCConnectionWorkerWriter(self.lineEditConnectionPath.text(), self.writer_mutex)
            QMessageBox.information(self, "Success", descr)
            self._worker.start()
        else:
            QMessageBox.warning(self, f"Error connecting to PLC", descr)
            self._worker_not_connected()

    def tab_changed(self, index):
        # print(f"Activate tab {index}")
        i = 0
        widget: FormTabWidget = self.tabWidget.widget(i)
        while widget is not None:
            if index == i:
                widget.you_are_visible(True)
            else:
                widget.you_are_visible(False)
            i += 1
            widget: FormTabWidget = self.tabWidget.widget(i)

    def on_connection_check_connected(self, success, long_string, name):
        # self.progress_dialog.hide()
        if success:
            self.labelProjectName.setText(name)
        else:
            pass
            # self._worker_not_connected()
            # QMessageBox.warning(self, f"Error connecting to PLC", long_string)

    def onAddTab(self):
        tab_name = self.lineEdit_2.text() or "Unnamed"
        if not tab_name:
            return

        # Create an instance of your FormTabWidget
        form_tab_widget = FormTabWidget(worker=self._worker, timer=self._update_timer)
        self.tabWidget.addTab(form_tab_widget, tab_name)

        self.lineEdit_2.clear()

    def plc_onboard_time(self, plc_time: datetime.datetime):
        time_repr = plc_time.strftime("%d %b %Y %H:%M:%S")
        self.status_bar_label_1.setText(time_repr)


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
    test_data = [
        ['TAG1', 111, 100],
        ['TAG2', 222, 100],
        ['TAG3', 333, 100],
        ['TAG4', 444, 100],

    ]
    win = HelperWindow(test_data, config_file_path)
    win.show()
    sys.exit(app.exec())
