from PySide2 import QtCore, QtGui, QtWidgets

from src.model import Book, Encounter, Minstrel, Treasure
from src.rulesets import RULESET


class Preview(QtWidgets.QMainWindow):
    SIZE = (400, 400)

    def __init__(self, feature: Book | Encounter | Minstrel | Treasure, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent, QtGui.Qt.ToolTip)
        self.label = QtWidgets.QLabel()
        self.frame = QtWidgets.QFrame()
        self.setStyleSheet('Preview{border: 2px solid black};')
        self.setCentralWidget(self.frame)
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setHtml(feature.get_html())
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet('QTextEdit{font-family: Roboto Slab; font-size: 10pt;};')
        self.text_edit.setFixedWidth(300)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.addWidget(self.label, QtCore.Qt.AlignCenter)
        additional_layout = QtWidgets.QVBoxLayout()
        if feature.get_plain_text():
            additional_layout.addWidget(self.text_edit)
        layout.addLayout(additional_layout)
        self.frame.setLayout(layout)

        self._feature = None
        self._image = None
        self.feature = feature

    def __bool__(self):
        try:
            return self.isWidgetType()
        except RuntimeError:
            return False

    @property
    def db_index(self):
        if not self.feature:
            return None
        return self.feature.db_index

    def enterEvent(self, _):
        self.deleteLater()

    @property
    def feature(self):
        return self._feature

    @feature.setter
    def feature(self, value):
        self._feature = value
        if self._feature:
            match self._feature.TABLE_NAME:
                case 'encounter':
                    self._image = RULESET.get_encounter_gage().preview(self._feature)
                case 'guard':
                    stat_block = RULESET.get_stat_block(self._feature)
                    stat_block.resize(stat_block.minimumWidth(), self.screen().size().height())
                    stat_block.update()
                    self._image = stat_block.to_pixmap()
                case _:
                    self._image = self._feature.to_image()
                    if self._image.width() > self.SIZE[0] or self._image.height() > self.SIZE[1]:
                        self._image = self._image.scaled(*self.SIZE, QtGui.Qt.KeepAspectRatio)
                    self.label.setFixedSize(self._image.size())
            self.label.setPixmap(QtGui.QPixmap(self._image))

        else:
            self._image = None
            self.label.setPixmap(QtGui.QPixmap())

    @property
    def image(self):
        return self._image

    def to_pixmap(self) -> QtGui.QPixmap:
        pixmap = QtGui.QPixmap(self.size())
        self.render(pixmap)
        return pixmap
