from PySide2 import QtCore, QtGui, QtWidgets

from .treasure_menu import TreasureMenu
from src.model import Treasure
from src.settings import SIGNALS, SHORTCUTS
from src.widgets import Icon, Preview


class ImagePopup(QtWidgets.QMainWindow):

    def __init__(self, treasure: Treasure, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        SHORTCUTS.activate_shortcuts(self)
        self.drag = None
        self.treasure = treasure
        self.setWindowTitle(treasure['name'])
        self.setWindowIcon(Icon(treasure.icon_name))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint
                            & ~QtCore.Qt.WindowMinimizeButtonHint)
        self.label = QtWidgets.QLabel(self)
        self.label.installEventFilter(self)
        self.setCentralWidget(self.label)
        self.resize_timer = QtCore.QTimer(self)

        SIGNALS.TREASURE_DELETE.connect(self.on_delete)
        SIGNALS.TREASURE_COMMIT.connect(self.on_commit)

        screen_size = QtWidgets.QApplication.primaryScreen().size()
        self.max_height = int(screen_size.height() * .8)
        self.max_width = int(screen_size.width() * .8)
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.resize(800, 600)
        self.update_image()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        if not self.treasure.db_index:
            return
        menu = TreasureMenu(self.treasure, self, popup=False)
        menu.popup(event.globalPos())

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Escape:
            self.deleteLater()

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.label:
            if event.type() == QtCore.QEvent.MouseButtonPress and event.buttons() == QtCore.Qt.LeftButton:
                self.on_preview_drag()
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def on_preview_drag(self):
        if not self.treasure.db_index:
            return
        self.drag = QtGui.QDrag(self)
        self.drag.setMimeData(self.treasure.to_mime_data())
        self.drag.setPixmap(Preview(self.treasure, self.parent()).to_pixmap())
        self.drag.start()

    def on_commit(self, db_index: int):
        if db_index != self.treasure.db_index:
            return
        self.treasure = Treasure.read_keep(self.treasure.keep, db_index)
        self.setWindowTitle(self.treasure['name'])

    def on_delete(self, db_index: int):
        if db_index != self.treasure.db_index:
            return
        self.deleteLater()

    def resizeEvent(self, event: QtCore.QEvent.Resize):
        if event.oldSize() != event.size():
            self.resize_timer.singleShot(300, self.update_image)

    def update_image(self):
        image = self.treasure.to_image()
        scaled_image = image.scaled(min(self.max_width, image.width(), self.width()),
                                    min(self.max_height * .8, image.height(), self.height()),
                                    QtGui.Qt.KeepAspectRatio)
        self.label.setPixmap(QtGui.QPixmap(scaled_image))
        self.resize(self.label.sizeHint())
        self.setMaximumSize(image.size())
