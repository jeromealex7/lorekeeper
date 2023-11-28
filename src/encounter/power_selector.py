from PySide2 import QtCore, QtWidgets

from src.rulesets import RULESET
from src.widgets import NumberEdit


class PowerSelector(QtWidgets.QWidget):
    CHANGED = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        if isinstance(RULESET.POWER_LEVELS, (tuple, list)):
            self.widget = QtWidgets.QComboBox(self)
            self.widget.addItems(list(map(str, RULESET.POWER_LEVELS)))
            self.widget.currentIndexChanged[str].connect(self.CHANGED.emit)
            self.get = self.widget.currentText
            self.set = lambda t: self.widget.setCurrentText(str(t))
        elif RULESET.POWER_LEVELS == 'int':
            self.widget = NumberEdit()
            self.widget.CHANGED.connect(lambda num: self.CHANGED.emit(str(num)))
            self.get = self.widget.get
            self.set = self.widget.set
        else:
            self.widget = QtWidgets.QLineEdit(self)
            self.widget.textChanged.connect(self.CHANGED.emit)
            self.get = self.widget.text
            self.set = lambda t: self.widget.setText(str(t))

        self.widget.setMinimumWidth(60)
        size_policy = QtWidgets.QSizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Ignored)
        size_policy.setVerticalPolicy(size_policy.Fixed)
        self.widget.setSizePolicy(size_policy)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.widget)
        self.setLayout(layout)
