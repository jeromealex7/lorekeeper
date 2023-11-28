import json
import re

from PySide2 import QtCore, QtWidgets

from src.rulesets.ruleset import StatBlock as BasicStatBlock
from .constants import XP_TABLE
from .guard import Guard


class Header(QtWidgets.QLabel):

    def __init__(self, text: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(text, parent)
        self.setStyleSheet('Header{font-size: 12pt}')


class Label(QtWidgets.QLabel):

    def __init__(self, title: str, text: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setText(f'<html><b>{title}</b></html> {text}')
        self.setStyleSheet('*{font-size: 8pt}')
        self.setWordWrap(True)


class AbilityLabel(QtWidgets.QLabel):

    def __init__(self, title: str, text: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setText(f'<html><b><i>{title}</i></b></html> {text}')
        self.setStyleSheet('*{font-size: 8pt}')
        self.setWordWrap(True)


class Line(QtWidgets.QFrame):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Raised)


class StatBlock(BasicStatBlock):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(guard, parent)
        self.guard = guard
        self.keep = guard.keep
        self.setStyleSheet('*{font-size: 8pt; background-color: white; font-family: Roboto Slab};')
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(400)
        self.resize(400, 1)
        self.layout().setSpacing(0)
        self.reload_guard()

    def reload_guard(self):
        self.clear()
        self.guard.reload()
        header = QtWidgets.QLabel(self.guard['name'], self)
        header.setStyleSheet('QLabel{font-size: 14pt; padding 0px};')
        size = self.guard['size'].capitalize()
        type_ = self.guard["type"].capitalize()
        sub_type = f'{type_} ({sub})' if (sub := self.guard['subtype'].strip()) else type_
        alignment = self.guard['alignment']
        subtitle = QtWidgets.QLabel(f'{size} {sub_type}, {alignment}')
        armor_class = Label('Armor Class', self.guard['armor_class'])
        try:
            count, die = self.guard['hit_dice'].split('d')
            modifier = int(count) * self.guard.con
            average = modifier + int(count) * (int(die) + 1) // 2
            modifier_str = f'{modifier:+d}' if modifier else ''
            hit_points_text = f'{average} ({count}d{die}{modifier_str})'
        except (IndexError, ValueError):
            hit_points_text = self.guard['hit_dice']
        hit_points = Label('Hit Points', hit_points_text)
        speed = Label('Speed', self.guard['speed'])
        ability_grid = QtWidgets.QGridLayout()
        ability_grid.setContentsMargins(10, 0, 10, 0)
        for column, ability in enumerate(('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom',
                                          'charisma')):
            label = QtWidgets.QLabel(ability[:3].upper(), None)
            label.setStyleSheet('QLabel{font-weight: bold};')
            label.setAlignment(QtCore.Qt.AlignCenter)
            value = QtWidgets.QLabel(f'{self.guard[ability]} ({(self.guard[ability] - 10) // 2:+d})')
            value.setAlignment(QtCore.Qt.AlignCenter)
            value.setContentsMargins(5, 0, 5, 0)
            ability_grid.addWidget(label, 0, column)
            ability_grid.addWidget(value, 1, column)

        self.layout().addWidget(header)
        self.layout().addWidget(subtitle)
        self.layout().addSpacing(5)
        self.layout().addWidget(Line())
        self.layout().addWidget(armor_class)
        self.layout().addWidget(hit_points)
        self.layout().addWidget(speed)
        self.layout().addWidget(Line())
        self.layout().addLayout(ability_grid)
        self.layout().addWidget(Line())
        for name, prop in (('Saving Throws', 'saves'), ('Skills', 'skills'),
                           ('Damage Resistances', 'damage_resistances'), ('Damage Immunities', 'damage_immunities'),
                           ('Damage Vulnerabilities', 'damage_vulnerabilities'),
                           ('Condition Immunities', 'condition_immunities')):
            value = self.guard[prop]
            if not value:
                continue
            self.layout().addWidget(Label(name, value))

        try:
            perception = 10 + int(re.search(r'Perception\s*([+-]?\d+)', self.guard['skills'],
                                            re.IGNORECASE).groups()[0])
        except (AttributeError, IndexError, ValueError):
            perception = 10 + (self.guard['wisdom'] - 10) // 2
        passive_perception = f'passive Perception {perception}'
        senses = f'{s}, {passive_perception}' if (s := self.guard['senses'].strip()) else passive_perception
        self.layout().addWidget(Label('Senses', senses))
        self.layout().addWidget(Label('Languages', self.guard['languages'] or '-'))

        xp = XP_TABLE.get(self.guard['challenge'], 0)
        challenge = f'{self.guard["challenge"]} ({xp:,} XP)'
        self.layout().addWidget(Label('Challenge', challenge))
        self.layout().addWidget(Line())
        self.layout().addSpacing(5)

        try:
            abilities = json.loads(self.guard['abilities'])
        except json.JSONDecodeError:
            abilities = []

        abilities.sort(key=lambda ab: ab['priority'], reverse=True)
        passive = [ability for ability in abilities if ability['type'] == 'passive']
        actions = [ability for ability in abilities if ability['type'] == 'action']
        reactions = [ability for ability in abilities if ability['type'] == 'reaction']
        bonus_actions = [ability for ability in abilities if ability['type'] == 'bonus']
        legendary_actions = [ability for ability in abilities if ability['type'] == 'legendary']

        for ability in passive:
            self.layout().addWidget(AbilityLabel(self.guard.parse(ability['title'] + '.'),
                                                 self.guard.parse(ability['text'])))
            self.layout().addSpacing(10)
        for ability_title, ability_list in (('Actions', actions), ('Bonus Actions', bonus_actions),
                                            ('Reactions', reactions), ('Legendary Actions', legendary_actions)):
            if not ability_list:
                continue
            self.layout().addSpacing(5)
            self.layout().addWidget(Header(ability_title, self))
            for ability in ability_list:
                self.layout().addWidget(AbilityLabel(self.guard.parse(ability['title'] + '.'),
                                                     self.guard.parse(ability['text'])))
                self.layout().addSpacing(10)
        self.layout().addStretch()
