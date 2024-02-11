import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from src.model import Book, Encounter, Feature, Keep, Minstrel, Treasure
from src.treasury import ClipboardAction, Importer, OpenTreasureDialog, TreasureMenu
from src.settings import SIGNALS
from src.widgets import Icon, Preview, RenameAction


class ReferenceFrame(QtWidgets.QWidget):
    REFERENCES_CHANGED = QtCore.Signal()

    def __init__(self, keep: Keep, db_index: int, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.db_index = db_index
        self.drag = None
        self.drop_object = None
        self.feature_preview = None
        self.keep = keep
        self.label = QtWidgets.QLabel('References:')
        self.label.setFont(QtGui.QFont('Roboto Slab', 12))
        self.list = QtWidgets.QListWidget()
        self.list.installEventFilter(self)
        self.list.setAcceptDrops(True)
        self.list.viewport().installEventFilter(self)
        self.list.viewport().setAcceptDrops(True)
        self.list.viewport().setMouseTracking(True)
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.list.setSelectionMode(self.list.SingleSelection)
        self.list.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.list.model().rowsMoved.connect(lambda *args: self.REFERENCES_CHANGED.emit())

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label, stretch=0)
        layout.addWidget(self.list, stretch=1)
        self.setLayout(layout)
        self.load_references()

        SIGNALS.BOOK_COMMIT.connect(lambda feature_db_index: self.reload('book', feature_db_index))
        SIGNALS.BOOK_DELETE.connect(lambda feature_db_index: self.reload('book', feature_db_index))
        SIGNALS.TREASURE_COMMIT.connect(lambda feature_db_index: self.reload('treasure', feature_db_index))
        SIGNALS.TREASURE_DELETE.connect(lambda feature_db_index: self.reload('treasure', feature_db_index))
        SIGNALS.MINSTREL_COMMIT.connect(lambda feature_db_index: self.reload('minstrel', feature_db_index))
        SIGNALS.MINSTREL_DELETE.connect(lambda feature_db_index: self.reload('minstrel', feature_db_index))
        SIGNALS.ENCOUNTER_COMMIT.connect(lambda feature_db_index: self.reload('encounter', feature_db_index))
        SIGNALS.ENCOUNTER_DELETE.connect(lambda feature_db_index: self.reload('encounter', feature_db_index))

    def add_feature(self, feature: Book | Encounter | Minstrel | Treasure):
        item_data = self.get_data(feature)
        if any(self.list.item(row).data(QtCore.Qt.UserRole) == item_data for row in range(self.list.count())):
            return
        item = QtWidgets.QListWidgetItem()
        item.setText(feature['name'])
        item.setIcon(Icon(feature.icon_name))
        item.setData(QtCore.Qt.UserRole, item_data)
        self.list.addItem(item)
        self.REFERENCES_CHANGED.emit()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        current = self.list.selectedItems()
        menu = QtWidgets.QMenu(self)
        if current:
            row = current[0]
            data = row.data(QtCore.Qt.UserRole)
            db_index = data['db_index']
            match table_name := data['table_name']:
                case 'book':
                    menu = QtWidgets.QMenu(self)
                    inspect_action = QtWidgets.QAction(Icon('book_open'), 'Open Selected Book', self)
                    inspect_action.triggered.connect(lambda: SIGNALS.BOOK_INSPECT.emit(db_index))
                    menu.addAction(inspect_action)
                case 'encounter':
                    menu = QtWidgets.QMenu(self)
                    inspect_action = QtWidgets.QAction(Icon('sword'), 'Inspect Selected Encounter', self)
                    inspect_action.triggered.connect(lambda: SIGNALS.ENCOUNTER_INSPECT.emit(db_index))
                    menu.addAction(inspect_action)
                case 'minstrel':
                    play_action = QtWidgets.QAction(Icon('media_play'), 'Play Selected Minstrel', self)

                    def play():
                        minstrel = Minstrel.read_keep(self.keep, db_index)
                        minstrel['state'] = 2
                        minstrel.commit()
                        SIGNALS.MUSIC_CONTINUE.emit(db_index)
                    play_action.triggered.connect(play)
                    rename_action = RenameAction(Minstrel.read_keep(self.keep, data['db_index']), 'clef', self)
                    menu.addAction(rename_action)
                    menu.addAction(play_action)
                case 'treasure':
                    menu = TreasureMenu(Treasure.read_keep(self.keep, data['db_index']), self)
                    inspect_action = QtWidgets.QAction(Icon('chest_open'), 'Inspect Selected Treasure', self)
                    inspect_action.triggered.connect(lambda: SIGNALS.TREASURE_INSPECT.emit(db_index))
                    menu.addAction(inspect_action)
                case _: return
            remove_action = QtWidgets.QAction(Icon('garbage'), 'Remove Reference', self)
            remove_action.triggered.connect(lambda: self.remove_feature(table_name, db_index))
            menu.addAction(remove_action)
            menu.addSeparator()

        if clipboard_action := ClipboardAction(self.keep, None, False, self):
            menu.addAction(clipboard_action)
            clipboard_action.triggered.connect(lambda: self.add_feature(clipboard_action.treasure))

        def open_dialog():
            dialog = OpenTreasureDialog(self.keep, None, self)
            treasure = dialog.get()
            if not treasure:
                return
            importer = Importer(treasure, False, self)
            if importer.exec_():
                self.add_feature(treasure)
        open_action = QtWidgets.QAction(Icon('folder_open'), 'Open File ...', self)
        open_action.triggered.connect(open_dialog)
        menu.addAction(open_action)

        def new_encounter():
            encounter = Encounter.new(self.keep)
            encounter['name'] = 'New Encounter'
            encounter_index = encounter.commit()
            self.add_feature(encounter)
            SIGNALS.ENCOUNTER_INSPECT.emit(encounter_index)
        encounter_action = QtWidgets.QAction(Icon('sword'), 'Create Encounter', self)
        encounter_action.triggered.connect(new_encounter)
        menu.addAction(encounter_action)

        menu.popup(event.globalPos())

    def delete_references(self):
        for building_name in ('chart', 'footnote', 'performance', 'sigil'):
            building = self.keep.buildings[building_name]
            df = building.df
            df.drop(df[df['_page'] == self.db_index].index, inplace=True)
            building.reset_columns()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.source() == self.list:
            return False
        mime_data = event.mimeData()
        self.drop_object = None
        for subtype in ('book', 'encounter', 'minstrel', 'treasure'):
            current_type = f'lorekeeper/{subtype}'
            if not mime_data.hasFormat(current_type):
                continue
            self.drop_object = self.keep.buildings[subtype].feature_type.read_keep(
                self.keep, mime_data.data(current_type).data())
            event.acceptProposedAction()
            return
        treasure = Treasure.read_mime_data(self.keep, mime_data)
        if treasure:
            self.drop_object = treasure
            event.acceptProposedAction()
            return
        event.setAccepted(False)

    def dropEvent(self, event: QtGui.QDropEvent):
        if not self.drop_object:
            return
        if not self.drop_object.db_index:
            self.drop_object.commit()
        self.add_feature(self.drop_object)
        self.drop_object = None
        event.accept()

    def eventFilter(self, watched: QtWidgets.QWidget, event: QtCore.QEvent) -> bool:
        if watched == self.list.viewport():
            if event.type() in (QtCore.QEvent.DragEnter, QtCore.QEvent.Drop):
                if event.source() == self.list:
                    return False
                self.event(event)
                return True
            if event.type() == QtCore.QEvent.MouseMove:
                if event.buttons() == QtCore.Qt.LeftButton:
                    self.drag = QtGui.QDrag(self)
                    return False
                self.event(event)
                return True
            if event.type() == QtCore.QEvent.MouseButtonPress:
                modifiers = QtWidgets.QApplication.keyboardModifiers()
                if modifiers != QtCore.Qt.ControlModifier and (item := self.list.itemAt(event.pos())):
                    data = item.data(QtCore.Qt.UserRole)
                    feature_type = self.keep.buildings[data['table_name']].feature_type
                    feature = feature_type.read_keep(self.keep, data['db_index'])
                    self.drag = QtGui.QDrag(self.list)
                    self.drag.setPixmap(Preview(feature, self).to_pixmap())
                    self.drag.setMimeData(feature.to_mime_data())
                    self.drag.start()
                    return False
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                self.on_double_click()
                return True
        elif watched == self.list:
            if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Delete \
                    and (rows := self.list.selectedIndexes()):
                self.remove_row(rows[0].row())
                return True
        return super().eventFilter(watched, event)

    @staticmethod
    def get_data(feature: Feature):
        return {'table_name': feature.TABLE_NAME, 'db_index': feature.db_index}

    def leaveEvent(self, event: QtCore.QEvent):
        if self.feature_preview:
            self.feature_preview.deleteLater()
            self.feature_preview = None

    def load_references(self):
        def to_reference(table_name, feature_name) -> pd.DataFrame:
            df = self.keep.buildings[table_name].df
            df = df[df['_page'] == self.db_index].copy()
            df['table_name'] = feature_name
            df.rename(columns={f'_{feature_name}': '_reference_index'}, inplace=True)
            return df

        def add_reference(series: pd.Series):
            feature_type = self.keep.buildings[series['table_name']].feature_type
            self.add_feature(feature_type.read_keep(self.keep, series['_reference_index']))

        reference_list = list(reference for table_name, feature_name in (('footnote', 'book'),
                                                                         ('performance', 'minstrel'),
                                                                         ('sigil', 'encounter'),
                                                                         ('chart', 'treasure'))
                              if not (reference := to_reference(table_name, feature_name)).empty)
        if reference_list:
            reference_df = pd.concat(reference_list).sort_values(by='list_index')
            reference_df.apply(add_reference, axis=1)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        try:
            data = self.list.itemAt(event.pos()).data(QtCore.Qt.UserRole)
            db_index = data['db_index']
            table_name = data['table_name']
        except (AttributeError, KeyError):
            db_index = None
            table_name = None
        if not db_index:
            if self.feature_preview:
                self.feature_preview.deleteLater()
            return
        if self.feature_preview:
            if self.feature_preview.db_index == db_index:
                self.feature_preview.move(event.globalPos() + QtCore.QPoint(10, 10))
                return
            self.feature_preview.deleteLater()
        feature = self.keep.buildings[table_name].feature_type.read_keep(self.keep, db_index)
        self.feature_preview = Preview(feature)
        self.feature_preview.show()
        self.feature_preview.move(event.globalPos() + QtCore.QPoint(10, 10))

    def on_double_click(self):
        if not (selected := self.list.selectedIndexes()):
            return
        row = selected[0].row()
        item = self.list.item(row)
        data = item.data(QtCore.Qt.UserRole)
        match data['table_name']:
            case 'book': SIGNALS.BOOK_INSPECT.emit(data['db_index'])
            case 'encounter': SIGNALS.ENCOUNTER_INSPECT.emit(data['db_index'])
            case 'minstrel': SIGNALS.MUSIC_CONTINUE.emit(data['db_index'])
            case 'treasure': SIGNALS.TREASURE_INSPECT.emit(data['db_index'])

    def reload(self, table_name: str, db_index: int):
        if table_name not in ('book', 'encounter', 'minstrel', 'treasure'):
            return
        for row in range(self.list.count()):
            item = self.list.item(row)
            data = item.data(QtCore.Qt.UserRole)
            if data['table_name'] != table_name or data['db_index'] != db_index:
                continue
            try:
                text = self.keep.buildings[data['table_name']].df.at[data['db_index'], 'name']
                self.list.item(row).setText(text)
            except KeyError:
                self.list.takeItem(row)

    def remove_feature(self, table_name: str, db_index: int):
        for row in range(self.list.count()):
            widget = self.list.item(row)
            data = widget.data(QtCore.Qt.UserRole)
            if data['table_name'] != table_name or data['db_index'] != db_index:
                continue
            self.remove_row(row)

    def remove_row(self, row: int):
        self.list.takeItem(row)
        self.REFERENCES_CHANGED.emit()

    def save_references(self):
        self.delete_references()
        for row in range(self.list.count()):
            data = self.list.item(row).data(QtCore.Qt.UserRole)
            table_name = data['table_name']
            match table_name:
                case 'treasure': reference_table_name = 'chart'
                case 'encounter': reference_table_name = 'sigil'
                case 'book': reference_table_name = 'footnote'
                case 'minstrel': reference_table_name = 'performance'
                case _: raise ValueError('Unexpected Reference')
            feature_type = self.keep.buildings[reference_table_name].feature_type
            feature = feature_type.new(self.keep)
            feature['_page'] = self.db_index
            feature[f'_{table_name}'] = data['db_index']
            feature['list_index'] = row
            feature.commit()
