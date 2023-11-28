import io
from typing import Sequence

import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from .default_abilities import DEFAULT_ABILITIES
from .guard import Guard
from src.widgets import Icon, AbilityDialog, AbilityEdit


class DefaultAbilityList(QtWidgets.QTreeWidget):
    ADD = QtCore.Signal(dict)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.df = pd.read_csv(io.StringIO(DEFAULT_ABILITIES), delimiter=';').sort_values(
            by=['type', 'name']
        )
        self.setColumnCount(1)
        self.setHeaderLabels(['Common Abilities:'])

        self.passive = QtWidgets.QTreeWidgetItem(self)
        self.passive.setText(0, 'Passive')
        self.action = QtWidgets.QTreeWidgetItem(self)
        self.action.setText(0, 'Actions')
        self.bonus = QtWidgets.QTreeWidgetItem(self)
        self.bonus.setText(0, 'Bonus Actions')
        self.reaction = QtWidgets.QTreeWidgetItem(self)
        self.reaction.setText(0, 'Reactions')
        self.legendary = QtWidgets.QTreeWidgetItem(self)
        self.legendary.setText(0, 'Legendary Actions')

        self.addTopLevelItems([self.passive, self.action, self.bonus, self.reaction, self.legendary])
        self.df.apply(self.add_row, axis=1)

    def add_row(self, series: pd.Series):
        match series['type']:
            case 'reaction': target = self.reaction
            case 'legendary': target = self.legendary
            case 'action': target = self.action
            case 'bonus': target = self.bonus
            case 'passive': target = self.passive
            case other: raise ValueError(f'Type {other} not recognised.')
        entry = QtWidgets.QTreeWidgetItem()
        entry.setText(0, series['name'])
        entry.setToolTip(0, series['text'])
        entry.setData(0, QtCore.Qt.UserRole, series.name)
        target.addChild(entry)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        selected = self.selectedIndexes()
        if not selected:
            return
        data = self.currentItem().data(0, QtCore.Qt.UserRole)
        if data is None:
            return
        self.ADD.emit(self.df.loc[data].to_dict())


class AbilityList(QtWidgets.QListWidget):

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)
        add_action = QtWidgets.QAction(Icon('plus'), 'Add New Ability', self)
        add_action.triggered.connect(self.on_new_ability)
        menu.addAction(add_action)
        if (selected := self.currentRow()) >= 0:
            name = self.currentItem().text()
            delete_action = QtWidgets.QAction(Icon('garbage_can'), f'Remove Ability "{name}"', self)
            delete_action.triggered.connect(lambda: self.takeItem(selected))
            menu.addAction(delete_action)
        menu.popup(event.globalPos())

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        super().keyPressEvent(event)
        if event.key() != QtCore.Qt.Key_Delete:
            return
        selected = self.selectedIndexes()
        if not selected:
            return
        self.takeItem(selected[0].row())

    def on_new_ability(self, data: dict = None):
        item = QtWidgets.QListWidgetItem()
        if not data:
            data = {'title': 'New Ability', 'type': 'passive', 'text': '', 'priority': 0}
        item.setData(QtCore.Qt.UserRole, data)
        self.addItem(item)
        self.setItemSelected(item, True)


class AbilityFrame(QtWidgets.QWidget):
    CHANGED = QtCore.Signal()

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.guard = guard

        self.ability_list = AbilityList(self)
        self.name_edit = QtWidgets.QLineEdit(self)
        self.type_edit = QtWidgets.QComboBox(self)
        self.type_edit.addItems(['passive', 'action', 'bonus', 'reaction', 'legendary'])
        self.priority_button = QtWidgets.QCheckBox(self)
        self.priority_button.setText('Priority')
        self.name_edit.setEnabled(False)
        self.type_edit.setEnabled(False)
        self.priority_button.setEnabled(False)
        self.ability_edit = AbilityEdit(guard, self)
        self.default_ability_list = DefaultAbilityList(self)

        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel('Ability:'))
        header.addWidget(self.name_edit)
        header.addWidget(self.type_edit)
        header.addWidget(self.priority_button)
        body = QtWidgets.QVBoxLayout()
        body.addLayout(header)
        body.addWidget(self.ability_edit)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.default_ability_list)
        layout.addWidget(self.ability_list)
        layout.addLayout(body)
        self.setLayout(layout)

        self.ability_list.itemSelectionChanged.connect(self.on_index_changed)
        self.default_ability_list.ADD.connect(self.add_ability)
        self.name_edit.textChanged.connect(self.on_ability_changed)
        self.ability_edit.textChanged.connect(self.on_ability_changed)
        self.priority_button.toggled.connect(self.on_ability_changed)
        self.type_edit.currentIndexChanged.connect(self.on_ability_changed)
        self.default_ability_list.installEventFilter(self)

    def add_ability(self, data: dict):
        dialog = AbilityDialog(self.guard, data['title'], data['text'], self)
        if dialog.has_details():
            dialog.exec_()
            text = dialog.text
            if not text:
                return
            data['text'] = text
            data['title'] = dialog.title
        self.ability_list.on_new_ability(data)

    def eventFilter(self, watched: QtWidgets.QWidget, event: QtCore.QEvent) -> bool:
        if watched == self.default_ability_list:
            if event.type() == QtCore.QEvent.KeyPress and self.default_ability_list.selectedIndexes():
                if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Space):
                    item = self.default_ability_list.currentItem()
                    try:
                        self.add_ability(self.default_ability_list.df.loc[item.data(0, QtCore.Qt.UserRole)].to_dict())
                    except KeyError:
                        pass
                    return True
        return super().eventFilter(watched, event)

    def get(self) -> list[dict[str, str | int]]:
        abilities = [self.ability_list.item(row).data(QtCore.Qt.UserRole) for row in range(self.ability_list.count())]
        abilities.sort(key=lambda a: (-a['priority'], a['title']))
        return abilities

    def on_index_changed(self):
        selected = self.ability_list.selectedIndexes()
        if selected:
            data = self.ability_list.item(selected[0].row()).data(QtCore.Qt.UserRole)
        else:
            data = {'title': '', 'text': '', 'type': 'passive', 'priority': 0}
        self.name_edit.setText(data['title'])
        self.ability_edit.setPlainText(data['text'])
        self.type_edit.setCurrentText(data['type'])
        self.priority_button.setChecked(bool(data['priority']))
        self.name_edit.setEnabled(bool(selected))
        self.ability_edit.setEnabled(bool(selected))
        self.type_edit.setEnabled(bool(selected))
        self.priority_button.setEnabled(bool(selected))
        self.on_ability_changed(self.name_edit.text())

    def on_ability_changed(self, _=None):
        selected = self.ability_list.selectedIndexes()
        if not selected:
            return
        item = self.ability_list.item(selected[0].row())
        item.setText(self.name_edit.text())
        data = {'title': self.name_edit.text(), 'priority': self.priority_button.checkState(),
                'text': self.ability_edit.toPlainText(),
                'type': self.type_edit.currentText()}
        item.setData(QtCore.Qt.UserRole, data)
        self.CHANGED.emit()

    def set(self, abilities: Sequence[dict[str, str | int]]):
        self.ability_list.clear()
        for ability in abilities:
            self.add_ability(ability)
