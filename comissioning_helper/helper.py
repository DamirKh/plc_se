import datetime
import logging
import sys
import time

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QObject, QMutex
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFontDatabase
from PyQt6.QtWidgets import QMainWindow, QApplication, QProgressDialog, QVBoxLayout, QMessageBox, QLabel
from pycomm3 import LogixDriver, ResponseError, RequestError, CommError

from helper_window_ui import Ui_MainWindow
from form_tab_widget import FormTabWidget
from Plc_connection_worker import PLCConnectionWorkerReader, PLCConnectionWorkerWriter

# driver = None
import helper_globals


class HelperWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        self.reader_mutex = QMutex()
        self.writer_mutex = QMutex()

        # creating a label widget for status bar
        self.status_bar_label_1 = QLabel("Not connected yet")
        # Get a suitable monospace font from the system
        # font_db = QFontDatabase()
        # monospace_font = font_db.systemFont(QFontDatabase.SystemFont.FixedFont)
        # self.status_bar_label_1.setFont(monospace_font)

        self.status_bar_label_1.setStyleSheet("border :1px solid blue;")
        # adding label to status bar
        self.statusBar().addPermanentWidget(self.status_bar_label_1)

    def connectSignalsSlots(self):
        self.pushButtonConnect.clicked.connect(self.onButtonConnect)
        self.pushButtonAddTab.clicked.connect(self.onAddTab)

    def onButtonConnect(self):
        _path = self.lineEditConnectionPath.text()
        # _name = self.lineEditSurname.text()

        self.progress_dialog = QProgressDialog(f"Connecting to PLC {_path}...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None)  # Disable the cancel button
        self.progress_dialog.show()

        self.read_worker = PLCConnectionWorkerReader(_path, self.reader_mutex)
        self.read_worker.signals.connected.connect(self.on_connection_check_connected)
        self.read_worker.start()

    def tab_changed(self, index):
        print(f"Activate tab {index}")
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
        self.progress_dialog.hide()
        self.labelProjectName.setText(name)
        if success:
            self.lineEditConnectionPath.setEnabled(False)
            QMessageBox.information(self, "Success", long_string)
            self.pushButtonAddTab.setEnabled(True)
            self.read_worker.signals.current_time.connect(self.plc_time_changed)
            self.writer_worker = PLCConnectionWorkerWriter(self.lineEditConnectionPath.text(), self.writer_mutex)
            # self.writer_worker.signals.connected.connect(self.on_writer_connected)
            if self.writer_worker._connected:
                self.writer_worker.start()
        else:
            self.progress_dialog.hide()
            QMessageBox.warning(self, f"Error connecting to PLC", long_string)

    def onAddTab(self):
        tab_name = self.lineEdit_2.text() or "Unnamed"
        if not tab_name:
            return

        # Create an instance of your FormTabWidget
        form_tab_widget = FormTabWidget(reader=self.read_worker, r_mutex=self.reader_mutex, writer=self.writer_worker,
                                        w_mutex=self.writer_mutex)
        self.tabWidget.addTab(form_tab_widget, tab_name)

        self.lineEdit_2.clear()

    def plc_time_changed(self, plc_time: datetime.datetime):
        # print(plc_time)
        time_repr = plc_time.strftime("%d %b %Y %H:%M:%S")
        self.status_bar_label_1.setText(time_repr)


if __name__ == "__main__":
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    log.info('Start application')
    app = QApplication(sys.argv)
    test_data = [
        ['TAG1', 111, 100],
        ['TAG2', 222, 100],
        ['TAG3', 333, 100],
        ['TAG4', 444, 100],

    ]
    win = HelperWindow(test_data)
    win.show()
    sys.exit(app.exec())
