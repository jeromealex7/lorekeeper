import logging
import sys
from typing import Sequence, Type

from PySide2 import QtCore, QtWidgets
import tomli

from .citadel import Citadel
from .keep_viewer import KeepViewer
from src.settings import APPLICATIONS, PATHS, SERVER, SESSION, SIGNALS
from src.widgets import Error, Loading


class Lorekeeper(QtWidgets.QApplication):

    def __init__(self, args: Sequence[str]):
        super().__init__(args)
        SESSION['threadpool'] = self
        sys.excepthook = self.exception_hook
        self.create_paths()
        self.load_settings()

        self.citadel = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.viewer = KeepViewer()
        self.viewer.show()
        self.loading = None

        SIGNALS.KEEP_NEW.connect(lambda ruleset: self.load_citadel(Citadel.new(ruleset)))
        SIGNALS.KEEP_OPEN.connect(self.on_keep_open)
        SIGNALS.FEATURE_COMMIT.connect(
            lambda table_name, db_index: self.logger.info(f'Commit {table_name}#{db_index}'))
        SIGNALS.FEATURE_DELETE.connect(
            lambda table_name, db_index: self.logger.info(f'Delete {table_name}#{db_index}'))

    @staticmethod
    def create_paths():
        for path in filter(None, PATHS.values()):
            if path.is_dir():
                path.mkdir(parents=True, exist_ok=True)
            elif path.is_file() and not path.exists():
                path.write_text('')

    def load_citadel(self, citadel: Citadel):
        self.citadel = citadel
        SIGNALS.CITADEL_SHOW.emit()
        self.viewer.deleteLater()
        if self.loading:
            self.loading.deleteLater()

    @staticmethod
    def load_settings():
        try:
            settings = tomli.loads(PATHS['settings'].read_text())
            applications = settings.get('applications', {})
            if 'word' in applications:
                APPLICATIONS['doc'] = APPLICATIONS['docm'] = APPLICATIONS['docx'] = applications.pop('word')
            if 'python' in applications:
                APPLICATIONS['py'] = applications.pop('python')
            if 'excel' in applications:
                APPLICATIONS['xls'] = APPLICATIONS['xlsm'] = APPLICATIONS['xlsx'] = applications.pop('excel')
            APPLICATIONS.update(applications)
            server = settings.get('server', {})
            SERVER.update(server)
        except Exception as err:
            Error.read_exception(err)

    def on_keep_open(self, config_file_name: str):
        QtCore.QTimer.singleShot(100, lambda: self.load_citadel(Citadel.read_signal(config_file_name)))
        self.loading = Loading('Loading Keep', 'Please wait while the Keep is being loaded.')
        self.loading.exec_()

    @staticmethod
    def exception_hook(exception_class: Type[BaseException], exception: BaseException, _):
        Error('Internal Error', f'An unexpected Error occurred in the application. Please notify the developer.'
                                f'\n\n{exception_class.__name__}:\n{exception.__str__()}').exec_()
