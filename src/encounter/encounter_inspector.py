from functools import partial
import re
from collections import defaultdict
from pathlib import Path
from typing import Literal

import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from .checkbox import Checkbox
from .hit_points_widget import HitPointsWidget
from .notes_edit import NotesEdit
from .number_edit_container import NumberEditContainer
from .power_selector import PowerSelector
from .roll_widget import RollWidget
from .text_edit import TextEdit
from .token_widget import TokenWidget
from .type_selector import TypeSelector
from src.model import Banner, Combatant, Encounter
from src.rulesets import RULESET
from src.settings import PATHS, SIGNALS, SHORTCUTS
from src.widgets import DeleteDialog, Icon, Preview, Summary, TagFrame


class NewEntryValidator(QtGui.QValidator):
    REGEX_NEW = re.compile(r'^[^:]*(?::(?:\s*[+-]?\s*\d+\s*(?:d\s*\d+|\.\d+)?)*\s*'
                           r'(?::(?:\s*[+-]?\s*\d+\s*(?:d\s*\d+)?)*)?)?$')
    VALIDATION_CHANGED = QtCore.Signal(bool)

    def validate(self, text: str, position: int) -> QtGui.QValidator.State:
        try:
            if any(not char.isnumeric() and char not in 'd +-.' for char in ''.join(text.split(':')[1:])) or \
                    text.count(':') > 2:
                return QtGui.QValidator.Invalid
        except IndexError:
            pass
        if self.REGEX_NEW.match(text):
            self.VALIDATION_CHANGED.emit(True)
            return QtGui.QValidator.Acceptable
        self.VALIDATION_CHANGED.emit(False)
        return QtGui.QValidator.Intermediate


class EncounterStateButton(QtWidgets.QToolButton):
    SIZE: int = 60

    def __init__(self, icon_name: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCheckable(True)
        self.setIcon(Icon(icon_name))
        self.setIconSize(QtCore.QSize(self.SIZE, self.SIZE))


class EncounterInspector(QtWidgets.QMainWindow):
    HEADER = (('name', 'Name'), ('index', '#'), ('token', 'Token'), ('notes', 'Notes'), ('type', 'Type'),
              ('initiative', 'Initiative'), ('initiative_roll', 'Initiative Roll'), ('hit_points', 'Hit Points'),
              ('maximum_hit_points', 'Max. Hit Points'), ('maximum_hit_points_roll', 'Hit Points Roll'),
              ('label', 'Label'), ('power', 'Power'), ('show', 'Show'), ('_ini', '_ini'), ('_guard', '_guard'))

    def __init__(self, encounter: Encounter, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet('*{font-family: Roboto Slab; font-size: 10pt;};')
        self.setWindowIcon(Icon('sword'))
        SHORTCUTS.activate_shortcuts(self)
        self.token_dict = defaultdict(str)
        self.encounter = encounter
        self.keep = encounter.keep
        self._is_modified = False
        self.frame = QtWidgets.QFrame(self)
        self.setCentralWidget(self.frame)
        self.resize(1280, 960)
        self.feature_preview = None

        self.name_label = QtWidgets.QLabel('Name:', self)
        self.name_entry = QtWidgets.QLineEdit(self)
        self.name_entry.setPlaceholderText('Encounter Name')
        self.summary = Summary(self)
        self.summary.setMaximumHeight(100)
        self.tag_frame = TagFrame(600, self.keep.buildings['banner'], 'Banner')
        self.new_label = QtWidgets.QLabel('New Entry:', self)
        self.new_validator = NewEntryValidator(self)
        self.new_entry = QtWidgets.QLineEdit(self)
        self.new_entry.setValidator(self.new_validator)
        self.new_entry.setPlaceholderText('Name : Initiative : Hit Points')
        self.table = QtWidgets.QTableWidget(self)
        self.header = QtWidgets.QWidget(self)

        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(self.name_label, stretch=0)
        name_layout.addWidget(self.name_entry, stretch=1)
        header_layout = QtWidgets.QVBoxLayout()
        header_layout.addLayout(name_layout)
        header_layout.addWidget(self.summary)
        header_layout.addWidget(self.tag_frame)
        self.image = RULESET.get_encounter_gage(parent=self)
        self.toolbar = QtWidgets.QToolBar(self)
        self.delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Delete Combatant(s)', self)
        self.delete_action.triggered.connect(self.on_delete)
        self.delete_action.setShortcut(QtGui.QKeySequence('Delete'))
        self.copy_action = QtWidgets.QAction(Icon('copy'), 'Copy Combatants', self)
        self.copy_action.triggered.connect(self.on_copy)
        self.copy_action.setShortcut(QtGui.QKeySequence('Ctrl+Shift+C'))
        self.damage_action = QtWidgets.QAction(Icon('axe'), 'Deal Damage', self)
        self.damage_action.setShortcut(QtGui.QKeySequence('Ctrl+Shift+D'))
        self.damage_action.triggered.connect(self.on_damage)
        self.reorder_action = QtWidgets.QAction(Icon('sort_up_down2'), 'Move')
        self.reorder_action.triggered.connect(self.on_reorder)
        self.roll_action = QtWidgets.QAction(Icon('dice'), 'Reroll', self)
        self.roll_action.triggered.connect(self.on_reroll)
        self.inspect_action = QtWidgets.QAction(Icon('helmet'), 'Inspect Guard', self)
        self.inspect_action.triggered.connect(self.on_inspect_guard)
        self.stats_action = QtWidgets.QAction(Icon('note_text'), 'Show Stats', self)
        self.stats_action.triggered.connect(self.on_stats_guard)
        self.popup_action = QtWidgets.QAction(Icon('photo_portrait'), 'Show Portrait', self)
        self.popup_action.triggered.connect(self.on_popup_guard)
        self.state_action = QtWidgets.QAction(Icon('sword'), 'Battle Mode', self)
        self.state_action.setCheckable(True)
        self.state_action.toggled.connect(self.on_battle_view_changed)
        self.presenter_action = QtWidgets.QAction(Icon('flatscreen_tv'), 'Show in Presenter', self)
        self.presenter_action.setCheckable(True)
        self.presenter_action.toggled.connect(self.on_presenter)
        self.auto_upload_action = QtWidgets.QAction(Icon('cloud_upload'), 'Automatic Upload', self)
        self.auto_upload_action.toggled.connect(lambda _: self.sort())
        self.auto_upload_action.setCheckable(True)
        self.toolbar.addActions([self.copy_action, self.damage_action, self.roll_action, self.inspect_action,
                                 self.reorder_action, self.stats_action, self.popup_action, self.delete_action])
        self.toolbar.addSeparator()
        self.toolbar.addActions([self.state_action, self.presenter_action, self.auto_upload_action])
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.new_label)
        self.toolbar.addWidget(self.new_entry)

        header_image_layout = QtWidgets.QHBoxLayout()
        header_image_layout.addLayout(header_layout)
        header_image_layout.addWidget(self.image)
        self.header.setLayout(header_image_layout)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.header, stretch=0)
        layout.addWidget(self.toolbar, stretch=0)
        layout.addWidget(self.table, stretch=1)
        self.frame.setLayout(layout)

        menu_bar = QtWidgets.QMenuBar(self)
        file_menu = QtWidgets.QMenu(self)
        file_menu.setTitle('&Encounter')
        delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Delete Encounter', self)
        delete_action.triggered.connect(self.delete_encounter)
        save_action = QtWidgets.QAction(Icon('floppy_disk'), 'Save Encounter', self)
        save_action.triggered.connect(self.save)
        save_action.setShortcut(QtGui.QKeySequence('Ctrl+S'))
        reload_action = QtWidgets.QAction(Icon('refresh'), 'Reload from Enlistment', self)
        reload_action.triggered.connect(self.load_encounter)
        close_action = QtWidgets.QAction(Icon('door_exit'), 'Exit', self)
        close_action.triggered.connect(self.close_window)
        close_action.setShortcut(QtGui.QKeySequence('Alt+F4'))
        sort_icon = Icon('sort_19_ascending.png') if RULESET.INITIATIVE_ASCENDING else Icon('sort_19_descending.png')
        sort_action = QtWidgets.QAction(sort_icon, 'Sort by Initiative', self)
        sort_action.triggered.connect(self.sort)
        sort_action.setShortcut(QtGui.QKeySequence('F6'))
        file_menu.addSeparator()
        file_menu.addActions([reload_action, save_action, delete_action, sort_action])
        file_menu.addSeparator()
        file_menu.addAction(close_action)
        menu_bar.addMenu(file_menu)

        self.setMenuBar(menu_bar)

        self.table.installEventFilter(self)
        self.table.viewport().setAcceptDrops(True)
        self.table.viewport().installEventFilter(self)
        self.table.setMouseTracking(True)

        self.name_entry.textChanged.connect(self.set_modified)
        self.new_entry.returnPressed.connect(self.add_new)
        self.new_validator.VALIDATION_CHANGED.connect(self.on_entry_validation)
        self.summary.textChanged.connect(self.set_modified)
        self.tag_frame.TAGS_CHANGED.connect(lambda _: self.set_modified(True))
        self.table.itemSelectionChanged.connect(self.on_selection_change)
        self.table.setContextMenuPolicy(QtGui.Qt.CustomContextMenu)
        SIGNALS.ENCOUNTER_DELETE.connect(self.on_encounter_delete)
        SIGNALS.ENCOUNTER_VARIABLES.connect(self.reload_gage)
        SIGNALS.ENCOUNTER_ACTIVATE.connect(self.on_encounter_activate)
        SIGNALS.GUARD_COMMIT.connect(self.on_selection_change)
        SIGNALS.GUARD_DELETE.connect(self.on_selection_change)

        self.load_encounter()
        self.on_selection_change()

    def add_combatant(self, combatant: Combatant):
        self.add_row(name=combatant['name'], index=None, token=None,
                     type='enemy', notes='', initiative=None,
                     initiative_roll=combatant['initiative_roll'], hit_points=None,
                     maximum_hit_points=None, label=combatant['label'],
                     maximum_hit_points_roll=combatant['maximum_hit_points_roll'], power=combatant['power'],
                     show=True, _guard=combatant['_guard'])

    def add_row(self, name: str, index: int = None, token: str = None,
                type: Literal['enemy', 'player', 'effect'] | str = 'enemy', notes: str = None,
                initiative: float | int = None, initiative_roll: float | int | str = '', hit_points: int = None,
                maximum_hit_points: int = None, maximum_hit_points_roll: int | str = '', label: str = '',
                power: str = '', show: bool = True, _guard: int = 0, **_):
        row = self.table.rowCount()
        index = index or max([self.table.cellWidget(r, 1).get() for r in range(row)
                              if self.table.cellWidget(r, 0).get() == name] + [0]) + 1
        self.table.insertRow(row)

        name_item = TextEdit(width=120, text=name, parent=self.table)
        index_item = NumberEditContainer(minimum=1, parent=self)
        index_item.set(index)
        token_item = TokenWidget(value=token, parent=self)
        label_item = TextEdit(width=120, text=label, parent=self)
        type_item = TypeSelector(type, self)
        notes_item = NotesEdit(notes, self)
        _guard_item = NumberEditContainer(parent=self)
        _guard_item.set(_guard or 0)
        _initiative_item = QtWidgets.QTableWidgetItem()
        _initiative_item.setFlags(_initiative_item.flags() & ~QtCore.Qt.ItemIsEditable)
        initiative_roll_item = RollWidget(self)
        initiative_item = NumberEditContainer(decimals=3, parent=self)
        maximum_hit_points_roll_item = RollWidget(self)
        maximum_hit_points_item = NumberEditContainer(parent=self)
        hit_points_item = HitPointsWidget(parent=self)
        power_item = PowerSelector(self)
        power_item.setMinimumWidth(120)
        power_item.set(power)
        show_item = Checkbox(self)
        show_item.set(show)

        self.table.setCellWidget(row, 0, name_item)
        self.table.setCellWidget(row, 1, index_item)
        self.table.setCellWidget(row, 2, token_item)
        self.table.setCellWidget(row, 3, notes_item)
        self.table.setCellWidget(row, 4, type_item)
        self.table.setCellWidget(row, 5, initiative_item)
        self.table.setCellWidget(row, 6, initiative_roll_item)
        self.table.setCellWidget(row, 7, hit_points_item)
        self.table.setCellWidget(row, 8, maximum_hit_points_item)
        self.table.setCellWidget(row, 9, maximum_hit_points_roll_item)
        self.table.setCellWidget(row, 10, label_item)
        self.table.setCellWidget(row, 11, power_item)
        self.table.setCellWidget(row, 12, show_item)
        self.table.setItem(row, 13, _initiative_item)
        self.table.setCellWidget(row, 14, _guard_item)

        initiative_roll_item.ROLLED.connect(initiative_item.set)
        initiative_item.CHANGED.connect(lambda value: _initiative_item.setText(f'{value:>020.10f}'))
        maximum_hit_points_roll_item.ROLLED.connect(maximum_hit_points_item.set)
        maximum_hit_points_roll_item.ROLLED.connect(hit_points_item.set)
        maximum_hit_points_item.CHANGED.connect(lambda value: hit_points_item.hp_edit.set_maximum(value))
        name_item.CHANGED.connect(lambda _: self.set_modified(True))
        index_item.CHANGED.connect(lambda _: self.set_modified(True))
        index_item.CHANGED.connect(self.reload_tokens)
        token_item.CHANGED.connect(lambda _: self.set_modified(True))
        token_item.CHANGED.connect(partial(self.on_change_token, name_item))
        notes_item.CHANGED.connect(lambda: self.set_modified(True))
        type_item.CHANGED.connect(lambda _: self.set_modified(True))
        type_item.CHANGED.connect(lambda _: self.reload_gage())
        initiative_item.CHANGED.connect(lambda _: self.set_modified(True))
        initiative_roll_item.CHANGED.connect(lambda _: self.set_modified(True))
        hit_points_item.CHANGED.connect(lambda _: self.set_modified(True))
        maximum_hit_points_item.CHANGED.connect(lambda _: self.set_modified(True))
        maximum_hit_points_roll_item.CHANGED.connect(lambda _: self.set_modified(True))
        label_item.CHANGED.connect(lambda _: self.set_modified(True))
        power_item.CHANGED.connect(lambda _: self.set_modified(True))
        power_item.CHANGED.connect(lambda _: self.reload_gage())
        show_item.CHANGED.connect(lambda _: self.set_modified(True))

        def reload_name_font(hp: int):
            font = name_item.font()
            dead = not bool(hp > RULESET.HIT_POINTS_CRITICAL) and \
                maximum_hit_points_item.get() > RULESET.HIT_POINTS_CRITICAL
            font.setStrikeOut(dead)
            name_item.text_edit.setFont(font)
            background_color = 'gray' if dead else 'white'
            name_item.text_edit.setStyleSheet(f'QLineEdit{{background-color: {background_color};}};')
        hit_points_item.hp_edit.CHANGED.connect(reload_name_font)

        initiative_roll_item.set(initiative_roll)
        initiative_item.set(initiative_roll_item.roll() if initiative is None else initiative)
        maximum_hit_points_roll_item.set(maximum_hit_points_roll)
        maximum_hit_points_item.set(maximum_hit_points_roll_item.roll()
                                    if maximum_hit_points is None else maximum_hit_points)
        hit_points_item.hp_edit.set(maximum_hit_points_item.get() if hit_points is None else hit_points)

        self.table.resizeRowsToContents()
        if not row:
            self.table.resizeColumnsToContents()

        if token is None:
            if (path := PATHS['custom_tokens'].joinpath(name).with_suffix('.png')).exists():
                token_item.set(path.as_posix())

        SIGNALS.GUARD_DELETE.connect(self.on_guard_delete)
        self.reload_tokens()

    def add_new(self):
        parts = self.new_entry.text().split(':', 4)
        name = parts[0].strip()
        if not name:
            return
        match len(parts):
            case 1:
                type_ = 'effect'
                initiative_roll = 100
                maximum_hit_points_roll = ''
            case 2:
                type_ = 'player'
                initiative_roll = parts[1].strip()
                maximum_hit_points_roll = ''
            case _:
                type_ = 'enemy'
                initiative_roll = parts[1].strip()
                maximum_hit_points_roll = parts[2].strip()
        self.add_row(name=name, type=type_, initiative_roll=initiative_roll,
                     maximum_hit_points_roll=maximum_hit_points_roll)
        self.reload_gage()
        self.new_entry.setText('')

    def closeEvent(self, event: QtGui.QCloseEvent):
        self.close_window()
        event.ignore()

    def close_window(self, ask: bool = True):
        if ask and self.is_modified:
            message_box = QtWidgets.QMessageBox(self)
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setWindowIcon(Icon('question_mark'))
            message_box.setWindowTitle('Close Window')
            message_box.setText('There are unsaved changes.')
            save_button = QtWidgets.QPushButton(Icon('floppy_disk'), 'Save and Close', self)
            close_button = QtWidgets.QPushButton(Icon('door_exit'), 'Close without saving', self)
            cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
            message_box.addButton(save_button, QtWidgets.QMessageBox.AcceptRole)
            message_box.addButton(close_button, QtWidgets.QMessageBox.ActionRole)
            message_box.addButton(cancel_button, QtWidgets.QMessageBox.RejectRole)
            message_box.exec_()
            if message_box.clickedButton() == save_button:
                self.encounter.commit()
                self.deleteLater()
            elif message_box.clickedButton() == close_button:
                self.deleteLater()
            return
        self.deleteLater()

    def delete_banners(self):
        banner = self.keep.buildings['banner']
        df = banner.df
        df.drop(df[df['_encounter'] == self.encounter.db_index].index, inplace=True)
        banner.reset_columns()
        banner.save(False)

    def delete_combatants(self):
        combatant = self.keep.buildings['combatant']
        df = combatant.df
        df.drop(df[df['_encounter'] == self.encounter.db_index].index, inplace=True)
        combatant.reset_columns()
        combatant.save(False)

    def delete_encounter(self):
        if DeleteDialog('Encounter', self).get() == 'cancel':
            return
        self.encounter.delete()

    def delete_rows(self, *rows: int):
        deleted = 0
        for row in sorted(rows):
            self.table.removeRow(row - deleted)
            deleted += 1
        self.set_modified(True)
        self.reload_gage()

    def eventFilter(self, watched: QtWidgets.QWidget, event: QtCore.QEvent) -> bool:
        if watched == self.table:
            selection = self.table.selectedIndexes()
            if selection:
                if event.type() == QtCore.QEvent.KeyPress:
                    if event.key() == QtCore.Qt.Key_Delete:
                        self.on_delete(*set(sel.row() for sel in selection if sel))
                        return True
            if event.type() == QtCore.QEvent.ContextMenu:
                self.on_header_menu(event.pos())
                return True
        elif watched == self.table.viewport():
            if event.type() in (QtCore.QEvent.DragEnter, QtCore.QEvent.DragMove):
                self.on_drag(event)
                return True
            if event.type() == QtCore.QEvent.Drop:
                self.on_drop(event)
                return True
        return super().eventFilter(watched, event)

    def get_combatant_string(self) -> str:
        combatant_dict = defaultdict(int)
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, 4).get() == 'player':
                continue
            name = self.table.cellWidget(row, 0,).get()
            combatant_dict[name] += 1
        return ', '.join(f'{name} x{count}' for name, count in sorted(combatant_dict.items()))

    def get_data_frame(self) -> pd.DataFrame:
        return pd.DataFrame([self.get_dict(row) for row in range(self.table.rowCount())],
                            columns=[header for header, _ in self.HEADER])

    def get_db_index(self, row: int) -> int | None:
        try:
            return self.table.cellWidget(row, 14).get()
        except AttributeError:
            return None

    def get_dict(self, row: int) -> dict:
        return {key: widget.get() if (widget := self.table.cellWidget(row, column)) else None
                for column, (key, _) in enumerate(self.HEADER)}

    @property
    def is_modified(self) -> bool:
        return self._is_modified

    @is_modified.setter
    def is_modified(self, value: bool):
        self._is_modified = value
        self.reload_title()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def load_encounter(self):
        self.summary.clear()
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(15)
        self.table.setColumnHidden(13, False)
        self.table.setColumnHidden(14, True)
        self.table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        vertical_header = self.table.verticalHeader()
        vertical_header.setMinimumWidth(40)
        vertical_header.setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.table.setHorizontalHeaderLabels(list(header[1] for header in self.HEADER))
        combatant = self.keep.buildings['combatant'].df
        try:
            data = combatant[combatant['_encounter'] == self.encounter.db_index].copy()

            def add_series(series: pd.Series):
                self.add_row(**{key: series.get(key) for key, _ in self.HEADER})
            if not data.empty:
                data.apply(add_series, axis=1)
            self.image.set_encounter_data(data)
        except ValueError:
            pass

        self.reload_gage()
        self.name_entry.setText(self.encounter['name'])
        self.summary.insertPlainText(self.encounter['text'])
        self.tag_frame.set_tags(self.encounter.get_tags())

        self.set_modified(False)

    def on_battle_view_changed(self, state: bool):
        columns = (6, 9, 11)
        for column in columns:
            self.table.setColumnHidden(column, state)
        self.header.setVisible(not state)

    def on_change_token(self, name_item: TextEdit, value: str):
        self.token_dict[name_item.get()] = value
        self.reload_tokens()

    def on_copy(self, *rows):
        if not rows:
            rows = set(sel.row() for sel in self.table.selectedIndexes())
        for row in rows:
            series = self.get_dict(row)
            d = {key: val for key, val in series.items()}
            d['index'] = None
            self.add_row(**d)
        self.reload_gage()
        self.reload_tokens()

    def on_damage(self, *rows):
        if not rows:
            rows = set(sel.row() for sel in self.table.selectedIndexes())
        if not rows:
            return

        def submit():
            if not damage_edit.number_edit.hasAcceptableInput():
                return
            for row in rows:
                self.table.cellWidget(row, 7).deal_damage(damage_edit.get())
            message_box.deleteLater()
        message_box = QtWidgets.QDialog(self)
        message_box.setWindowFlags(message_box.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        message_box.setWindowIcon(Icon('axe'))
        message_box.setWindowTitle('Deal Damage')
        button_box = QtWidgets.QDialogButtonBox(self)
        accept_button = QtWidgets.QPushButton(Icon('axe'), 'Deal Damage', self)
        accept_button.clicked.connect(submit)
        cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
        cancel_button.clicked.connect(self.deleteLater)
        button_box.addButton(accept_button, button_box.AcceptRole)
        button_box.addButton(cancel_button, button_box.RejectRole)
        label = QtWidgets.QLabel(message_box)
        label.setText('Deal Damage to:\n' + '\n'.join(f'• {self.table.cellWidget(row, 0).get()} '
                                                      f'{int(self.table.cellWidget(row, 1).get())}'
                                                      for row in rows))
        damage_edit = NumberEditContainer(parent=message_box)
        damage_edit.number_edit.textChanged.connect(
            lambda _: accept_button.setEnabled(damage_edit.number_edit.hasAcceptableInput()))
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(damage_edit)
        layout.addWidget(button_box)
        message_box.setLayout(layout)

        damage_edit.number_edit.setPlaceholderText('Enter Damage')
        message_box.exec_()

    def on_delete(self, *rows):
        if not rows:
            rows = set(sel.row() for sel in self.table.selectedIndexes())
        if not rows:
            return
        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowIcon(Icon('garbage_can'))
        message_box.setIcon(message_box.Question)
        message_box.setWindowTitle(f'Remove {len(rows)} Combatants')
        message_box.setText(f'Remove the following Combatant(s)?\n' +
                            '\n'.join(f'• {self.table.cellWidget(row, 0).get()} '
                                      f'{int(self.table.cellWidget(row, 1).get())}'
                                      for row in rows))
        yes_button = QtWidgets.QPushButton(Icon('garbage_can'), 'Remove', self)
        yes_button.clicked.connect(lambda: self.delete_rows(*rows))
        cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
        message_box.addButton(yes_button, message_box.AcceptRole)
        message_box.addButton(cancel_button, message_box.RejectRole)
        message_box.exec()

    @staticmethod
    def on_drag(event: QtGui.QDragEnterEvent | QtGui.QDragMoveEvent):
        mime_data = event.mimeData()
        if mime_data.hasFormat('lorekeeper/guard'):
            event.accept()

    def on_drop(self, event: QtGui.QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasFormat('lorekeeper/guard'):
            event.accept()
            guard = RULESET.GUARD_TYPE.read_keep(self.keep, mime_data.data('lorekeeper/guard').data())
            self.add_combatant(guard.to_combatant())
            self.reload_gage()

    def on_encounter_activate(self, db_index: int):
        if db_index == self.encounter.db_index:
            return
        self.presenter_action.setChecked(False)

    def on_encounter_delete(self, db_index: int):
        if db_index != self.encounter.db_index:
            return
        self.deleteLater()

    def on_entry_validation(self, validated: bool):
        if validated:
            color = 'white'
        else:
            color = 'red'
        self.new_entry.setStyleSheet(f'QLineEdit{{background-color: {color};}};')

    def on_guard_delete(self, db_index: int):
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 14)
            if widget.get() == db_index:
                widget.set(0)
        self.on_selection_change()

    def on_header_menu(self, point: QtCore.QPoint):
        menu = QtWidgets.QMenu(self)
        for index in range(1, self.table.columnCount()):
            action = QtWidgets.QAction(self.table.horizontalHeaderItem(index).text(), self)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(index))
            action.toggled.connect(partial(lambda i, state: self.table.setColumnHidden(i, not state), index))
            menu.addAction(action)
        menu.popup(self.table.mapToGlobal(point))

    def on_inspect_guard(self, db_index: int = None):
        if not db_index and (selection := set(sel.row() for sel in self.table.selectedIndexes())):
            db_index = self.table.cellWidget(selection.pop(), 14).get()
        if not db_index:
            return
        SIGNALS.GUARD_INSPECT.emit(db_index)

    def on_mouse_move(self, event: QtGui.QMouseEvent):
        db_index = self.get_db_index(self.table.rowAt(event.y()))
        if not db_index:
            if self.feature_preview:
                self.feature_preview.deleteLater()
            return
        if self.feature_preview:
            if self.feature_preview.db_index == db_index:
                self.feature_preview.move(event.globalPos() + QtCore.QPoint(10, 10))
                return
            self.feature_preview.deleteLater()
        self.feature_preview = Preview(RULESET.GUARD_TYPE.read_keep(self.keep, db_index))
        self.feature_preview.show()
        self.feature_preview.move(event.globalPos() + QtCore.QPoint(10, 10))

    def on_popup_guard(self, db_index: int = None):
        if not db_index and (selection := set(sel.row() for sel in self.table.selectedIndexes())):
            db_index = self.table.cellWidget(selection.pop(), 14).get()
        if not db_index:
            return
        treasure_db_index = self.keep.buildings['guard'].df.at[db_index, '_treasure']
        if not treasure_db_index:
            return
        SIGNALS.IMAGE_POPUP.emit(treasure_db_index)

    def on_presenter(self, state: bool):
        if state:
            SIGNALS.ENCOUNTER_ACTIVATE.emit(self.encounter.db_index)
            self.auto_upload_action.setEnabled(True)
        else:
            self.auto_upload_action.setChecked(False)
            self.auto_upload_action.setEnabled(False)

    def on_reorder(self):
        self.sort()
        items = self.table.selectedIndexes()
        if not items:
            return
        current_row = items[0].row()
        menu = QtWidgets.QMenu(self)
        before_menu = QtWidgets.QMenu('Move Before', self)
        before_menu.setIcon(Icon('sort_up'))
        after_menu = QtWidgets.QMenu('Move After', self)
        after_menu.setIcon(Icon('sort_down'))

        def adjust_ini(revert: bool = False):
            for row in range(self.table.rowCount()):
                widget = self.table.cellWidget(row, 5)
                if revert:
                    widget.number_edit.set_decimals(3)
                    continue
                widget.number_edit.set_decimals(8)
                new_value = widget.get() + 2 * (2 * RULESET.INITIATIVE_ASCENDING - 1) * row * 0.0000001
                widget.set(new_value)

        def set_row(new_row: int, before: bool):
            adjust_ini(False)
            ini = self.table.cellWidget(new_row, 5).get()
            delta = 0.0000001 * (2 * (before ^ RULESET.INITIATIVE_ASCENDING) - 1)
            self.table.cellWidget(current_row, 5).set(ini + delta)
            self.sort()
            adjust_ini(True)

        for row in range(self.table.rowCount()):
            if row == current_row:
                continue
            display_name = self.table.cellWidget(row, 0).get() + ' ' + str(self.table.cellWidget(row, 1).get())
            before_action = QtWidgets.QAction(display_name, self)
            before_action.triggered.connect(partial(set_row, row, True))
            before_menu.addAction(before_action)
            after_action = QtWidgets.QAction(display_name, self)
            after_action.triggered.connect(partial(set_row, row, False))
            after_menu.addAction(after_action)
        menu.addMenu(before_menu)
        menu.addMenu(after_menu)
        menu.popup(self.table.mapToGlobal(QtCore.QPoint(0, 0)))


    def on_reroll(self, *rows: int):
        if not rows:
            rows = set(sel.row() for sel in self.table.selectedIndexes())
        for row in rows:
            self.table.cellWidget(row, 6).roll()
            self.table.cellWidget(row, 9).roll()

    def on_selection_change(self, _=None):
        selection = self.table.selectedIndexes()
        enabled = bool(selection)
        db_indices = set(self.table.cellWidget(sel.row(), 14).get() for sel in selection)
        inspect = len(db_indices) == 1 and db_indices.pop()
        try:
            popup = inspect and self.keep.buildings['guard'].df.at[inspect, '_treasure']
        except KeyError:
            popup = False
        self.delete_action.setEnabled(enabled)
        self.copy_action.setEnabled(enabled)
        self.damage_action.setEnabled(enabled)
        self.roll_action.setEnabled(enabled)
        self.reorder_action.setEnabled(inspect)
        self.inspect_action.setEnabled(inspect)
        self.stats_action.setEnabled(inspect)
        self.popup_action.setEnabled(popup)

    def on_stats_guard(self, db_index: int = None):
        if not db_index and (selection := set(sel.row() for sel in self.table.selectedIndexes())):
            db_index = self.table.cellWidget(selection.pop(), 14).get()
        if not db_index:
            return
        SIGNALS.GUARD_POPUP.emit(db_index)

    def reload_gage(self):
        data = self.get_data_frame()
        self.image.set_encounter_data(data)

    def reload_title(self):
        title = f'{self.name_entry.text()} - Encounter'
        if self.is_modified:
            title += ' (modified)'
        self.setWindowTitle(title)

    def reload_tokens(self):
        for row in range(self.table.rowCount()):
            token_widget = self.table.cellWidget(row, 2)
            name = self.table.cellWidget(row, 0).get()
            token_path = Path(self.token_dict[name])
            if not token_path.exists():
                continue
            if PATHS['tokens'] in token_path.parents:
                index = self.table.cellWidget(row, 1).get()
                token_name = token_path.stem
                token_path = token_path.parent.joinpath(token_name, f'{token_name}_{index}.png')
            token_widget.blockSignals(True)
            if token_path.exists():
                token_widget.set(token_path.as_posix())
            else:
                token_widget.set('')
            token_widget.blockSignals(False)
        self.set_modified(True)

    def save(self):
        self.save_banners()
        self.save_combatants()
        self.encounter['name'] = self.name_entry.text()
        self.encounter['text'] = self.summary.toPlainText()
        self.encounter['combatants'] = self.get_combatant_string()
        self.encounter.commit()
        self.set_modified(False)

    def save_banners(self):
        self.delete_banners()
        keep = self.keep
        db_index = self.encounter.db_index
        for tag_name in self.tag_frame.tags:
            Banner(keep, data={'_encounter': db_index, 'name': tag_name}).commit()
        keep.buildings['banner'].save(False)

    def save_combatants(self):
        self.delete_combatants()
        keep = self.keep
        db_index = self.encounter.db_index
        for row in range(self.table.rowCount()):
            data = self.get_dict(row)
            data['_encounter'] = db_index
            Combatant(keep, data=data).commit()
        keep.buildings['combatant'].save(False)

    def set_modified(self, value: bool = True):
        self.is_modified = value
        if value and self.auto_upload_action.isChecked():
            SIGNALS.REFRESH.emit()

    def sort(self):
        order = QtGui.Qt.AscendingOrder if RULESET.INITIATIVE_ASCENDING else QtGui.Qt.DescendingOrder
        self.table.sortItems(13, order)
