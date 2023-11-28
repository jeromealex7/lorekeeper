from .icon import Icon

import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
import PySide2.QtCore as QtCore


class _Text(QtWidgets.QTextEdit):

    def insertFromMimeData(self, source: QtCore.QMimeData):
        mime_data = QtCore.QMimeData()
        mime_data.setText(source.text())
        super().insertFromMimeData(mime_data)


class Text(QtWidgets.QWidget):
    FONT_SIZES = (8, 9, 10, 11, 12, 14, 16, 20, 24, 28, 40)
    textChanged = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)

        self.editor = _Text()
        self.editor.setAutoFormatting(QtWidgets.QTextEdit.AutoAll)
        self.editor.selectionChanged.connect(self.update_format)

        self.toolbar = QtWidgets.QToolBar()
        self.font_box = QtWidgets.QFontComboBox()
        self.font_box.setEditable(False)
        self.font_box.currentFontChanged.connect(self.set_font)
        self.size_box = QtWidgets.QComboBox()
        self.size_box.setFixedWidth(50)
        self.size_box.addItems(list(map(str, self.FONT_SIZES)))
        self.size_box.setEditable(False)
        self.size_box.currentIndexChanged[str].connect(lambda size: self.editor.setFontPointSize(float(size)))
        self.bold_action = QtWidgets.QAction(Icon('font_style_bold'), 'Bold', self)
        self.bold_action.setStatusTip('Bold')
        self.bold_action.setShortcut(QtGui.QKeySequence.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.toggled.connect(lambda checked: self.editor.setFontWeight(QtGui.QFont.Bold
                                                                                   if checked else QtGui.QFont.Normal))
        self.italic_action = QtWidgets.QAction(Icon('font_style_italics'), 'Italic', self)
        self.italic_action.setStatusTip('Italic')
        self.italic_action.setShortcut(QtGui.QKeySequence.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.toggled.connect(lambda checked: self.editor.setFontItalic(checked))
        self.underline_action = QtWidgets.QAction(Icon('font_style_underline'), 'Underline', self)
        self.underline_action.setStatusTip('Underline')
        self.underline_action.setShortcut(QtGui.QKeySequence.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.toggled.connect(lambda checked: self.editor.setFontUnderline(checked))
        self.align_left_action = QtWidgets.QAction(Icon('text_align_left'), 'Align Left', self)
        self.align_left_action.setStatusTip('Align Left')
        self.align_left_action.setCheckable(True)
        self.align_left_action.triggered.connect(lambda: self.editor.setAlignment(QtCore.Qt.AlignLeft))
        self.align_left_action.triggered.connect(lambda: self.update_format())
        self.align_right_action = QtWidgets.QAction(Icon('text_align_right'), 'Align Right', self)
        self.align_right_action.setStatusTip('Align Left')
        self.align_right_action.setCheckable(True)
        self.align_right_action.triggered.connect(lambda: self.editor.setAlignment(QtCore.Qt.AlignRight))
        self.align_right_action.triggered.connect(lambda: self.update_format())
        self.align_center_action = QtWidgets.QAction(Icon('text_align_center'), 'Align Center', self)
        self.align_center_action.setStatusTip('Align Center')
        self.align_center_action.setCheckable(True)
        self.align_center_action.triggered.connect(lambda: self.editor.setAlignment(QtCore.Qt.AlignCenter))
        self.align_center_action.triggered.connect(lambda: self.update_format())
        self.align_justify_action = QtWidgets.QAction(Icon('text_align_justified'), 'Align Justify', self)
        self.align_justify_action.setStatusTip('Align Justify')
        self.align_justify_action.setCheckable(True)
        self.align_justify_action.triggered.connect(lambda: self.editor.setAlignment(QtCore.Qt.AlignJustify))
        self.align_justify_action.triggered.connect(lambda: self.update_format())
        self.toolbar.addWidget(self.font_box)
        self.toolbar.addWidget(self.size_box)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.bold_action)
        self.toolbar.addAction(self.italic_action)
        self.toolbar.addAction(self.underline_action)
        self.toolbar.addAction(self.align_left_action)
        self.toolbar.addAction(self.align_right_action)
        self.toolbar.addAction(self.align_center_action)
        self.toolbar.addAction(self.align_justify_action)
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.editor.setAcceptRichText(True)

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.editor)
        self.editor.setFont(QtGui.QFont('Roboto Slab', 10))
        self.setLayout(layout)
        self.update_format()
        self.editor.textChanged.connect(self.textChanged.emit)

    def block_format_signals(self, block: bool = True):
        for item in self.toolbar.actions() + [self.font_box, self.size_box]:
            item.blockSignals(block)

    def get_html(self) -> str:
        return self.editor.toHtml()

    def set_font(self, font):
        text_format = QtGui.QTextCharFormat()
        text_format.setFontFamily(font.family())
        self.editor.textCursor().setCharFormat(text_format)

    def set_html(self, text: str):
        self.editor.setHtml(text)

    def show_toolbar(self, show: bool = True):
        self.toolbar.setHidden(not show)

    def update_format(self):

        self.block_format_signals(True)
        self.font_box.setCurrentFont(self.editor.currentFont())
        self.size_box.setCurrentText(str(int(self.editor.currentFont().pointSize())))

        self.italic_action.setChecked(self.editor.fontItalic())
        self.align_center_action.setChecked(self.editor.alignment() == QtCore.Qt.AlignCenter)
        self.align_justify_action.setChecked(self.editor.alignment() == QtCore.Qt.AlignJustify)
        self.align_left_action.setChecked(self.editor.alignment() == QtCore.Qt.AlignLeft)
        self.align_right_action.setChecked(self.editor.alignment() == QtCore.Qt.AlignRight)
        self.bold_action.setChecked(self.editor.fontWeight() == QtGui.QFont.Bold)
        self.underline_action.setChecked(self.editor.fontUnderline())

        self.block_format_signals(False)
