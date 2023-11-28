import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from src.model import Keep, Minstrel
from src.settings import SIGNALS
from src.widgets import BuildingTable, Icon, RenameAction, RenameDialog


class MinstrelTable(BuildingTable):
    SEARCH = QtCore.Signal()

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=Minstrel, parent=parent)
        self.search_black_list: tuple[str, ...] = ()
        self.search_white_list: tuple[str, ...] = ()
        self.genre_df = keep.buildings['genre'].df
        self.row_num = None
        self.reload_data()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        context_menu = QtWidgets.QMenu(self)
        new_minstrel = QtWidgets.QAction(Icon('plus'), 'New Minstrel', self)
        new_minstrel.triggered.connect(self.new_minstrel)
        context_menu.addAction(new_minstrel)
        context_menu.addSeparator()
        if current := self.get_db_index(self.currentRow()):
            if self.df.at[current, 'state'] > 0:
                play_action = QtWidgets.QAction(Icon('media_play'), 'Play Minstrel', self)
                play_action.triggered.connect(lambda: SIGNALS.MUSIC_CONTINUE.emit(current))
                rename_action = RenameAction(Minstrel.read_keep(self.keep, current), 'clef', self)
                context_menu.addAction(play_action)
                context_menu.addAction(rename_action)
            delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Expel Minstrel', self)
            delete_action.triggered.connect(lambda: self.on_delete(current))
            context_menu.addAction(delete_action)
        context_menu.popup(event.globalPos())

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtGui.Qt.Key_F and event.modifiers() == QtGui.Qt.CTRL:
            self.SEARCH.emit()
        elif (db_index := self.get_db_index(self.currentRow())) is not None:
            if event.key() == QtGui.Qt.Key_Space:
                minstrel = Minstrel.read_keep(self.keep, db_index=db_index)
                minstrel['state'] = 2 - 2 * bool(minstrel['state'])
                minstrel.commit()
                event.ignore()
                return True
        super().keyPressEvent(event)

    def load_series(self, series: pd.Series, row: int | None = None):
        self.blockSignals(True)
        new_row = row is None
        if new_row:
            row = self.row_num
        series = series.copy(False)
        db_index = int(series.name)  # noqa
        name_item = QtWidgets.QTableWidgetItem(series['name'])
        name_item.setData(QtCore.Qt.UserRole, db_index)
        name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
        hidden_item = QtWidgets.QWidget()
        hidden_layout = QtWidgets.QHBoxLayout()
        hidden_box = QtWidgets.QCheckBox()
        hidden_box.setChecked(series['state'] != 0)
        hidden_box.stateChanged.connect(lambda state: self.on_check(db_index, state))
        hidden_layout.addWidget(hidden_box)
        hidden_layout.setAlignment(QtCore.Qt.AlignCenter)
        hidden_layout.setContentsMargins(0, 0, 0, 0)
        hidden_item.setLayout(hidden_layout)

        genres_item = QtWidgets.QTableWidgetItem(series['genres'])
        genres_item.setFlags(genres_item.flags() & ~QtCore.Qt.ItemIsEditable)
        genres_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        count_item = QtWidgets.QTableWidgetItem(str(series['count']))
        count_item.setFlags(count_item.flags() & ~QtCore.Qt.ItemIsEditable)
        count_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        created_item = QtWidgets.QTableWidgetItem(series['_created'])
        created_item.setFlags(created_item.flags() & ~QtCore.Qt.ItemIsEditable)
        created_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        modified_item = QtWidgets.QTableWidgetItem(series['_modified'])
        modified_item.setFlags(modified_item.flags() & ~QtCore.Qt.ItemIsEditable)
        modified_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.setItem(row, 0, name_item)
        self.setCellWidget(row, 1, hidden_item)
        self.setItem(row, 2, count_item)
        self.setItem(row, 3, created_item)
        self.setItem(row, 4, modified_item)
        self.setItem(row, 5, genres_item)
        self.blockSignals(False)
        if new_row:
            self.row_num += 1

    def on_check(self, db_index: int, state: int):
        minstrel = Minstrel.read_keep(self.keep, db_index=db_index)
        minstrel['state'] = state
        minstrel.commit()

    def new_minstrel(self):
        minstrel = Minstrel.new(self.keep)
        minstrel['state'] = 2
        minstrel['name'] = 'New Minstrel'
        minstrel.commit()
        RenameDialog(minstrel, 'clef', self).exec()

    def reload_data(self):
        self.clear()
        self.setRowCount(len(self.df.index))
        self.row_num = 0
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['Minstrel', 'Show', '#', 'Created', 'Last Modified', 'Genres'])
        if not self.df.empty:
            self.df.apply(self.load_series, axis=1)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().resizeSection(1, 20)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def refresh_hidden(self):
        for row in range(self.rowCount()):
            search_string = self.item(row, 0).text().lower() + ', ' + self.item(row, 5).text().lower()
            hide = any(keyword in search_string for keyword in self.search_black_list) or \
                not all(keyword in search_string for keyword in self.search_white_list)
            self.setRowHidden(row, hide)

    def toolbar_set_search(self, white_list: tuple[str], black_list: tuple[str]):
        self.search_white_list = white_list
        self.search_black_list = black_list
        self.refresh_hidden()
