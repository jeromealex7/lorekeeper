from PySide2 import QtCore, QtGui, QtWidgets

from .icon import Icon


class SuggestionEdit(QtWidgets.QLineEdit):
    CHANGED = QtCore.Signal(str)
    SUGGESTION_LENGTH = 40

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        default = ''
        self._suggestion = default
        self.set_editable(False)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)
        if self.isReadOnly():
            edit_action = QtWidgets.QAction(Icon('pencil'), 'Edit Text', self)
            edit_action.triggered.connect(lambda: self.set_editable(True))
            menu.addAction(edit_action)
        else:
            suggestion = self.suggestion if len(self.suggestion) <= self.SUGGESTION_LENGTH \
                else self.suggestion[:self.SUGGESTION_LENGTH - 3] + '...'
            default_action = QtWidgets.QAction(Icon('clipboard_checks'), f'Use suggestion: "{suggestion}"', self)
            default_action.triggered.connect(lambda: self.set_editable(False))
            menu.addAction(default_action)
        menu.popup(event.globalPos())

    def get(self) -> str:
        return self._suggestion if self.isReadOnly() else self.text()

    @property
    def is_suggested(self) -> bool:
        return self.isReadOnly()

    @property
    def is_suggestion(self) -> bool:
        return self.text() == self.suggestion

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Escape:
            self.set_editable(False)
            return
        super().keyPressEvent(event)

    def set_editable(self, editable: bool = True):
        self.setReadOnly(not editable)
        if not editable:
            self.setText(self.suggestion)

        font_style = 'normal' if editable else 'italic'
        background_color = 'white' if editable else '#f2f2f2'
        self.setStyleSheet(f'SuggestionEdit{{font-style: {font_style}; background-color: {background_color}}};')

    def set_suggestion(self, value: str):
        self._suggestion = value
        if self.isReadOnly():
            self.setText(value)

    def set(self, value: str):
        self.setText(value)
        self.set_editable(not self.is_suggestion)

    @property
    def suggestion(self):
        return self._suggestion
