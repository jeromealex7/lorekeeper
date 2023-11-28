from typing import Sequence

from PySide2 import QtCore, QtGui


class AbilityHighlighter(QtGui.QSyntaxHighlighter):

    def __init__(self, document: QtGui.QTextDocument, keywords: Sequence[str], dialog: bool = False):
        super().__init__(document)
        self.highlight_rules = []
        self.dialog = dialog

        keyword_list = list(keywords)
        allowed_format = QtGui.QTextCharFormat()
        allowed_format.setForeground(QtGui.QColor(0, 0, 255))
        allowed_format.setBackground(QtGui.QColor(255, 255, 255))
        disallowed_format = QtGui.QTextCharFormat()
        disallowed_format.setForeground(QtGui.QColor(0, 0, 0))
        disallowed_format.setBackground(QtGui.QColor(255, 0, 0))
        html_format = QtGui.QTextCharFormat()
        html_format.setForeground(QtGui.QColor(180, 180, 180))
        html_format.setBackground(QtGui.QColor(255, 255, 255))
        self.highlight_rules.append((fr'(<.*?>)', html_format))
        self.highlight_rules.append((r'(\[[^\]]*?/[^\]]*?/[^\]]*?\])', disallowed_format))
        if dialog:
            keyword_list.append(r'{.*?}')
            dialog_format = QtGui.QTextCharFormat()
            dialog_format.setForeground(QtGui.QColor(0, 140, 0))
            dialog_format.setBackground(QtGui.QColor(255, 255, 255))
            self.highlight_rules.append((r'({.*?})', dialog_format))
        self.highlight_rules.append((fr'(\[(?:(?:{"|".join("(?<![a-zA-Z0-9 ])" + keyword for keyword in keyword_list)}|\d+|[+-](?=\s*[\w{{}}]))*|[\w\s]*?\/[\w\s]*?\/[\w\s]*?)\])',
                                     allowed_format))

    def highlightBlock(self, text):
        for pattern, formatting in self.highlight_rules:
            regex = QtCore.QRegularExpression(pattern, QtCore.QRegularExpression.CaseInsensitiveOption)
            iterator = regex.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(1), match.capturedLength(1), formatting)
