import json
import re

from PySide2 import QtCore, QtGui, QtWidgets

from .ability_frame import AbilityFrame
from .constants import ABILITIES, ALIGNMENTS, CONDITIONS, DAMAGE_TYPES, GENDERS, SIZES, SKILLS, TYPES
from .stat_block import StatBlock
from src.garrison import StatArea
from src.model import Guard, Trait
from src.rulesets import RULESET
from src.settings import SIGNALS, SHORTCUTS
from src.treasury import ImageContainer
from src.widgets import DeleteDialog, Icon, NumberEdit, RollEdit, SuggestionEdit, TagFrame


class GuardInspector(QtWidgets.QMainWindow):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        SHORTCUTS.activate_shortcuts(self)
        self.setStyleSheet('*{font-family: Roboto Slab; font-size: 10pt;};')
        self.setWindowIcon(Icon('helmet'))
        self.showMaximized()
        self.guard = guard
        self.keep = guard.keep
        self._is_modified = False

        self.frame = QtWidgets.QFrame(self)
        self.general_layout = QtWidgets.QGridLayout()

        self.name_edit = QtWidgets.QLineEdit(self)
        self.name_edit.setMinimumWidth(300)
        self.short_name_edit = QtWidgets.QLineEdit(self)
        self.gender = QtWidgets.QComboBox(self)
        self.gender.addItems(GENDERS)
        self.alignment = QtWidgets.QComboBox(self)
        self.alignment.setEditable(True)
        self.alignment.addItems(ALIGNMENTS)
        self.type = QtWidgets.QComboBox(parent)
        for type_name in TYPES:
            self.type.addItem(Icon(RULESET.GUARD_TYPE.get_icon_name(type_name)), type_name, type_name)
        self.type.setIconSize(QtCore.QSize(30, 30))
        self.subtype = QtWidgets.QLineEdit(self)
        self.size_edit = QtWidgets.QComboBox(self)
        self.size_edit.addItems(SIZES)
        self.challenge = QtWidgets.QComboBox(self)
        self.challenge.addItems(list(map(lambda level: level.removeprefix('CR '), RULESET.POWER_LEVELS)))
        self.languages = QtWidgets.QLineEdit(self)
        self.armor = QtWidgets.QLineEdit(self)
        self.hit_dice = RollEdit(self)
        self.speed = QtWidgets.QLineEdit(self)
        self.skills = SuggestionEdit(self)
        self.senses = SuggestionEdit(self)
        self.saves = SuggestionEdit(self)
        self.condition_immunities = SuggestionEdit(self)
        self.damage_resistances = SuggestionEdit(self)
        self.damage_immunities = SuggestionEdit(self)
        self.damage_vulnerabilities = SuggestionEdit(self)
        for row, (label_text, item) in enumerate(
                (('Name', self.name_edit), ('Short Name', self.short_name_edit), ('Gender', self.gender),
                 ('Alignment', self.alignment), ('Type', self.type), ('Subtype', self.subtype),
                 ('Size', self.size_edit), ('Challenge', self.challenge), ('Languages', self.languages),
                 ('Armor', self.armor), ('Hit Dice', self.hit_dice), ('Speed', self.speed), ('Skills', self.skills),
                 ('Senses', self.senses), ('Saves', self.saves), ('Condition Immunities', self.condition_immunities),
                 ('Damage Resistances', self.damage_resistances), ('Damage Immunities', self.damage_immunities),
                 ('Damage Vulnerabilities', self.damage_vulnerabilities))
        ):
            label = QtWidgets.QLabel(label_text + ':')
            label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.general_layout.addWidget(label, row, 0)
            self.general_layout.addWidget(item, row, 1)

        self.immunities_layout = QtWidgets.QVBoxLayout()
        self.immunities_layout.setAlignment(QtCore.Qt.AlignTop)
        self.immunities_layout.addWidget(QtWidgets.QLabel('Condition Immunities:', self))
        self.immunities_list = QtWidgets.QVBoxLayout()
        self.immunities_dict = {}
        self.immunities_list.setAlignment(QtCore.Qt.AlignTop)
        for row, condition in enumerate(CONDITIONS):
            button = QtWidgets.QCheckBox(condition, self)

            def reload_immunities():
                self.condition_immunities.set_suggestion(self.get_condition_immunities())
            self.immunities_list.addWidget(button)
            self.immunities_dict[condition] = button
            button.toggled.connect(lambda _: reload_immunities())
        self.immunities_layout.addLayout(self.immunities_list)

        self.damage_layout = QtWidgets.QVBoxLayout()
        self.damage_layout.setAlignment(QtCore.Qt.AlignTop)
        self.damage_layout.addWidget(QtWidgets.QLabel('Damage Sensitivities:', self))
        self.damage_list = QtWidgets.QGridLayout()
        self.damage_dict = {}
        self.damage_list.setAlignment(QtCore.Qt.AlignTop)
        for row, damage_type in enumerate(DAMAGE_TYPES):
            label = QtWidgets.QLabel(damage_type + ':', self)
            label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            edit = QtWidgets.QComboBox(self)
            edit.addItems(['Normal', 'Vulnerable', 'Resistant', 'Immune'])
            self.damage_dict[damage_type] = edit

            def reload_damage_sensitivities():
                self.damage_vulnerabilities.set_suggestion(self.get_damage_sensitivities(1))
                self.damage_resistances.set_suggestion(self.get_damage_sensitivities(2))
                self.damage_immunities.set_suggestion(self.get_damage_sensitivities(3))
            edit.currentIndexChanged.connect(lambda _: reload_damage_sensitivities())
            self.damage_list.addWidget(label, row, 0)
            self.damage_list.addWidget(edit, row, 1)
        self.damage_layout.addLayout(self.damage_list)

        self.skill_layout = QtWidgets.QVBoxLayout()
        self.skill_layout.setAlignment(QtCore.Qt.AlignTop)
        self.skill_layout.addWidget(QtWidgets.QLabel('Skill Proficiencies:', self))
        self.skill_list = QtWidgets.QGridLayout()
        self.skill_dict = {}
        self.skill_list.setAlignment(QtCore.Qt.AlignTop)
        for row, (skill_name, _) in enumerate(SKILLS):
            label = QtWidgets.QLabel(skill_name + ':', self)
            label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            edit = QtWidgets.QComboBox(self)
            edit.addItems(['Untrained', 'Trained', 'Expert'])
            self.skill_dict[skill_name] = edit

            def reload_skills():
                self.skills.set_suggestion(self.get_skills())
            edit.currentIndexChanged.connect(lambda _: reload_skills())
            self.skill_list.addWidget(label, row, 0)
            self.skill_list.addWidget(edit, row, 1)
        self.skill_layout.addLayout(self.skill_list)

        self.save_ability_layout = QtWidgets.QVBoxLayout()
        self.save_ability_layout.setAlignment(QtCore.Qt.AlignTop)
        self.ability_edits = {}
        self.save_edits = {}
        self.save_ability_layout.addWidget(QtWidgets.QLabel('Abilities and Saves:', self))
        self.ability_layout = QtWidgets.QGridLayout(self)
        self.ability_layout.setAlignment(QtCore.Qt.AlignTop)
        for row, ability in enumerate(ABILITIES):
            label = QtWidgets.QLabel(ability + ':')
            label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            edit = NumberEdit(default=10, minimum=1, parent=self)
            edit.textChanged.connect(lambda _: reload_save())
            edit.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            save = QtWidgets.QComboBox(self)
            save.addItems(['Untrained', 'Trained', 'Expert'])
            save.setFixedWidth(100)
            save.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

            def reload_save():
                self.saves.set_suggestion(self.get_saves())
            save.currentIndexChanged.connect(lambda _: reload_save())
            edit.CHANGED.connect(lambda _: reload_skills())
            edit.CHANGED.connect(lambda _: self.set_modified(True))
            self.ability_edits[ability] = edit
            self.save_edits[ability] = save
            self.ability_layout.addWidget(label, row, 0)
            self.ability_layout.addWidget(edit, row, 1)
            self.ability_layout.addWidget(save, row, 2)
        self.save_ability_layout.addLayout(self.ability_layout)
        self.tag_frame = TagFrame(200, self.keep.buildings['trait'], tag_name='Trait', parent=self)
        self.save_ability_layout.addWidget(self.tag_frame, alignment=QtCore.Qt.AlignTop)
        self.image_container = ImageContainer(self.keep, self)
        self.image_container.set_content(None)
        self.save_ability_layout.addWidget(self.image_container, alignment=QtCore.Qt.AlignCenter)

        self.preview = StatArea(self.guard, self)

        self.challenge.currentIndexChanged.connect(lambda _: (reload_skills(), reload_save()))
        layout = QtWidgets.QHBoxLayout()
        input_layout = QtWidgets.QVBoxLayout()
        header = QtWidgets.QHBoxLayout()
        header.addLayout(self.general_layout)
        header.addSpacing(5)
        header.addLayout(self.save_ability_layout, stretch=0)
        header.addSpacing(5)
        header.addLayout(self.immunities_layout, stretch=0)
        header.addSpacing(5)
        header.addLayout(self.damage_layout, stretch=0)
        header.addSpacing(5)
        header.addLayout(self.skill_layout, stretch=0)
        input_layout.addLayout(header)
        input_layout.addWidget(QtWidgets.QLabel('Abilities:', self))
        self.ability_frame = AbilityFrame(guard, self)
        self.ability_frame.setContentsMargins(0, 0, 0, 0)
        input_layout.addWidget(self.ability_frame)
        layout.addLayout(input_layout)
        layout.addWidget(self.preview)
        self.frame.setLayout(layout)
        self.setCentralWidget(self.frame)
        self.reload_guard()

        menu_bar = QtWidgets.QMenuBar(self)
        guard_menu = QtWidgets.QMenu('&Guard', menu_bar)
        save_action = QtWidgets.QAction(Icon('floppy_disk'), 'Save Guard', self)
        save_action.triggered.connect(self.on_save)
        save_action.setShortcut(QtGui.QKeySequence('Ctrl+S'))
        reload_action = QtWidgets.QAction(Icon('refresh'), 'Reload from Garrison', self)
        reload_action.triggered.connect(self.reload_guard)
        inspect_action = QtWidgets.QAction(Icon('note_text'), 'Show Stats', self)
        inspect_action.triggered.connect(lambda: SIGNALS.GUARD_POPUP.emit(self.guard.db_index))
        delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Exile Guard', self)
        delete_action.triggered.connect(self.on_delete)
        close_action = QtWidgets.QAction(Icon('door_exit'), 'Exit', self)
        close_action.triggered.connect(self.close)
        guard_menu.addActions([save_action, reload_action, inspect_action, delete_action])
        guard_menu.addSeparator()
        guard_menu.addAction(close_action)
        menu_bar.addMenu(guard_menu)
        self.setMenuBar(menu_bar)

        SIGNALS.GUARD_DELETE.connect(self.on_guard_delete)

        self.name_edit.textChanged.connect(lambda _: self.set_modified())
        self.short_name_edit.textChanged.connect(lambda _: self.set_modified())
        self.gender.currentIndexChanged.connect(lambda _: self.set_modified())
        self.alignment.currentTextChanged.connect(lambda _: self.set_modified())
        self.type.currentIndexChanged.connect(lambda _: self.set_modified())
        self.subtype.textChanged.connect(lambda _: self.set_modified())
        self.size_edit.currentIndexChanged.connect(lambda _: self.set_modified())
        self.challenge.currentIndexChanged.connect(lambda _: self.set_modified())
        self.languages.textChanged.connect(lambda _: self.set_modified())
        self.armor.textChanged.connect(lambda _: self.set_modified())
        self.hit_dice.textChanged.connect(lambda _: self.set_modified())
        self.speed.textChanged.connect(lambda _: self.set_modified())
        self.skills.textChanged.connect(lambda _: self.set_modified())
        self.senses.textChanged.connect(lambda _: self.set_modified())
        self.saves.textChanged.connect(lambda _: self.set_modified())
        self.condition_immunities.textChanged.connect(lambda _: self.set_modified())
        self.damage_resistances.textChanged.connect(lambda _: self.set_modified())
        self.damage_immunities.textChanged.connect(lambda _: self.set_modified())
        self.damage_vulnerabilities.textChanged.connect(lambda _: self.set_modified())
        self.ability_frame.CHANGED.connect(self.set_modified)
        self.image_container.TREASURE_CHANGED.connect(lambda: self.set_modified(True))
        self.reload_title()
        self.set_modified(False)

    def closeEvent(self, event: QtGui.QCloseEvent):
        self.close_window()
        event.ignore()

    def close_window(self, ask: bool = True):
        if ask and self.is_modified:
            message_box = QtWidgets.QMessageBox(self)
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setWindowIcon(Icon('question_mark'))
            message_box.setWindowTitle('Close Window')
            message_box.setText('There are unsaved changes.')
            save_button = QtWidgets.QPushButton(Icon('floppy_disk'), 'Save and Close', self)
            close_button = QtWidgets.QPushButton(Icon('door_exit'), 'Close without saving', self)
            cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
            message_box.addButton(save_button, QtWidgets.QMessageBox.AcceptRole)
            message_box.addButton(close_button, QtWidgets.QMessageBox.ActionRole)
            message_box.addButton(cancel_button, QtWidgets.QMessageBox.RejectRole)
            message_box.exec_()
            if message_box.clickedButton() == save_button:
                self.on_save()
                self.deleteLater()
            elif message_box.clickedButton() == close_button:
                self.deleteLater()
            return
        self.deleteLater()

    @property
    def db_index(self):
        return self.guard.db_index

    def delete_traits(self):
        trait = self.keep.buildings['trait']
        df = trait.df
        df.drop(df[df['_guard'] == self.guard.db_index].index, inplace=True)
        trait.reset_columns()
        trait.save(False)

    def get_ability_modifier(self, ability: str) -> int:
        return int(self.ability_edits[ability].get() - 10) // 2

    def get_condition_immunities(self) -> str:
        return ', '.join(key.lower() for key, val in self.immunities_dict.items() if val.isChecked())

    def get_damage_sensitivities(self, sensitivity: int) -> str:
        return ', '.join(key.lower() for key, val in self.damage_dict.items() if val.currentIndex() == sensitivity)

    def get_proficiency(self) -> int:
        return max((self.challenge.currentIndex() - 4) // 4, 0) + 2

    def get_saves(self) -> str:
        return ', '.join(f'{ab[:3]} {self.get_proficiency() * index + self.get_ability_modifier(ab):+d}'
                         for ab, save_edit in self.save_edits.items() if (index := save_edit.currentIndex()))

    def get_skills(self) -> str:
        return ', '.join(f'{skill_name} {self.get_proficiency() * index + self.get_ability_modifier(ab):+d}'
                         for (skill_name, ab) in SKILLS if (index := self.skill_dict[skill_name].currentIndex()))

    @property
    def is_modified(self) -> bool:
        return self._is_modified

    @is_modified.setter
    def is_modified(self, value):
        self.set_modified(value)

    def on_delete(self):
        if DeleteDialog('guard').get() == 'cancel':
            return
        self.guard.delete()

    def on_guard_delete(self, db_index: int):
        if self.guard.db_index != db_index:
            return
        self.deleteLater()

    def on_save(self):
        self.save_traits()
        self.guard['name'] = self.name_edit.text().strip()
        self.guard['short_name'] = self.short_name_edit.text().strip()
        self.guard['challenge'] = self.challenge.currentText()
        self.guard['alignment'] = self.alignment.currentText()
        self.guard['armor_class'] = self.armor.text()
        self.guard['damage_resistances'] = self.damage_resistances.text()
        self.guard['damage_vulnerabilities'] = self.damage_vulnerabilities.text()
        self.guard['damage_immunities'] = self.damage_immunities.text()
        self.guard['condition_immunities'] = self.condition_immunities.text()
        self.guard['hit_dice'] = self.hit_dice.get()
        self.guard['size'] = self.size_edit.currentText()
        self.guard['type'] = self.type.currentText()
        self.guard['strength'] = self.ability_edits['Strength'].get()
        self.guard['dexterity'] = self.ability_edits['Dexterity'].get()
        self.guard['constitution'] = self.ability_edits['Constitution'].get()
        self.guard['intelligence'] = self.ability_edits['Intelligence'].get()
        self.guard['wisdom'] = self.ability_edits['Wisdom'].get()
        self.guard['charisma'] = self.ability_edits['Charisma'].get()
        self.guard['abilities'] = json.dumps(self.ability_frame.get())
        self.guard['speed'] = self.speed.text()
        self.guard['senses'] = self.senses.text()
        self.guard['subtype'] = self.subtype.text()
        self.guard['gender'] = self.gender.currentIndex()
        self.guard['languages'] = self.languages.text()
        self.guard['skills'] = self.skills.text()
        self.guard['_treasure'] = treasure.commit() if (treasure := self.image_container.treasure) else 0
        self.guard['saves'] = self.saves.text()
        self.guard.commit()
        self.set_modified(False)

    def reload_guard(self):
        self.ability_edits['Strength'].set(self.guard['strength'])
        self.ability_edits['Dexterity'].set(self.guard['dexterity'])
        self.ability_edits['Constitution'].set(self.guard['constitution'])
        self.ability_edits['Intelligence'].set(self.guard['intelligence'])
        self.ability_edits['Wisdom'].set(self.guard['wisdom'])
        self.ability_edits['Charisma'].set(self.guard['charisma'])
        self.name_edit.setText(self.guard['name'])
        self.short_name_edit.setText(self.guard['short_name'])
        self.gender.setCurrentIndex(self.guard['gender'])
        self.alignment.setCurrentText(self.guard['alignment'])
        self.type.setCurrentText(self.guard['type'])
        self.subtype.setText(self.guard['subtype'])
        self.size_edit.setCurrentText(self.guard['size'])
        self.challenge.setCurrentText(self.guard['challenge'])
        self.languages.setText(self.guard['languages'])
        self.hit_dice.set(self.guard['hit_dice'])
        self.speed.setText(self.guard['speed'])
        self.armor.setText(self.guard['armor_class'])
        self.image_container.set_content(self.guard['_treasure'])

        for ability in ABILITIES:
            for rank in range(1, 3):
                regex = rf'{ability[:3]}\s*\+?{rank * self.get_proficiency() + self.get_ability_modifier(ability):d}'
                if re.search(regex, self.guard['saves'], re.IGNORECASE):
                    self.save_edits[ability].setCurrentIndex(rank)
                    break
            else:
                self.save_edits[ability].setCurrentIndex(0)
        self.saves.set(self.guard['saves'])

        for skill_name, ability in SKILLS:
            for rank in range(1, 3):
                regex = rf'{skill_name}\s*\+?{rank * self.get_proficiency() + self.get_ability_modifier(ability):d}'
                if re.search(regex, self.guard['skills'], re.IGNORECASE):
                    self.skill_dict[skill_name].setCurrentIndex(rank)
                    break
            else:
                self.skill_dict[skill_name].setCurrentIndex(0)
        self.skills.set(self.guard['skills'])

        for condition in CONDITIONS:
            self.immunities_dict[condition].setChecked(condition.lower() in self.guard['condition_immunities'].lower())
        self.condition_immunities.set(self.guard['condition_immunities'])

        for damage_type in DAMAGE_TYPES:
            if damage_type.lower() in self.guard['damage_vulnerabilities'].lower():
                self.damage_dict[damage_type].setCurrentIndex(1)
            elif damage_type.lower() in self.guard['damage_resistances'].lower():
                self.damage_dict[damage_type].setCurrentIndex(2)
            elif damage_type.lower() in self.guard['damage_immunities'].lower():
                self.damage_dict[damage_type].setCurrentIndex(3)
            else:
                self.damage_dict[damage_type].setCurrentIndex(0)
        self.damage_immunities.set(self.guard['damage_immunities'])
        self.damage_vulnerabilities.set(self.guard['damage_vulnerabilities'])
        self.damage_resistances.set(self.guard['damage_resistances'])
        self.senses.set(self.guard['senses'])

        try:
            abilities = json.loads(self.guard['abilities'])
        except json.JSONDecodeError:
            abilities = []
        self.ability_frame.set(abilities)
        self.set_modified(False)

    def reload_title(self):
        title = f'{self.name_edit.text()} - Guard'
        if self.is_modified:
            title += ' (modified)'
        self.setWindowTitle(title)

    def save_traits(self):
        self.delete_traits()
        keep = self.keep
        db_index = self.guard.db_index
        for tag_name in self.tag_frame.tags:
            Trait(keep, data={'_guard': db_index, 'name': tag_name}).commit()
        keep.buildings['trait'].save(False)

    def set_modified(self, value: bool = True):
        self._is_modified = value
        self.reload_title()
