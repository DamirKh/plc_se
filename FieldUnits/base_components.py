import logging
from collections import UserDict

log = logging.getLogger(__name__)

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtWidgets import QGraphicsProxyWidget, QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, QDialog, \
    QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QCursor

# app = QtWidgets.QApplication.instance()
from .unit_config_dialog import FieldUnitConfigDialog


class FieldUnitMenuButton(QGraphicsProxyWidget):
    """Represents CONFIG menu button"""
    SettingsUpdated = pyqtSignal(dict)  # Define the signal when updated config
    def __init__(self, unit_settings):
        super().__init__()
        print(unit_settings)
        self._kwargs = unit_settings
        self._button = QtWidgets.QPushButton(f"...")
        self._button.setFixedSize(25, 25)
        self._button.clicked.connect(self.onclick)
        self.setWidget(self._button)

    def onclick(self):
        # print("Click on button")
        dialog = FieldUnitConfigDialog(self._kwargs)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_kwargs_from_table(dialog._settings)

    def update_kwargs_from_table(self, settings_dict: dict):
        _kwargs = {}  # Clear existing kwargs
        _kwargs.update(settings_dict)
        log.debug(f"Updated kwargs: {_kwargs}")
        self.SettingsUpdated.emit(_kwargs)  # Emit the signal


class BaseMovableGraphic(object):
    def _base_movable_graphic_init(self):
        if not issubclass(self.__class__, QGraphicsItem):
            return
        print(f"{self} is a subclass of QGraphicsItem")
        self._app: QtWidgets.QApplication = QtWidgets.QApplication.instance()
        # self._kwargs = kwargs
        settings = getattr(self, '_config', None)
        if not settings:
            self._config = {}
        pos_settings = {  # TODO
            'pos_x': self.pos().x(),
            'pos_y': self.pos().y()
        }
        self._config.update(pos_settings)

        self.setAcceptHoverEvents(True)
        for child in self.childItems():
            child.setAcceptHoverEvents(False)

        self._rect = QGraphicsRectItem(self.childrenBoundingRect())
        self._rect.setParentItem(self)

        self._anchor = FieldUnitMenuButton(self._config)
        self._anchor.SettingsUpdated.connect(self.update_from_menu)  # Connect signal
        self._anchor.setParentItem(self)
        self._anchor.hide()

        # unhide methods if self is a subclass of QGraphicsItem
        self.hoverEnterEvent = self._hoverEnterEvent
        self.hoverLeaveEvent = self._hoverLeaveEvent
        self.mousePressEvent = self._mousePressEvent
        self.mouseMoveEvent = self._mouseMoveEvent
        self.mouseReleaseEvent = self._mouseReleaseEvent
        log.debug(f"Base movable graphic init complete")

    def base_movable_graphic_update_rect(self):
        # 'pos_x': self.pos().x(),
        # 'pos_y': self.pos().y()
        _x = int(self._config['pos_x'])
        _y = int(self._config['pos_y'])
        self.setPos(QPointF(_x, _y))

        self._anchor.setParentItem(None)
        self._rect.setParentItem(None)
        self._rect.setRect(QGraphicsRectItem(self.childrenBoundingRect()).rect() )
        self._anchor.setParentItem(self)
        self._rect.setParentItem(self)

    def update_from_menu(self, kwargs):
        # Override this method!
        print(f"Before: {self._kwargs}")
        self._kwargs = kwargs
        print(f"After: {self._kwargs}")

    def boundingRect(self):
        # return QRectF(-20, -20, 20, 20)
        return QRectF(self._rect.rect())

    def _hoverEnterEvent(self, event):
        self._app.instance().setOverrideCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self._anchor.show()

    def _hoverLeaveEvent(self, event):
        self._app.instance().restoreOverrideCursor()
        self._anchor.hide()

    # mouse click event
    def _mousePressEvent(self, event):
        pass

    def _mouseMoveEvent(self, event):
        try:
            self._rect.show()
            self._anchor.hide()
        except AttributeError:
            # self._rect = QGraphicsRectItem(self.childrenBoundingRect())

            pass  # TODO show rect
        orig_cursor_position = event.lastScenePos()
        updated_cursor_position = event.scenePos()

        orig_position = self.scenePos()

        updated_cursor_x = updated_cursor_position.x() - orig_cursor_position.x() + orig_position.x()
        updated_cursor_y = updated_cursor_position.y() - orig_cursor_position.y() + orig_position.y()
        self.setPos(QPointF(updated_cursor_x, updated_cursor_y))

    def _mouseReleaseEvent(self, event):
        try:
            self._rect.hide()
        except AttributeError:
            pass
        # print('x: {0}, y: {1}'.format(self.pos().x(), self.pos().y()))
        pos_settings = {
            'pos_x':self.pos().x(),
            'pos_y':self.pos().y()
        }
        self._config.update(pos_settings)

from collections import UserDict

class ConfigSaver(object):
    def __init__(self, **kwargs):
        self._data = kwargs
    def __dir__(self):
        return self._data.keys()

    def __getattr__(self, item):
        # Attempt to get the attribute from 'data' first
        try:
            return self._data[item]
        except KeyError:
            return None
    def __setattr__(self, key, value):
        self._data[key] = value