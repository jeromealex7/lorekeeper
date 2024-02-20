from collections import defaultdict
from typing import Iterable

from PySide2 import QtCore, QtGui, QtWidgets

from .icon import Icon
from src.model import Building
from src.settings import SIGNALS

LABEL_SIZES: dict[str, int] = defaultdict(int)
TAG_ICON_SIZE: int = 22


class TagFrame(QtWidgets.QFrame):
    TAGS_CHANGED = QtCore.Signal(tuple)

    def __init__(self, width: int, building: Building = None, tag_name: str = 'Tag',
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet('TagLabel {border-style: outset; background-color: #D0D0D0; border-width: 1px; '
                           'border-radius: 5px; border-color: black; padding: 0px;};')
        self.is_reloading = False
        self.content_width = width
        self.editable = bool(building)
        self._tags: set[str] = set()
        self.label_layout = QtWidgets.QVBoxLayout()
        self.label_layout.setContentsMargins(0, 0, 0, 0)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.label_layout)
        if self.editable:
            self.tag_edit = TagEdit(tag_name, building, self)
            layout.addWidget(self.tag_edit)
            self.tag_edit.SUBMIT.connect(self.add_tag)
        self.setLayout(layout)

    def add_tag(self, tag_name: str):
        self._tags.add(tag_name.strip())
        self.reload_layout()
        self.TAGS_CHANGED.emit(self.tags)

    def reload_layout(self):
        if self.is_reloading:
            return
        self.is_reloading = True
        while self.label_layout.count():
            row = self.label_layout.takeAt(0)
            while row.count():
                widget = row.takeAt(0).widget()
                widget.setParent(None)

        def new_row() -> QtWidgets.QHBoxLayout:
            r = QtWidgets.QHBoxLayout()
            r.setContentsMargins(0, 0, 0, 0)
            self.label_layout.addLayout(r, stretch=0)
            self.label_layout.setAlignment(QtCore.Qt.AlignLeft)
            return r
        row = new_row()
        current_width = 0
        for index, tag in enumerate(self.tags, start=1):
            widget = TagLabel(tag, self.editable)
            widget.SUBMIT.connect(self.remove_tag)
            current_width += widget.approximate_width + row.spacing()
            if current_width >= self.content_width - 2 * self.label_layout.spacing():
                row = new_row()
                current_width = 0
            row.addWidget(widget, stretch=0, alignment=QtCore.Qt.AlignLeft)
            row.setAlignment(QtCore.Qt.AlignLeft)
        self.is_reloading = False

    def remove_tag(self, tag: str):
        self._tags.remove(tag)
        self.reload_layout()
        self.TAGS_CHANGED.emit(self.tags)

    def set_tags(self, tags: Iterable[str]):
        self._tags = set(tags)
        self.reload_layout()

    @property
    def tags(self):
        return tuple(sorted(self._tags))


class TagLabel(QtWidgets.QFrame):
    SUBMIT = QtCore.Signal(str)

    def __init__(self, name: str, editable: bool = True):
        super().__init__()
        self.name_label = QtWidgets.QLabel(self)
        self.name_label.setText(name)
        self.name = name
        self.name_label.setStyleSheet('QLabel {font-family: Bahnschrift Condensed;font-size: 14pt;};')
        layout = QtWidgets.QHBoxLayout()
        if editable:
            self.delete_button = QtWidgets.QPushButton(Icon('minus'), '', self)
            self.delete_button.setFixedSize(TAG_ICON_SIZE, TAG_ICON_SIZE)
            layout.addWidget(self.delete_button)
            layout.setContentsMargins(2, 2, 5, 2)
            self.delete_button.clicked.connect(lambda: self.SUBMIT.emit(self.name))
        else:
            layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.name_label)
        layout.setSpacing(2)
        self.setLayout(layout)

    @property
    def approximate_width(self):
        return self.fontMetrics().boundingRect(self.name).width() + 12


class TagEdit(QtWidgets.QWidget):
    SUBMIT = QtCore.Signal(str)

    class Validator(QtGui.QValidator):
        def validate(self, string: str, pos: int = 0) -> tuple[QtGui.QValidator.State, str, int]:
            if all((char.isalnum() or char in ' -_()') for char in string):
                if len(string) < 2:
                    return QtGui.QValidator.Intermediate, string, pos
                return QtGui.QValidator.Acceptable, string, pos
            return QtGui.QValidator.Invalid, '', pos

    def __init__(self, tag_name: str = 'Tag', building: Building = None, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.building = building
        self.table_name = building.feature_type.TABLE_NAME
        self.validator = self.Validator()
        self.add_button = QtWidgets.QPushButton(Icon('plus'), '', self)
        self.add_button.setFixedSize(TAG_ICON_SIZE, TAG_ICON_SIZE)
        self.text_edit = QtWidgets.QLineEdit(self)
        self.text_edit.setMaximumWidth(150)
        self.text_edit.setMaxLength(30)
        self.text_edit.setValidator(self.validator)
        self.text_edit.setPlaceholderText(f'Add {tag_name}')

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.add_button)
        layout.addWidget(self.text_edit)
        layout.setAlignment(QtCore.Qt.AlignLeft)
        self.setLayout(layout)

        self.text_edit.textChanged.connect(self.reload_validation)
        self.text_edit.returnPressed.connect(self.submit)
        self.add_button.clicked.connect(self.submit)
        self.reload_validation()
        self.reload_completer(self.table_name)
        SIGNALS.FEATURE_COMMIT.connect(self.reload_completer)
        SIGNALS.FEATURE_DELETE.connect(self.reload_completer)

    def reload_completer(self, table_name: str, _: int = None):
        if table_name != self.table_name:
            return
        completer = QtWidgets.QCompleter(self.building.df['name'].unique().tolist())
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.text_edit.setCompleter(completer)

    def reload_validation(self):
        self.add_button.setEnabled(self.text_edit.hasAcceptableInput())

    def submit(self):
        if not self.text_edit.hasAcceptableInput():
            return
        self.SUBMIT.emit(self.text_edit.text())
        self.text_edit.setText('')
