from PySide2 import QtCore, QtWidgets

from .image_popup import ImagePopup
from .treasure_inspector import TreasureInspector
from .treasure_table import TreasureTable
from .treasury_toolbar import TreasuryToolbar
from src.model import Keep, Treasure
from src.settings import SIGNALS
from src.widgets import BuildingWindow, Icon


class Treasury(BuildingWindow):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.frame = QtWidgets.QFrame(self)
        self.setCentralWidget(self.frame)
        self.setWindowTitle('Treasury - Lorekeeper')
        self.setWindowIcon(Icon('chest'))
        self.table = TreasureTable(keep, self)
        self.toolbar = TreasuryToolbar(keep, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar, alignment=QtCore.Qt.AlignLeft)
        layout.addWidget(self.table)
        self.frame.setLayout(layout)
        self.resize(800, 600)

        self.toolbar.STATE.connect(self.table.toolbar_set_type)
        self.toolbar.STRING.connect(self.table.toolbar_set_search)
        self.table.SEARCH.connect(self.toolbar.search)
        SIGNALS.TREASURE_COMMIT.connect(lambda _: keep.buildings['treasure'].save())
        SIGNALS.TREASURE_DELETE.connect(self.on_delete_treasure)
        SIGNALS.TREASURE_INSPECT.connect(self.on_inspect_treasure)
        SIGNALS.IMAGE_POPUP.connect(self.on_image_popup)

    def on_delete_treasure(self, db_index):
        for building_name in ('inscription', 'repertoire', 'chart'):
            building = self.keep.buildings[building_name]
            df = building.df
            df.drop(df[df['_treasure'] == db_index].index, inplace=True)
            building.reset_columns()
            building.save(modified_only=False)
        book = self.keep.buildings['book']
        book.df.loc[book.df['_treasure'] == db_index, '_treasure'] = 0
        guard = self.keep.buildings['guard']
        guard.df.loc[guard.df['_treasure'] == db_index, '_treasure'] = 0
        self.keep.buildings['guard'].save(False)
        self.keep.buildings['book'].save(False)
        self.keep.buildings['treasure'].save(False)

    def on_image_popup(self, db_index: int):
        for child in QtWidgets.QApplication.topLevelWidgets():
            if not isinstance(child, ImagePopup):
                continue
            if child.treasure.db_index == db_index:
                child.show()
                child.update_image()
                child.activateWindow()
                child.raise_()
                return
        viewer = ImagePopup(Treasure.read_keep(self.keep, db_index=db_index))
        viewer.update_image()
        viewer.show()

    def on_inspect_treasure(self, db_index: int):
        for child in QtWidgets.QApplication.topLevelWidgets():
            if not isinstance(child, TreasureInspector):
                continue
            if child.treasure.db_index == db_index:
                child.show()
                child.activateWindow()
                child.raise_()
                return
        inspector = TreasureInspector(Treasure.read_keep(self.keep, db_index=db_index))
        inspector.show()
