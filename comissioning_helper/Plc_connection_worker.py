import logging
import time

import pycomm3

log = logging.getLogger(__name__)

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex
from pycomm3 import LogixDriver, ResponseError, RequestError, CommError

import helper_globals


class PLCConnectionWorkerSignals(QObject):
    connected = pyqtSignal(bool, str, str)  # Success (bool), Message (str)
    error = pyqtSignal(str)
    read_done = pyqtSignal(dict)
    write_done = pyqtSignal(dict)
    lost_connection = pyqtSignal(str)


class PLCConnectionWorkerReader(QThread):
    def __init__(self, path, mutex):
        super().__init__()
        self.path = path
        self.mutex: QMutex = mutex  # this is an external mutex
        self.signals = PLCConnectionWorkerSignals()
        self._read_tags_q = []
        self._connected = False

    def run(self):
        try:
            # global driver
            self.driver = LogixDriver(self.path)
            self.driver.open()
            log.info(f"Reader Connected to {self.path}")
            plc_name = self.driver.get_plc_name()
            plc_info = self.driver.get_plc_info()
            # print(tmp_driver.get_plc_info())
            formatted_info = f"""
            Vendor: {plc_info['vendor']}
            Product Type: {plc_info['product_type']}
            Product Code: {plc_info['product_code']}
            Product Name: {plc_info['product_name']}
            Revision: {plc_info['revision']['major']}.{plc_info['revision']['minor']}
            Serial: {plc_info['serial']}
            Keyswitch: {plc_info['keyswitch']}
            """
            self._connected = True
            self.signals.connected.emit(True, f"PLC Name: {plc_name}\n{formatted_info}", plc_name)

            while self._connected:
                time.sleep(1)
                self.mutex.lock()
                _now_reading = self._read_tags_q.copy()
                self._read_tags_q = []
                self.mutex.unlock()
                if not len(_now_reading):
                    continue
                try:
                    _now_tags = self.driver.read(*_now_reading)
                except ConnectionError as e:
                    log.error(f"Connection error: {e}")
                    self._connected = False
                    self.signals.lost_connection.emit()
                    return
                log.debug(f"Read {len(_now_tags)} tags")
                _temporary_dict = {}
                if isinstance(_now_tags, pycomm3.Tag):
                    _now_tag_list = [_now_tags, ]
                else:
                    _now_tag_list = _now_tags

                for _tag in _now_tag_list:
                    if _tag:
                        _temporary_dict[_tag.tag] = _tag.value
                    else:
                        _temporary_dict[_tag.tag] = None
                self.mutex.lock()
                helper_globals.tags.update(_temporary_dict)
                self.mutex.unlock()
                print(f"Read tags:\n {_temporary_dict}")

                self.signals.read_done.emit(_temporary_dict)

        except (ResponseError, RequestError, CommError, ConnectionError) as e:
            self._connected = False
            self.signals.connected.emit(False, f"Connection error: {e}", "Error")

    def read_tags_append(self, list_of_tags):
        """Read tags (list of tag)"""
        self._read_tags_q.extend(list_of_tags)


class PLCConnectionWorkerWriter(QThread):
    def __init__(self, path, mutex):
        super().__init__()
        self.path = path
        self.mutex: QMutex = mutex  # this is an external mutex
        self.signals = PLCConnectionWorkerSignals()
        self._write_tags_q = []
        self._connected = False
        self._open_driver()
        print(f"Writer init complete")

    def _open_driver(self):
        try:
            self.driver = LogixDriver(self.path)
            self.driver.open()
            log.info(f"Writer Connected to {self.path}")
            self._connected = True
            self.signals.connected.emit(True, f"Writer connected to : {self.path}", "")

        except (ResponseError, RequestError, CommError, ConnectionError) as e:
            self._connected = False
            self.signals.connected.emit(False, f"Connection error: {e}", "Error")


    def run(self):
        try:
            while self._connected:
                time.sleep(0.1)
                self.mutex.lock()
                _now_writing = self._write_tags_q.copy()
                self._write_tags_q = []
                self.mutex.unlock()
                if not len(_now_writing):
                    continue
                try:
                    _now_tags = self.driver.write(*_now_writing) ##   convert with emit
                except ConnectionError as e:
                    log.error(f"Connection error: {e}")
                    self._connected = False
                    self.signals.lost_connection.emit()
                    return
                log.debug(f"Write {len(_now_tags)} tags")
                _temporary_dict = {}
                if isinstance(_now_tags, pycomm3.Tag):
                    _now_tag_list = [_now_tags, ]
                else:
                    _now_tag_list = _now_tags

                for _tag in _now_tag_list:
                    if _tag:
                        _temporary_dict[_tag.tag] = _tag.value
                    else:
                        _temporary_dict[_tag.tag] = None
                self.mutex.lock()
                helper_globals.tags.update(_temporary_dict)
                self.mutex.unlock()
                print(f"Wrote tags:\n {_temporary_dict}")  #TODO: log.error

                self.signals.write_done.emit(_temporary_dict)

        except (ResponseError, RequestError, CommError, ConnectionError) as e:
            self._connected = False
            self.signals.connected.emit(False, f"Connection error: {e}", "Error")

    def write_tags_append(self, list_of_tags):
        """Read tags (list of tag)"""
        self._write_tags_q.extend(list_of_tags)