from PySide2 import QtCore, QtGui, QtWidgets

from .encounter_inspector import EncounterInspector
from .encounter_table import EncounterTable
from .encounter_toolbar import EncounterToolbar
from src.model import Encounter, Keep
from src.settings import SIGNALS
from src.widgets import BuildingWindow, DeleteDialog, Icon


class Enlistment(BuildingWindow):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.frame = QtWidgets.QFrame(self)
        self.setCentralWidget(self.frame)
        self.setWindowTitle('Enlistment - Lorekeeper')
        self.setWindowIcon(Icon('sword'))
        self.toolbar = EncounterToolbar(keep, self)
        self.table = EncounterTable(self.keep, self)
        self.resize(800, 600)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.table)
        self.frame.setLayout(layout)

        self.toolbar.STRING.connect(self.table.toolbar_set_search)
        self.table.SEARCH.connect(self.toolbar.search)
        SIGNALS.ENCOUNTER_COMMIT.connect(lambda _: keep.buildings['encounter'].save())
        SIGNALS.ENCOUNTER_DELETE.connect(self.on_encounter_delete)
        SIGNALS.ENCOUNTER_INSPECT.connect(self.on_encounter_inspect)
        SIGNALS.GUARD_DELETE.connect(self.on_guard_delete)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)
        new_action = QtWidgets.QAction(Icon('plus'), 'New Encounter', self)
        new_action.triggered.connect(self.on_new_encounter)
        menu.addAction(new_action)
        if selected := self.table.selectedIndexes():
            db_index = self.table.item(selected[0].row(), 0).data(QtCore.Qt.UserRole)
            inspect_action = QtWidgets.QAction(Icon('sword'), 'Inspect Encounter', self)
            inspect_action.triggered.connect(lambda: SIGNALS.ENCOUNTER_INSPECT.emit(db_index))
            menu.addAction(inspect_action)
            delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Delete Encounter', self)
            delete_action.triggered.connect(lambda: self.on_delete(db_index))
            menu.addAction(delete_action)
        menu.popup(event.globalPos())

    def on_delete(self, db_index: int):
        if DeleteDialog('encounter').get() == 'delete':
            Encounter.read_keep(self.keep, db_index=db_index).delete()

    def on_guard_delete(self, db_index: int):
        building = self.keep.buildings['combatant']
        building.df.loc[building.df['_guard'] == db_index, '_guard'] = 0
        building.save(False)

    def on_encounter_delete(self, db_index: int):
        for building_name in ('banner', 'sigil', 'combatant'):
            building = self.keep.buildings[building_name]
            df = building.df
            df.drop(df[df['_encounter'] == db_index].index, inplace=True)
            building.reset_columns()
            building.save(modified_only=False)
        self.keep.buildings['encounter'].save()

    def on_encounter_inspect(self, db_index: int):
        for child in QtWidgets.QApplication.topLevelWidgets():
            if not isinstance(child, EncounterInspector):
                continue
            if child.encounter.db_index == db_index:
                child.show()
                child.activateWindow()
                child.raise_()
                return
        inspector = EncounterInspector(Encounter.read_keep(self.keep, db_index=db_index))
        inspector.show()

    def on_new_encounter(self):
        encounter = Encounter.new(self.keep)
        encounter['name'] = 'New Encounter'
        db_index = encounter.commit()
        SIGNALS.ENCOUNTER_INSPECT.emit(db_index)
