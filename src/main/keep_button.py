import json
import os
from pathlib import Path

from PySide2 import QtGui, QtWidgets

from src.settings import PATHS, SIGNALS
from src.widgets.icon import Icon


class KeepButton(QtWidgets.QPushButton):

    def __init__(self, config_file: str | os.PathLike[str], parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.config_path = Path(config_file)
        self.inventory_path = PATHS['keeps'].joinpath(self.config_path.stem)
        self.thumbnail_path = self.config_path.with_suffix('.png')
        self.db_path = self.config_path.with_suffix('.db')

        thumbnail_url_path = self.thumbnail_path.as_posix().__str__()
        self.name = None
        self.setStyleSheet(f'KeepButton{{background-image : url(\'{thumbnail_url_path}\');}};')
        self.setFixedSize(250, 250)
        self.setFont(QtGui.QFont('Roboto Slab', 20))
        self.load_config()

        self.clicked.connect(self.open_keep)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        context_menu = QtWidgets.QMenu(self)
        open_action = QtWidgets.QAction(Icon('fortress_tower'), 'Enter Keep', self)
        delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Destroy Keep', self)
        context_menu.addActions([open_action, delete_action])
        context_menu.popup(event.globalPos())
        open_action.triggered.connect(self.open_keep)
        delete_action.triggered.connect(self.delete_keep)

    def delete_keep(self):
        dialog = QtWidgets.QMessageBox.question(self, 'Destroy Keep', f'Are you sure you want to destroy "{self.name}"? '
                                                                      f'This cannot be undone.')
        if dialog != QtWidgets.QMessageBox.Yes:
            return

        def _delete(_path: Path):
            if _path.is_file():
                _path.unlink(missing_ok=True)
                return
            for p in _path.glob('*'):
                _delete(p)
            if _path.is_dir():
                _path.rmdir()
        path_list = [self.inventory_path, self.config_path, self.thumbnail_path, self.db_path]
        for path in path_list:
            _delete(path)

        self.setEnabled(False)
        self.setStyleSheet('KeepButton{}')
        self.setText('DESTROYED')
        self.setFont(QtGui.QFont('Arial Black', 20))

    def load_config(self):
        config = json.loads(self.config_path.with_suffix('.json').read_text())
        self.name = config['name']
        self.setText(config['name'])

    def open_keep(self):
        SIGNALS.KEEP_OPEN.emit(self.config_path.name)
