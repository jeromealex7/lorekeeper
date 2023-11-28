import pandas as pd
from PySide2 import QtCore, QtWidgets

from src.model import Encounter, Keep
from src.widgets import BuildingTable


class EncounterTable(BuildingTable):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=Encounter, parent=parent)
        self.row_num = None
        self.df = self.keep.buildings['encounter'].df
        self.banner_df = self.keep.buildings['banner'].df
        self.search_black_list: tuple[str, ...] = ()
        self.search_white_list: tuple[str, ...] = ()

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
        combatants_item = QtWidgets.QTableWidgetItem(series['combatants'])
        combatants_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
        created_item = QtWidgets.QTableWidgetItem()
        created_item.setText(series['_created'])
        created_item.setFlags(created_item.flags() & ~QtCore.Qt.ItemIsEditable)
        created_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        modified_item = QtWidgets.QTableWidgetItem()
        modified_item.setText(series['_modified'])
        modified_item.setFlags(modified_item.flags() & ~QtCore.Qt.ItemIsEditable)
        modified_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        banners_item = QtWidgets.QTableWidgetItem()
        banners_item.setText(series['banners'])
        banners_item.setFlags(banners_item.flags() & ~QtCore.Qt.ItemIsEditable)
        banners_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, combatants_item)
        self.setItem(row, 2, created_item)
        self.setItem(row, 3, modified_item)
        self.setItem(row, 4, banners_item)

        self.blockSignals(False)
        if new_row:
            self.row_num += 1

    def refresh_hidden(self):
        for row in range(self.rowCount()):
            search_string = self.item(row, 0).text().lower() + ', ' + self.item(row, 4).text().lower()
            hide = any(keyword in search_string for keyword in self.search_black_list) or \
                not all(keyword in search_string for keyword in self.search_white_list)
            self.setRowHidden(row, hide)

    def reload_data(self):
        self.clear()
        self.setRowCount(len(self.df.index))
        self.row_num = 0
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['Name', 'Combatants', 'Created', 'Last Modified', 'Banners'])
        if not self.df.empty:
            self.df.apply(self.load_series, axis=1)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setMinimumSectionSize(20)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def toolbar_set_type(self, value: bool, type_: str):
        self.display_type[type_] = value
        self.refresh_hidden()

    def toolbar_set_search(self, white_list: tuple[str], black_list: tuple[str]):
        self.search_white_list = white_list
        self.search_black_list = black_list
        self.refresh_hidden()
