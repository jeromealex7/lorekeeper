from PySide2 import QtCore, QtGui, QtWidgets

from .stat_area import StatArea
from src.model import Guard
from src.settings import SHORTCUTS, SIGNALS
from src.widgets import Icon, Preview


class GuardPopup(QtWidgets.QMainWindow):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        SHORTCUTS.activate_shortcuts(self)
        self.drag = None
        self.guard = guard
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint
                            & ~QtCore.Qt.WindowMinimizeButtonHint)
        self.area = StatArea(guard, self)
        self.area.installEventFilter(self)
        self.setCentralWidget(self.area)

        SIGNALS.GUARD_DELETE.connect(self.on_delete)
        SIGNALS.GUARD_COMMIT.connect(self.reload_guard)
        self.reload_guard(guard.db_index)
        self.area.fit()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Escape:
            self.deleteLater()

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.area:
            if event.type() == QtCore.QEvent.MouseButtonPress and event.buttons() == QtCore.Qt.LeftButton:
                self.on_preview_drag()
                event.accept()
                return True
            if event.type() == QtCore.QEvent.Resize:
                self.area.update()
                self.resize(self.area.size())
        return super().eventFilter(watched, event)

    def on_delete(self, db_index: int):
        if db_index != self.guard.db_index:
            return
        self.deleteLater()

    def on_preview_drag(self):
        self.drag = QtGui.QDrag(self)
        self.drag.setMimeData(self.guard.to_mime_data())
        self.drag.setPixmap(Preview(self.guard, self.parent()).to_pixmap())
        self.drag.start()

    def reload_guard(self, db_index: int):
        if db_index != self.guard.db_index:
            return
        self.setWindowTitle(self.guard['name'])
        self.setWindowIcon(Icon(self.guard.icon_name))
