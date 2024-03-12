import pandas as pd
from PySide2 import QtCore, QtMultimedia, QtWidgets

from .control_frame import ControlFrame
from .minstrel_toolbar import MinstrelToolbar
from .minstrel_table import MinstrelTable
from .minstrel_tab import MinstrelTab
from src.model import Keep, Minstrel, Treasure
from src.settings import SIGNALS
from src.widgets import BuildingWindow, Icon, RenameAction


class MusicHall(BuildingWindow):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None, settings: dict = None):
        super().__init__(parent)
        self.frame = QtWidgets.QFrame()
        self.resize(800, 600)
        self.setWindowIcon(Icon('clef'))
        self.setWindowTitle('Music Hall - Lorekeeper')
        self.keep = keep
        self.df = keep.buildings['minstrel'].df
        self.tab_view = QtWidgets.QTabWidget()
        self.setCentralWidget(self.frame)
        self.tab_view.setTabsClosable(True)
        self.tab_view.tabBar().setChangeCurrentOnDrag(True)
        self.tab_view.tabBar().installEventFilter(self)
        self.tab_view.setDocumentMode(True)
        self.tab_view.setMovable(True)
        self._player = QtMultimedia.QMediaPlayer()
        self._playlist = QtMultimedia.QMediaPlaylist()
        self._playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.Loop)
        self._player.setPlaylist(self._playlist)

        self.control_frame = ControlFrame(keep, self)
        self.minstrel_table = MinstrelTable(keep, self)
        self.toolbar = MinstrelToolbar(keep, self)
        self.set_settings(settings)

        layout = QtWidgets.QHBoxLayout()
        splitter = QtWidgets.QSplitter()
        splitter.setHandleWidth(1)
        splitter.setStyleSheet('QSplitter::handle {background-color: #cccccc; border: 1px solid #999999; width 0px;};')
        controls = QtWidgets.QVBoxLayout()
        controls_widget = QtWidgets.QWidget()
        controls_widget.setLayout(controls)
        controls.addWidget(self.control_frame)
        controls.addWidget(self.toolbar)
        controls.addWidget(self.minstrel_table)
        layout.addWidget(splitter)
        splitter.addWidget(controls_widget)
        splitter.addWidget(self.tab_view)
        self.frame.setLayout(layout)
        self.add_tabs()

        SIGNALS.MUSIC_DIRECT.connect(self.on_direct)
        SIGNALS.MUSIC_CONTINUE.connect(self.on_play)
        SIGNALS.MINSTREL_COMMIT.connect(self.load_tab)
        SIGNALS.MINSTREL_COMMIT.connect(self.save)
        SIGNALS.MINSTREL_INSPECT.connect(self.on_minstrel_inspect)
        SIGNALS.MINSTREL_DELETE.connect(self.on_minstrel_delete)
        SIGNALS.MINSTREL_DELETE.connect(self.save)
        SIGNALS.TAB_RENAME.connect(self.on_minstrel_rename)
        self.tab_view.tabCloseRequested.connect(self.on_tab_close)
        self.toolbar.STRING.connect(self.minstrel_table.toolbar_set_search)
        self.minstrel_table.SEARCH.connect(self.toolbar.search)

    def add_tabs(self):
        def _add(series: pd.Series):
            self.tab_view.addTab(MinstrelTab(self.keep, int(series.name), self), series['name'])  # noqa
        self.df[self.df['state'] > 0].apply(_add, axis=1)

    def delete_tab(self, db_index: int):
        index, tab = self.get_tab(db_index)
        if not tab:
            return
        tab.stop()
        self.tab_view.removeTab(index)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.tab_view.tabBar() and event.type() == QtCore.QEvent.MouseButtonPress and \
                event.buttons() == QtCore.Qt.RightButton:
            menu = QtWidgets.QMenu(self)
            tab = self.tab_view.widget(self.tab_view.tabBar().tabAt(event.pos()))
            if not tab:
                return False
            rename_action = RenameAction(tab.minstrel, 'clef', self)
            menu.addAction(rename_action)
            menu.popup(event.globalPos())
        return super().eventFilter(watched, event)

    def get_settings(self) -> dict:
        return {'hidden': tuple(self.minstrel_table.isColumnHidden(column)
                                for column in range(self.minstrel_table.columnCount()))}

    def get_tab(self, db_index: int) -> tuple[int, QtWidgets.QTableWidgetItem | None]:
        for index in range(self.tab_view.count()):
            widget = self.tab_view.widget(index)
            if widget.db_index == db_index:
                return index, widget
        return -1, None

    def load_tab(self, db_index: int):
        index, tab = self.get_tab(db_index)

        try:
            series = self.df.loc[db_index]
        except KeyError:
            if tab:
                self.tab_view.removeTab(index)
                tab.stop()
            return
        if not tab:
            if not series['state']:
                return
            tab = MinstrelTab(self.keep, db_index, self)
            index = self.tab_view.count()
            self.tab_view.addTab(tab, series['name'])
            self.tab_view.activateWindow()
        self.tab_view.setTabText(index, series['name'])
        if not series['state']:
            self.tab_view.removeTab(index)
            tab.stop()

    def on_direct(self, db_index: int):
        SIGNALS.MUSIC_CONTINUE.emit(-1)
        SIGNALS.MUSIC_NOW_PLAYING.emit(db_index)
        self._playlist.clear()
        treasure = Treasure.read_keep(self.keep, db_index=db_index)
        url = QtCore.QUrl.fromLocalFile(treasure.path.as_posix().__str__())
        self._playlist.addMedia(url)
        self._player.play()

    def on_minstrel_delete(self, db_index: int):
        self.delete_tab(db_index)
        for building_name in ('genre', 'repertoire', 'performance'):
            building = self.keep.buildings[building_name]
            building.df.drop(building.df[building.df['_minstrel'] == db_index].index, inplace=True)
            building.reset_columns()
            building.save(False)

    def on_minstrel_inspect(self, db_index):
        minstrel = Minstrel.read_keep(self.keep, db_index=db_index)
        minstrel['state'] = 2
        minstrel.commit()

    def on_minstrel_rename(self, table_name: str, db_index: int, name: str):
        if table_name != 'minstrel':
            return
        minstrel = Minstrel.read_keep(self.keep, db_index=db_index)
        minstrel['name'] = name
        minstrel.commit()

    def on_play(self, minstrel_index: int):
        if minstrel_index == -1:
            return
        self._player.stop()

    def on_tab_close(self, index: int):
        tab = self.tab_view.widget(index)
        minstrel = tab.minstrel
        minstrel['state'] = 0
        minstrel.commit()

    def save(self, _: int = None):
        self.keep.buildings['genre'].save()
        self.keep.buildings['minstrel'].save()
        self.keep.buildings['repertoire'].save()

    def set_settings(self, settings: dict):
        if not settings:
            return
        for column, hidden in enumerate(settings.get('hidden', ())):
            self.minstrel_table.setColumnHidden(column, hidden)
