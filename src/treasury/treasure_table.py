from collections import defaultdict

import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from .import_tools import ClipboardAction, Importer, OpenTreasureDialog
from .treasure_menu import TreasureMenu
from src.model import Keep, Treasure
from src.settings import SIGNALS
from src.widgets import Icon

from src.widgets import BuildingTable


class TreasureTable(BuildingTable):
    HEADERS = (('name', 'Name'), ('type', 'Type'), ('info', 'Info'), ('size', 'Size'),
               ('_modified', 'Last Modified'), ('_created', 'Created'), ('inscriptions', 'Inscriptions'))

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=Treasure, parent=parent)
        self.drop_treasure = None
        self.inscription_df = keep.buildings['inscription'].df
        self.row_num = None
        self.display_type: dict[str, bool] = defaultdict(lambda: True)
        self.search_black_list: tuple[str, ...] = ()
        self.search_white_list: tuple[str, ...] = ()
        self.viewport().setAcceptDrops(True)

        self.reload_data()
        self.refresh_hidden()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        db_index = self.get_db_index(self.rowAt(event.pos().y()))
        try:
            selected_treasure = Treasure.read_keep(self.keep, db_index)
        except KeyError:
            selected_treasure = None
        context_menu = QtWidgets.QMenu(self)
        if selected_treasure:
            context_menu = TreasureMenu(selected_treasure, context_menu)
            delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Destroy Treasure', context_menu)
            delete_action.triggered.connect(lambda: self.on_delete(selected_treasure.db_index))
            context_menu.addAction(delete_action)
            context_menu.addSeparator()
        if clipboard_action := ClipboardAction(self.keep, None, True, context_menu):
            context_menu.addAction(clipboard_action)

            def inspect():
                if index := clipboard_action.treasure.db_index:
                    SIGNALS.TREASURE_INSPECT.emit(index)
            clipboard_action.triggered.connect(inspect)
        open_action = QtWidgets.QAction(Icon('folder_open'), 'Open File ...', context_menu)
        open_action.triggered.connect(self.on_open)
        context_menu.addAction(open_action)
        context_menu.popup(event.globalPos())

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        self.drop_treasure = Treasure.read_mime_data(self.keep, event.mimeData())
        if not self.drop_treasure:
            event.setAccepted(False)
            return False
        if self.drop_treasure.db_index:
            event.setAccepted(False)
            return False
        return True

    def dropEvent(self, event: QtGui.QDropEvent):
        if not self.drop_treasure or event.source() == self:
            event.setDropAction(QtCore.Qt.IgnoreAction)
            return
        for treasure in Treasure.read_drag_data(self.keep, event.mimeData()):
            Importer(treasure, parent=self).exec_()
        self.drop_treasure = None

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtGui.Qt.Key_V and event.modifiers() == QtGui.Qt.CTRL:
            if clipboard_action := ClipboardAction(self.keep, None, True, self):
                clipboard_action.exec_()
        elif event.key() == QtGui.Qt.Key_F and event.modifiers() == QtGui.Qt.CTRL:
            self.SEARCH.emit()
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
        type_item = QtWidgets.QTableWidgetItem(Icon(Treasure.get_icon_name(series['type'])),
                                               series['type'].capitalize())
        type_item.setFlags(type_item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.setItem(row, 0, name_item)
        self.setItem(row, 1, type_item)

        for column, (column_name, _) in enumerate(self.HEADERS[2:], start=2):
            item = QtWidgets.QTableWidgetItem(str(series[column_name]))
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.setItem(row, column, item)

        self.blockSignals(False)
        if new_row:
            self.row_num += 1

    def on_open(self):
        dialog = OpenTreasureDialog(self.keep)
        if treasure := dialog.get():
            importer = Importer(treasure, True, self)
            importer.exec_()

    def reload_data(self):
        self.clear()
        self.setRowCount(len(self.df.index))
        self.row_num = 0
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(list(header[1] for header in self.HEADERS))
        if not self.df.empty:
            self.df.apply(self.load_series, axis=1)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setMinimumSectionSize(20)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def refresh_hidden(self):
        for row in range(self.rowCount()):
            search_string = self.item(row, 0).text().lower() + ', ' + self.item(row, 6).text().lower()
            hide = any(keyword in search_string for keyword in self.search_black_list) or \
                not all(keyword in search_string for keyword in self.search_white_list)
            self.setRowHidden(row, hide or not self.display_type[self.item(row, 1).text().lower()])

    def toolbar_set_type(self, value: bool, type_: str):
        self.display_type[type_] = value
        self.refresh_hidden()

    def toolbar_set_search(self, white_list: tuple[str], black_list: tuple[str]):
        self.search_white_list = white_list
        self.search_black_list = black_list
        self.refresh_hidden()
