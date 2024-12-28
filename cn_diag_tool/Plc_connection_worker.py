import datetime
import logging
import time

import pycomm3
import cip_request

log = logging.getLogger(__name__)

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex
from pycomm3 import LogixDriver, ResponseError, RequestError, CommError
from pycomm3.logger import configure_default_logger

configure_default_logger(logging.WARNING)


class PLCConnectionWorkerSignals(QObject):
    read_done = pyqtSignal(int, dict)
    connection_lost = pyqtSignal(int, str)
    non_fatal_error = pyqtSignal(int, str)


class PLCConnectionWorker(QThread):
    def __init__(self, node_num: int, parent=None):  # Add parent for proper cleanup
        super().__init__(parent)
        self.node_num = node_num
        self._path = ''
        self.signals = PLCConnectionWorkerSignals()
        self._stop_event = False  # Use an event for stopping
        self._loop_time = 1.0  # Default loop time
        self.enable_writing = False
        self._mutex = QMutex()  # Mutex for thread safety during writes

        self._previous_counters = {}  # Store previous counter values
        self._previous_timestamp = time.monotonic()  # Initialize previous timestamp

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, p: str):
        self._path = p

    def stop(self):
        self._stop_event = True

    def update_cn_counters(self, new_counters):  # write_cn_counter implementation
        self._mutex.lock()
        self.cn_counters = new_counters.copy()  # Thread-safe copy
        self._mutex.unlock()

    def run(self):
        self._stop_event = False
        try:
            with pycomm3.CIPDriver(self._path) as driver:  # Context manager for cleanup
                while not self._stop_event:
                    start_time = time.monotonic()  # Use monotonic time for accurate timing
                    try:
                        ## ControlNet module counters
                        CN_counters_raw = driver.generic_message(**cip_request.cn_diag_counters)
                        if CN_counters_raw.error:
                            self.signals.non_fatal_error.emit(self.node_num, str(CN_counters_raw.error))
                        else:
                            reply_time = time.monotonic() - start_time
                            counters = cip_request.ControlNetCounters.decode(CN_counters_raw.value)
                            # self.update_cn_counters(counters)
                            current_timestamp = time.monotonic()
                            time_delta = current_timestamp - self._previous_timestamp

                            counters_with_rates = counters.copy()  # Create a copy to avoid modifying original data

                            # error emulation
                            counters_with_rates['#err_0'] = 8
                            counters_with_rates['#err_1'] = 8
                            counters_with_rates['#err_2'] = 8
                            counters_with_rates['#err_3'] = 5
                            counters_with_rates['#err_4'] = 5
                            counters_with_rates['#err_5'] = 7
                            # end of error emulation

                            counters_with_rates['reply_time'] = int(reply_time * 1_000_000)

                            for key, value in counters.items():
                                if key.startswith('#'):
                                    continue  # do not calculate per_sec for counters starts with #
                                try:
                                    increment = value - self._previous_counters.get(key,
                                                                                    value)  # Handle missing previous value
                                    rate = increment / time_delta if time_delta > 0 else 0  # Avoid division by zero
                                    counters_with_rates[key + "_per_sec"] = int(rate)  # Add increment per second

                                except TypeError:  # Handle cases where counter values are not numeric
                                    counters_with_rates[key + "_per_sec"] = "N/A"

                            self.signals.read_done.emit(self.node_num, counters_with_rates)

                            self._previous_counters = counters.copy()
                            self._previous_timestamp = current_timestamp

                        ## ControlNet module LEDs state
                        CN_LED_states_raw = driver.generic_message(**cip_request.cn_diag_LED)
                        if CN_LED_states_raw.error:
                            self.signals.non_fatal_error.emit(self.node_num, str(CN_LED_states_raw.error))
                        else:
                            leds = cip_request.ControlNetLED.decode(CN_LED_states_raw.value)
                            self.signals.read_done.emit(self.node_num, leds)

                    except (ResponseError, RequestError) as e:
                        self.signals.non_fatal_error.emit(self.node_num, str(e))
                    except CommError as e:
                        self.signals.connection_lost.emit(self.node_num, str(e))
                        break  # Exit loop on connection error
                    except Exception as e:  # Catch other errors
                        log.exception(f"Unexpected error in worker: {e}")  # Log traceback
                        self.signals.connection_lost.emit(self.node_num, str(e))
                        break

                    end_time = time.monotonic()
                    elapsed_time = end_time - start_time
                    sleep_duration = max(0, self._loop_time - elapsed_time)  # Ensure non-negative sleep
                    time.sleep(sleep_duration)


        except Exception as e:  # Catch initial connection error
            self.signals.connection_lost.emit(self.node_num, f"Failed to connect: {e}")
