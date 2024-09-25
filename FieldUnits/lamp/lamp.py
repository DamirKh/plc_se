import logging
from collections import UserDict

log = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QDialog, QMessageBox, QFileDialog, QGraphicsEllipseItem, QGraphicsProxyWidget, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsItem
)
from PyQt6.QtGui import QColor, QStaticText
from PyQt6.QtGui import QCursor

lamp_counter = 0

from FieldUnits.base_components import BaseMovableGraphic


class Lamp(QGraphicsItem, BaseMovableGraphic):
    def __init__(self, r=20, parent=None, **kwargs):
        QGraphicsItem.__init__(self, parent)
        global lamp_counter
        lamp_counter += 1
        # _init_lamp_config = {
        #     'name': f'Lamp{lamp_counter:03d}',
        #     'color_on': 'green',
        #     'color_off': 'grey',
        #     'io_in': ''
        # }
        # self._config = ConfigSaver(dict=_init_lamp_config)
        self._config = {
            'name': f'Lamp{lamp_counter:03d}',
            'color_on': 'green',
            'color_off': 'grey',
            'io_in': ''
        }
        self._config.update(kwargs)
        self._radius = r
        self.setupUi()
        self._base_movable_graphic_init()
        log.debug(f"New Lamp created {self._config}")

    def update_from_menu(self, kwargs):
        log.debug(f"Got: {kwargs}")
        self._label.setPlainText(kwargs['name'])
        self._lamp.setBrush(QColor(kwargs['color_off']))
        self.base_movable_graphic_update_rect()
        log.debug(f"New Lamp updated {self._config}")

    def setupUi(self):
        self._label = QGraphicsTextItem(self._config['name'])
        self._lamp = QGraphicsEllipseItem(0, 25, self._radius, self._radius)
        self._lamp.setBrush(QColor(self._config['color_off']))

        self._label.setParentItem(self)
        self._lamp.setParentItem(self)

    def paint(self, painter, option, widget):
        pass
