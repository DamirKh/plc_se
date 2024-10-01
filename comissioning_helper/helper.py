import logging
import sys
import time

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QObject, QMutex
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMainWindow, QApplication, QProgressDialog, QVBoxLayout, QMessageBox
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
        # self.onAddTab()

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

    def on_connection_check_connected(self, success, long_string, name):
        self.progress_dialog.hide()
        self.labelProjectName.setText(name)
        if success:
            QMessageBox.information(self, "Success", long_string)
            self.pushButtonAddTab.setEnabled(True)
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

        new_tab = QtWidgets.QWidget()
        self.tabWidget.addTab(new_tab, tab_name)

        # Create an instance of your FormTabWidget
        form_tab_widget = FormTabWidget(reader=self.read_worker, r_mutex=self.reader_mutex, writer=self.writer_worker, w_mutex=self.writer_mutex)

        # Create a layout for the new tab and add the FormTabWidget
        layout = QVBoxLayout()
        layout.addWidget(form_tab_widget)
        new_tab.setLayout(layout)

        self.lineEdit_2.clear()


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
