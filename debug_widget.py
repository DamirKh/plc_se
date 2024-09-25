from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
import pprint  # For pretty-printing data structures

class DebugWidget(QWidget):

    names_to_show = 'project_config', 'project_changed', 'plcs', 'units', 'drivers'
    def __init__(self, g_namespace):
        super().__init__()
        self.g_namespace = g_namespace
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Debug Widget")
        self.layout = QVBoxLayout()
        self.label = QLabel("Global Variables:")
        self.layout.addWidget(self.label)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)  # Make it read-only
        self.text_edit.setFontFamily('monospace')
        self.layout.addWidget(self.text_edit)

        self.setLayout(self.layout)

    def update_debug_info(self):
        """Updates the debug information, excluding internal attributes."""
        filtered_data = {
            key: value
            for key, value in self.g_namespace.items()
            # if not (key.startswith('__') and key.endswith('__'))
            if key in self.names_to_show
        }
        debug_text = pprint.pformat(filtered_data)
        self.text_edit.setPlainText(debug_text)

    # def update_debug_info(self):
    #     """Updates the debug information in the text edit."""
    #
    #     no_bi = self.g_namespace
    #     del(no_bi['__builtins__'])
    #     debug_text = pprint.pformat(no_bi)  # Pretty-print the namespace
    #     self.text_edit.setPlainText(debug_text)
