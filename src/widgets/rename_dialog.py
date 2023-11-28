from PySide2 import QtCore, QtWidgets

from src.model import Feature
from src.settings import SIGNALS
from src.widgets import Icon


class RenameAction(QtWidgets.QAction):

    def __init__(self, feature: Feature, icon_name: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(Icon('note_text'), f'Rename {feature.__class__.__name__}', parent)
        self.triggered.connect(RenameDialog(feature, icon_name, parent).exec_)


class RenameDialog(QtWidgets.QDialog):

    def __init__(self, feature: Feature, icon_name: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.feature = feature
        name = feature.__class__.__name__

        self.setWindowIcon(Icon(icon_name))
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowTitle(f'Rename {name}')
        self.text_edit = QtWidgets.QLineEdit(self)
        self.text_edit.setPlaceholderText(f'Enter {name} Name')
        self.text_edit.setText(feature['name'])
        self.text_edit.setSelection(0, len(feature['name']))
        self.text_edit.setMinimumWidth(250)
        self.button_box = QtWidgets.QDialogButtonBox(self)
        accept_button = QtWidgets.QPushButton(Icon(icon_name), 'Rename', self)
        accept_button.clicked.connect(self.rename)
        cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
        cancel_button.clicked.connect(self.deleteLater)
        self.button_box.addButton(accept_button, self.button_box.AcceptRole)
        self.button_box.addButton(cancel_button, self.button_box.RejectRole)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def rename(self):
        SIGNALS.TAB_RENAME.emit(self.feature.TABLE_NAME, self.feature.db_index, self.text_edit.text())
        self.deleteLater()
