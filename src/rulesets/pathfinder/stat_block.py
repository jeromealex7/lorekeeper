import json

from PySide2 import QtCore, QtGui, QtWidgets

from src.model import Guard
from src.rulesets.ruleset import StatBlock as BasicStatBlock
from src.settings import PATHS
from src.widgets import TagFrame


class AbilityLabel(QtWidgets.QHBoxLayout):

    def __init__(self, ability: dict, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.guard = guard
        self.setContentsMargins(0, 0, 0, 0)
        self.ability = ability
        self.setSpacing(2)
        title = QtWidgets.QLabel(f'<b>{ability["name"]}</b>')
        symbol = self.get_symbol_widget()
        text = QtWidgets.QLabel(self.guard.parse(ability["text"]))
        text.setWordWrap(True)
        self.addWidget(title, stretch=0, alignment=QtCore.Qt.AlignTop)
        if symbol:
            self.addWidget(symbol, stretch=0, alignment=QtCore.Qt.AlignTop)
        self.addWidget(text, stretch=1, alignment=QtCore.Qt.AlignTop)

    def get_symbol_widget(self) -> QtWidgets.QWidget | None:
        label = QtWidgets.QLabel()
        match self.ability['actions']:
            case '1 action':
                icon = QtGui.QPixmap(PATHS['images'].joinpath('pathfinder/1action.png').as_posix()).scaledToHeight(
                    label.sizeHint().height())
                label.setPixmap(icon)
            case '2 actions':
                icon = QtGui.QPixmap(PATHS['images'].joinpath('pathfinder/2actions.png').as_posix()).scaledToHeight(
                    label.sizeHint().height())
                label.setPixmap(icon)
            case '3 actions':
                icon = QtGui.QPixmap(PATHS['images'].joinpath('pathfinder/3actions.png').as_posix()).scaledToHeight(
                    label.sizeHint().height())
                label.setPixmap(icon)
            case 'reaction':
                icon = QtGui.QPixmap(PATHS['images'].joinpath('pathfinder/reaction.png').as_posix()).scaledToHeight(
                    label.sizeHint().height())
                label.setPixmap(icon)
            case 'free action':
                icon = QtGui.QPixmap(PATHS['images'].joinpath('pathfinder/freeaction.png').as_posix()).scaledToHeight(
                    label.sizeHint().height())
                label.setPixmap(icon)
            case actions if actions:
                label.setText(f'({actions})')
            case _:
                return None
        return label


class Line(QtWidgets.QFrame):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.resize(1, 1)


class StatBlock(BasicStatBlock):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(guard, parent)
        self._layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._layout)
        self.guard = guard
        self.keep = guard.keep
        self.setStyleSheet('*{font-size: 8pt; background-color: white; font-family: Roboto Slab};')
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(400)
        self.resize(400, 1)
        self._layout.setSpacing(0)
        self.reload_guard()

    def reload_guard(self):
        self.clear()
        self.guard.reload()
        header = QtWidgets.QHBoxLayout()
        name_label = QtWidgets.QLabel(self.guard['name'], self)
        level_label = QtWidgets.QLabel(f'Creature {self.guard["level"]}', self)
        name_label.setStyleSheet('QLabel{font-size: 14pt;}')
        level_label.setStyleSheet(name_label.styleSheet())
        header.addWidget(name_label, alignment=QtCore.Qt.AlignLeft)
        header.addWidget(level_label, alignment=QtCore.Qt.AlignRight)
        self._layout.addLayout(header)
        self._layout.addWidget(Line())
        tag_frame = TagFrame(300)
        tag_frame.setContentsMargins(0, 0, 0, 0)
        tag_frame.layout().setSpacing(0)
        tags = (self.guard['size'], self.guard['type'], *filter(None, self.guard['traits'].split(', ')))
        tag_frame.set_tags(tags)
        self._layout.addWidget(tag_frame)
        tag_frame.setStyleSheet('QLabel{font-size: 9pt; border-style: outset; background-color: rgb(200,200,200);'
                                'border-width: 2px;border-color: black;};')
        if info_text := self.guard['info']:
            info = QtWidgets.QLabel(info_text, self)
            self._layout.addWidget(info)
        perception_text = f'<b>Perception</b> {self.guard["perception"]:+d}'
        if senses := self.guard['senses']:
            perception_text += f'; {senses}'
        perception_label = QtWidgets.QLabel(perception_text, self)
        self._layout.addWidget(perception_label)
        if languages := self.guard['languages']:
            self._layout.addWidget(QtWidgets.QLabel(f'<b>Languages</b> {languages}'))
        if skills := self.guard['skills']:
            self._layout.addWidget(QtWidgets.QLabel(f'<b>Skills</b> {skills}'))
        ability_text = ', '.join(f'<b>{ability_short}</b> {self.guard[ability]}'
                                 for ability_short, ability in (('Str', 'strength'), ('Dex', 'dexterity'),
                                                                ('Con', 'constitution'), ('Int', 'intelligence'),
                                                                ('Wis', 'wisdom'), ('Cha', 'charisma')))
        ability_label = QtWidgets.QLabel(ability_text, self)
        self._layout.addWidget(ability_label)
        try:
            abilities = json.loads(self.guard['abilities'])
        except json.JSONDecodeError:
            abilities = []
        general_abilities = [ability for ability in abilities if ability['type'] == 'general']
        offensive_abilities = [ability for ability in abilities if ability['type'] == 'offensive']
        for ability in general_abilities:
            self._layout.addLayout(AbilityLabel(ability, self.guard))
        if items := self.guard['items']:
            self._layout.addWidget(QtWidgets.QLabel(f'<b>Items</b> {items}'))
        self._layout.addWidget(Line())
        defenses_text = f'<b>AC</b> {self.guard["armor_class"]}; <b>Fort</b> {self.guard["fortitude"]}, ' \
                        f'<b>Ref</b> {self.guard["reflex"]}, <b>Will</b> {self.guard["will"]}'
        if saves := self.guard['saves']:
            defenses_text += f'; {saves}'

        self._layout.addWidget(QtWidgets.QLabel(defenses_text, self))
        hit_points = str(self.guard['hit_points'])
        if comment := self.guard['hit_points_comment']:
            hit_points += f' ({comment})'
        life_text = '; '.join(f'<b>{name}</b> {value}' for name, value in (('HP', hit_points),
                                                                           ('Immunities', self.guard['immunities']),
                                                                           ('Resistances', self.guard['resistances']),
                                                                           ('Weaknesses', self.guard["weaknesses"]))
                              if value)
        self._layout.addWidget(QtWidgets.QLabel(life_text, self))
        defensive_abilities = [ability for ability in abilities if ability['type'] == 'defensive']
        for ability in defensive_abilities:
            self._layout.addLayout(AbilityLabel(ability, self.guard))
        self._layout.addWidget(Line())
        self._layout.addWidget(QtWidgets.QLabel(f'<b>Speed</b> {self.guard["speed"]}', self))
        for ability in offensive_abilities:
            self._layout.addLayout(AbilityLabel(ability, self.guard))
        if desc := self.guard['text']:
            self._layout.addWidget(Line())
            self._layout.addWidget(QtWidgets.QLabel(desc, self))
        for label in self.findChildren(QtWidgets.QLabel):
            label.setWordWrap(True)
        self._layout.addStretch()
