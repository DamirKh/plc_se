import logging

from PyQt6.QtCore import Qt

log = logging.getLogger(__name__)

from PyQt6.QtGui import QStandardItem

from plc import Plc
from FieldUnits import ConfigSaver


class BaseTreeViewComponent(object):
    def _base_tree_view_component_init(self):
        if not issubclass(self.__class__, QStandardItem):
            log.warning(f"{self} IS NOT an QStandardItem subclass")
            return
        log.debug(f"{self} IS an QStandardItem subclass")
        self._fillin_data()

    def _base_tree_view_component_update(self):
        log.debug(f"Update BaseTreeViewComponent: {self.text()}")
        # Remove all existing child rows
        self.removeRows(0, self.rowCount())
        self._fillin_data()

    def _fillin_data(self):
        my_user_data = self.data(Qt.ItemDataRole.UserRole)
        for prop in dir(my_user_data):
            _emptyItem = QStandardItem('')
            _emptyItem.setEditable(self.isEditable())  #from child object
            _property_item = QStandardItem(prop)
            _property_item.setEditable(self.isEditable())
            _value_item = QStandardItem(getattr(my_user_data, prop))
            _value_item.setEditable(self.isEditable())
            self.appendRow([
                _emptyItem, _property_item, _value_item
            ])


class BaseTreeViewFieldUnitComponent(BaseTreeViewComponent):
    def _fillin_data(self):
        my_user_data: dict = self.data(Qt.ItemDataRole.UserRole)
        log.debug(f"BaseTreeViewFieldUnitComponent filling {my_user_data}")
        for prop in my_user_data.keys():
            _emptyItem = QStandardItem('')
            _emptyItem.setEditable(self.isEditable())  #from child object
            _property_item = QStandardItem(prop)
            _property_item.setEditable(self.isEditable())
            _value_item = QStandardItem(str(my_user_data.get(prop, '')))
            _value_item.setEditable(self.isEditable())
            self.appendRow([
                _emptyItem, _property_item, _value_item
            ])


class PLC_treview_item(QStandardItem, BaseTreeViewComponent):
    def __init__(self, *args, **kwargs):
        if 'my_user_data' in kwargs.keys():
            my_user_data = kwargs.get('my_user_data')
            if not isinstance(my_user_data, Plc):
                log.warning(f"Unexpected data type {type(my_user_data)}")
            del (kwargs['my_user_data'])
        else:
            my_user_data = None
        super().__init__(*args, **kwargs)
        self.setEditable(False)  # Make it non-editable

        self.setData(my_user_data, Qt.ItemDataRole.UserRole)
        self.setColumnCount(3)  ## Help here

        self._base_tree_view_component_init()

    def update_treeview_item(self):
        self._base_tree_view_component_update()


class UnitTreeViewItem(QStandardItem, BaseTreeViewFieldUnitComponent):
    def __init__(self, *args, **kwargs):
        log.info(f"New Field Unit treeview component")
        if 'my_user_data' in kwargs.keys():
            my_user_data = kwargs.get('my_user_data')
            if not type(my_user_data) is type({}):
                log.warning(f"Unexpected data type {type(my_user_data)}")
            del (kwargs['my_user_data'])
        else:
            my_user_data = {}
        super().__init__(*args, **kwargs)
        self.setEditable(False)  # Make it non-editable

        self.setData(my_user_data, Qt.ItemDataRole.UserRole)
        self.setColumnCount(3)

        self._base_tree_view_component_init()

    def update_treeview_item(self):
        self._base_tree_view_component_update()
