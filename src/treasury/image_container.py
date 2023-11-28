import numbers

from PySide2 import QtCore, QtGui, QtWidgets

from .image_popup import ImagePopup
from .import_tools import ClipboardAction, OpenTreasureDialog
from .treasure_menu import TreasureMenu
from src.model import Keep, Treasure
from src.settings import SIGNALS
from src.widgets import Icon, Preview


class ImageContainer(QtWidgets.QLabel):
    SIZE = 300
    TREASURE_CHANGED = QtCore.Signal()

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.setAcceptDrops(True)
        self.setFont(QtGui.QFont('Arial Black', 16))
        self.setStyleSheet('ImageContainer{border-size: 1pt; border-style: solid; border-color: black;};')
        self.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.treasure = None
        self.drop_object = None
        self.drag = None
        self.clipboard = None
        self._image = None
        SIGNALS.FEATURE_COMMIT.connect(self.on_feature_commit)
        SIGNALS.FEATURE_DELETE.connect(self.on_feature_delete)

    def clear_content(self):
        self.treasure = None
        self.image = None

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        if self.treasure:
            if self.treasure.db_index:
                menu = TreasureMenu(self.treasure, self)
                menu.addSeparator()
            else:
                menu = QtWidgets.QMenu(self)
                add_action = QtWidgets.QAction(Icon('chest'), 'Add to Treasury', self)
                add_action.triggered.connect(lambda: self.treasure.commit())
                popup_action = QtWidgets.QAction(Icon('window'), 'Preview', self)
                popup_action.triggered.connect(lambda: ImagePopup(self.treasure, self).show())
                menu.addAction(add_action)
                menu.addAction(popup_action)
            clear_action = QtWidgets.QAction(Icon('garbage'), 'Clear Image', self)
            menu.addAction(clear_action)
            clear_action.triggered.connect(self.clear_content)
        else:
            menu = QtWidgets.QMenu(self)

        def clipboard_exec():
            self.set_content(clipboard_action.treasure)
        if clipboard_action := ClipboardAction(self.keep, 'image', False, menu):
            menu.addAction(clipboard_action)
            clipboard_action.triggered.connect(clipboard_exec)
        open_action = QtWidgets.QAction(Icon('folder_open'), 'Open File ...', self)
        open_action.triggered.connect(self.on_open)
        menu.addAction(open_action)
        menu.popup(event.globalPos())

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.source() == self:
            return
        drag_object = Treasure.read_mime_data(self.keep, event.mimeData())
        if drag_object and drag_object['type'] == 'image':
            event.acceptProposedAction()
            self.drop_object = drag_object
        else:
            self.drop_object = None

    def dropEvent(self, event: QtGui.QDropEvent):
        if not self.drop_object:
            return
        self.treasure = self.drop_object
        self.drop_object = None
        self.image = self.treasure.to_image()

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, value):
        self._image = value
        self.update_image()
        self.TREASURE_CHANGED.emit()

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        if self.treasure:
            ImagePopup(self.treasure, self).show()
            return
        self.on_open()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if not event.buttons() == QtGui.Qt.LeftButton:
            return
        if self.treasure and self.treasure.db_index:
            self.drag = QtGui.QDrag(self)
            self.drag.setPixmap(Preview(self.treasure).to_pixmap())
            self.drag.setMimeData(self.treasure.to_mime_data())
            self.drag.start()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.drag = None

    def on_feature_commit(self, table_name: str, db_index: int):
        if not self.treasure or self.treasure.TABLE_NAME != table_name or self.treasure.db_index != db_index:
            return
        self.treasure.reload()

    def on_feature_delete(self, table_name: str, db_index: int):
        if not self.treasure or self.treasure.TABLE_NAME != table_name or self.treasure.db_index != db_index:
            return
        self.set_content(None)

    def on_open(self):
        dialog = OpenTreasureDialog(self.keep, 'image', self)
        if treasure := dialog.get():
            self.set_content(treasure)

    def set_content(self, treasure: Treasure | int | None):
        if not treasure:
            self.clear_content()
            return
        if isinstance(treasure, numbers.Integral):
            try:
                treasure = Treasure.read_keep(self.keep, db_index=int(treasure))
            except (KeyError, ValueError):
                self.clear_content()
                return
        self.treasure = treasure
        self.setWindowTitle(treasure['name'])
        self.image = treasure.to_image()

    def update_image(self):
        if not self.image:
            self.setPixmap(QtGui.QPixmap())
            self.setText('- No Image -')
            self.setMinimumSize(200, 100)
            return
        self.setPixmap(QtGui.QPixmap(self.image.scaled(min(self.SIZE, self.image.width()),
                                                       min(self.SIZE, self.image.height()), QtGui.Qt.KeepAspectRatio)))
        self.setMinimumSize(self.sizeHint())
        self.setText('')
