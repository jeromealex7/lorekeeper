from functools import partial
from typing import Type

from PySide2 import QtCore, QtGui, QtWidgets

from .delete_dialog import DeleteDialog
from src.model import Feature, Keep
from src.settings import SIGNALS
from .preview import Preview


class BuildingTable(QtWidgets.QTableWidget):
    SEARCH = QtCore.Signal()

    def __init__(self, keep: Keep, feature_type: Type[Feature], parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep

        self.display_string = ''
        self.df = keep.buildings[feature_type.TABLE_NAME].df
        self.drag = None
        self.feature_type = feature_type
        self.feature_preview = None
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.on_header_menu)
        self.setDragEnabled(True)
        self.setMouseTracking(True)
        self.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.setSelectionMode(QtWidgets.QTableWidget.SingleSelection)
        self.setSortingEnabled(True)
        self.viewport().installEventFilter(self)
        self.viewport().setMouseTracking(True)

        SIGNALS.FEATURE_COMMIT.connect(self.on_feature_commit)
        SIGNALS.FEATURE_DELETE.connect(self.on_feature_delete)

    def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if source == self.viewport():
            if event.type() in (QtCore.QEvent.DragEnter, QtCore.QEvent.DragMove):
                if self.dragEnterEvent(event):
                    event.accept()
                    return True
            if event.type() == QtCore.QEvent.Drop:
                self.dropEvent(event)
                event.accept()
                return True
        if source == self.feature_preview:
            if event.type() in (QtCore.QEvent.MouseMove, QtCore.QEvent.Enter):
                self.event(event)
                return True
        return super().eventFilter(source, event)

    def get_db_index(self, row: int) -> int | None:
        try:
            return self.item(row, 0).data(QtCore.Qt.UserRole)
        except AttributeError:
            return None

    def get_row(self, db_index: int) -> int | None:
        for row in range(self.rowCount()):
            if self.get_db_index(row) == db_index:
                return row
        return None

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        selection = self.selectedIndexes()
        if selection:
            row = selection[0].row()
            if (db_index := self.get_db_index(row)) is not None:
                if event.key() == QtGui.Qt.Key_Delete:
                    if DeleteDialog(self.feature_type.__name__, self).get() == 'delete':
                        self.feature_type.read_keep(self.keep, db_index=db_index).delete()
                elif event.key() in (QtGui.Qt.Key_Enter, QtGui.Qt.Key_Return):
                    SIGNALS.FEATURE_INSPECT.emit(self.feature_type.TABLE_NAME, db_index)
        super().keyPressEvent(event)

    def leaveEvent(self, event: QtCore.QEvent):
        if self.feature_preview:
            self.feature_preview.deleteLater()

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        if event.button() != QtGui.Qt.LeftButton:
            return
        db_index = self.get_db_index(self.rowAt(event.y()))
        if db_index is None:
            return
        SIGNALS.FEATURE_INSPECT.emit(self.feature_type.TABLE_NAME, db_index)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        db_index = self.get_db_index(self.rowAt(event.y()))
        if not db_index:
            if self.feature_preview:
                self.feature_preview.deleteLater()
            return
        if self.feature_preview:
            if self.feature_preview.db_index == db_index:
                self.feature_preview.move(event.globalPos() + QtCore.QPoint(10, 10))
                return
            self.feature_preview.deleteLater()
        if self.feature_type.TAG_TABLE_NAME:
            self.feature_preview = Preview(self.feature_type.read_keep(self.keep, db_index))
            self.feature_preview.show()
            self.feature_preview.move(event.globalPos() + QtCore.QPoint(10, 10))

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super().mousePressEvent(event)
        db_index = self.get_db_index(self.rowAt(event.y()))
        if not db_index or event.button() == QtCore.Qt.RightButton:
            event.ignore()
            super().mousePressEvent(event)
            return False
        feature = self.feature_type.read_keep(self.keep, db_index=db_index)
        self.drag = QtGui.QDrag(self)
        self.drag.setMimeData(feature.to_mime_data())
        if self.feature_type.TAG_TABLE_NAME:
            preview = Preview(feature)
            self.drag.setPixmap(preview.to_pixmap())
        self.drag.start()

    def mouseReleaseEvent(self, _):
        self.drag = None

    def on_delete(self, db_index: int):
        if DeleteDialog(self.feature_type.__name__, self).get() == 'cancel':
            return
        self.feature_type.read_keep(self.keep, db_index=db_index).delete()

    def on_feature_commit(self, table_name: str, db_index: int):
        if table_name != self.feature_type.TABLE_NAME:
            return
        row = self.get_row(db_index)
        if row is None:
            row = self.rowCount()
            self.insertRow(row)
        try:
            self.load_series(self.df.loc[db_index], row)
            self.resizeColumnsToContents()
            self.resizeRowToContents(row)
        except KeyError:
            pass

    def on_feature_delete(self, table_name: str, db_index: int):
        if table_name != self.feature_type.TABLE_NAME:
            return
        self.removeRow(self.get_row(db_index))

    def on_header_menu(self, point: QtCore.QPoint):
        menu = QtWidgets.QMenu(self)
        for index in range(1, self.columnCount()):
            action = QtWidgets.QAction(self.horizontalHeaderItem(index).text(), self)
            action.setCheckable(True)
            action.setChecked(not self.isColumnHidden(index))
            action.toggled.connect(partial(lambda i, state: self.setColumnHidden(i, not state), index))
            menu.addAction(action)
        menu.popup(self.mapToGlobal(point))
