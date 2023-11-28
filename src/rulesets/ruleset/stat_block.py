from PySide2 import QtGui, QtWidgets

from src.model import Guard
from src.settings import SIGNALS


class StatBlock(QtWidgets.QFrame):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.guard = guard
        SIGNALS.GUARD_COMMIT.connect(self._reload_guard)

    def clear(self, layout=None):
        if not layout:
            layout = self.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
            if child.layout():
                self.clear(child.layout())

    def _reload_guard(self, db_index: int):
        if self.guard.db_index != db_index:
            return
        self.reload_guard()

    def reload_guard(self):
        raise NotImplementedError

    def to_pixmap(self) -> QtGui.QPixmap:
        self.update()
        pixmap = QtGui.QPixmap(self.size())
        self.render(pixmap)
        return pixmap
