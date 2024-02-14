from collections import defaultdict
import re

import pandas as pd
from PySide2 import QtCore, QtWidgets

from src.model import Keep
from src.rulesets import RULESET
from src.widgets import BuildingTable

REGEX_REMOVE_HTML = re.compile('<.*?>')


class GuardTable(BuildingTable):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=RULESET.GUARD_TYPE, parent=parent)
        self.row_num = None
        self.display_type: dict[str, bool] = defaultdict(lambda: True)
        self.df = self.keep.buildings['guard'].df
        self.trait_df = self.keep.buildings['trait'].df
        self.search_white_list: tuple[str, ...] = ()
        self.search_black_list: tuple[str, ...] = ()
        self.trait_index = 0
        self.type_index = 0
        self.name_index = 0

        self.reload_data()
        self.refresh_hidden()

    def load_series(self, series: pd.Series, row: int | None = None):
        self.blockSignals(True)
        new_row = row is None
        if new_row:
            row = self.row_num
        series = series.copy(False)
        db_index = int(series.name)  # noqa
        for column, (key, value) in enumerate(RULESET.GARRISON_HEADER):
            item = QtWidgets.QTableWidgetItem(REGEX_REMOVE_HTML.sub('', str(series.get(key, ''))))
            item.setData(QtCore.Qt.UserRole, db_index)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.setItem(row, column, item)

        self.blockSignals(False)
        if new_row:
            self.row_num += 1

    def refresh_hidden(self):
        for row in range(self.rowCount()):
            search_string = self.item(row, self.name_index).text().lower() + ', ' + \
                            self.item(row, self.trait_index).text().lower()
            hide = any(keyword in search_string for keyword in self.search_black_list) or \
                not all(keyword in search_string for keyword in self.search_white_list)
            self.setRowHidden(row, hide or not self.display_type[self.item(row, self.type_index).text()])

    def reload_data(self):
        self.clear()
        self.setRowCount(len(self.df.index))
        self.row_num = 0
        index = 0
        for index, (key, name) in enumerate(RULESET.GARRISON_HEADER):
            if key == 'traits':
                self.trait_index = index
            elif key == 'name':
                self.name_index = index
            elif key == 'type':
                self.type_index = index
        self.setColumnCount(index + 1)
        self.setHorizontalHeaderLabels([name for column, name in RULESET.GARRISON_HEADER])
        if not self.df.empty:
            self.df.apply(self.load_series, axis=1)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setMinimumSectionSize(20)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def toolbar_set_type(self, value: bool, type_: str):
        self.display_type[type_] = value
        self.refresh_hidden()

    def toolbar_set_search(self, white_list: tuple[str, ...], black_list: tuple[str, ...]):
        self.search_white_list = white_list
        self.search_black_list = black_list
        self.refresh_hidden()
