from PySide2 import QtCore, QtGui, QtWidgets

from .guard_popup import GuardPopup
from .guard_table import GuardTable
from .guard_toolbar import GuardToolbar
from src.model import Guard, Keep
from src.rulesets import RULESET
from src.settings import SIGNALS
from src.widgets import BuildingWindow, DeleteDialog, Icon


class Garrison(BuildingWindow):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.frame = QtWidgets.QFrame(self)
        self.setCentralWidget(self.frame)
        self.setWindowTitle('Garrison - Lorekeeper')
        self.setWindowIcon(Icon('helmet'))
        self.table = GuardTable(keep, self)
        self.toolbar = GuardToolbar(keep, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar, alignment=QtCore.Qt.AlignLeft)
        layout.addWidget(self.table)
        self.frame.setLayout(layout)
        self.resize(800, 600)

        self.toolbar.STATE.connect(self.table.toolbar_set_type)
        self.toolbar.STRING.connect(self.table.toolbar_set_search)
        self.table.SEARCH.connect(self.toolbar.search)
        SIGNALS.GUARD_COMMIT.connect(lambda _: keep.buildings['guard'].save(False))
        SIGNALS.GUARD_DELETE.connect(self.on_delete_guard)
        SIGNALS.GUARD_INSPECT.connect(self.on_inspect_guard)
        SIGNALS.GUARD_POPUP.connect(self.on_guard_popup)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)

        def new_guard():
            guard = RULESET.GUARD_TYPE.new(self.keep)
            new_db_index = guard.commit()
            SIGNALS.GUARD_INSPECT.emit(new_db_index)
        new_action = QtWidgets.QAction(Icon('plus'), 'New Guard', self)
        new_action.triggered.connect(new_guard)
        menu.addAction(new_action)
        if selected := self.table.selectedIndexes():
            db_index = self.table.item(selected[0].row(), 0).data(QtCore.Qt.UserRole)
            copy_action = QtWidgets.QAction(Icon('copy'), 'Copy Guard', self)
            treasure_db_index = self.keep.buildings['guard'].df.at[db_index, '_treasure']

            def copy():
                guard = RULESET.GUARD_TYPE.new(self.keep)
                data = RULESET.GUARD_TYPE.read_keep(self.keep, db_index=db_index)
                guard.update(data)
                guard['name'] = f'Copy of {guard["name"]}'
                new_db_index = guard.commit()
                SIGNALS.GUARD_INSPECT.emit(new_db_index)
            copy_action.triggered.connect(copy)
            menu.addAction(copy_action)
            inspect_action = QtWidgets.QAction(Icon('helmet'), 'Inspect Guard', self)
            inspect_action.triggered.connect(lambda: SIGNALS.GUARD_INSPECT.emit(db_index))
            menu.addAction(inspect_action)
            popup_action = QtWidgets.QAction(Icon('note_text'), 'Show Stats', self)
            popup_action.triggered.connect(lambda: SIGNALS.GUARD_POPUP.emit(db_index))
            menu.addAction(popup_action)
            delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Dismiss Guard', self)
            delete_action.triggered.connect(lambda: self.on_delete(db_index))
            menu.addAction(delete_action)
        menu.popup(event.globalPos())

    def on_delete(self, db_index: int):
        if DeleteDialog('guard').get() == 'delete':
            RULESET.GUARD_TYPE.read_keep(self.keep, db_index=db_index).delete()

    def on_delete_guard(self, db_index):
        for building_name in ('trait', 'combatant'):
            building = self.keep.buildings[building_name]
            df = building.df
            df.drop(df[df['_guard'] == db_index].index, inplace=True)
            building.reset_columns()
            building.save(modified_only=False)
        self.keep.buildings['guard'].save()

    def on_guard_popup(self, db_index: int):
        for child in QtWidgets.QApplication.topLevelWidgets():
            if not isinstance(child, GuardPopup):
                continue
            if child.guard.db_index == db_index:
                child.show()
                child.activateWindow()
                child.raise_()
                return
        try:
            viewer = GuardPopup(RULESET.GUARD_TYPE.read_keep(self.keep, db_index=db_index))
            viewer.show()
        except KeyError:
            raise KeyError('The guard you\'re trying to inspect was exiled from the keep.')

    def on_inspect_guard(self, db_index: int):
        for child in QtWidgets.QApplication.topLevelWidgets():
            if not isinstance(child, RULESET.GUARD_INSPECTOR):
                continue
            if child.guard.db_index == db_index:
                child.show()
                child.activateWindow()
                child.raise_()
                return
        inspector = RULESET.GUARD_INSPECTOR(RULESET.GUARD_TYPE.read_keep(self.keep, db_index=db_index))
        inspector.show()
