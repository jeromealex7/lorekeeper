from PySide2 import QtCore, QtGui


class SQLHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document: QtGui.QTextDocument):
        super().__init__(document)
        self.highlight_rules = []

        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setFontWeight(0)
        keyword_format.setForeground(QtGui.QColor(0, 0, 255))

        self.highlight_rules.append((r'\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|AND|OR|GROUP BY|LEFT JOIN|RIGHT JOIN|'
                                     r'JOIN|CREATE|ALTER|DROP|ORDER BY|WITH|AS|ON|LIKE)\b',
                                     keyword_format))

    def highlightBlock(self, text):
        for pattern, formatting in self.highlight_rules:
            regex = QtCore.QRegularExpression(pattern, QtCore.QRegularExpression.CaseInsensitiveOption)
            iterator = regex.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(1), match.capturedLength(1), formatting)
