import logging
log = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QDialog, QMessageBox, QFileDialog
)

from utilites.empty import is_directory_empty
from utilites.writable import is_directory_writable
from new_project_dialog_ui import Ui_Dialog


def display_empty_directory_message(parent=None):
    """Displays a message box prompting the user to choose an empty directory.

    Args:
        parent: The parent widget for the message box (optional).
    """

    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)  # Set the icon (optional)
    msg_box.setWindowTitle("Select Empty Writable Directory")
    msg_box.setText("Please specify an empty and writable directory for the project.")
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def display_select_file_message(parent=None):
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)  # Set the icon (optional)
    msg_box.setWindowTitle("Select PLC programm file")
    msg_box.setText("Please specify a PLC programm *.L5X readable file")
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


class CreateNewProjectDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        log.debug("CreateNewProjectDialog")

    def connectSignalsSlots(self):
        pass

    def Check(self):
        directory = self.lineEditDir.text()
        name = self.lineEditName.text()
        if not name:
            QMessageBox.warning(self, f"Name should not be empty", 'Please, specify the project name')
        if directory and is_directory_empty(directory) and is_directory_writable(directory):
            pass
        else:
            display_empty_directory_message(self)
            return
        self.project_dir = directory
        self.project_name =name
        self.accept()



    def selectDir(self):
        options = QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks

        directory = QFileDialog.getExistingDirectory(
            self, "Select or Create Directory", options=options
        )
        self.lineEditDir.setText(directory)
        # print(directory)
