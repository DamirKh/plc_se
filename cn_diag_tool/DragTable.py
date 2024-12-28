from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, pyqtSignal


class DraggableTableWidget(QtWidgets.QTableWidget):
    rowsMoved = pyqtSignal()  # Add a signal

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.setDragEnabled(True)
        # self.setAcceptDrops(True)
        # self.setDropIndicatorShown(True)
        # self.setSelectionMode(
        #     QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)  # For multiple row/column selection
        # self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)  # Or SelectColumns
        self.verticalHeader().setSectionsMovable(True)  # Enable row moving
        self.horizontalHeader().setSectionsMovable(True)  # Enable column moving
        self.verticalHeader().sectionMoved.connect(self._row_moved)

    def _row_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        print(f'row moved')
        self.rowsMoved.emit()

