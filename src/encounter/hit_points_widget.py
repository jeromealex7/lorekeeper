from PySide2 import QtCore, QtWidgets

from src.widgets.number_edit import NumberEdit
from src.rulesets import RULESET


class HitPointsEdit(NumberEdit):

    def on_validation_changed(self, validated: bool):
        if validated:
            value = self.get()
            if (maximum := self._validator.maximum) is not None and value >= maximum:
                color = 'green'
            elif (critical := RULESET.HIT_POINTS_CRITICAL) is not None and value <= critical:
                color = 'red'
            else:
                color = 'black'
            self.setStyleSheet(f'HitPointsEdit{{background-color: white; color: {color};}};')
        else:
            self.setStyleSheet('HitPointsEdit{background-color: red;};')


class HitPointsWidget(QtWidgets.QWidget):
    CHANGED = QtCore.Signal(int)

    def __init__(self, maximum: float | int = None, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.hp_edit = HitPointsEdit(minimum=RULESET.HIT_POINTS_MINIMUM, maximum=maximum, decimals=0,
                                     parent=self)
        font = self.hp_edit.font()
        font.setBold(True)
        self.hp_edit.setFont(font)
        self.damage_edit = NumberEdit(decimals=0, minimum=-32000, parent=self)
        self.damage_edit.setPlaceholderText('Damage')

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.hp_edit)
        layout.addWidget(self.damage_edit)
        self.setLayout(layout)

        self.damage_edit.returnPressed.connect(self.on_damage_submit)
        self.hp_edit.CHANGED.connect(self.CHANGED.emit)

    def deal_damage(self, damage: int):
        self.hp_edit.set(self.hp_edit.get() - damage)

    def get(self) -> int:
        return self.hp_edit.get()

    def on_damage_submit(self):
        if not self.damage_edit.hasAcceptableInput():
            return
        self.deal_damage(self.damage_edit.get())
        self.damage_edit.set('')

    def set(self, value: int):
        self.hp_edit.set(value)
