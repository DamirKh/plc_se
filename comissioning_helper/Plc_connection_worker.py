import datetime
import logging
import time

import pycomm3

log = logging.getLogger(__name__)

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex
from pycomm3 import LogixDriver, ResponseError, RequestError, CommError
from pycomm3.logger import configure_default_logger

configure_default_logger(logging.WARNING)


class PLCConnectionWorkerSignals(QObject):
    connected = pyqtSignal(bool, str, str)  # Success (bool), Message (str)
    error = pyqtSignal(str)
    read_done = pyqtSignal(list)
    write_done = pyqtSignal(dict)
    lost_connection = pyqtSignal(str)
    current_time = pyqtSignal(datetime.datetime, int)


class PLCConnectionWorker(QThread):
    def __init__(self, mutex=None):
        super().__init__()
        self._path = ''
        self.mutex: QMutex = mutex or QMutex()  # an external mutex or create new one
        self.signals = PLCConnectionWorkerSignals()
        self._read_tags_q = []
        self._write_tags_q = []
        self._connected = False
        self._write_enabled = False
        self._loop_time = 0.01
        self._worker_communication_time = 0

    @property
    def enable_writing(self):
        return self._write_enabled

    @enable_writing.setter
    def enable_writing(self, enable: bool):
        self.mutex.lock()
        self._write_tags_q = []  # drop write query
        self._write_enabled = enable
        self.mutex.unlock()

    @property
    def connected(self):
        return self._connected

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, p: str):
        if not self._connected:
            log.info(f"Path to PLC set to {p}")
            self._path = p

    def connect(self):
        self._connected = False
        if self._path:
            try:
                self.driver = LogixDriver(self._path)
                log.debug(f"Opening connection to {self._path}...")
                self.driver.open()
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
                log.info(f"Connected to {plc_name}: {self._path}")
                self.signals.connected.emit(True, f"PLC Name: {plc_name}\n{formatted_info}", plc_name)
                return True, f"PLC Name: {plc_name}\n{formatted_info}"
            except (ResponseError, RequestError, CommError, ConnectionError) as e:
                # self.signals.connected.emit(False, f"Connection error: {e}", "Error")
                log.error(f"Connection error: {e}")
                return False, f"Connection error: {e}"
        else:
            log.info(f"set path to PLC first")
            return False, "set path to PLC first"

    def run(self):
        try:
            prev_seconds = 0
            while self._connected:
                time.sleep(self._loop_time)
                circle_start_time = time.monotonic_ns()
                current_seconds = int(time.time())
                if current_seconds != prev_seconds:
                    plc_time = self.driver.get_plc_time()
                    prev_seconds = current_seconds
                    self.signals.current_time.emit(plc_time.value['datetime'], self._worker_communication_time)  # once per second
                    self._worker_communication_time = 0
                self.mutex.lock()
                _now_reading = self._read_tags_q.copy()
                self._read_tags_q = []
                self.mutex.unlock()
                if len(_now_reading):
                    try:
                        _now_tags = self.driver.read(*_now_reading)
                    except ConnectionError as e:
                        log.error(f"Connection error: {e}")
                        self._connected = False
                        self.signals.lost_connection.emit(f"Connection error: {e}")
                        continue
                    # _temporary_dict = {}
                    if isinstance(_now_tags, pycomm3.Tag):
                        _now_tag_list = [_now_tags, ]
                    else:
                        _now_tag_list = _now_tags
                    self.signals.read_done.emit(_now_tag_list)

                # write tags #####################################################################################
                if self._write_enabled:
                    self.mutex.lock()
                    _now_writing = self._write_tags_q.copy()
                    self._write_tags_q = []
                    self.mutex.unlock()
                    if len(_now_writing):
                        try:
                            _now_tags = self.driver.write(*_now_writing)
                        except ConnectionError as e:
                            log.error(f"Connection error: {e}")
                            self._connected = False
                            self.signals.lost_connection.emit(f"Connection error: {e}")
                            continue
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
                        log.debug(f"Wrote tags:\n {_temporary_dict}")

                        self.signals.write_done.emit(_temporary_dict)
                        # self.signals.read_done.emit(_temporary_dict)

                _cycle_comm_time = time.monotonic_ns() - circle_start_time
                self._worker_communication_time += _cycle_comm_time

        except (ResponseError, RequestError, CommError, ConnectionError) as e:
            self._connected = False
            self.signals.connected.emit(False, f"Connection error: {e}", "Error")

    @property
    def read_tags(self):
        return self._read_tags_q

    @read_tags.setter
    def read_tags(self, list_of_tags):
        print(list_of_tags)
        self.mutex.lock()
        self._read_tags_q.extend(list_of_tags)
        self.mutex.unlock()

    @property
    def write_tags(self):
        return self._write_tags_q

    @write_tags.setter
    def write_tags(self, list_of_tags):
        self.mutex.lock()
        self._write_tags_q.extend(list_of_tags)
        self.mutex.unlock()
