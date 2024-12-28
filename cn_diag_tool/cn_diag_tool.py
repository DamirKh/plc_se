import datetime
import subprocess
import logging
import os
import sys
import time

import json

from PyQt6.QtCore import Qt
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QCursor, QColor, QBrush
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QMainWindow, QApplication, QProgressDialog, QVBoxLayout, QMessageBox, QLabel, QDialog, \
    QWidget, QTableWidgetItem, QTableWidget

from cn_diag_tool_ui import Ui_MainWindow
from form_tab_widget import FormTabWidget
from cndt_config_dialog import Ui_Dialog
from Plc_connection_worker import PLCConnectionWorker
from cn_lib import scan_cn

from logger_widget import QTextEditLogger
import floating_table_ui

import user_data

# from DragTable import DraggableTableWidget

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

MEDIA_CONVERTER = '=/='

class Header_Item_NodeNum(QTableWidgetItem):
    def __init__(self, node_num: int, *args, **kwargs):
        color = QColor('yellow')
        super().__init__(*args, **kwargs)
        assert 0 < node_num < 100
        self.setText(f'[{node_num:02}]')
        # self.setBackground(QBrush(color))
        self.setData(Qt.ItemDataRole.UserRole, node_num)

class Item_Placeholder(QTableWidgetItem):
    def __init__(self, *args, **kwargs):
        color = QColor('peru')
        super().__init__(*args, **kwargs)
        self.setBackground(QBrush(color))

class GeometrySaver(QWidget):
    def geometry_saver_init(self, settings_key: str):
        self.geometry_saver_settings = Glob_settings
        self._geometry_settings_key = settings_key
        self.restore_geometry()

    def save_geometry(self):
        if self._geometry_settings_key:
            self.geometry_saver_settings.setValue(self._geometry_settings_key, self.saveGeometry())
            log.debug(f'Geometry {self._geometry_settings_key} loaded ')

    def restore_geometry(self):
        if self._geometry_settings_key:
            geometry = self.geometry_saver_settings.value(self._geometry_settings_key)
            if geometry is not None:
                try:
                    self.restoreGeometry(geometry)
                    log.debug(f'Geometry {self._geometry_settings_key} restored')
                except TypeError as e:
                    log.error(f"Error restoring geometry: {e}")

    def closeEvent(self, event):  # Override closeEvent if not using a main window.
        self.save_geometry()
        super().closeEvent(event)


class CrossTableDialog(QDialog, floating_table_ui.Ui_Dialog, GeometrySaver):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Bad Frame Cross Table")

        self.setupUi(self)
        self.connectSignalsSlots()
        self.geometry_saver_init(settings_key="CrossTableDialog")
        self.hide()

    def connectSignalsSlots(self):
        pass

    def fill_table(self, from_table: QTableWidget):
        log.debug('Fill crosstable')
        self.tableWidget.clear()
        rows = from_table.rowCount()
        self.tableWidget.setRowCount(rows)
        self.tableWidget.setColumnCount(rows)
        for row in range(rows):
            visual_index = from_table.verticalHeader().visualIndex(row)
            V_item = QTableWidgetItem(from_table.verticalHeaderItem(row).text())
            H_item = QTableWidgetItem(from_table.verticalHeaderItem(row).text())
            self.tableWidget.setVerticalHeaderItem(visual_index, V_item)
            self.tableWidget.setHorizontalHeaderItem(visual_index, H_item)
            if V_item.text()==MEDIA_CONVERTER:
                placeholder = Item_Placeholder()
                for c in range(self.tableWidget.columnCount()):
                    self.tableWidget.setItem(visual_index, c, placeholder.clone())
                    self.tableWidget.setItem(c, visual_index, placeholder.clone())


    def update_diag_data(self, node_num, diag_data: dict):
        """Updates diagnostic data in the crosstable for the specified node.

        Args:
            node_num: The node number to update.
            diag_data: A dictionary where keys correspond to column header labels
                       and values are the data to be displayed.
        """

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.verticalHeaderItem(row)
            if item and item.text() == f'[{node_num:02}]':
                for key, value in diag_data.items():
                    # ## Node intersection updates here
                    if type(key) == type('') and key.startswith('#err_'):
                        if value:
                            error_node_num_in_log = f'[{value:02}]'

                            for col in range(self.tableWidget.columnCount()):
                                header_item = self.tableWidget.horizontalHeaderItem(col)
                                if header_item and header_item.text() == error_node_num_in_log:
                                    err_item = QTableWidgetItem('')
                                    if error_node_num_in_log == item.text():
                                        err_item.setData(Qt.ItemDataRole.DecorationRole, QtGui.QColor('yellow'))
                                        # err_item.setData(Qt.ItemDataRole.UserRole)
                                    else:
                                        err_item.setData(Qt.ItemDataRole.DecorationRole, QtGui.QColor('red'))
                                    self.tableWidget.setItem(row, col, err_item)
                                    break  # Found the column
                    # ## End of Node intersection updates


class LogWindow(QDialog, GeometrySaver):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
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
        self.geometry_saver_init(settings_key="LogWindowGeometry")
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
    labels = [
        'Serial',
        'reply_time',
        # '#err_0',
        # '#err_1',
        # '#err_2',
        # '#err_3',
        # '#err_4',
        # '#err_5',
        # '#err_6',
        # '#err_7',
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

    def __init__(self, config_file_path, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # self.tableWidget = DraggableTableWidget(parent=self.centralwidget)
        # self.tableWidget.setObjectName("tableWidget")

        self.logger_window = LogWindow(self)
        self.MyCrossTable = CrossTableDialog(parent=self)
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
        self.actionShow_CrossTable.triggered.connect(self.show_crosstable)
        self.tableWidget.rowsMoved.connect(self.sync_crosstable_rows)

    def sync_crosstable_rows(self):
        """Synchronizes the row order of the CrossTableDialog with self.tableWidget."""
        if self.MyCrossTable is not None:  # Check if dialog was created.
            log.debug(f'Synchronise table')
            self.MyCrossTable.fill_table(self.tableWidget)

    def show_log(self):
        self.logger_window.show()

    def show_crosstable(self):
        log.debug('Hit show crosstable')
        self.MyCrossTable.show()

    def add_media_converter(self):
        cn_media_converter_item = QTableWidgetItem(MEDIA_CONVERTER)

        log.debug("Hit add media converter")
        new_row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(new_row)
        self.tableWidget.setVerticalHeaderItem(new_row, cn_media_converter_item)

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

        self.tableWidget.setRowCount(len(nodes))
        self.tableWidget.setColumnCount(len(DiagWindow.labels))
        self.tableWidget.setHorizontalHeaderLabels(DiagWindow.labels)

        row = -1
        for cn_module_serial, cn_path in paths.items():
            row += 1
            node_num = int(cn_path.split('/')[-1])

            cn_node_worker = PLCConnectionWorker(node_num)
            cn_node_worker.path = cn_path
            cn_node_worker.signals.read_done.connect(self.update_diag_data)
            cn_node_worker.signals.read_done.connect(self.MyCrossTable.update_diag_data)
            cn_node_worker.start()

            self._workers[node_num] = cn_node_worker

            cn_module_nodenum_Item = Header_Item_NodeNum(node_num)
            self.tableWidget.setVerticalHeaderItem(row, cn_module_nodenum_Item)

            cn_module_serial_Item = QTableWidgetItem(str(cn_module_serial))
            self.tableWidget.setItem(row, 0, cn_module_serial_Item)

        self._app.instance().restoreOverrideCursor()
        self.MyCrossTable.fill_table(self.tableWidget)
        self.pushButtonAddMediaConverter.setEnabled(True)
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
        """Updates diagnostic data in the table for the specified node using a dictionary.

        Args:
            node_num: The node number to update.
            diag_data: A dictionary where keys correspond to column header labels
                       and values are the data to be displayed.
        """

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.verticalHeaderItem(row)
            if item and item.text() == f'[{node_num:02}]':
                for key, value in diag_data.items():
                    if key not in DiagWindow.labels:
                        continue
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

    def update_node_error_intersect(self, row_num: int, error_dict: dict):
        pass


if __name__ == "__main__":
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    log.info('Start application')

    config_dir_path = user_data.get_user_data_path()
    config_file_path = config_dir_path / 'config.json'

    Glob_settings = QSettings(user_data.Organisation, user_data.AppName)

    # Create the directory if it doesn't exist
    if not config_dir_path.exists():
        config_dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Config dir created {config_dir_path}")

    app = QApplication(sys.argv)

    win = DiagWindow(config_file_path)
    win.show()
    sys.exit(app.exec())
