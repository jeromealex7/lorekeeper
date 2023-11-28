import os
import shutil
import subprocess

import pandas as pd
from PySide2 import QtGui, QtWidgets

from .import_tools import Importer
from src.model import Treasure
from src.settings import APPLICATIONS, PATHS, SIGNALS
from src.widgets import Icon


class TreasureMenu(QtWidgets.QMenu):

    def __init__(self, treasure: Treasure, parent: QtWidgets.QWidget | None = None, inspect: bool = True,
                 find: bool = True, popup: bool = True):
        super().__init__(parent=parent)
        self.treasure = treasure
        self.setIcon(Icon(self.treasure.icon_name))
        self.setTitle(self.treasure['name'])

        self.add_type_actions()
        self.addSeparator()
        if popup:
            popup_action = QtWidgets.QAction(Icon('window'), 'Popup', self)
            popup_action.triggered.connect(lambda: SIGNALS.IMAGE_POPUP.emit(self.treasure.db_index))
            self.addAction(popup_action)
        if inspect:
            inspect_action = QtWidgets.QAction(Icon('chest_open'), 'Inspect Treasure', self)
            inspect_action.triggered.connect(lambda: SIGNALS.TREASURE_INSPECT.emit(self.treasure.db_index))
            self.addAction(inspect_action)
        if find:
            find_usage_action = QtWidgets.QAction(Icon('hand_offer'), 'Find Usages', self)
            find_usage_action.triggered.connect(self.find_usage)
            self.addAction(find_usage_action)

    def add_type_actions(self):
        match self.treasure['type']:
            case 'image':
                self.add_image_actions()
            case 'music':
                self.add_music_actions()
            case 'url' | 'youtube':
                self.add_url_actions()
            case _:
                self.add_file_actions()

    def add_image_actions(self):
        show_single = QtWidgets.QAction(Icon('flatscreen_tv'), 'Show in Presenter', self)
        show_additional = QtWidgets.QAction(Icon('plus'), 'Add to Presenter', self)
        show_background = QtWidgets.QAction(Icon('back'), 'Show as Background', self)
        show_single.triggered.connect(lambda: SIGNALS.PRESENTER_SET.emit(self.treasure.db_index))
        show_additional.triggered.connect(lambda: SIGNALS.PRESENTER_ADD.emit(self.treasure.db_index))
        show_background.triggered.connect(lambda: SIGNALS.PRESENTER_BACKGROUND.emit(self.treasure.db_index))
        self.addActions([show_single, show_additional, show_background])

    def add_music_actions(self):
        instant_play = QtWidgets.QAction(Icon('media_play'), 'Play', self)
        instant_play.triggered.connect(lambda: SIGNALS.MUSIC_DIRECT.emit(self.treasure.db_index))
        df = self.treasure.keep.buildings['minstrel'].df

        playlist_menu = QtWidgets.QMenu(self)

        def _add_playlist(series: pd.Series):
            action = QtWidgets.QAction(Icon('music'), series['name'], self)
            action.triggered.connect(lambda event: SIGNALS.MUSIC_ADD.emit(int(series.name), self.treasure.db_index))  # noqa
            playlist_menu.addAction(action)
        playlist_menu.setIcon(Icon('plus'))
        playlist_menu.setTitle('Add to Minstrel')
        df[df['state'] > 0].apply(_add_playlist, axis=1)
        playlist_menu.setEnabled(bool(playlist_menu.columnCount()))
        self.addActions([instant_play])
        self.addMenu(playlist_menu)

    def add_url_actions(self):
        open_url = QtWidgets.QAction(Icon(self.treasure.icon_name), 'Open URL', self)
        open_url.triggered.connect(lambda: os.startfile(self.treasure['info']))
        clipboard = QtWidgets.QAction(Icon('clipboard'), 'Copy to Clipboard', self)
        clipboard.triggered.connect(lambda: QtGui.QClipboard().setText(self.treasure['info']))
        self.addActions([open_url, clipboard])
        if self.treasure['type'] == 'youtube':
            download = QtWidgets.QAction(Icon('download'), 'Download', self)
            download.triggered.connect(lambda: Importer(self.treasure, parent=self).exec_())
            self.addAction(download)

    def add_file_actions(self):
        start_action = QtWidgets.QAction(Icon(self.treasure.icon_name), 'Start File', self)
        copy_start_action = QtWidgets.QAction(Icon('copy'), 'Start Copy', self)
        start_action.triggered.connect(lambda: self.start_file(False))
        copy_start_action.triggered.connect(lambda: self.start_file(True))
        self.addActions([start_action, copy_start_action])

    def find_usage(self):
        text = self.treasure.find_usage() or 'The Treasure is not used anywhere in this Keep.'
        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowIcon(Icon('chest_open'))
        message_box.setWindowTitle('Find Usages')
        message_box.setIcon(message_box.Information)
        message_box.setText(text)
        ok_button = QtWidgets.QPushButton(Icon('ok'), 'Ok', self)
        message_box.addButton(ok_button, message_box.AcceptRole)
        message_box.exec_()

    def start_file(self, copy: bool):
        if copy:
            target_file = PATHS['workbench'].joinpath(
                ''.join(char for char in self.treasure['name']
                        if char.isalnum() or char in ' ()-_[].')).with_suffix(self.treasure['suffix'])
            shutil.copyfile(self.treasure.path, target_file)
        else:
            target_file = self.treasure.path
        if application := APPLICATIONS.get(self.treasure['suffix'].removeprefix('.')):
            subprocess.Popen([application, target_file.__str__()], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True)
        else:
            os.startfile(target_file)
