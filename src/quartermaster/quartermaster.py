import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from .sql_highlighter import SQLHighlighter
from src.model import Keep
from src.widgets import BuildingWindow, Error, Icon


class Quartermaster(BuildingWindow):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.setWindowTitle('Quartermaster - Lorekeeper')
        self.setWindowIcon(Icon('warehouse'))
        self.frame = QtWidgets.QFrame(self)
        self.setCentralWidget(self.frame)

        layout = QtWidgets.QHBoxLayout()
        splitter = QtWidgets.QSplitter()
        splitter.setHandleWidth(1)
        splitter.setStyleSheet('QSplitter::handle {background-color: #cccccc; border: 1px solid #999999; width 0px;};')
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter)
        self.query_edit = QtWidgets.QTextEdit()
        self.query_edit.setStyleSheet('QTextEdit{font-family: Consolas; font-size: 12pt};')
        self.resize(800, 500)
        self.query_edit.setTabStopWidth(3)
        self.highlighter = SQLHighlighter(self.query_edit.document())
        self.result = QtWidgets.QTableWidget()
        splitter.addWidget(self.query_edit)
        splitter.addWidget(self.result)

        self.frame.setLayout(layout)

        menu_bar = QtWidgets.QMenuBar(self)
        query_menu = QtWidgets.QMenu('Q&uery', self)
        run_action = QtWidgets.QAction(Icon('media_play'), 'Execute Query', self)
        run_action.setShortcut(QtGui.QKeySequence('F8'))
        run_action.triggered.connect(self.execute)
        close_action = QtWidgets.QAction(Icon('door_exit'), 'Exit', self)
        close_action.triggered.connect(self.close)
        query_menu.addAction(run_action)
        query_menu.addSeparator()
        query_menu.addAction(close_action)
        menu_bar.addMenu(query_menu)
        self.setMenuBar(menu_bar)

    def execute(self):
        query = self.query_edit.toPlainText()
        try:
            result = pd.read_sql(query, self.keep.connection).copy()
        except TypeError:
            return
        except Exception as err:
            Error.read_exception(err, self).exec()
            return
        self.result.clear()
        self.result.setRowCount(0)
        self.result.setColumnCount(len(result.columns))

        def _insert(series: pd.Series):
            row = self.result.rowCount()
            self.result.insertRow(row)
            for column, (key, val) in enumerate(series.items()):
                item = QtWidgets.QTableWidgetItem()
                self.result.setItem(row, column, item)
                item.setText(str(val))
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.result.setHorizontalHeaderLabels(list(result.head()))
        self.result.verticalHeader().setVisible(False)
        result.apply(_insert, axis=1)
        self.result.resizeColumnsToContents()
        self.result.resizeRowsToContents()
