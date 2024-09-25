import logging

import pycomm3
from PyQt6 import QtWidgets
from PyQt6.QtGui import QCursor

log = logging.getLogger(__name__)

from PyQt6.QtCore import QThread, pyqtSignal, Qt, QAbstractListModel, QAbstractTableModel, QModelIndex, \
    QSortFilterProxyModel, QRegularExpression
from pycomm3 import LogixDriver, ResponseError, RequestError, CommError

from PyQt6.QtWidgets import (
    QDialog,  # QMessageBox,
)

import g
from .select_tag_dialog_ui import Ui_Select_tag

from plc_utils.tags import LogixTags

class PandasTableModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self._original_data = data.copy()  # Keep a copy of the original data

    def rowCount(self, parent=QModelIndex()):
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._data.shape[1]

    # def data(self, index, role=Qt.ItemDataRole.DisplayRole):
    #     if role == Qt.ItemDataRole.DisplayRole:
    #         row = index.row()
    #         col = index.column()
    #         return str(self._data.iloc[row, col])
    #     return None
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            return str(self._data.iloc[row, col])
        return None

    def filterData(self, plc_filter, name_filter, type_filter):
        # self._app.instance().setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        filtered_data = self._original_data.copy()

        if plc_filter:
            filtered_data = filtered_data[filtered_data["plc_name"].str.contains(plc_filter, case=False)]
        if name_filter:
            filtered_data = filtered_data[filtered_data["tag_name"].str.contains(name_filter, case=False)]
        if type_filter != "All":
            filtered_data = filtered_data[filtered_data["data_type_name"].str.contains(type_filter, case=False)]

        self.beginResetModel()
        self._data = filtered_data
        self.endResetModel()
        # self._app.instance().restoreOverrideCursor()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(self._data.index[section])
        return None

class SelectTagDialog(QDialog, Ui_Select_tag):
    def __init__(self, parent=None, tag=None):
        super().__init__(parent)
        self.setupUi(self)
        self._app: QtWidgets.QApplication = QtWidgets.QApplication.instance()
        self._app.instance().setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        logix_tags_loader = LogixTags()
        for plc_name in g.plcs.keys():
            logix_tags_loader.load_cache(plc_name)

        # self._model = PandasTableModel(data=logix_tags_loader.all_tags_df)
        # self.tableView.setModel(self._model)
        # if tag and isinstance(tag, str):
        #     self.lineEditFilter.setText(tag)
        # self.connectSignalsSlots()

        # self._proxyModel = QSortFilterProxyModel()
        self._model = PandasTableModel(data=logix_tags_loader.all_tags_df)
        # self._proxyModel.setSourceModel(self._model)
        # self._proxyModel.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.tableView.setModel(self._model)
        if tag and isinstance(tag, str):
            self.lineEditNameFilter.setText(tag)

        # Populate comboBoxTypeFilter (assuming 'data_type_name' is the column)
        unique_types = self._model._data["data_type_name"].unique()
        self.comboBoxTypeFilter.addItem("All")  # Add an "All" option
        self.comboBoxTypeFilter.addItems(unique_types)

        self.connectSignalsSlots()
        self._app.instance().restoreOverrideCursor()

    def connectSignalsSlots(self):
        self.lineEditNameFilter.textChanged.connect(self.applyFilters)
        self.comboBoxTypeFilter.currentIndexChanged.connect(self.applyFilters)
        self.comboBoxPLCFilter.currentIndexChanged.connect(self.applyFilters)

    def applyFilters(self):
        self._app.instance().setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        plc_filter = self.comboBoxPLCFilter.currentText()
        name_filter = self.lineEditNameFilter.text()
        type_filter = self.comboBoxTypeFilter.currentText()
        self._model.filterData(plc_filter, name_filter, type_filter)
        self._app.instance().restoreOverrideCursor()


