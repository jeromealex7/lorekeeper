from functools import partial
import re
from typing import Literal

from PySide2 import QtCore, QtGui, QtWidgets

from .atelier import Atelier
from .notes import Notes
from src.encounter import Enlistment
from src.garrison import Garrison
from src.library import Library
from src.model import Keep, Treasure
from src.music import MusicHall
from src.presenter import Presenter
from src.rulesets import load_ruleset
from src.settings import PATHS, SESSION, SHORTCUTS, SIGNALS
from src.timer import TimerMenu
from src.treasury import ImageContainer, Treasury
from src.quartermaster import Quartermaster
from src.widgets import BuildingWindow, Icon, Loading, PlayerVariableSetter


class Citadel(QtWidgets.QMainWindow):

    def __init__(self, keep: Keep):
        super().__init__()
        self.setStyleSheet('*{font-family: Roboto Slab;font-size: 10pt;};')

        self._is_modified = False
        self.keep = keep

        load_ruleset(self.keep.ruleset, self.keep)
        self.keep.save(modified_only=False)
        self.setWindowTitle('Citadel - Lorekeeper')
        self.setWindowIcon(Icon('fortress_tower'))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint)
        self.setMinimumWidth(300)

        self.frame = QtWidgets.QFrame()
        self.setCentralWidget(self.frame)

        self.name_edit = QtWidgets.QLineEdit()
        self.player_setter = PlayerVariableSetter(self.keep, self)
        self.notes = Notes(self.keep, self)
        self.image_container = ImageContainer(self.keep, self)

        self.resolution = QtWidgets.QComboBox(self)
        for res in ('1920x1080 (recommended)', '1680x1050', '1600x900'):
            self.resolution.addItem(res)
        self.resolution.currentTextChanged.connect(
            lambda r: self.canvas.setFixedSize(*list(map(int, re.split(r'x\s', r, 2)))[:2]))
        header = QtWidgets.QGridLayout()
        header.addWidget(QtWidgets.QLabel('Name:'), 0, 0)
        header.addWidget(self.name_edit, 0, 1)
        header.addWidget(QtWidgets.QLabel('Players:'), 1, 0)
        header.addWidget(self.player_setter, 1, 1)
        header.addWidget(QtWidgets.QLabel('Export:'), 2, 0)
        header.addWidget(self.resolution, 2, 1)
        layout = QtWidgets.QHBoxLayout()
        summary_layout = QtWidgets.QVBoxLayout()
        summary_layout.addLayout(header, stretch=0)
        summary_layout.addWidget(self.image_container, stretch=1)
        layout.addLayout(summary_layout, stretch=0)
        layout.addWidget(self.notes, stretch=1)
        self.frame.setLayout(layout)

        self.canvas = Presenter(keep, canvas=True, parent=self)
        self.canvas.setFixedSize(1920, 1080)

        self.enlistment = Enlistment(keep)
        self.garrison = Garrison(keep)
        self.quartermaster = Quartermaster(keep)
        self.library = Library(keep)
        self.music_hall = MusicHall(keep)
        self.presenter = Presenter(keep)
        self.atelier = Atelier(keep)
        self.timer_menu = TimerMenu()
        self.treasury = Treasury(keep)

        self.reload_keep()
        menu = self.menuBar()
        file_menu = menu.addMenu('&Keep')
        save_action = QtWidgets.QAction(Icon('floppy_disk'), 'Save', self)
        save_action.setShortcut(QtGui.QKeySequence('Ctrl+S'))
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        close_action = QtWidgets.QAction(Icon('door_exit'), 'Close', self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        view_menu = menu.addMenu('&View')
        close_temporary = QtWidgets.QAction(Icon('window_close'), 'Close all Windows', self)
        close_temporary.setShortcut(QtGui.QKeySequence('Ctrl+Shift+W'))
        close_temporary.triggered.connect(self.on_close_temporary)
        view_menu.addAction(close_temporary)
        toggle_atelier = QtWidgets.QAction(Icon('photo_portrait'), 'Show Atelier', self)
        toggle_atelier.setShortcut(QtGui.QKeySequence('Ctrl+A'))
        toggle_atelier.triggered.connect(lambda: self.atelier.set_visibility('toggle'))
        toggle_encounter = QtWidgets.QAction(Icon('gauntlet'), 'Show Enlistment', self)
        toggle_encounter.setShortcut(QtGui.QKeySequence('Ctrl+E'))
        toggle_encounter.triggered.connect(lambda: self.enlistment.set_visibility('toggle'))
        toggle_garrison = QtWidgets.QAction(Icon('helmet'), 'Show Garrison', self)
        toggle_garrison.setShortcut(QtGui.QKeySequence('Ctrl+G'))
        toggle_garrison.triggered.connect(lambda: self.garrison.set_visibility('toggle'))
        toggle_library = QtWidgets.QAction(Icon('book_open'), 'Show Library', self)
        toggle_library.setShortcut(QtGui.QKeySequence('Ctrl+L'))
        toggle_library.triggered.connect(lambda: self.library.set_visibility('toggle'))
        toggle_citadel = QtWidgets.QAction(Icon('fortress_tower'), 'Show Keep', self)
        toggle_citadel.setShortcut(QtGui.QKeySequence('Ctrl+K'))
        toggle_citadel.triggered.connect(lambda: self.set_visibility(True))
        toggle_music = QtWidgets.QAction(Icon('clef'), 'Show Music Hall', self)
        toggle_music.setShortcut(QtGui.QKeySequence('Ctrl+M'))
        toggle_music.triggered.connect(lambda: self.music_hall.set_visibility('toggle'))
        toggle_presenter = QtWidgets.QAction(Icon('flatscreen_tv'), 'Show Presenter', self)
        toggle_presenter.setShortcut(QtGui.QKeySequence('Ctrl+P'))
        toggle_presenter.triggered.connect(lambda: self.presenter.set_visibility('toggle'))
        toggle_quarter = QtWidgets.QAction(Icon('warehouse'), 'Show Quartermaster', self)
        toggle_quarter.setShortcut(QtGui.QKeySequence('Ctrl+Q'))
        toggle_quarter.triggered.connect(lambda: self.quartermaster.set_visibility('toggle'))
        toggle_rider = QtWidgets.QAction(Icon('horse'), 'Show Rider', self)
        toggle_rider.setShortcut(QtGui.QKeySequence('Ctrl+R'))
        toggle_rider.triggered.connect(lambda: self.timer_menu.set_visibility('toggle'))
        toggle_treasury = QtWidgets.QAction(Icon('chest'), 'Show Treasury', self)
        toggle_treasury.setShortcut(QtGui.QKeySequence('Ctrl+T'))
        toggle_treasury.triggered.connect(lambda: self.treasury.set_visibility('toggle'))
        refresh_action = QtWidgets.QAction(Icon('cloud_upload'), 'Upload Presenter', self)
        refresh_action.setShortcut(QtGui.QKeySequence('F5'))
        refresh_action.triggered.connect(lambda: SIGNALS.REFRESH.emit())
        view_menu.addActions([toggle_atelier, toggle_encounter, toggle_garrison, toggle_library, toggle_citadel,
                              toggle_music, toggle_presenter, toggle_quarter, toggle_rider, toggle_treasury])
        view_menu.addSeparator()
        view_menu.addAction(refresh_action)
        self.resize(900, 400)

        SHORTCUTS.create_shortcut('Ctrl+Shift+W', lambda _: self.on_close_temporary())
        SHORTCUTS.create_shortcut('Ctrl+A', lambda _: self.atelier.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+E', lambda _: self.enlistment.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+G', lambda _: self.garrison.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+L', lambda _: self.library.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+M', lambda _: self.music_hall.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+P', lambda _: self.presenter.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+Q', lambda _: self.quartermaster.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+R', lambda _: self.timer_menu.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+T', lambda _: self.treasury.set_visibility(True))
        SHORTCUTS.create_shortcut('Ctrl+K', lambda _: self.set_visibility(True))
        SHORTCUTS.create_shortcut('F5', lambda _: SIGNALS.REFRESH.emit())
        SHORTCUTS.create_shortcut('Ctrl+Shift+E', partial(self.on_arrange, self.enlistment))
        SHORTCUTS.create_shortcut('Ctrl+Shift+G', partial(self.on_arrange, self.garrison))
        SHORTCUTS.create_shortcut('Ctrl+Shift+L', partial(self.on_arrange, self.library))
        SHORTCUTS.create_shortcut('Ctrl+Shift+M', partial(self.on_arrange, self.music_hall))
        SHORTCUTS.create_shortcut('Ctrl+Shift+P', partial(self.on_arrange, self.presenter))
        SHORTCUTS.create_shortcut('Ctrl+Shift+Q', partial(self.on_arrange, self.quartermaster))
        SHORTCUTS.create_shortcut('Ctrl+Shift+T', partial(self.on_arrange, self.treasury))
        SHORTCUTS.activate_shortcuts(self.atelier)
        SHORTCUTS.activate_shortcuts(self.enlistment)
        SHORTCUTS.activate_shortcuts(self.garrison)
        SHORTCUTS.activate_shortcuts(self.library)
        SHORTCUTS.activate_shortcuts(self.music_hall)
        SHORTCUTS.activate_shortcuts(self.presenter)
        SHORTCUTS.activate_shortcuts(self.quartermaster)
        SHORTCUTS.activate_shortcuts(self.timer_menu)
        SHORTCUTS.activate_shortcuts(self.treasury)
        SIGNALS.FEATURE_COMMIT.connect(self.on_feature)
        SIGNALS.FEATURE_DELETE.connect(self.on_feature)
        SIGNALS.ENCOUNTER_VARIABLES.connect(self.on_feature)
        SIGNALS.TREASURE_DELETE.connect(self.on_treasure_delete)
        SIGNALS.CITADEL_SHOW.connect(self.activate)
        self.name_edit.textChanged.connect(lambda: self.on_feature())
        self.image_container.TREASURE_CHANGED.connect(lambda: self.on_feature())
        self.notes.CHANGED.connect(lambda: self.on_feature())

    def activate(self):
        if self.windowState() == QtCore.Qt.WindowActive:
            self.setWindowState(QtCore.Qt.WindowMinimized)
            return
        self.activateWindow()
        self.setFocus()
        self.raise_()
        self.show()

    def closeEvent(self, event: QtGui.QCloseEvent):
        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle('Close Lorekeeper')
        message_box.setWindowIcon(Icon('fortress_tower'))
        text = 'Close the application?'
        icon = message_box.Question
        if self.is_modified:
            text += ' There are unsaved changes.'
            icon = message_box.Warning
        if SESSION['processes']:
            text += '\n\nClosing the application will terminate all unfinished processes:\n' +\
                    '\n'.join(f'- {p.name}' for p in SESSION['processes'])
            icon = message_box.Warning
        message_box.setIcon(icon)
        message_box.setText(text)
        close_button = QtWidgets.QPushButton(Icon('door_exit'), 'Close', self)
        cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
        message_box.addButton(close_button, message_box.AcceptRole)
        message_box.addButton(cancel_button, message_box.RejectRole)
        message_box.exec_()
        if message_box.clickedButton() == cancel_button:
            event.ignore()
            return
        self.keep.save()
        for window in QtWidgets.QApplication.topLevelWidgets():
            window.deleteLater()

    @property
    def is_modified(self):
        return self._is_modified or any(building.is_modified for building in self.keep.buildings.values())

    @is_modified.setter
    def is_modified(self, value):
        self._is_modified = value
        self.reload_title()

    @classmethod
    def new(cls, ruleset: str):
        keep = Keep.new(ruleset)
        citadel = cls(keep)
        match ruleset:
            case 'dnd':
                from src.rulesets.dnd5e import scrape
                process = Loading('Import Monster Manual', 'Please wait while the Monster Manual 5e is being imported.')
                process.get(lambda: scrape.import_monsters(keep))
            case 'adnd':
                from src.rulesets.adnd import scrape
                process = Loading('Import Monstrous Compendium',
                                  'Please wait while the Monstrous Compendium is being imported.')
                process.get(lambda: scrape.import_monsters(keep))
            case 'pathfinder':
                from src.rulesets.pathfinder import scrape
                process = Loading('Import Beastiary',
                                  'Please wait while the Beastiary is being imported.')
                process.get(lambda: scrape.import_monsters(keep))

        citadel.save(modified_only=False)
        return citadel

    @staticmethod
    def on_arrange(building: BuildingWindow, other: QtWidgets.QMainWindow):
        if building == other:
            return
        app = QtWidgets.QApplication
        width, height = app.primaryScreen().size().toTuple()
        building.set_visibility(True)
        building.resize(width // 2, height)
        other.resize(width // 2, height)
        other.move(0, 0)
        building.move(width // 2 + 1, 0)

    def on_close_temporary(self, force: bool = False):
        for window in QtWidgets.QApplication.topLevelWidgets():
            if window == self:
                self.set_visibility(True)
                continue
            if force and not isinstance(window, BuildingWindow):
                window.deleteLater()
            else:
                window.close()

    def on_feature(self, _: str = None, __: int = None):
        self.is_modified = True

    def on_treasure_delete(self, db_index: int):
        if not (treasure := self.image_container.treasure) or db_index != treasure.db_index:
            return
        self.image_container.set_content(None)
        self.keep.treasure_index = 0
        self.keep.save_config()

    @classmethod
    def read_signal(cls, config_file_name: str):
        keep = Keep.read_config(PATHS['keeps'].joinpath(config_file_name))
        return cls(keep)

    def reload_keep(self):
        self.name_edit.setText(self.keep.name)
        self.notes.set(self.keep.notes)
        treasure = Treasure.read_keep(self.keep, db_index) if (db_index := self.keep.treasure_index) else None
        self.image_container.set_content(treasure)

    def reload_title(self):
        title = 'Citadel - Lorekeeper'
        if self.is_modified:
            title += ' (modified)'
        self.setWindowTitle(title)

    def save(self, modified_only: bool = True):
        self.keep.name = self.name_edit.text()
        self.keep.treasure_index = treasure.commit() if (treasure := self.image_container.treasure) else 0
        self.keep.notes = self.notes.get()
        self.keep.save(modified_only=modified_only)
        self.is_modified = False

    def set_visibility(self, state: bool | Literal['toggle'] = True):
        state = self.isHidden() if state == 'toggle' else state
        if state:
            self.activateWindow()
            self.showNormal()
            self.setFocus()
        else:
            self.hide()
