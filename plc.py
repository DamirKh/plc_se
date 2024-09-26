import logging
log = logging.getLogger(__name__)

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from pycomm3 import LogixDriver, ResponseError, RequestError, CommError

from PyQt6.QtWidgets import (
    QDialog, QMessageBox, QFileDialog, QProgressDialog
)

from utilites.empty import is_directory_empty
from utilites.writable import is_directory_writable

from plc_utils.tags import LogixTags

from plc_dialog_ui import Ui_Dialog


class PLCConnectionWorker(QThread):
    finished = pyqtSignal(bool, str)  # Success (bool), Message (str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            tmp_driver = LogixDriver(self.path)
            with tmp_driver:
                plc_name = tmp_driver.get_plc_name()
                plc_info = tmp_driver.get_plc_info()
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

                self.finished.emit(True, f"PLC Name: {plc_name}\n{formatted_info}")
        except (ResponseError, RequestError, CommError, ConnectionError) as e:
            self.finished.emit(False, f"Connection error: {e}")


class Plc(object):
    def __init__(self, **kwargs):
        self.plc_name = kwargs.get('plc_name') or ''
        self.plc_connect_path = kwargs.get('plc_connect_path') or ''
        self.plc_l5x_path = kwargs.get('plc_l5x_path') or ''
        log.debug(f"New PLC {self.plc_name} created")

    def __dir__(self):
        return ['plc_name',
                'plc_connect_path',
                'plc_l5x_path',
                ]

    def __str__(self):
        """Returns a human-readable string representation."""
        return (
            f"Plc("
            f"plc_name='{self.plc_name}', "
            f"connect_path='{self.plc_connect_path}', "
            f"l5x_path='{self.plc_l5x_path}'"
            f")"
        )

    def __repr__(self):
        """Returns a string representation for debugging."""
        return (
            f"Plc("
            f"plc_name='{self.plc_name}', "
            f"plc_connect_path='{self.plc_connect_path}', "
            f"plc_l5x_path='{self.plc_l5x_path}'"
            f")"
        )


class PlcDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None, plc=None):
        super().__init__(parent)
        self.setupUi(self)
        if plc and isinstance(plc, Plc):
            self.plc = plc
            self.checkBox.setEnabled(False)  # if PLC object already exist "Copy..." checkbox disabled
            self.checkBox.setChecked(False)
            self.setWindowTitle("Edit PLC property")
        else:
            self.plc = Plc()
        self._tag_loader = LogixTags()
        self.update_from_PLC_obj()
        self.connectSignalsSlots()

    def update_from_PLC_obj(self):
        self.lineEditSurname.setText(self.plc.plc_name)
        self.lineEditL5X.setText(self.plc.plc_l5x_path)
        self.lineEditConnectionPath.setText(self.plc.plc_connect_path)

    def connectSignalsSlots(self):
        pass

    def ok_press(self):
        self.plc.plc_name = self.lineEditSurname.text()
        self.plc.plc_l5x_path = self.lineEditL5X.text()
        self.plc.plc_connect_path = self.lineEditConnectionPath.text()
        self.accept()

    def selectL5X(self):
        _name = self.lineEditSurname.text()
        print(f"select L5X for PLC {_name}")
        options = QFileDialog.Option.ReadOnly
        file_filter = "*.L5X"  # Create the file filter string
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select project file for PLC {_name}", "", file_filter, options=options
        )
        if file_path:
            self.lineEditL5X.setText(file_path)
        # print(file_path)

    def CheckConnection(self):
        _path = self.lineEditConnectionPath.text()
        _name = self.lineEditSurname.text()

        self.progress_dialog = QProgressDialog(f"Connecting to PLC {_name} ({_path})...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None)  # Disable the cancel button
        self.progress_dialog.show()

        self.worker = PLCConnectionWorker(_path)
        self.worker.finished.connect(self.on_connection_check_finished)
        self.worker.start()

    def LoadProgram(self):
        log.info(f"Loading programm from L5x {self.lineEditL5X.text()}")
        self._tag_loader.add_l5x(self.lineEditSurname.text(),
                                 self.lineEditL5X.text())
        self._tag_loader.save_cache(self.lineEditSurname.text(),
                                    self._tag_loader.all_tags_df)
        pass

    def LoadPLCtags(self):
        log.info(f"Loading PLC tags from {self.lineEditConnectionPath.text()}")
        self._tag_loader.add_driver(self.lineEditSurname.text(),
                                    self.lineEditConnectionPath.text())
        self._tag_loader.save_cache(self.lineEditSurname.text(),
                                    self._tag_loader.all_tags_df)
        self.pushButtonLoadProgram.setEnabled(True)
        pass

    def on_connection_check_finished(self, success, message):
        self.progress_dialog.hide()

        if success:
            QMessageBox.information(self, "Success", message)

        else:
            QMessageBox.warning(self, f"Error connecting to PLC", message)
