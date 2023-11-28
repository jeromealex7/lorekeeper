from PySide2 import QtCore, QtWidgets

from .number_edit import NumberEdit
from src.model import Keep
from src.rulesets import RULESET
from src.settings import SIGNALS


class PlayerVariableSetter(QtWidgets.QWidget):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep

        self.player_count_edit = QtWidgets.QComboBox(self)
        for player_count in range(2, 10):
            self.player_count_edit.addItem(f'{player_count} Players', player_count)
        self.player_count_edit.setCurrentText(f'{self.keep.player_count} Players')
        match RULESET.PLAYER_LEVELS:
            case 'str':
                self.player_level_edit = QtWidgets.QLineEdit(self)
                self.player_level_edit.textChanged.connect(self.refresh_variables)

                def set_level():
                    self.player_level_edit.setText(str(self.keep.player_level))

                def get_level():
                    return self.player_level_edit.text()
            case 'int':
                self.player_level_edit = NumberEdit(minimum=0, parent=self)
                self.player_level_edit.CHANGED.connect(lambda _: self.refresh_variables())

                def set_level():
                    self.player_level_edit.set(str(self.keep.player_level))

                def get_level():
                    return self.player_level_edit.get()
            case levels:
                self.player_level_edit = QtWidgets.QComboBox(self)
                for level_name, level in levels:
                    self.player_level_edit.addItem(level_name, level)
                self.player_level_edit.currentIndexChanged.connect(lambda _: self.refresh_variables())

                def set_level():
                    for n, lvl in levels:
                        if lvl == self.keep.player_level:
                            self.player_level_edit.setCurrentText(n)
                            break

                def get_level():
                    return self.player_level_edit.currentData(QtCore.Qt.UserRole)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.player_count_edit)
        layout.addWidget(self.player_level_edit)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self._get_level = get_level
        self._set_level = set_level
        self.reload_variables()
        self.player_count_edit.currentIndexChanged.connect(lambda _: self.refresh_variables())

    def refresh_variables(self):
        self.keep.player_count = self.player_count_edit.currentData(QtCore.Qt.UserRole)
        self.keep.player_level = self._get_level()
        SIGNALS.ENCOUNTER_VARIABLES.emit()

    def reload_variables(self):
        self._set_level()
        self.player_count_edit.setCurrentText(f'{self.keep.player_count} Players')
