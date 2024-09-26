import logging
import re

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
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            return str(self._data.iloc[row, col])
        return None

    def filterData(self, plc_filter, name_filter, type_filter):
        filtered_data = self._original_data.copy()

        if plc_filter != "All":
            filtered_data = filtered_data[filtered_data["plc_name"].str.contains(plc_filter)]
        if name_filter:
            filtered_data = filtered_data[filtered_data["tag_name"].str.contains(name_filter, case=False, regex=False)]
        if type_filter != "All":
            filtered_data = filtered_data[filtered_data["data_type_name"].str.contains(type_filter)]

        self.beginResetModel()
        self._data = filtered_data
        self.endResetModel()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(self._data.index[section])
        return None

class SelectTagDialog(QDialog, Ui_Select_tag):
    def __init__(self, parent=None, tag=None, name=None, current_tag: str = ''):
        super().__init__(parent)
        self.setupUi(self)
        _title = f"Select PLC Tag to connect to {name}.{tag}"
        self.setWindowTitle(_title)
        self._app: QtWidgets.QApplication = QtWidgets.QApplication.instance()
        self._app.instance().setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        logix_tags_loader = LogixTags()
        for plc_name in g.plcs.keys():
            logix_tags_loader.load_cache(plc_name)

        self._model = PandasTableModel(data=logix_tags_loader.all_tags_df)
        self.tableView.setModel(self._model)

        # Populate comboBoxTypeFilter (assuming 'data_type_name' is the column)
        unique_types = self._model._data["data_type_name"].unique()
        self.comboBoxTypeFilter.addItem("All")  # Add an "All" option
        self.comboBoxTypeFilter.addItems(unique_types)

        # Populate comboBoxPLCFilter (assuming 'plc_name' is the column)
        unique_types = self._model._data["plc_name"].unique()
        self.comboBoxPLCFilter.addItem("All")  # Add an "All" option
        self.comboBoxPLCFilter.addItems(unique_types)

        if current_tag:
            self.lineEditSelectedTag.setText((current_tag))
            # Create boolean Series for each column
            tag_name_match = self._model._data['tag_name'] == current_tag
            plc_name_match = self._model._data['base_tag'] == current_tag

            # Combine using logical OR (|)
            combined_match = tag_name_match | plc_name_match

            # Select rows based on the combined match
            row = self._model._data.index[combined_match].tolist()

            if row:  # If the tag is found
                index = self._model.index(row[0], 0)  # Create a QModelIndex
                # self.tableView.setCurrentIndex(index)  # Select the tag
                self.tableView.selectRow(row[0])  # Select the entire row
                self.tableView.scrollTo(index)       # Make the tag visible
        else:
            # preset filter
            if name and isinstance(tag, str):
                match = re.search(r'\d+', name)  # Search for one or more digits
                if match:
                    numbers = match.group(0)  # Get the matched digits
                else:
                    numbers = ""  # Set to empty string if no match
                self.lineEditNameFilter.setText(numbers)
                self.applyFilters()
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

    def onCellDblClick(self, index):
        item = index.data()
        self.lineEditSelectedTag.setText(item)

    def onReset(self):
        self.lineEditNameFilter.setText('')
        self.comboBoxTypeFilter.setCurrentText('All')
        self.comboBoxPLCFilter.setCurrentText('All')
        self.applyFilters()



