from PyQt6.QtCore import QThread, pyqtSignal

import g
from l5x import l5x


class WorkerThread(QThread):
    """Worker thread for performing long-running tasks."""

    result_ready = pyqtSignal(str)  # Signal to emit the result

    def __init__(self, l5x_filename, parent=None):
        super().__init__(parent)
        self.filename = l5x_filename

    def run(self):
        """Long-running task is executed here."""
        g.l5x = l5x.Project(self.filename)
        self.result_ready.emit(f"Reading {self.filename} successfully!")
