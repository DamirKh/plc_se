from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QPushButton, QSizePolicy, QHeaderView
import sys
from pycomm3 import LogixDriver

from form_tab_widget_ui import Ui_FormTabWidget


class TableModel(QtCore.QAbstractTableModel):
    #'Tag Name' 'Current Value' 'Set Value'
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


class MyTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        header = self.horizontalHeader()
        header.setSectionsClickable(True)  # Enable clicks on header sections
        header.sectionClicked.connect(self.on_header_clicked)
        self.setObjectName("tableView")

    def columnResized(self, column, oldWidth, newWidth):
        print(f"Column {column} = {newWidth}")

    def on_header_clicked(self, logicalIndex):
        """Handle clicks on header labels."""
        print(f"Clicked header label for column: {logicalIndex}")



#     updated = QtCore.pyqtSignal(list)
#
#     def __init__(self, driver, data, checkbox):
#         super().__init__()
#         self.driver = driver
#         self.data = data
#         self.checkbox = checkbox
#
#     def run(self):
#         while True:
#             if self.checkbox.isChecked():
#                 for row in range(len(self.data)):
#                     tag_name = self.data[row]['Tag Name']
#                     if not tag_name:
#                         self.data[row]['Current Value'] = ''
#                         continue
#                     tag = self.driver.read(tag_name)
#                     if tag:
#                         self.data[row]['Current Value'] = tag.value
#                     else:
#                         self.data[row]['Current Value'] = '-'
#                 self.updated.emit(self.data)  # Emit signal when data is updated
#             self.msleep(1000)  # Sleep for 1 second (1000 milliseconds)


class FormTabWidget(QtWidgets.QWidget, Ui_FormTabWidget):
    def __init__(self, data=None):
        super().__init__()
        # self.driver = driver
        self.setupUi(self)
        empty_data = [
            ['', '', '']
        ]
        data = data or empty_data

        self.tableView = MyTableView(self)
        self.ButtonsLayout.addWidget(self.tableView)

        self.model = TableModel(data)
        self.tableView.setModel(self.model)
        # column resize handler
        self.tableView.horizontalHeader().sectionResized.connect(self.column_resized)
        self.populate_buttons()

    def column_resized(self, index, old_size, new_size):
        pass

    def populate_buttons(self):
        add_row_button = QPushButton('+row')
        add_row_button.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        # self.ButtonsLayout.insertWidget(0, add_row_button)
        #
        # read_button = QPushButton('Read')
        # self.ButtonsLayout.insertWidget(1, read_button)
        #
        # write_button = QPushButton('Write')
        # self.ButtonsLayout.insertWidget(2, write_button)

        plus_button = QPushButton('+')
        plus_button.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        plus_button.setFixedSize(20, 50)
        self.ButtonsLayout.addWidget(plus_button)

    def add_new_row(self):
        pass

    def upload_table_from_PLC(self):
        pass

    def send_data(self):
        self.update_data_from_table()
        for row in range(len(self.data)):
            tag_name = self.data[row]['Tag Name']
            if not tag_name:
                continue
            value = self.data[row]['Set Value']
            if not value:
                continue
            tag = self.driver.write(tag_name, eval(value))
            if tag:
                continue
            else:
                self.data[row]['Current Value'] = '-'
        self.populate_table(self.data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FormTabWidget()
    window.show()
    sys.exit(app.exec())
