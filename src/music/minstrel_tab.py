import random

from PySide2 import QtCore, QtGui, QtMultimedia, QtWidgets

from src.model import Genre, Keep, Minstrel, Repertoire, Treasure
from src.settings import SIGNALS
from src.treasury import ClipboardAction, Importer, OpenTreasureDialog
from src.widgets import Icon, RenameAction, Preview, TagFrame


class MinstrelTab(QtWidgets.QWidget):

    def __init__(self, keep: Keep, db_index: int, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.keep = keep
        self.db_index = db_index
        self.df = self.keep.buildings['treasure'].df
        self.minstrel = Minstrel.read_keep(keep, db_index)
        self.feature_preview = None
        self._playlist = QtMultimedia.QMediaPlaylist(self)
        self._playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.Loop)
        self._player = QtMultimedia.QMediaPlayer(self)
        self._player.setPlaylist(self._playlist)
        self._duration_player = QtMultimedia.QMediaPlayer(self)
        self._container = QtWidgets.QListWidget()
        self.drop_object = None
        self.tag_frame = TagFrame(self._container.width(), self.keep.buildings['genre'], 'Genre', self)

        layout = QtWidgets.QVBoxLayout()
        buttons = QtWidgets.QHBoxLayout()
        self.play_pause = QtWidgets.QPushButton(Icon('media_play'), 'Play', self)
        self.play_pause.clicked.connect(self.on_play_pause)
        self.play_pause.setEnabled(False)
        self.stop_button = QtWidgets.QPushButton(Icon('media_stop'), 'Stop', self)
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setEnabled(False)
        self.shuffle_button = QtWidgets.QPushButton(Icon('arrow_shuffle'), 'Shuffle', self)
        self.shuffle_button.clicked.connect(self.shuffle)
        self.shuffle_button.setEnabled(False)
        buttons.addWidget(self.play_pause)
        buttons.addWidget(self.stop_button)
        buttons.addWidget(self.shuffle_button)
        layout.addLayout(buttons)
        layout.addWidget(self._container)
        layout.addWidget(self.tag_frame)
        self.setLayout(layout)
        self.setAcceptDrops(True)
        self._container.installEventFilter(self)
        self._container.setAcceptDrops(True)
        self._container.viewport().installEventFilter(self)
        self._container.viewport().setAcceptDrops(True)
        self._container.viewport().setMouseTracking(True)
        self._container.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self._container.setSelectionMode(self._container.SingleSelection)
        self._container.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self._container.model().rowsMoved.connect(
            lambda _, old_index, __, ___, new_index: self.on_move_item(old_index, new_index))

        SIGNALS.MUSIC_CONTINUE.connect(self.on_play_signal)
        SIGNALS.MUSIC_ADD.connect(self.on_add_treasure)
        SIGNALS.TREASURE_COMMIT.connect(self.reload_treasure)
        SIGNALS.TREASURE_DELETE.connect(self.on_treasure_delete)
        SIGNALS.MINSTREL_COMMIT.connect(self.on_minstrel_commit)
        self._playlist.mediaInserted.connect(lambda _, __: self.on_list_changed())
        self._playlist.mediaRemoved.connect(lambda _, __: self.on_list_changed())
        self._playlist.currentIndexChanged.connect(
            lambda index: SIGNALS.MUSIC_NOW_PLAYING.emit(self.get_db_index(index)))
        self.tag_frame.TAGS_CHANGED.connect(self.on_tags_changed)
        self.load_genres()
        self.load_repertoire()

    def add_treasure(self, treasure: int | Treasure, commit: bool = True):
        if isinstance(treasure, (int, float)):
            db_index = int(treasure)
            treasure = Treasure.read_keep(self.keep, db_index=treasure)
        else:
            db_index = treasure.db_index
        if any(self._container.item(row).data(QtCore.Qt.UserRole) == db_index
               for row in range(self._container.count())):
            return
        item = QtWidgets.QListWidgetItem(Icon('music'), treasure['name'], self._container)
        item.setData(QtCore.Qt.UserRole, treasure.db_index)
        medium = QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(treasure.path.as_posix().__str__()))
        self._playlist.addMedia(medium)
        if commit:
            self.save_repertoire()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)
        if clipboard_action := ClipboardAction(self.keep, 'music', False, self):
            menu.addAction(clipboard_action)
            clipboard_action.triggered.connect(lambda: self.add_treasure(clipboard_action.treasure))
        open_action = QtWidgets.QAction(Icon('folder_open'), 'Open File ...', self)
        if selected := self._container.selectedIndexes():
            row = selected[0].row()
            db_index = self.get_db_index(row)
            inspect_action = QtWidgets.QAction(Icon('chest_open'), 'Inspect Treasure', self)
            inspect_action.triggered.connect(lambda: SIGNALS.TREASURE_INSPECT.emit(db_index))
            remove_action = QtWidgets.QAction(Icon('garbage'), 'Remove Treasure', self)
            remove_action.triggered.connect(lambda: self.remove_row(row))
            menu.addAction(inspect_action)
            menu.addAction(remove_action)

        def open_dialog():
            dialog = OpenTreasureDialog(self.keep, 'music', self)
            treasure = dialog.get()
            if not treasure:
                return
            importer = Importer(treasure, True, self)
            if importer.exec_():
                self.add_treasure(treasure)
        open_action.triggered.connect(open_dialog)
        menu.addAction(open_action)
        menu.popup(event.globalPos())

    def delete_genres(self):
        genre = self.keep.buildings['genre']
        df = genre.df
        df.drop(df[df['_minstrel'] == self.db_index].index, inplace=True)
        genre.reset_columns()
        genre.save(False)

    def delete_repertoire(self):
        repertoire = self.keep.buildings['repertoire']
        df = repertoire.df
        df.drop(df[df['_minstrel'] == self.db_index].index, inplace=True)
        repertoire.reset_columns()
        repertoire.save(False)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        drop_object = Treasure.read_mime_data(self.keep, event.mimeData())
        if drop_object and drop_object['type'] == 'music':
            event.acceptProposedAction()
            self.drop_object = drop_object
        else:
            self.drop_object = None
        return super().dragEnterEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent):
        if event.source() == self._container:
            return
        if not self.drop_object:
            return
        if not self.drop_object.db_index:
            self.drop_object.commit()
        self.add_treasure(self.drop_object)
        self.drop_object = None
        event.accept()

    def eventFilter(self, watched: QtWidgets.QWidget, event: QtCore.QEvent) -> bool:
        if watched == self._container.viewport():
            if event.type() == QtCore.QEvent.ContextMenu:
                self.contextMenuEvent(event)
                return True
            if event.type() == QtCore.QEvent.MouseMove:
                if event.buttons() == QtCore.Qt.LeftButton:
                    return False
                self.event(event)
                return True
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                self._playlist.setCurrentIndex(self._container.row(self._container.itemAt(event.pos())))
                SIGNALS.MUSIC_CONTINUE.emit(self.db_index)
                return True
            if event.type() in (QtCore.QEvent.DragEnter, QtCore.QEvent.Drop):
                if event.source() == self._container:
                    return False
                self.event(event)
                return True
        elif watched == self._container:
            if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Delete \
                    and (selected := self._container.selectedIndexes()):
                self.remove_row(selected[0].row())
                return True
        return super().eventFilter(watched, event)

    def get_db_index(self, row: int) -> int | None:
        try:
            return self._container.item(row).data(QtCore.Qt.UserRole)
        except (AttributeError, KeyError):
            return None

    @property
    def is_playing(self) -> bool:
        return self._player.state() == self._player.PlayingState

    def leaveEvent(self, event: QtCore.QEvent):
        if self.feature_preview:
            self.feature_preview.deleteLater()

    def load_genres(self):
        self.tag_frame.set_tags(self.minstrel.get_tags())

    def load_repertoire(self):
        for treasure in self.minstrel.get_treasures():
            self.add_treasure(treasure, commit=False)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        try:
            db_index = self._container.itemAt(event.pos()).data(QtCore.Qt.UserRole)
        except (AttributeError, KeyError):
            db_index = None
        if not db_index:
            if self.feature_preview:
                self.feature_preview.deleteLater()
            return
        if self.feature_preview:
            if self.feature_preview.db_index == db_index:
                self.feature_preview.move(event.globalPos() + QtCore.QPoint(10, 10))
                return
            self.feature_preview.deleteLater()
        feature = Treasure.read_keep(self.keep, db_index)
        self.feature_preview = Preview(feature)
        self.feature_preview.show()
        self.feature_preview.move(event.globalPos() + QtCore.QPoint(10, 10))

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.buttons() == QtGui.Qt.RightButton:
            menu = QtWidgets.QMenu(self)
            rename_action = RenameAction(self.minstrel, 'clef', menu)
            menu.addAction(rename_action)
            menu.popup(event.globalPos())

    def on_add_treasure(self, minstrel_index: int, treasure_index: int):
        if minstrel_index != self.db_index:
            return
        self.add_treasure(treasure_index)

    def on_current_index_changed(self, _: int = None):
        count = self._container.count()
        if not count:
            return
        new_icon_name = 'media_play' if self.is_playing else 'media_pause'
        current = self._playlist.currentIndex()
        if db_index := self.get_db_index(current):
            SIGNALS.MUSIC_NOW_PLAYING.emit(db_index)
        for row in range(count):
            self._container.item(row).setIcon(Icon(new_icon_name if row == current else 'music'))
        if self.is_playing:
            self.play_pause.setIcon(Icon('media_pause'))
            self.play_pause.setText('Pause')
        else:
            self.play_pause.setIcon(Icon('media_play'))
            self.play_pause.setText('Play')

    def on_list_changed(self):
        enabled = bool(self._playlist.mediaCount())
        self.stop_button.setEnabled(enabled)
        self.play_pause.setEnabled(enabled)
        self.shuffle_button.setEnabled(enabled)
        self.minstrel['count'] = self._playlist.mediaCount()

    def on_minstrel_commit(self, db_index: int):
        if self.minstrel.db_index != db_index:
            return
        self.minstrel = Minstrel.read_keep(self.keep, db_index)

    def on_move_item(self, old_index: int, new_index: int):
        if old_index == self._playlist.currentIndex():
            self._playlist.setCurrentIndex(new_index)
        self._playlist.moveMedia(old_index, new_index - (new_index > old_index))
        self.save_repertoire()
        self.on_current_index_changed()

    def on_play_pause(self):
        if self.is_playing:
            self.pause()
            return
        SIGNALS.MUSIC_CONTINUE.emit(self.db_index)

    def on_play_signal(self, db_index: int, ):
        if db_index == self.db_index:
            self.play()
        else:
            self.pause()

    def on_tags_changed(self, _: list[str]):
        self.save_genres()

    def on_treasure_delete(self, db_index: int):
        for row in range(self._container.count()):
            if self.get_db_index(row) == db_index:
                self.remove_row(row)
                break

    def pause(self):
        self._player.pause()
        self.on_current_index_changed(self._playlist.currentIndex())

    def play(self):
        self._player.play()
        self.on_current_index_changed(self._playlist.currentIndex())

    def reload_treasure(self, db_index: int):
        for row in range(self._container.count()):
            if self.get_db_index(row) == db_index:
                self._container.item(row).setText(self.df.at[db_index, 'name'])
                break

    def remove_row(self, row: int):
        item = self._container.item(row)
        if not item:
            return
        self._playlist.removeMedia(row)
        self._container.takeItem(row)
        self.save_repertoire()

    def save_genres(self):
        self.delete_genres()
        for tag_name in self.tag_frame.tags:
            Genre(self.keep, data={'_minstrel': self.db_index, 'name': tag_name}).commit()
        self.minstrel.commit()

    def save_minstrel(self):
        self.save_repertoire()
        self.save_genres()

    def save_repertoire(self):
        self.delete_repertoire()
        for row in range(self._container.count()):
            Repertoire(self.keep, data={'_minstrel': self.db_index, '_treasure': self.get_db_index(row),
                                        '_index': row}).commit()
        self.minstrel.commit()

    def shuffle(self):
        count = self._container.count()
        index_list = list(range(count))
        random.shuffle(index_list)
        for row in index_list:
            self._playlist.moveMedia(row, 0)
            self._container.insertItem(0, self._container.takeItem(row))
        self.save_repertoire()
        self.on_current_index_changed()

    def stop(self):
        playing = self.is_playing
        self._playlist.setCurrentIndex(0)
        self.pause()
        self._player.stop()
        if playing:
            SIGNALS.MUSIC_NOW_PLAYING.emit('')
