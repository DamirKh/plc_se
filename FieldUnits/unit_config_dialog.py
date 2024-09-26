import logging

log = logging.getLogger(__name__)

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy, QComboBox, \
    QColorDialog

from .select_tag_dialog import SelectTagDialog


class FieldUnitConfigDialog(QDialog):
    """Dialog for configuring field unit options."""

    def __init__(self, settings_dict: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Field Unit Configuration")
        self._settings = settings_dict
        # self._unit_name = kwargs.get("name", '')
        self.setupUi()

    def setupUi(self):
        layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Key", "Value"])

        for i, (key, value) in enumerate(self._settings.items()):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(str(key)))

            if str(key).startswith("color"):
                # Create color selection button
                color_button = QPushButton()
                color_button.clicked.connect(
                    lambda _, key=key: self.open_color_dialog(key)
                )

                # Set initial color
                color = QColor(value)
                color_button.setStyleSheet(f"background-color: {color.name()}")

                # Add button to the cell
                self.table_widget.setCellWidget(i, 1, color_button)

            elif str(key).startswith("io"):
                log.debug("Key hits IO")
                select_tag_button = QPushButton(value)
                select_tag_button.clicked.connect(
                    lambda _, key=key: self.open_select_tag_dialog_button(key)
                )
                self.table_widget.setCellWidget(i, 1, select_tag_button)
                pass

            else:
                self.table_widget.setItem(i, 1, QTableWidgetItem(str(value)))

        # Connect cellChanged signal of the table widget
        self.table_widget.cellChanged.connect(self.on_cell_changed)

        # Set size policy to Expanding:
        self.table_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        # Make the Value column (column 1) stretch:
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)  # Key column
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)  # Value column

        layout.addWidget(self.table_widget)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def open_color_dialog(self, key):
        """Opens the color dialog and updates the button color."""
        button_index = list(self._settings.keys()).index(key)
        button = self.table_widget.cellWidget(button_index, 1)

        # Get current color from button style sheet
        current_color = button.palette().color(QtGui.QPalette.ColorRole.Button).name()
        # color = QColorDialog.getColor(QtGui.QColor(current_color), self)

        # Create QColorDialog and set title
        color_dialog = QColorDialog(QtGui.QColor(current_color), self)
        color_dialog.setWindowTitle(f"Select {key.replace('_', ' ').title()}")

        if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
            color = color_dialog.selectedColor()
            self._settings[key] = color.name()
            button.setStyleSheet(f"background-color: {color.name()}")

    def open_select_tag_dialog_button(self, key):
        """opens the tag dialog and update button label"""
        button_index = list(self._settings.keys()).index((key))
        button: QPushButton = self.table_widget.cellWidget(button_index, 1)
        current_tag = button.text()

        #get current label from button
        current_button_label = button.text()

        #create tag dialog
        tag_dialog = SelectTagDialog(parent=self,
                                     tag=key,
                                     name=self._settings.get("name", ''),
                                     current_tag=current_tag)
        if tag_dialog.exec():
            tag = tag_dialog.lineEditSelectedTag.text()
            self._settings[key] = tag
            button.setText(tag)
            log.info(f"Select tag {tag} accepted")
        else:
            log.debug("Selecting tag canceled")

    def on_cell_changed(self, row, column):
        """Handles changes in the table widget cells."""
        if column == 1:  # Only handle changes in the Value column
            item = self.table_widget.item(row, column)
            key_item = self.table_widget.item(row, 0)
            if item is not None and key_item is not None:
                key = key_item.text()
                new_value = item.text()
                self.update_kwarg(key, new_value)

    def update_kwarg(self, key, new_value):
        """Updates the _kwargs dictionary with the new color value."""
        self._settings[key] = new_value
