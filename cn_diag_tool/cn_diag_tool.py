import datetime
import subprocess
import logging
import os
import sys
import time

import json
from fileinput import filename

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QCursor, QColor, QBrush, QFont
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QMainWindow, QApplication, QProgressDialog, QVBoxLayout, QMessageBox, QLabel, QDialog, \
    QWidget, QTableWidgetItem, QTableWidget, QGridLayout, QGroupBox, QCheckBox, QLineEdit, QDialogButtonBox, \
    QHeaderView, QFileDialog

#https://stackoverflow.com/a/66104687/8124158
QtCore.QDir.addSearchPath('asset', 'asset/')

from cn_diag_tool_ui import Ui_MainWindow
from cndt_config_dialog import Ui_Dialog
from Plc_connection_worker import PLCConnectionWorker
from cn_lib import scan_cn
from pycomm3.exceptions import CommError, RequestError

import floating_table_ui

import user_data

# from DragTable import DraggableTableWidget

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

MEDIA_CONVERTER = '=/='
RED = QColor('red')
GREEN = QColor('green')
GREY = QColor('grey')
LED_blink_period = 300  # msec
TICK_TACK = False
My_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
HOR_HEADER_FONT = QFont()


class HeaderData(object):
    def __init__(self, sid: str, comment: str = '', hint: str = '', longread: str = '', size: int = None):
        self.sid = sid
        self.comment = comment
        self.hint = hint
        self.longread = longread
        self.size = size


LABELS = [
    HeaderData('Serial',
               comment='номер',
               hint='Серийный номер модуля',
               ),
    HeaderData('reply_time',
               comment='Ответ',
               hint='Время ответа, мкс',
               longread="""Время ответа в микросекундах. 
               Возможно, показания некоректны и малоинформативны""",
               ),
    HeaderData('LED_A',
               comment='A',
               hint='Состояние индикатора A',
               longread="""Состояние индикатора на модуле. 
               Состояния при которых нет связи с модулем не могут быть отображены, потому что нет связи с модулем""",
               ),
    HeaderData('LED_B',
               comment='B',
               hint='Состояние индикатора B',
               longread="""Состояние индикатора на модуле. 
               Состояния при которых нет связи с модулем не могут быть отображены, потому что нет связи с модулем""",
               ),
    # '#err_0',
    # '#err_1',
    # '#err_2',
    # '#err_3',
    # '#err_4',
    # '#err_5',
    # '#err_6',
    # '#err_7',
    HeaderData('channel_A_frame_error',
               comment='A err',
               hint='Счетчик ошибок канала A',
               longread="Счетчик ошибок канала A\n"
                        "8 bit",
               ),
    HeaderData('channel_A_frame_error/s',
               comment='A err/s',
               hint='Ошибки канала A в секунду',
               longread="""Ошибки по каналу А за последнюю секунду""",
               ),
    HeaderData('channel_B_frame_error',
               comment='B err',
               hint='Счетчик ошибок канала B',
               longread="""Счетчик ошибок канала B 
               (8bit)""",
               ),
    HeaderData('channel_B_frame_error/s',
               comment='B err/s',
               hint='Ошибки канала B в секунду',
               longread="""Ошибки по каналу B за последнюю секунду""",
               ),
    HeaderData('selected_channel_frame_error',
               comment='Err',
               hint='Счетчик ошибок по активному каналу',
               longread="Счетчик ошибок по активному каналу\n"
                        "8 bit",
               ),
    HeaderData('selected_channel_frame_error/s',
               comment='Err/s',
               hint='Ошибки по активному каналу',
               longread="""Ошибки по активному каналу за последнюю секунду""",
               ),
    HeaderData('Active_Channel',
               comment='Акт.',
               hint='Активный канал',
               longread="""Канал, выбранный активным на данный момент""",
               ),
    HeaderData('Redundancy_Warning',
               comment='Резерв',
               hint='Флаг отсутсвия резерва',
               longread="""Флаг отсутсвия резерва
               активируется в случае отсутсвия резервного канала""",
               ),

    HeaderData('good_frames_transmitted',
               comment='⇑',
               hint='Счетчик успешно переданных кадров',
               longread="""Счетчик успешно переданных кадров\n24 бита\nБолее информативно поле '⇑/с'""",
               ),
    HeaderData('good_frames_transmitted/s',
               comment='⇑/с',
               hint='Передано успешно',
               longread="""Успешно передано кадров за последнюю секунду""",
               ),
    HeaderData('aborted_frame_transmitted',
               comment='⇞',
               hint='Счетчик оборыва передачи',
               longread="""Счетчик обрыва передачи\n8 бит""",
               ),

    HeaderData('good_frames_received',
               comment='⇓',
               hint='Счетчик успешно принятых кадров',
               longread="""Счетчик успешно принятых кадров\n24 бита\nБолее информативно поле '⇓/с'""",
               ),
    HeaderData('good_frames_received/s',
               comment='⇓/с',
               hint='Принято успешно',
               longread="""Успешно принято кадров за последнюю секунду""",
               ),
    HeaderData('aborted_frames_received',
               comment='⇟',
               hint='Счетчик обрыва приема',
               longread="""Счетчик обрыва приема\n8 бит""",
               ),

    HeaderData('noise_hits',
               comment='∿',
               hint='Счетчик обнаружения шума',
               longread="""Счетчик обнаружения шума на линии
               (8 бит)""",
               ),
    HeaderData('noise_hits/s',
               comment='∿/с',
               hint='Приращение шума за секунду',
               longread="""Приращение счетчика шума за последнюю секунду""",
               ),

    HeaderData('collisions',
               comment='⇆',
               hint='',
               longread="Счетчик обнаруженных столкновений\n"
                        "8 бит",
               ),
    HeaderData('collisions/s',
               comment='⇆/с',
               hint='',
               longread="""Приращение счетчика столкновений за последнюю секунду""",
               ),

    HeaderData('highwaters',
               comment='Перегрузка',
               hint='',
               longread="""""",
               ),
    HeaderData('nut_overloads',
               comment='NUT перегрузка',
               hint='',
               longread="""""",
               ),
    HeaderData('nut_overloads/s',
               comment='NUT перегрузка/c',
               hint='',
               longread="""""",
               ),
    HeaderData('slot_overloads',
               comment='slot_overloads',
               hint='',
               longread="""""",
               ),
    HeaderData('slot_overloads/s',
               comment='slot_overloads/s',
               hint='',
               longread="""""",
               ),
    HeaderData('blockages',
               comment='blockages',
               hint='',
               longread="""""",
               ),
    HeaderData('blockages/s',
               comment='blockages/s',
               hint='',
               longread="""""",
               ),
    HeaderData('non_concurrence',
               comment='non_concurrence',
               hint='',
               longread="""""",
               ),
    HeaderData('non_concurrence/s',
               comment='non_concurrence/s',
               hint='',
               longread="""""",
               ),
    # rarely used
    HeaderData('lonely_counter',
               comment='lonely_counter',
               hint='',
               longread="""""",
               ),
    HeaderData('duplicate_node',
               comment='duplicate_node',
               hint='',
               longread="""""",
               ),
    HeaderData('mod_mac_id',
               comment='mod_mac_id',
               hint='',
               longread="""""",
               ),
    HeaderData('non_lowman_mods',
               comment='non_lowman_mods',
               hint='',
               longread="""""",
               ),
    HeaderData('rogue_count',
               comment='rogue_count',
               hint='',
               longread="""""",
               ),
]


class GeometrySaver(QWidget):
    def geometry_saver_init(self, settings_key: str):
        self.geometry_saver_settings = Glob_settings
        self._geometry_settings_key = settings_key
        self.restore_geometry()

    def save_geometry(self):
        if self._geometry_settings_key:
            self.geometry_saver_settings.setValue(self._geometry_settings_key, self.saveGeometry())
            log.debug(f'Geometry {self._geometry_settings_key} saved')

    def restore_geometry(self):
        if self._geometry_settings_key:
            geometry = self.geometry_saver_settings.value(self._geometry_settings_key)
            if geometry is not None:
                try:
                    self.restoreGeometry(geometry)
                    log.debug(f'Geometry {self._geometry_settings_key} restored')
                except TypeError as e:
                    log.error(f"Error restoring geometry: {e}")
            else:
                log.debug(f'No geometry settings found for {self._geometry_settings_key}')

    def closeEvent(self, event):  # Override closeEvent if not using a main window.
        self.save_geometry()
        super().closeEvent(event)


class ConfigureDialog(QDialog, GeometrySaver):
    filterChanged = QtCore.pyqtSignal(int, str)  # Define the signal

    def __init__(self, table_widget: QTableWidget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Data View")
        self.tableWidget = table_widget

        # Use a QTableWidget for the configuration options
        self.configTable = QTableWidget(0, 3, self)  # 0 rows initially, 3 columns
        self.configTable.setHorizontalHeaderLabels(["Column Name", "Description", "Visibility"])
        header = self.configTable.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Stretch column Hint
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Fit checkbox

        try:
            for col in range(self.tableWidget.columnCount()):
                header_item = self.tableWidget.horizontalHeaderItem(col)
                header_data:HeaderData = header_item.data(My_ROLE)
                if header_item and header_item.text():
                    column_name = header_item.text()
                else:
                    continue  # do not configure the column without header or text in header

                row = self.configTable.rowCount()
                self.configTable.insertRow(row)

                name_item = QTableWidgetItem(column_name)
                name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)  # Make name read-only
                self.configTable.setItem(row, 0, name_item)

                hint = QTableWidgetItem(header_data.hint)
                hint.setToolTip(header_data.longread)
                self.configTable.setItem(row, 1, hint)

                check_box = QtWidgets.QCheckBox()
                check_box.setChecked(not self.tableWidget.isColumnHidden(col))
                check_box.stateChanged.connect(lambda state, col=col: self.toggle_column_visibility(col, state))
                self.configTable.setCellWidget(row, 2, check_box)

        except IndexError as e:
            QMessageBox.critical(self, "Error", str(e))
            raise  # Reraise for external handling

        # Layout
        main_layout = QtWidgets.QVBoxLayout(self)  # Use a QVBoxLayout
        main_layout.addWidget(self.configTable)  # Add the table to the layout

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        self.geometry_saver_init(settings_key="ConfigDialog")

    def toggle_column_visibility(self, column_index, state):
        if state == 2:  # Checked (Qt.CheckState.Checked is 2)
            self.tableWidget.setColumnHidden(column_index, False)
        elif state == 0:  # Unchecked (Qt.CheckState.Unchecked is 0)
            self.tableWidget.setColumnHidden(column_index, True)


class QTextEditLogger(logging.Handler, QtCore.QObject):
    appendPlainText = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        QtCore.QObject.__init__(self)
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.appendPlainText.connect(self.widget.appendPlainText)

    def emit(self, record):
        msg = self.format(record)
        self.appendPlainText.emit(msg)


class StatusBarLogger(logging.Handler, QtCore.QObject):
    updateStatusBar = QtCore.pyqtSignal(str)

    def __init__(self, statusbar, level = logging.INFO):
        logging.Handler.__init__(self, level)
        QtCore.QObject.__init__(self)
        self.statusbar = statusbar
        self.updateStatusBar.connect(self.statusbar.showMessage)

    def emit(self, record):
        msg = self.format(record)
        self.updateStatusBar.emit(msg)


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
            self.tableWidget.setColumnWidth(row, 15)
            self.tableWidget.setVerticalHeaderItem(visual_index, V_item)
            self.tableWidget.setHorizontalHeaderItem(visual_index, H_item)
            if V_item.text() == MEDIA_CONVERTER:
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


class HelperConfigDialog(QDialog, Ui_Dialog):
    def __init__(self, callback, timer_value, confirmation, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._callback = callback
        self.connectSignalsSlots()
        self.spinBox.setValue(timer_value)
        self.checkBox.setChecked(confirmation)

    def connectSignalsSlots(self):
        self.spinBox.valueChanged.connect(self._callback)


class DiagWindow(QMainWindow, Ui_MainWindow):
    labels = [l.sid for l in LABELS]

    def __init__(self, config_file_path, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.statusbar.showMessage("Start application")

        self.my_status_updater = StatusBarLogger(self.statusbar)
        self.my_status_updater.setFormatter(
            logging.Formatter('%(message)s')
        )
        logging.getLogger().addHandler(self.my_status_updater)

        # self.tableWidget = DraggableTableWidget(parent=self.centralwidget)
        # self.tableWidget.setObjectName("tableWidget")

        self.logger_window = LogWindow(self)
        self.MyCrossTable = CrossTableDialog(parent=self)
        self.connectSignalsSlots()
        self._app_config_file_path = config_file_path
        self._config_file_path = None
        self._confirm_on_close = True
        self._site_changed = False
        self._prev_update_time = time.monotonic_ns()

        self._app: QtWidgets.QApplication = QtWidgets.QApplication.instance()
        # creating a label widget for status bar
        self.status_bar_label_1 = QLabel("Not connected yet")

        self.status_bar_label_1.setStyleSheet("border :1px solid blue;")
        # adding label to status bar
        self.statusBar().addPermanentWidget(self.status_bar_label_1)

        self._workers = {}
        self._site_loaded = False

        # Create a timer for periodic LED blinkers
        self.led_blink_timer = QTimer(self)
        self.led_blink_timer.setSingleShot(False)
        self.led_blink_timer.setInterval(300)
        self.led_blink_timer.timeout.connect(self.led_blinker)
        self.load_app_config()
        self.tableWidget._config_file = user_data.get_user_data_path() / 'main_table.json'

    @property
    def config_file_path(self):
        return self._config_file_path

    @config_file_path.setter
    def config_file_path(self, value: str):
        self._config_file_path = value
        self.setWindowTitle(f"ControlNet diagnostic tool  {value}")

    def non_fatal(self, message):
        self.statusBar().showMessage(message, 10000)

    def save_site_config(self, filename=None):
        """Saves the application configuration to a JSON file."""

        filename = filename or self.config_file_path
        if not filename:
            self.save_site_config_as()
            return
        config = {}

        # CN Settings
        config['CN'] = {
            'path': self.lineEditConnectionPath.text(),
        }

        # nodes settings
        nodes = {}
        nodes[MEDIA_CONVERTER] = []
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.verticalHeaderItem(row)
            if item and item.text() !=  MEDIA_CONVERTER:
                nodes[item.text()] = self.tableWidget.verticalHeader().visualIndex(row)
            else:
                nodes[MEDIA_CONVERTER].append(self.tableWidget.verticalHeader().visualIndex(row))
        config['nodes'] = nodes

        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=4)  # Use indent for readability
            log.info(f"Configuration saved to {filename}")
            self._site_changed = False
            return True
        except (IOError, OSError) as e:
            log.error(f"Error saving configuration: {e}")
            # Use a QMessageBox for error dialog:
            QMessageBox.critical(self, "Error Saving Configuration",
                                 f"Could not save configuration to {filename}:\n{e}")
            return False

    def save_app_config(self):
        config = {}
        # confirmation on tab close
        config['Close_tab_confirm'] = self._confirm_on_close
        # timer setting
        config['Blinker'] = self.led_blink_timer.interval()
        try:
            with open(self._app_config_file_path, 'w') as f:
                json.dump(config, f, indent=4)  # Use indent for readability
            log.info(f'Application configuration saved to {self._app_config_file_path}')
            return True
        except (IOError, OSError) as e:
            log.error(f"Error saving configuration: {e}")
            return False

    def load_app_config(self):
        """Loads the application configuration from a JSON file."""
        try:
            with open(self._app_config_file_path, 'r') as f:
                config: dict = json.load(f)
                self._confirm_on_close = config.get('Close_tab_confirm', True)
                self.led_blink_timer.setInterval(config.get('Blinker', LED_blink_period))
            log.info(f'Application configuration loaded from {self._app_config_file_path}')
            return True
        except FileNotFoundError:
            log.warning("Configuration file not found. Using defaults.")
        except json.JSONDecodeError as e:
            log.error(f"Error decoding JSON configuration: {e}")
        self._confirm_on_close = True
        self.led_blink_timer.setInterval(LED_blink_period)

    def save_site_config_as(self):
        """Saves the application configuration to a user-specified JSON file."""
        prposed_filename_or_dir = self.config_file_path or user_data.get_user_data_path()/'sites'
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Site Configuration As...",
            str(prposed_filename_or_dir),  # Default directory (empty string for user's home directory)
            "JSON Files (*.json);;All Files (*)",  # Filter
        )

        if filename:  # Check if the user selected a file
            if not filename.lower().endswith(".json"):
                filename += ".json"  # Add .json extension if not present
            if self.save_site_config(filename=filename): # if success
                self.config_file_path = filename  # update path in-place for future 'save' calls
            else:
                pass

    def load_site_config(self, site_conf_filename):
        """Loads the application configuration from a JSON file."""
        try:
            with open(site_conf_filename, 'r') as f:
                config = json.load(f)

            # Load ControlNet Settings
            plc_settings = config.get('CN', {})  # Get CN settings with fallback
            plc_path = plc_settings.get('path', "")
            self.lineEditConnectionPath.setText(plc_path)

            self.tableWidget.clearContents()
            self.tableWidget.setRowCount(0)

            for _node_num, worker in self._workers.items():
                # assert worker is PLCConnectionWorker
                worker.stop()
            if len(self._workers):
                progress = QProgressDialog("Please wait...", '', 0, 0, self)  # 0,0 for indeterminate progress
                progress.setWindowModality(Qt.WindowModality.WindowModal)  # Make it blocking (optional)
                progress.show()
                QApplication.processEvents()  # Important to show the dialog before sleeping
                t = QTimer()
                t.setSingleShot(True)  # Run only once
                # t.timeout.connect(self.finish_work)
                t.start(2000)  # 2000 ms = 2 seconds
                while t.isActive():
                    QApplication.processEvents()
                # Check if cancelled (if you made the dialog modal and added a cancel button)
                if progress.wasCanceled():
                    # Handle cancellation
                    pass
                self._workers = {}
                progress.close()  # Close the dialog after completion

            self.pushButtonConnect.setEnabled(True)

            # load nodes
            visual_order = []
            _media_convs = config['nodes'].pop(MEDIA_CONVERTER, [])
            for node in config['nodes']:
                node_num = int(node[1:-1])
                row = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row)
                cn_module_nodenum_Item = Header_Item_NodeNum(node_num)
                visual_order.append(config['nodes'][node])
                self.tableWidget.setVerticalHeaderItem(row, cn_module_nodenum_Item)

            # Restore row order (important to do this LAST)
            for i, visual_index in enumerate(visual_order):
                self.tableWidget.verticalHeader().moveSection(self.tableWidget.verticalHeader().visualIndex(i), visual_index)
            for _media_conv in _media_convs:
                self.add_media_converter()
                self.tableWidget.verticalHeader().moveSection(self.tableWidget.rowCount()-1, _media_conv)
            self._site_loaded = True
            self._site_changed = False
            log.info(f"Configuration loaded from {site_conf_filename}")

        except FileNotFoundError:
            log.warning("Configuration file not found. Using defaults.")
        except json.JSONDecodeError as e:
            log.error(f"Error decoding JSON configuration: {e}")

    def load_site_from_file(self):
        """Load the application configuration from a user-specified JSON file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Site Configuration From...",
            str(user_data.get_user_data_path()/'sites'),  # Default directory (empty string for user's home directory)
            "JSON Files (*.json);;All Files (*)",  # Filter
        )

        if filename:  # Check if the user selected a file
            self.load_site_config(site_conf_filename=filename)
            self.config_file_path = filename  # update path in-place for future 'save' calls

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
        self.actionAbout.triggered.connect(self.about)
        self.actionLoad_site.triggered.connect(self.load_site_from_file)
        self.actionSave.triggered.connect(self.save_site_config)
        self.actionSave_as.triggered.connect(self.save_site_config_as)
        self.actionRead_Timer.triggered.connect(self.on_read_timer_conf)
        # self.actionEnable_writing_to_PLC.triggered.connect(self.on_write_enable)
        self.actionOpen_config_folder.triggered.connect(self.on_open_folder)
        self.actionShow_log.triggered.connect(self.show_log)
        self.actionShow_CrossTable.triggered.connect(self.show_crosstable)
        self.actionTable_Config.triggered.connect(self.config_dialog)
        self.actionExport_to_Excel.triggered.connect(self.export_to)
        self.tableWidget.rowsMoved.connect(self.sync_crosstable_rows)

    def config_dialog(self):
        log.debug("Open config dialog")
        dialog = ConfigureDialog(self.tableWidget, self)  # Pass tableWidget and parent
        dialog.exec()  # Show modally

    def sync_crosstable_rows(self):
        """Synchronizes the row order of the CrossTableDialog with self.tableWidget."""
        self._site_changed = True
        if self.MyCrossTable is not None:  # Check if dialog was created.
            log.debug(f'Synchronise table')
            self.MyCrossTable.fill_table(self.tableWidget)

    def show_log(self):
        self.logger_window.show()

    def show_crosstable(self):
        log.debug('Hit show crosstable')
        self.MyCrossTable.show()

    def export_to(self):
        if len(self._workers):
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export data to...",
                "",  # Default directory (empty string for user's home directory)
                "XLSX Files (*.xlsx);;All Files (*)",  # Filter
            )

            if filename:  # Check if the user selected a file
                if not filename.lower().endswith(".xlsx"):
                    filename += ".xlsx"  # Add .xlsx extension if not present
                if self.tableWidget.export_to_excel(filename=filename):  # if success
                    QMessageBox.information(self, "Success Exporting Data",
                                         f"Data exported to {filename}")
                    pass
                else:
                    QMessageBox.critical(self, "Error Exporting Data",
                                         f"Could not export data to {filename}:\n See log window for details")

    def add_media_converter(self):
        cn_media_converter_item = QTableWidgetItem(MEDIA_CONVERTER)

        log.debug("Hit add media converter")
        new_row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(new_row)
        self.tableWidget.setVerticalHeaderItem(new_row, cn_media_converter_item)
        self._site_changed = True

    def on_write_enable(self, state):
        # print(f"Enable writing {state}")
        log.info(f"Write enabled = {state}")

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
        old_value = self.led_blink_timer.interval()
        dialog = HelperConfigDialog(parent=self,
                                    timer_value=self.led_blink_timer.interval(),
                                    confirmation=self._confirm_on_close,
                                    callback=self.led_blink_timer.setInterval)
        result = dialog.exec()
        if result:
            self._confirm_on_close = dialog.checkBox.checkState().value == QtCore.Qt.CheckState.Checked.value
        else:
            self.led_blink_timer.setInterval(old_value)

    def onButtonConnect(self):
        self.lineEditConnectionPath.setEnabled(False)
        self.pushButtonConnect.setEnabled(False)
        _path = self.lineEditConnectionPath.text()

        self._app.instance().setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))

        try:
            nodes, paths = scan_cn(_path, p=log.debug)
        except (TimeoutError, CommError) as e:
            self._app.instance().restoreOverrideCursor()
            log.critical(f"Error Scanning ControlNet (no route to IP address?) {e}")
            QMessageBox.critical(self, "Error Scanning ControlNet",
                                 f"Error occurs while scanning ControlNet!\n(no route to IP address?)\n\n"
                                 f"{e}")
            return
        except RequestError as e:
            self._app.instance().restoreOverrideCursor()
            log.critical(f"Error Scanning ControlNet (bad connection path?) {e}")
            QMessageBox.critical(self, "Error Scanning ControlNet",
                                 f"Error occurs while scanning ControlNet!\n(bad connection path?)\n\n"
                                 f"{e}")
            return
        log.info(f'ControlNet [{_path}] scan complete')
        if not self._site_loaded:
            self.tableWidget.setRowCount(len(nodes))

        #columns
        self.tableWidget.setColumnCount(len(LABELS))
        for column, header_data in enumerate(LABELS):
            column_header_item = QTableWidgetItem(header_data.comment)
            column_header_item.setData(My_ROLE, header_data)
            column_header_item.setToolTip(header_data.longread)
            font = column_header_item.font()  # Get the current font
            font.setPointSize(12)  # Set the desired point size (e.g., 12)
            column_header_item.setFont(font)  # Set the modified font back
            self.tableWidget.setHorizontalHeaderItem(column, column_header_item)

        # labels = [s.sid for s in LABELS]
        # self.tableWidget.setHorizontalHeaderLabels(labels)

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

            if not self._site_loaded:
                cn_module_nodenum_Item = Header_Item_NodeNum(node_num)
                self.tableWidget.setVerticalHeaderItem(row, cn_module_nodenum_Item)

                cn_module_serial_Item = QTableWidgetItem(str(cn_module_serial))
                self.tableWidget.setItem(row, 0, cn_module_serial_Item)

        self.tableWidget.load_configuration()
        self._app.instance().restoreOverrideCursor()
        self.MyCrossTable.fill_table(self.tableWidget)
        self.pushButtonAddMediaConverter.setEnabled(True)
        self.led_blink_timer.start()
        return

    def led_blinker(self):
        global TICK_TACK
        TICK_TACK = not TICK_TACK

        for col in range(self.tableWidget.columnCount()):
            horisontal_header_item = self.tableWidget.horizontalHeaderItem(col)
            column_data: HeaderData = self.tableWidget.horizontalHeaderItem(col).data(My_ROLE)
            if horisontal_header_item and column_data.sid in ('LED_A', 'LED_B'):
                # found LED column
                key = horisontal_header_item.text()
                for row in range(self.tableWidget.rowCount()):
                    vertical_header_item = self.tableWidget.verticalHeaderItem(row)
                    if vertical_header_item and vertical_header_item.text() == MEDIA_CONVERTER:
                        continue

                    cell_item = self.tableWidget.item(row, col)
                    try:
                        value = int(cell_item.text())
                    except ValueError:
                        continue
                    except AttributeError:
                        continue

                    match value:
                        case 0:
                            cell_item.setData(Qt.ItemDataRole.DecorationRole, GREY)
                        case 1:
                            cell_item.setData(Qt.ItemDataRole.DecorationRole, GREEN)
                        case 2:
                            if TICK_TACK:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, GREEN)
                            else:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, GREY)
                        case 3:
                            if TICK_TACK:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, RED)
                            else:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, GREY)
                        case 4:
                            if TICK_TACK:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, RED)
                            else:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, GREEN)
                        case 5:
                            if key == 'LED_A' and TICK_TACK:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, RED)
                            else:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, GREY)
                            if key == 'LED_B' and not TICK_TACK:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, RED)
                            else:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, GREY)
                        case 6:
                            if key == 'LED_A' and TICK_TACK:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, RED)
                            else:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, GREEN)
                            if key == 'LED_B' and not TICK_TACK:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, RED)
                            else:
                                cell_item.setData(Qt.ItemDataRole.DecorationRole, GREEN)
                        case 7:
                            cell_item.setData(Qt.ItemDataRole.DecorationRole, RED)

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
                            column_data: HeaderData = self.tableWidget.horizontalHeaderItem(col).data(My_ROLE)
                            if header_item and column_data.sid == key:
                                break  # Found the column
                        else:  # Loop completed without finding the header
                            raise ValueError(f"Header '{key}' not found")
                    except ValueError as e:
                        log.debug(f'{e}')
                        # print(f"Warning: {e}")
                        continue

                    try:
                        str_value = str(value)
                    except (TypeError, ValueError) as e:
                        str_value = f"Error: {e}"
                    item = self.tableWidget.item(row, col)
                    if item:
                        item.setText(str_value)
                    else:
                        new_item = QTableWidgetItem(str_value)
                        self.tableWidget.setItem(row, col, new_item)

    def closeEvent(self, event):
        self.save_app_config()
        if self._confirm_on_close and self._site_changed:
            reply = QMessageBox.question(self, 'Message',
                "Are you sure to quit? Any unsaved changes will be lost.", QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def about(self):
        QMessageBox.about(
            self,
            "About ControlNet Diagnostic Tool",
            f"<p>By using ControlNet Diagnostic Tool</p>"
            f"<p>you can significantly improve the troubleshooting speed of ControlNet networks.</p>"
            f"<p> - PyQt6</p>"
            f"<p> - Qt Designer6</p>"
            f"<p> - Python3.12</p>"
            f"System: {os.name}"
        )

    def about_pyqt(self):
        QMessageBox.aboutQt(self)


if __name__ == "__main__":
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    log.info('Start application')

    app_config_dir_path = user_data.get_user_data_path()
    sites_path = app_config_dir_path / 'sites'
    app_config_file_path = app_config_dir_path / 'config.json'

    Glob_settings = QSettings(user_data.Organisation, user_data.AppName)

    # Create the directory if it doesn't exist
    if not app_config_dir_path.exists():
        app_config_dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Config dir created {app_config_dir_path}")
    if not sites_path.exists():
        sites_path.mkdir(parents=True, exist_ok=True)
        log.info(f"sites dir created {sites_path}")

    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(user_data.asset_dir, 'cn_media.ico')))

    win = DiagWindow(app_config_file_path)
    win.show()
    sys.exit(app.exec())
