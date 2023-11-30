import pandas as pd
from PySide2 import QtGui, QtWidgets

from src.rulesets import RULESET


class HealthBar(QtWidgets.QLabel):
    BORDER: int = 2

    def __init__(self, current: int, maximum: int, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.current = current
        self.maximum = maximum
        self.setStyleSheet(f'HealthBar{{background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 darkred, '
                           f'stop:0.5 rgb(159, 153, 77), stop:1 darkgreen);border: {self.BORDER}px solid black;}}')
        self.setFixedSize(300, 14)

        self.whiteout = QtWidgets.QLabel(self)
        self.whiteout.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.whiteout.setStyleSheet('QLabel{background-color: white;};')

        self.set_hit_points()

    def set_hit_points(self, current: int | None = None, maximum: int | None = None):
        if current is not None:
            self.current = current
        if maximum is not None:
            self.maximum = maximum
        try:
            percentage = self.current / self.maximum
        except ZeroDivisionError:
            percentage = 0
        width = int((self.width() - 2 * self.BORDER) * percentage)
        self.whiteout.setGeometry(self.BORDER + width,
                                  self.BORDER, self.width() - width - 2 * self.BORDER,
                                  self.height() - 2 * self.BORDER)


class EncounterBlock(QtWidgets.QFrame):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet('*{background-color: white; font-family: Roboto Slab; font-size: 12pt};'
                           'EncounterBlock{border: 2px solid black};')
        self.encounter_data = None
        self.setFrameStyle(QtWidgets.QFrame.Raised | QtWidgets.QFrame.Panel)
        self._layout = QtWidgets.QGridLayout()
        self._layout.setSpacing(5)
        self.setLayout(self._layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def add_series(self, series: pd.Series):
        if not series['show']:
            return
        token = QtWidgets.QToolButton(self)
        token.setFixedSize(50, 50)
        token.setIconSize(token.size())
        token.setIcon(QtGui.QIcon(series['token']))
        token.setAutoRaise(True)

        count = self.encounter_data['name'].value_counts()[series['name']]
        display_name = series['name'] if count == 1 else f'{series["name"]} {series["index"]}'
        name = QtWidgets.QLabel(display_name, self)
        name_font = {'font-family': 'Roboto Slab', 'font-size': '12pt'}
        health_bar = HealthBar(series['hit_points'], series['maximum_hit_points'], self)
        label = QtWidgets.QLabel(series['label'], self)
        label.setStyleSheet('QLabel{font-size: 10pt};')
        match series['type']:
            case 'player':
                name_font['font-weight'] = 'bold'
                health_bar.setVisible(False)
            case 'enemy':
                if series['hit_points'] <= RULESET.HIT_POINTS_CRITICAL:
                    name_font['color'] = 'gray'
                    name_font['text-decoration'] = 'line-through'
                    health_bar.setVisible(False)
                    label.setVisible(False)
                    token.setVisible(False)
            case 'effect':
                name_font['font-style'] = 'italic'
                health_bar.setVisible(False)
        name.setStyleSheet(f'QLabel{{{";".join(key + ": " + val for key, val in name_font.items())}}}')
        row = int(series.name)
        self._layout.addWidget(name, row, 1)
        self._layout.addWidget(health_bar, row, 2)
        self._layout.addWidget(token, row, 0)
        self._layout.addWidget(label, row, 3)

    def clear_layout(self, layout: QtWidgets.QLayout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.layout():
                self.clear_layout(item)
            if item.widget():
                item.widget().setParent(None)

    def set_data(self, data: pd.DataFrame):
        self.encounter_data = data
        self.clear_layout(self.layout())
        if data is None:
            return
        data.apply(self.add_series, axis=1)
