from PySide2 import QtCore, QtGui, QtWidgets


class HTMLHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, document: QtGui.QTextDocument):
        super().__init__(document)
        self.highlight_rules = []

        html_format = QtGui.QTextCharFormat()
        html_format.setForeground(QtGui.QColor(180, 180, 180))
        html_format.setBackground(QtGui.QColor(255, 255, 255))
        self.highlight_rules.append((r'(<.*?>)', html_format))

    def highlightBlock(self, text):
        for pattern, formatting in self.highlight_rules:
            regex = QtCore.QRegularExpression(pattern, QtCore.QRegularExpression.CaseInsensitiveOption)
            iterator = regex.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(1), match.capturedLength(1), formatting)


class Summary(QtWidgets.QPlainTextEdit):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.highlighter = HTMLHighlighter(self.document())
