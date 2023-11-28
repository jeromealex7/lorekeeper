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

        self.general = QtWidgets.QTreeWidgetItem(self)
        self.general.setText(0, 'General')
        self.defensive = QtWidgets.QTreeWidgetItem(self)
        self.defensive.setText(0, 'Defensive')
        self.offensive = QtWidgets.QTreeWidgetItem(self)
        self.offensive.setText(0, 'Offensive')

        self.addTopLevelItems([self.general, self.defensive, self.offensive])
        self.df.apply(self.add_row, axis=1)

    def add_row(self, series: pd.Series):
        match series['type']:
            case 'general': target = self.general
            case 'defensive': target = self.defensive
            case 'offensive': target = self.offensive
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
            data = {'name': 'New Ability', 'type': 'general', 'text': '', 'actions': ''}
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
        self.type_edit.addItems(['general', 'defensive', 'offensive'])
        self.actions_edit = QtWidgets.QComboBox(self)
        self.actions_edit.addItems(['', '1 action', '2 actions', '3 actions', 'free action', 'reaction', '1 minute',
                                    '10 minutes'])
        self.actions_edit.setEditable(True)
        self.name_edit.setEnabled(False)
        self.type_edit.setEnabled(False)
        self.actions_edit.setEnabled(False)
        self.ability_edit = AbilityEdit(guard, self)
        self.default_ability_list = DefaultAbilityList(self)

        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel('Ability:'))
        header.addWidget(self.name_edit)
        header.addWidget(self.type_edit)
        header.addWidget(self.actions_edit)
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
        self.type_edit.currentIndexChanged.connect(self.on_ability_changed)
        self.actions_edit.currentIndexChanged.connect(self.on_ability_changed)
        self.default_ability_list.installEventFilter(self)

    def add_ability(self, data: dict):
        dialog = AbilityDialog(self.guard, data['name'], data['text'], self)
        if dialog.has_details():
            dialog.exec_()
            text = dialog.text
            if not text:
                return
            data['text'] = text
            data['name'] = dialog.title
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
        abilities.sort(key=lambda a: a['name'])
        return abilities

    def on_index_changed(self):
        selected = self.ability_list.selectedIndexes()
        if selected:
            data = self.ability_list.item(selected[0].row()).data(QtCore.Qt.UserRole)
        else:
            data = {'name': '', 'text': '', 'type': 'general', 'actions': ''}
        self.name_edit.setText(data['name'])
        self.ability_edit.setPlainText(data['text'])
        self.type_edit.setCurrentText(data['type'])
        self.actions_edit.setCurrentText(data['actions'])
        self.name_edit.setEnabled(bool(selected))
        self.ability_edit.setEnabled(bool(selected))
        self.type_edit.setEnabled(bool(selected))
        self.actions_edit.setEnabled(bool(selected))
        self.on_ability_changed(self.name_edit.text())

    def on_ability_changed(self, _=None):
        selected = self.ability_list.selectedIndexes()
        if not selected:
            return
        item = self.ability_list.item(selected[0].row())
        item.setText(self.name_edit.text())
        data = {'name': self.name_edit.text(), 'actions': self.actions_edit.currentText(),
                'text': self.ability_edit.toPlainText(),
                'type': self.type_edit.currentText()}
        item.setData(QtCore.Qt.UserRole, data)
        self.CHANGED.emit()

    def set(self, abilities: Sequence[dict[str, str | int]]):
        self.ability_list.clear()
        for ability in abilities:
            self.add_ability(ability)
