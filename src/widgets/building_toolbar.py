from functools import partial
from typing import Type

from PySide2 import QtCore, QtWidgets

from .icon import Icon
from src.model import Feature, Keep
from src.settings import SIGNALS


class BuildingTypeAction(QtWidgets.QAction):

    def __init__(self, type_: str = None, icon_name: str = '', checked: bool = True,
                 parent: QtWidgets.QToolBar | None = None):
        super().__init__(Icon(icon_name), '', parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.type_ = type_


class BuildingToolbar(QtWidgets.QToolBar):
    STATE = QtCore.Signal(bool, str)
    STRING = QtCore.Signal(tuple, tuple)
    TIMER_SECONDS: int = 400

    def __init__(self, keep: Keep, feature_type: Type[Feature], parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.feature_type = feature_type
        self.keep = keep

        self.building_type_actions: dict[str, BuildingTypeAction] = {}
        self.hidden_button = QtWidgets.QToolButton(self)
        self.hidden_button.setCheckable(True)
        self.hidden_button.setToolTip('Show Hidden')
        self.hidden_button.setIcon(Icon('eye_blind'))
        self.hidden_button.setChecked(True)
        self.hidden_button.toggled.connect(lambda _: self.emit_search())
        self.search_edit = QtWidgets.QLineEdit(self)
        self.search_edit.setPlaceholderText('Enter search string')
        self.search_edit.textChanged.connect(self.on_search_string_changed)
        self.addWidget(QtWidgets.QLabel('Search: '))
        self.addWidget(self.search_edit)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.emit_search)

        if 'type' in feature_type.get_default_data():
            self.addWidget(QtWidgets.QLabel(' Filter Types: '))
            SIGNALS.FEATURE_COMMIT.connect(self.on_feature_commit)
            SIGNALS.FEATURE_DELETE.connect(self.on_feature_commit)
            self.on_feature_commit(self.feature_type.TABLE_NAME)

        self.addSeparator()
        self.addWidget(self.hidden_button)

    def emit_search(self):
        white_list = []
        black_list = []
        if not self.hidden_button.isChecked():
            black_list.append('_hidden')
        for tag in self.search_edit.text().split('&'):
            tag = tag.strip().lower()
            if tag.startswith('~'):
                black_list.append(tag[1:].strip())
            else:
                white_list.append(tag.strip())
        self.STRING.emit(white_list, black_list)

    @staticmethod
    def get_icon_name(type_: str) -> str:
        return ''

    def on_clicked(self, action: BuildingTypeAction):
        if QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.ShiftModifier:
            return
        for other in self.findChildren(BuildingTypeAction):
            other.setChecked(action == other)

    def on_feature_commit(self, table_name: str, _: int = None):
        if table_name != self.feature_type.TABLE_NAME:
            return
        completer = QtWidgets.QCompleter(
            self.keep.buildings[self.feature_type.TAG_TABLE_NAME].df['name'].unique().tolist())
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.reload_feature_types()
        self.search_edit.setCompleter(completer)

    def on_search_string_changed(self, _: str):
        self.timer.start(self.TIMER_SECONDS)

    def on_toggle(self, action: BuildingTypeAction, state: bool):
        self.STATE.emit(state, action.type_)

    def reload_feature_types(self):
        type_list = self.keep.buildings[self.feature_type.TABLE_NAME].df['type'].unique()
        for type_name in type_list:
            if type_name in self.building_type_actions:
                continue
            action = BuildingTypeAction(type_name, self.get_icon_name(type_name), True, self)
            self.building_type_actions[type_name] = action
            self.addAction(action)
            action.toggled.connect(partial(self.on_toggle, action))
            action.triggered.connect(partial(self.on_clicked, action))
        for type_name in list(self.building_type_actions.keys()).copy():
            if type_name in type_list:
                continue
            self.removeAction(self.building_type_actions.pop(type_name))

    def search(self):
        self.search_edit.setFocus()
        self.search_edit.setSelection(0, len(self.search_edit.text()))
