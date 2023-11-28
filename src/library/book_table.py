from collections import defaultdict

import pandas as pd
from PySide2 import QtCore, QtWidgets

from src.model import Book, Keep
from src.settings import SIGNALS
from src.widgets import BuildingTable, Icon


class BookTable(BuildingTable):
    SEARCH = QtCore.Signal()

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=Book, parent=parent)
        self.display_type: dict[str, bool] = defaultdict(lambda: True)
        self.keyword_df = keep.buildings['keyword'].df
        self.search_black_list: tuple[str, ...] = ()
        self.search_white_list: tuple[str, ...] = ()
        self.row_num = None
        self.reload_data()

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
        type_item = QtWidgets.QWidget()
        type_layout = QtWidgets.QHBoxLayout()
        type_icon = QtWidgets.QToolButton()
        type_icon.setIcon(Icon(series['type']))
        type_item.type_name = series['type']
        type_icon.setIconSize(QtCore.QSize(22, 22))
        type_icon.setAutoRaise(True)
        type_icon.clicked.connect(lambda: SIGNALS.BOOK_INSPECT.emit(db_index))
        type_layout.addWidget(type_icon, alignment=QtCore.Qt.AlignCenter)
        type_layout.setAlignment(QtCore.Qt.AlignCenter)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_item.setLayout(type_layout)
        created_item = QtWidgets.QTableWidgetItem()
        created_item.setText(series['_created'])
        created_item.setFlags(created_item.flags() & ~QtCore.Qt.ItemIsEditable)
        created_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        modified_item = QtWidgets.QTableWidgetItem()
        modified_item.setText(series['_modified'])
        modified_item.setFlags(modified_item.flags() & ~QtCore.Qt.ItemIsEditable)
        modified_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        keywords_item = QtWidgets.QTableWidgetItem()
        keywords_item.setText(series['keywords'])
        keywords_item.setFlags(keywords_item.flags() & ~QtCore.Qt.ItemIsEditable)
        keywords_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.setItem(row, 0, name_item)
        self.setCellWidget(row, 1, type_item)
        self.setItem(row, 2, created_item)
        self.setItem(row, 3, modified_item)
        self.setItem(row, 4, keywords_item)

        self.blockSignals(False)
        if new_row:
            self.row_num += 1

    def reload_data(self):
        self.clear()
        self.setRowCount(len(self.df.index))
        self.row_num = 0
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['Name', 'Type', 'Created', 'Last Modified', 'Keywords'])
        if not self.df.empty:
            self.df.apply(self.load_series, axis=1)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setMinimumSectionSize(20)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def refresh_hidden(self):
        for row in range(self.rowCount()):
            search_string = self.item(row, 0).text().lower() + ', ' + self.item(row, 4).text().lower()
            hide = any(keyword in search_string for keyword in self.search_black_list) or \
                not all(keyword in search_string for keyword in self.search_white_list)
            self.setRowHidden(row, hide or not self.display_type[self.cellWidget(row, 1).type_name.lower()])

    def toolbar_set_type(self, value: bool, type_: str):
        self.display_type[type_] = value
        self.refresh_hidden()

    def toolbar_set_search(self, white_list: tuple[str], black_list: tuple[str]):
        self.search_white_list = white_list
        self.search_black_list = black_list
        self.refresh_hidden()
