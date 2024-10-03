import logging
log = logging.getLogger(__name__)
import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QMutex, QTimer
from PyQt6.QtWidgets import QApplication, QPushButton, QSizePolicy, QHeaderView
import sys

from Plc_connection_worker import PLCConnectionWorkerReader, PLCConnectionWorkerWriter
from form_tab2_widget_ui import Ui_FormTabWidget
# from helper import PLCConnectionWorker

import helper_globals


class TableModel(QtCore.QAbstractTableModel):
    #'Tag Name' 'Current Value' 'Set Value'
    def __init__(self, data):
        super().__init__()
        self._data: pd.DataFrame = data

    def flags(self, index) -> Qt.ItemFlag:
        """Set flags for editable items."""
        # print(index.column())
        _flags = QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled
        if index.column() == 1:  # Current value column
            pass
        else:
            _flags = _flags | QtCore.Qt.ItemFlag.ItemIsEditable

        return _flags

    def get_tags(self):
        # Get a list of tag names, excluding empty ones
        return [tag for tag in self._data['Tag Name'] if tag]

    def get_tag_value_pairs(self, column_index):
        """
        Gets a list of (tag_name, value) pairs for the specified column,
        excluding pairs where either the tag name or value is empty.

        Args:
            column_index (integer): The index of the column to retrieve values from.

        Returns:
            list: A list of tuples, where each tuple is (tag_name, value).
        """
        tag_value_pairs = []
        for row in range(self.rowCount(QtCore.QModelIndex())):
            tag_name = self._data.iloc[row, 0]
            value = self._data.iloc[row, column_index]

            # Check if both tag_name and value are non-empty
            if tag_name and value:
                try:
                    value = eval(value)
                except:
                    log.error()
                    continue
                tag_value_pairs.append((tag_name, value))
        return tag_value_pairs

    def set_current_values(self, tag_dict: dict):
        for tag_name, tag_value in tag_dict.items():
            # Find matching tag names (can be multiple matches)
            matching_rows = self._data.index[
                self._data['Tag Name'] == tag_name
                ].tolist()

            # Set the 'Current Value' for all matching rows
            for row in matching_rows:
                self._data.loc[row, 'Read'] = str(tag_value)

        # Emit dataChanged signal for the entire column
        top_left = self.index(0, 1)  # Row 0, Column 1 ('Current Value')
        bottom_right = self.index(
            self.rowCount(QtCore.QModelIndex()) - 1, 1
        )
        self.dataChanged.emit(top_left, bottom_right)

    def data(self, index, role):
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        if role == Qt.ItemDataRole.DecorationRole:
            value = self._data.iloc[index.row(), index.column()]
            if value =='None':
                return QtGui.QColor('red')

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Save data when edited."""
        if role == Qt.ItemDataRole.EditRole:
            # Save the edited value to your DataFrame
            row = index.row()
            col = index.column()
            self._data.iloc[row, col] = value
            self.dataChanged.emit(index, index)  # Notify view of change
            return True
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

        if orientation == Qt.Orientation.Vertical:
            return str(self._data.index[section])

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def add_new_column(self, index=None):
        if index is None:
            index = self.columnCount(QtCore.QModelIndex())
        new_column_name = f"Set {index-2}"
        self._data.insert(index, new_column_name, "")
        self.layoutChanged.emit()

    def add_new_row(self):
        row_count = self.rowCount(QtCore.QModelIndex())
        self._data.loc[row_count] = ''
        self.layoutChanged.emit()


class FormTabWidget(QtWidgets.QWidget, Ui_FormTabWidget):
    empty_row_data = ['', '', '']
    new_table_columns = [
        'Tag Name',
        'Read',
        'Set',
    ]

    def __init__(self, reader: PLCConnectionWorkerReader, r_mutex: QMutex, writer: PLCConnectionWorkerWriter=None, w_mutex: QMutex = None, data=None):
        super().__init__()
        self.reader = reader
        self.reader.signals.read_done.connect(self.update_from_reader)
        self.r_mutex = r_mutex
        self.writer = writer
        self.w_mutex = w_mutex
        self.setupUi(self)

        my_data_row = data or self.empty_row_data.copy()

        data = pd.DataFrame(
            [
                my_data_row,
            ],
            columns=self.new_table_columns.copy()
        )

        # self.tableView = MyTableView(self)
        self.tableView.horizontalHeader().setSectionsClickable(True)
        self.tableView.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.tableView.horizontalHeader().sectionResized.connect(self.column_resized)

        self.model = TableModel(data)
        self.tableView.setModel(self.model)
        self._visible = False

        self.connectSignalsSlots()

    def connectSignalsSlots(self):
        self.pushButtonPlusColumn.clicked.connect(self.add_new_column)
        self.pushButtonPlusRow.clicked.connect(self.add_new_row)
        self.checkBoxRead.stateChanged.connect(self.on_checkbox_checked)

        # Create a timer for periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)  # Update every 1000ms (1 second)
        self.update_timer.timeout.connect(self.upload_table_from_PLC)

    def you_are_visible(self, visible):
        self._visible = visible
        if visible:
            print("I'm visible")
            self.on_checkbox_checked(self.checkBoxRead.checkState().value)
        else:
            self.on_checkbox_checked(QtCore.Qt.CheckState.Unchecked.value)

    def on_checkbox_checked(self, state):
        if state == QtCore.Qt.CheckState.Checked.value:
            log.debug("Start periodicaly reading")
            print("Start periodicaly reading")
            self.update_timer.start()  # Start the timer when checked
        else:
            log.debug("Stop periodicaly reading")
            print("Stop periodicaly reading")
            self.update_timer.stop()   # Stop the timer when unchecked

    def on_header_clicked(self, logicalIndex):
        """Handle clicks on header labels."""
        match logicalIndex:
            case 0:
                print(f"Clicked on Tag Name")
            case 1:
                print(f"Read data")
                self.upload_table_from_PLC()
            case _:
                print(f"Write data column {logicalIndex}")
                self.download_to_plc(logicalIndex)

    def download_to_plc(self, logical_index):
        if self.writer:
            tags_to_write = self.model.get_tag_value_pairs(logical_index)
            self.w_mutex.lock()
            self.writer.write_tags_append(tags_to_write)
            self.w_mutex.unlock()


    def column_resized(self, index, old_size, new_size):
        pass

    def add_new_row(self):
        self.model.add_new_row()

    def add_new_column(self):
        self.model.add_new_column()

    def upload_table_from_PLC(self):
        _tags = self.model.get_tags()
        self.r_mutex.lock()
        self.reader.read_tags_append(_tags) #TODO convert to signal
        self.r_mutex.unlock()

    def update_from_reader(self, tags_dict):
        if not self._visible:
            return
        self.model.set_current_values(tags_dict)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FormTabWidget()
    window.show()
    sys.exit(app.exec())
