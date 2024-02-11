import json

from PySide2 import QtCore, QtGui, QtWidgets

from .ability_frame import AbilityFrame
from .constants import SIZES, TYPES
from src.garrison import StatArea
from src.model import Guard, Trait
from src.rulesets import RULESET
from src.settings import SIGNALS, SHORTCUTS
from src.treasury import ImageContainer
from src.widgets import DeleteDialog, Icon, NumberEdit, RollEdit, TagFrame


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
        self.frame = QtWidgets.QFrame()
        self.setCentralWidget(self.frame)

        layout = QtWidgets.QHBoxLayout()
        self.frame.setLayout(layout)

        self.name_edit = QtWidgets.QLineEdit(self)

        data_layout = QtWidgets.QGridLayout()
        data_layout.addWidget(QtWidgets.QLabel('Name:'), 0, 0, QtCore.Qt.AlignRight)
        data_layout.addWidget(self.name_edit, 0, 1, 1, 3)

        self.level_edit = QtWidgets.QComboBox(self)
        for level in range(-2, 22):
            self.level_edit.addItem(f'Level {level}', level)
        self.type_edit = QtWidgets.QComboBox(self)
        for monster_type in TYPES:
            self.type_edit.addItem(Icon(RULESET.GUARD_TYPE.get_icon_name(monster_type)), monster_type, monster_type)
        self.size_edit = QtWidgets.QComboBox(self)
        for size in SIZES:
            self.size_edit.addItem(size, size)
        self.gender_edit = QtWidgets.QComboBox(self)
        for index, name in enumerate(('male', 'female', 'other')):
            self.gender_edit.addItem(Icon(f'symbol_{name}'), name, index)
        self.perception_edit = NumberEdit()
        self.senses_edit = QtWidgets.QLineEdit(self)
        self.strength_edit = QtWidgets.QLineEdit(self)
        self.dexterity_edit = QtWidgets.QLineEdit(self)
        self.constitution_edit = QtWidgets.QLineEdit(self)
        self.intelligence_edit = QtWidgets.QLineEdit(self)
        self.wisdom_edit = QtWidgets.QLineEdit(self)
        self.charisma_edit = QtWidgets.QLineEdit(self)
        self.languages_edit = QtWidgets.QLineEdit(self)
        self.items_edit = QtWidgets.QLineEdit(self)
        self.ac_edit = QtWidgets.QLineEdit(self)
        self.fort_edit = QtWidgets.QLineEdit(self)
        self.ref_edit = QtWidgets.QLineEdit(self)
        self.will_edit = QtWidgets.QLineEdit(self)
        self.save_edit = QtWidgets.QLineEdit(self)
        self.hit_points_edit = RollEdit(self)
        self.hit_points_comment_edit = QtWidgets.QLineEdit(self)
        self.immunities_edit = QtWidgets.QLineEdit(self)
        self.resistances_edit = QtWidgets.QLineEdit(self)
        self.weaknesses_edit = QtWidgets.QLineEdit(self)
        self.speed_edit = QtWidgets.QLineEdit(self)
        self.skills_edit = QtWidgets.QLineEdit(self)

        for row, (label, widget) in enumerate((
                ('Level', self.level_edit), ('Type', self.type_edit), ('Size', self.size_edit),
                ('Gender', self.gender_edit), ('Perception', self.perception_edit), ('Senses', self.senses_edit),
                ('Strength', self.strength_edit), ('Dexterity', self.dexterity_edit),
                ('Constitution', self.constitution_edit), ('Intelligence', self.intelligence_edit),
                ('Wisdom', self.wisdom_edit), ('Charisma', self.charisma_edit), ('Languages', self.languages_edit),
                ('Items', self.items_edit), ('Armor Class', self.ac_edit), ('Fortitude', self.fort_edit),
                ('Reflex', self.ref_edit), ('Will', self.will_edit), ('Saves', self.save_edit),
                ('Hit Points', self.hit_points_edit), ('HP Comment', self.hit_points_comment_edit),
                ('Immunities', self.immunities_edit), ('Resistances', self.resistances_edit),
                ('Weaknesses', self.weaknesses_edit), ('Speed', self.speed_edit), ('Skills', self.skills_edit))):
            label_widget = QtWidgets.QLabel(label + ':', self)
            label_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            data_layout.addWidget(label_widget, 1 + row % 13, 2 * (row // 13), QtCore.Qt.AlignRight)
            data_layout.addWidget(widget, 1 + row % 13, 1 + 2 * (row // 13))
            widget.setMinimumWidth(200)

        self.info_edit = QtWidgets.QTextEdit(self)
        self.info_edit.resize(1, 1)
        self.description_edit = QtWidgets.QTextEdit(self)
        self.description_edit.resize(1, 1)
        self.image_container = ImageContainer(self.guard.keep, self)
        self.image_container.setFixedSize(250, 250)
        self.tag_frame = TagFrame(200, self.keep.buildings['trait'], tag_name='Tag', parent=self)
        self.ability_frame = AbilityFrame(guard, self)
        self.ability_frame.setContentsMargins(0, 0, 0, 0)

        self.stat_block = StatArea(self.guard, self)
        self.stat_block.setFixedWidth(400)

        tag_image_layout = QtWidgets.QVBoxLayout()
        tag_image_layout.addWidget(self.image_container, alignment=QtCore.Qt.AlignCenter, stretch=1)
        tag_image_layout.addWidget(self.tag_frame, alignment=QtCore.Qt.AlignBottom, stretch=0)
        additional_layout = QtWidgets.QVBoxLayout()
        additional_layout.addWidget(QtWidgets.QLabel('Info Text:'))
        additional_layout.addWidget(self.info_edit)
        additional_layout.addWidget(QtWidgets.QLabel('Description:'))
        additional_layout.addWidget(self.description_edit)

        input_layout = QtWidgets.QVBoxLayout()
        fields_layout = QtWidgets.QHBoxLayout()
        fields_layout.addLayout(data_layout, stretch=0)
        fields_layout.addLayout(tag_image_layout, stretch=0)
        fields_layout.addLayout(additional_layout, stretch=1)
        input_layout.addLayout(fields_layout, stretch=0)
        input_layout.addWidget(self.ability_frame, stretch=1)
        layout.addLayout(input_layout, stretch=1)
        layout.addWidget(self.stat_block, stretch=0, alignment=QtCore.Qt.AlignTop)

        SIGNALS.GUARD_DELETE.connect(self.on_guard_delete)

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

        for child in self.findChildren(QtWidgets.QLineEdit):
            child.textChanged.connect(lambda _: self.set_modified(True))
        for child in self.findChildren(QtWidgets.QComboBox):
            child.currentIndexChanged.connect(lambda _: self.set_modified(True))
        for child in self.findChildren(QtWidgets.QTextEdit):
            child.textChanged.connect(lambda: self.set_modified(True))
        self.image_container.TREASURE_CHANGED.connect(lambda: self.set_modified(True))
        self.reload_guard()

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

    def delete_traits(self):
        trait = self.keep.buildings['trait']
        df = trait.df
        df.drop(df[df['_guard'] == self.guard.db_index].index, inplace=True)
        trait.reset_columns()
        trait.save(False)

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
        self.guard['level'] = self.level_edit.currentData(QtCore.Qt.UserRole)
        self.guard['size'] = self.size_edit.currentText()
        self.guard['type'] = self.type_edit.currentText()
        self.guard['perception'] = self.perception_edit.get()
        self.guard['gender'] = self.gender_edit.currentData(QtCore.Qt.UserRole)
        self.guard['languages'] = self.languages_edit.text().strip()
        self.guard['senses'] = self.senses_edit.text().strip()
        self.guard['strength'] = self.strength_edit.text().strip()
        self.guard['dexterity'] = self.dexterity_edit.text().strip()
        self.guard['constitution'] = self.constitution_edit.text().strip()
        self.guard['intelligence'] = self.intelligence_edit.text().strip()
        self.guard['wisdom'] = self.wisdom_edit.text().strip()
        self.guard['charisma'] = self.charisma_edit.text().strip()
        self.guard['armor_class'] = self.ac_edit.text().strip()
        self.guard['fortitude'] = self.fort_edit.text().strip()
        self.guard['reflex'] = self.ref_edit.text().strip()
        self.guard['will'] = self.will_edit.text().strip()
        self.guard['saves'] = self.save_edit.text().strip()
        self.guard['items'] = self.items_edit.text().strip()
        self.guard['speed'] = self.speed_edit.text().strip()
        self.guard['_treasure'] = treasure.commit() if (treasure := self.image_container.treasure) else 0
        self.guard['info'] = self.info_edit.toPlainText().strip()
        self.guard['text'] = self.description_edit.toPlainText().strip()
        self.guard['immunities'] = self.immunities_edit.text().strip()
        self.guard['resistances'] = self.resistances_edit.text().strip()
        self.guard['weaknesses'] = self.weaknesses_edit.text().strip()
        self.guard['hit_points'] = self.hit_points_edit.get()
        self.guard['hit_points_comment'] = self.hit_points_comment_edit.text().strip()
        self.guard['skills'] = self.skills_edit.text().strip()
        self.guard['abilities'] = json.dumps(self.ability_frame.get())
        self.guard.commit()
        self.set_modified(False)

    def reload_guard(self):
        self.name_edit.setText(self.guard['name'])
        self.level_edit.setCurrentText(f'Level {self.guard["level"]}')
        self.type_edit.setCurrentText(self.guard['type'])
        self.size_edit.setCurrentText(self.guard['size'])
        self.perception_edit.set(self.guard['perception'])
        self.gender_edit.setCurrentText(('male', 'female', 'other')[self.guard['gender']])
        self.senses_edit.setText(self.guard['senses'])
        self.languages_edit.setText(self.guard['languages'])
        self.strength_edit.setText(self.guard['strength'])
        self.dexterity_edit.setText(self.guard['dexterity'])
        self.constitution_edit.setText(self.guard['constitution'])
        self.intelligence_edit.setText(self.guard['intelligence'])
        self.wisdom_edit.setText(self.guard['wisdom'])
        self.charisma_edit.setText(self.guard['charisma'])
        self.ac_edit.setText(self.guard['armor_class'])
        self.fort_edit.setText(self.guard['fortitude'])
        self.ref_edit.setText(self.guard['reflex'])
        self.will_edit.setText(self.guard['will'])
        self.save_edit.setText(self.guard['saves'])
        self.speed_edit.setText(self.guard['speed'])
        self.image_container.set_content(self.guard['_treasure'])
        self.info_edit.setText(self.guard['info'])
        self.description_edit.setText(self.guard['text'])
        self.items_edit.setText(self.guard['items'])
        self.hit_points_edit.set(self.guard['hit_points'])
        self.hit_points_comment_edit.setText(self.guard['hit_points_comment'])
        self.immunities_edit.setText(self.guard['immunities'])
        self.resistances_edit.setText(self.guard['resistances'])
        self.weaknesses_edit.setText(self.guard['weaknesses'])
        self.skills_edit.setText(self.guard['skills'])
        try:
            self.ability_frame.set(json.loads(self.guard['abilities']))
        except json.JSONDecodeError:
            self.ability_frame.set([])
        self.tag_frame.set_tags(self.guard.get_tags())
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
