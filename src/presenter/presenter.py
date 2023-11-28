import os
import subprocess

import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from .encounter_block import EncounterBlock
from src.encounter import EncounterInspector
from src.model import Keep, Treasure
from src.settings import PATHS, SERVER, SIGNALS
from src.treasury import ClipboardAction
from src.widgets import BuildingWindow, Icon


class BackgroundFrame(QtWidgets.QFrame):
    pass


class BoxedImage(QtWidgets.QLabel):

    def __init__(self, db_index: int, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.db_index = db_index
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

    @classmethod
    def from_image(cls, image: QtGui.QImage, db_index: int, max_width: int, max_height: int,
                   parent: QtWidgets.QWidget | None = None):
        label = cls(db_index, parent)
        size = QtCore.QSize(min(image.width(), max_width) - 4, min(image.height(), max_height) - 4)
        image = image.scaled(size, QtCore.Qt.KeepAspectRatio)
        background = QtGui.QImage(image.size(), QtGui.QImage.Format_ARGB32)
        background.fill(QtGui.QColor('white').rgb())
        painter = QtGui.QPainter(background)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        painter.drawImage(0, 0, image)
        painter.end()
        label.resize(image.width(), image.height())
        label.setPixmap(QtGui.QPixmap.fromImage(background))
        label.setStyleSheet('QLabel{border: 2px solid black;background-colo: white};')
        return label


class Presenter(BuildingWindow):

    def __init__(self, keep: Keep, canvas: bool = False, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowIcon(Icon('flatscreen_tv'))
        self.setWindowTitle('Presenter - Lorekeeper')
        self.canvas = canvas
        self.keep = keep
        self.treasures: list[Treasure] = []
        self._background = 0
        self.resize_timer = QtCore.QTimer()
        self.resize_timer.timeout.connect(self.reload_images)
        self.export_timer = QtCore.QTimer()
        self.export_timer.timeout.connect(self.export)

        self.encounter_widget = EncounterBlock(self)
        self.frame_layout = QtWidgets.QHBoxLayout()
        self.image_layout = QtWidgets.QGridLayout()
        self.frame = BackgroundFrame(self)
        self.setCentralWidget(self.frame)
        self.setAcceptDrops(True)
        self.frame.setLayout(self.frame_layout)
        self.frame_layout.addWidget(self.encounter_widget, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft,
                                    stretch=0)
        self.frame_layout.addLayout(self.image_layout, stretch=1)
        self.frame.installEventFilter(self)
        SIGNALS.PRESENTER_ADD.connect(lambda db_index: self.set_image(db_index, add=True))
        SIGNALS.PRESENTER_SET.connect(lambda db_index: self.set_image(db_index, add=False))
        SIGNALS.PRESENTER_BACKGROUND.connect(lambda db_index: self.set_background(db_index))
        SIGNALS.PRESENTER_REMOVE.connect(lambda db_index: self.remove_image(db_index))
        SIGNALS.TREASURE_DELETE.connect(self.on_delete_treasure)
        SIGNALS.REFRESH.connect(self.on_refresh)
        self.on_refresh()

    def clear_layout(self, layout: QtWidgets.QLayout):
        if layout is None:
            return
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
            elif child.layout():
                self.clear_layout(child.layout())

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        treasure = Treasure.read_mime_data(self.keep, event.mimeData())
        if treasure and treasure.type_ == 'image':
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        treasure = Treasure.read_mime_data(self.keep, event.mimeData())
        db_index = treasure.commit()
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            if modifiers == QtCore.Qt.ShiftModifier:
                SIGNALS.PRESENTER_BACKGROUND.emit(db_index)
            else:
                SIGNALS.PRESENTER_SET.emit(db_index)
        else:
            SIGNALS.PRESENTER_ADD.emit(db_index)

    def eventFilter(self, watched: QtWidgets.QWidget, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.ContextMenu:
            menu = QtWidgets.QMenu(self)
            if watched == self.frame:
                if self._background:
                    clear_action = QtWidgets.QAction(Icon('garbage'), 'Clear Background', self)
                    clear_action.triggered.connect(lambda: SIGNALS.PRESENTER_BACKGROUND.emit(0))
                    inspect_action = QtWidgets.QAction(Icon('chest_open'), 'Inspect Background Treasure', self)
                    inspect_action.triggered.connect(lambda: SIGNALS.TREASURE_INSPECT.emit(self._background))
                    menu.addActions([clear_action, inspect_action])
            elif isinstance(watched, BoxedImage):
                clear_action = QtWidgets.QAction(Icon('garbage'), 'Remove Treasure', self)
                clear_action.triggered.connect(lambda: SIGNALS.PRESENTER_REMOVE.emit(watched.db_index))
                inspect_action = QtWidgets.QAction(Icon('chest_open'), 'Inspect Treasure', self)
                inspect_action.triggered.connect(lambda: SIGNALS.TREASURE_INSPECT.emit(watched.db_index))
                popup_action = QtWidgets.QAction(Icon('window'), 'Popup Treasure', self)
                popup_action.triggered.connect(lambda: SIGNALS.IMAGE_POPUP.emit(watched.db_index))
                menu.addActions([clear_action, inspect_action, popup_action])
            if clipboard_action := ClipboardAction(self.keep, format_filter='image', parent=menu):
                clipboard_background_action = ClipboardAction(self.keep, format_filter='image', parent=menu)
                clipboard_action.setText('Add Image from Clipboard')
                clipboard_background_action.setText('Set Background from Clipboard')
                menu.addSeparator()
                menu.addAction(clipboard_action)
                menu.addAction(clipboard_background_action)
                clipboard_action.triggered.connect(
                    lambda: SIGNALS.PRESENTER_ADD.emit(clipboard_action.treasure.db_index))
                clipboard_background_action.triggered.connect(
                    lambda: SIGNALS.PRESENTER_BACKGROUND.emit(clipboard_background_action.treasure.db_index))
            if menu.actions():
                menu.popup(event.globalPos())
                return True
        if watched == self.frame:
            if event.type() == QtCore.QEvent.DragEnter:
                self.on_drag_enter(event)
                return True
        return super().eventFilter(watched, event)

    def export(self):
        self.export_timer.stop()
        pixmap = QtGui.QPixmap(self.size())
        self.render(pixmap)
        target_path = PATHS['export'].joinpath(f'{self.keep.uuid}_{self.frame.width()}x{self.frame.height()}.png')
        target_posix = target_path.absolute().as_posix()
        pixmap.save(target_posix, 'JPEG', 100)
        process = subprocess.Popen(self.get_upload_command(target_posix), stdout=subprocess.PIPE, shell=True,
                                   stderr=subprocess.PIPE)


    @staticmethod
    def get_upload_command(source: str | os.PathLike[str]) -> list[str]:
        return list(map(str, (SERVER['pscp'], '-pw', SERVER['password'], '-P', SERVER['port'], '-l', SERVER['user'],
                              source, f'{SERVER["host"]}:{SERVER["target"]}')))

    def on_delete_treasure(self, db_index: int):
        self.treasures = [treasure for treasure in self.treasures if treasure.db_index != db_index]
        if self._background == db_index:
            self.set_background(0)
        self.reload_images()

    def on_refresh(self):
        encounter_data = None
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if not isinstance(widget, EncounterInspector):
                continue
            if not widget.presenter_action.isChecked():
                continue
            widget.sort()
            encounter_data = widget.get_data_frame()
            break
        self.set_encounter_data(encounter_data)
        if self.canvas:
            self.export_timer.start(1000)

    def reload_images(self):
        self.resize_timer.stop()
        self.clear_layout(self.image_layout)
        self.encounter_widget.updateGeometry()
        db_images = [(treasure.db_index, treasure.to_image()) for treasure in self.treasures]
        db_images.sort(key=lambda img: img[1].height() / img[1].width(), reverse=True)
        width, height = self.size().toTuple()
        spacing = self.layout().spacing()
        height -= 2 * spacing
        width -= 3 * spacing + self.encounter_widget.width()
        total = len(db_images)
        rows = 1 + (total >= 3)
        columns = (total + 1) // 2 + (total == 2)

        for index, (db_index, image) in enumerate(db_images, start=1):
            box_width = width // columns - (columns + 1) * spacing
            box_row = 1 + (index > (total % 2) + total // 2) - int(total == index == 2)
            if box_row == 1:
                box_column = index
            else:
                box_column = columns - index + (total % 2) + total // 2 + 1
            if total % 2 and index == 1:
                box_height = height - 2 * spacing
                row_span = rows
            else:
                box_height = height // rows - 2 * spacing
                row_span = 1
            boxed_image = BoxedImage.from_image(image, db_index=db_index, max_width=box_width, max_height=box_height)
            boxed_image.installEventFilter(self)
            self.image_layout.addWidget(boxed_image, box_row, box_column, row_span, 1, QtCore.Qt.AlignCenter)

    def remove_image(self, db_index: int):
        self.treasures = [treasure for treasure in self.treasures if treasure.db_index != db_index]
        self.reload_images()

    def resizeEvent(self, event: QtGui.QResizeEvent):
        if event.oldSize() == event.size():
            return
        self.resize_timer.start(400)

    def set_image(self, db_index: int, add: bool = False):
        treasure = Treasure.read_keep(self.keep, db_index)
        if not add:
            self.treasures.clear()
        if db_index in (t.db_index for t in self.treasures):
            return
        self.treasures.append(treasure)
        self.reload_images()

    def set_background(self, db_index: int):
        self._background = db_index
        if db_index:
            treasure = Treasure.read_keep(self.keep, db_index)
            background_image = f'url({treasure.path.absolute().as_posix()})'
        else:
            background_image = ''

        self.setStyleSheet(f'BackgroundFrame{{border-image: {background_image} 0 0 0 0 stretch stretch;'
                           f'font-family: Roboto Slab; font-size: 12pt;}}')

    def set_encounter_data(self, data: pd.DataFrame | None):
        self.encounter_widget.setHidden(data is None or data.empty)
        self.encounter_widget.set_data(data)
        self.reload_images()
