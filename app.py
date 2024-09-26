import pickle
import sys, os, shutil
import tempfile
from datetime import datetime

import logging

import plc
from FieldUnits.unit_config_dialog import FieldUnitConfigDialog

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog, QGraphicsScene, QPushButton, QLabel, QHeaderView
)

import pycomm3

import g
from global_keys import *
from main_ui import Ui_MainWindow
from new_project_dialog import CreateNewProjectDialog
from plc import PlcDialog
import l5x_loader_thread
from debug_widget import DebugWidget

from FieldUnits import Lamp
from interface.base_tree_view_component import PLC_treview_item, BaseTreeViewComponent, UnitTreeViewItem


# noinspection PyAttributeOutsideInit
class MainWindow(QMainWindow, Ui_MainWindow):
    ProjectChanged = pyqtSignal(bool, str)  # Success (bool), Message (str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.__title = self.windowTitle()
        self.setupSb()

        # --- Create and show the debug widget ---
        self.debug_widget = DebugWidget(g.__dict__)  # Pass the g namespace
        self.debug_widget.show()

        self.connectSignalsSlots()
        self.loader = None
        self.project_path = None

        self.scene = QGraphicsScene(self)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setInteractive(True)

        self.project_model = QStandardItemModel()
        self.project_model.setHorizontalHeaderLabels(['Name', 'Property', 'Value'])

        self.drop_project_model()

        self.treeView.setModel(self.project_model)

    def connectSignalsSlots(self):
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.about)
        self.actionAbout_PyQt.triggered.connect(self.about_pyqt)
        self.actionNew_Project.triggered.connect(self.newProject)
        self.actionOpen_Project.triggered.connect(self.openProject)
        self.actionAdd_PLC.triggered.connect(self.add_plc)
        self.actionSave_project.triggered.connect(self.saveProject)

        self.treeView.clicked.connect(self.handle_tree_view_clicked)

        self.actionAdd_Lamp.triggered.connect(self.field_add_lamp)
        self.actionDelete_Unit.triggered.connect(self.unit_delete)
        self.actionConnect.triggered.connect(self.connect_to_PLC)
        self.actionUpdate_Debug_widget.triggered.connect(self._update_debug_info)

        self.ProjectChanged.connect(self._update_debug_info)
        self.ProjectChanged.connect(self.on_project_changed)
        self.ProjectChanged.connect(self._update_label_project_name)

    def connect_to_PLC(self):
        if not g.drivers.keys():
            #no plc
            return
        for driver in g.drivers.items():
            log.info(f"Connecting to PLC {driver[0]}")


    def unit_delete(self):
        selected_indexes = self.treeView.selectedIndexes()
        # Remove items in reverse order to avoid index issues
        for index in reversed(selected_indexes):
            item = self.project_model.itemFromIndex(index)
            if item.parent() is None:
                return
            match item.parent().text():
                case "PLCs":
                    # remove plc
                    pass
                case "Units":
                    # remove unit
                    unit_config: dict = item.data(Qt.ItemDataRole.UserRole)
                    _name = unit_config['name']
                    if unit_config:
                        del g.units[_name]
                        self.project_model.removeRow(index.row(), index.parent())
                        self.treeView.clearSelection()
                        self.ProjectChanged.emit(True, f"Deleted {_name}")
    def save_project_model(self):
        print("Project model save method here")

    def load_project_model(self):
        log.debug("Update project tree view from global config ...")
        self.drop_project_model()
        logging.debug("Updating PLCs list...")
        for _name, plc_obj in g.plcs.items():
            # _plc = QStandardItem(f"[{plc_name}]")
            _plc = PLC_treview_item(f"[{_name}]", my_user_data=plc_obj)
            log.debug(f"Append PLC {_name}")
            self._plcs.appendRow([_plc])
            g.drivers[_name] = pycomm3.LogixDriver(plc_obj.plc_connect_path)
        logging.debug("Updating Unit list...")
        for _name, _field_unit_config in g.units.items():
            _item = UnitTreeViewItem(_name,
                                     my_user_data=_field_unit_config)
            self._units.appendRow([_item])
            log.debug(f"Append Field Unit {_name}")

    def drop_project_model(self):
        """Removes all rows from the project model."""
        self.project_model.clear()
        self.project_model.setHorizontalHeaderLabels(['Name', 'Property', 'Value'])

        ## top level folders elements
        self._plcs = QStandardItem(f'PLCs')
        self.project_model.appendRow(self._plcs)
        self._units = QStandardItem(f"Units")
        self.project_model.appendRow(self._units)
        self.ProjectChanged.emit(True, f"Model dropped")

    def setupSb(self):
        # creating a label widget
        self.status_bar_label_1 = QLabel("Init")
        self.status_bar_label_1.setStyleSheet("border :1px solid blue;")
        # adding label to status bar
        self.statusBar().addPermanentWidget(self.status_bar_label_1)

    def handle_tree_view_clicked(self, index):
        """Handles clicks on items in the treeView."""
        print("handle_tree_view_clicked")
        item = self.project_model.itemFromIndex(index)

        # Check if the clicked item is a PLC
        if item.parent() is None:
            return
        match item.parent().text():
            case "PLCs":
                # Get the PLC data stored in the item
                plc_obj: plc.Plc = item.data(Qt.ItemDataRole.UserRole)
                if plc_obj:
                    # You have the PLC data!
                    log.debug(f"PLC has data: {plc_obj}")

                    # --- Open the PLC Property Dialog ---
                    dialog = PlcDialog(self, plc_obj)
                    dialog.lineEditSurname.setEnabled(False)

                    result = dialog.exec()
                    if result:  # If the dialog was accepted (e.g., user clicked OK)
                        item.update_treeview_item()
                        self.ProjectChanged.emit(True, f"Changed PLC {dialog.plc}")
            case "Units":
                log.debug(f"Hit Unit")
                unit_config: dict = item.data(Qt.ItemDataRole.UserRole)
                if unit_config:
                    log.debug(f"Unit has data: {unit_config}")
                    dialog = FieldUnitConfigDialog(unit_config)
                    result = dialog.exec()
                    if result:
                        log.debug(f"Accept config field unit dialog for {item.text()} from project tree view")
                        item.setData(dialog._settings, Qt.ItemDataRole.UserRole)
                        # field_item_settings: dict = item.data(Qt.ItemDataRole.UserRole)
                        # field_item_settings.update(dialog._settings)
                        # # Global project config  # TODO
                        g.units[item.text()] = dialog._settings
                        item.update_treeview_item()
                        pass

    def saveProject(self):
        if self.project_path:
            # Save to the existing project directory
            project_dir = self.project_path
        else:
            # Create a temporary directory in the user's Documents directory
            project_dir = tempfile.mkdtemp(prefix="PLC_SE_Project_", dir=os.path.expanduser("~/Documents"))
            self.ProjectChanged.emit(True, f"Project dir set to {project_dir}.")

        g.project_config[PROJECT_PATH] = project_dir

        project_file = os.path.join(project_dir, PROJECT_FILE_NAME)
        plc_file = os.path.join(project_dir, PLC_CONFIG_FILE)
        units_file = os.path.join(project_dir, UNITS_CONFIG_FILE)

        try:
            with open(project_file, 'wb') as file:
                pickle.dump(g.project_config, file)

            with open(plc_file, 'wb') as file:
                pickle.dump(g.plcs, file)

            with open(units_file, 'wb') as file:
                pickle.dump(g.units, file)

            g.project_changed = False
            self.ProjectChanged.emit(False, 'Saved')
            self.statusBar().showMessage(f"Project file {project_file} saved.", 10000)

        except (pickle.PickleError, OSError) as e:
            QMessageBox.critical(self, "Error", f"Could not save project:\n{e}")
            log.error(f"Error wile saving: {e}")
            return

    def on_project_changed(self, b: bool, s: str):
        if b:
            g.project_changed = True
            g.project_config[PROJECT_CHANGE_DATE] = g.now()
        changed = "+" if b else " "
        log.debug(f"via _log: {changed} {s}")

    def _update_debug_info(self, b: bool = False, s: str = ""):
        self.debug_widget.update_debug_info()
        self.debug_widget.show()

    def add_plc(self):
        dialog = PlcDialog(self)
        result = dialog.exec()
        if result:
            log.info(f'Accept adding PLC {dialog.plc}')

            if dialog.checkBox.isChecked():  # Use isChecked() for checkboxes
                try:
                    # 1. Construct the new file path inside the project directory
                    file_name = os.path.basename(dialog.lineEditL5X.text())
                    _path = os.path.join(self.project_path, L5X_DIRECTORY_PATH, file_name)

                    # 2. Copy the file
                    shutil.copy2(dialog.lineEditL5X.text(), _path)
                    dialog.plc.plc_l5x_path = _path
                    log.info(f"Copied PLC file to: {_path}")

                except (shutil.Error, OSError) as e:
                    QMessageBox.critical(self, "Error", f"Could not copy file:\n{e}")
                    return  # Exit if copying fails
            else:
                _path = dialog.lineEditL5X.text()
                log.info(f"File {_path} not copied due to user!")

            _name = dialog.plc.plc_name or f'plc_{len(g.plcs)}'

            g.plcs[_name] = dialog.plc  #  this is a Plc-class object!
            g.drivers[_name] = pycomm3.LogixDriver(dialog.plc.plc_connect_path)
            _plc = PLC_treview_item(f"[{_name}]", my_user_data=dialog.plc)
            self._plcs.appendRow([_plc])
            self.ProjectChanged.emit(True, f"Added PLC {dialog.plc}")

        else:
            log.debug("Reject adding PLC")

    def _update_label_project_name(self, b=False, s=""):
        changed = "*" if g.project_changed else " "
        self.label_project_name.setText(
            f"{g.project_config.get(PROJECT_NAME, 'New_simulation_project')}  [{g.project_config.get(PROJECT_CREATE_DATE, '--')}]")
        self.status_bar_label_1.setText(f"{changed} {g.project_config.get(PROJECT_PATH, 'NOT SAVED')}")
        _new_title = changed + self.windowTitle()
        self.setWindowTitle(_new_title)

    def openProject(self):
        """Opens an existing project from a pickle file."""
        project_dir = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if not project_dir:
            return  # User canceled the dialog

        project_file = os.path.join(project_dir, PROJECT_FILE_NAME)
        plc_file = os.path.join(project_dir, PLC_CONFIG_FILE)
        units_file = os.path.join(project_dir, UNITS_CONFIG_FILE)

        g.drop_project()

        try:
            with open(project_file, 'rb') as file:
                g.project_config = pickle.load(file)

            with open(plc_file, 'rb') as file:
                g.plcs = pickle.load(file)

            with open(units_file, 'rb') as file:
                g.units = pickle.load(file)

            self.project_path = g.project_config[PROJECT_PATH]
            self.load_project_model()
            g.project_changed = False
            self.ProjectChanged.emit(False, 'Loaded')
            self.statusBar().showMessage(f"Project file {project_file} saved.", 10000)


        except (FileNotFoundError, pickle.PickleError, KeyError) as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{e}")
            log.error(f"Error while loading: {e}")
            return

            # self._log()

            # Access loaded settings
            # l5x_file = init_settings['l5x']
            # print("Loaded project settings:")
            # print(f"  L5X file: {l5x_file}")

            # Now, can use these settings to load your project data
            # (e.g., start the L5X loader thread)
            # self.statusBar().showMessage(f"Reading {l5x_file} file..", 10000)
            # self.loader = l5x_loader_thread.WorkerThread(l5x_file)
            # self.loader.result_ready.connect(self.set_plc_name)
            # self.loader.start()

    def newProject(self):
        pass
        dialog = CreateNewProjectDialog(self)
        result = dialog.exec()
        if result:
            print("Accept")
            print(dialog.project_dir)
            print(dialog.project_name)
            # Save settings to a pickle file
            init_settings = {
                PROJECT_PATH: dialog.project_dir,
                PROJECT_NAME: dialog.project_name,
                PROJECT_CREATE_DATE: g.now(),
                PROJECT_CHANGE_DATE: g.now(),
            }
            self.project_path = init_settings[PROJECT_PATH]
            filename = os.path.join(dialog.project_dir, PROJECT_FILE_NAME)  # Choose a filename for your pickle file
            with open(filename, 'wb') as file:
                pickle.dump(init_settings, file)
            l5x_directory = os.path.join(dialog.project_dir, L5X_DIRECTORY_PATH)
            os.mkdir(l5x_directory)
            self.statusBar().showMessage(f"Project file {filename} saved.", 10000)
            # self.statusBar().showMessage(f"Reading {dialog.l5x} file..", 10000)
            # self.loader = l5x_loader_thread.WorkerThread(dialog.l5x)
            # self.loader.result_ready.connect(self.set_plc_name)
            # self.loader.start()
            # except:
            #     self.statusBar().showMessage(f"Error reading {dialog.l5x}")
            g.project_config.update(init_settings)
            g.project_changed = True
            self.drop_project_model()
            # self._update_label_project_name()
            self.ProjectChanged.emit(True, f"New project {dialog.project_dir} created")
            # self.status_bar_label_1.setText(f"{dialog.project_dir}")
        else:
            print("Reject")

    def field_add_lamp(self):
        # Graphic object
        lamp = Lamp()

        # Project tree presentation
        _lamp_3v = UnitTreeViewItem(lamp._config['name'],
                                    my_user_data=lamp._config,
                                    )
        _name = lamp._config['name']

        # Global project config
        g.units[_name] = lamp._config
        self._units.appendRow([_lamp_3v, ])  # add to tree view
        self.scene.addItem(lamp)  # add to scene
        self.ProjectChanged.emit(True, f"Added Lamp {_name}")

    def about(self):
        QMessageBox.about(
            self,
            "About PLC simulation environment",
            f"<p>By using PLC simulation environment and virtual commissioning, </p>"
            f"<p>you can significantly improve the quality, reliability, and development speed of your PLC programs</p>"
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
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
