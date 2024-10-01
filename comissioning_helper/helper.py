import logging
import sys

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import pyqtSignal, Qt, QThread
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMainWindow, QApplication, QProgressDialog, QVBoxLayout, QMessageBox
from pycomm3 import LogixDriver, ResponseError, RequestError, CommError

from helper_window_ui import Ui_MainWindow
from form_tab_widget import FormTabWidget

driver = None


class PLCConnectionWorker(QThread):
    finished = pyqtSignal(bool, str, str)  # Success (bool), Message (str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            global driver
            driver = LogixDriver(self.path)
            driver.open()
            log.info(f"Connected to {self.path}")
            plc_name = driver.get_plc_name()
            plc_info = driver.get_plc_info()
            # print(tmp_driver.get_plc_info())
            formatted_info = f"""
            Vendor: {plc_info['vendor']}
            Product Type: {plc_info['product_type']}
            Product Code: {plc_info['product_code']}
            Product Name: {plc_info['product_name']}
            Revision: {plc_info['revision']['major']}.{plc_info['revision']['minor']}
            Serial: {plc_info['serial']}
            Keyswitch: {plc_info['keyswitch']}
            """

            self.finished.emit(True, f"PLC Name: {plc_name}\n{formatted_info}", plc_name)
        except (ResponseError, RequestError, CommError, ConnectionError) as e:
            self.finished.emit(False, f"Connection error: {e}", "Error")


class HelperWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        # self.onAddTab()

    def connectSignalsSlots(self):
        self.pushButtonConnect.clicked.connect(self.onConnect)
        self.pushButtonAddTab.clicked.connect(self.onAddTab)

    def onConnect(self):
        _path = self.lineEditConnectionPath.text()
        # _name = self.lineEditSurname.text()

        self.progress_dialog = QProgressDialog(f"Connecting to PLC {_path}...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None)  # Disable the cancel button
        self.progress_dialog.show()

        self.worker = PLCConnectionWorker(_path)
        self.worker.finished.connect(self.on_connection_check_finished)
        self.worker.start()

    def on_connection_check_finished(self, success, long_string, name):
        self.progress_dialog.hide()
        self.labelProjectName.setText(name)
        if success:
            QMessageBox.information(self, "Success", long_string)
            self.pushButtonAddTab.setEnabled(True)
        else:
            QMessageBox.warning(self, f"Error connecting to PLC", long_string)

    def onAddTab(self):
        tab_name = self.lineEdit_2.text() or "Unnamed"
        if not tab_name:
            return

        new_tab = QtWidgets.QWidget()
        self.tabWidget.addTab(new_tab, tab_name)

        # Create an instance of your FormTabWidget
        form_tab_widget = FormTabWidget(driver)

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
