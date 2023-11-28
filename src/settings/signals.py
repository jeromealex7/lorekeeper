import logging

from PySide2.QtCore import QObject, Signal


class SignalManager(QObject):
    BOOK_COMMIT = Signal(int)                   # db_index
    BOOK_DELETE = Signal(int)                   # db_index
    BOOK_INSPECT = Signal(int)                  # db_index
    ENCOUNTER_COMMIT = Signal(int)              # db_index
    ENCOUNTER_DELETE = Signal(int)              # db_index
    ENCOUNTER_INSPECT = Signal(int)             # db_index
    ENCOUNTER_VARIABLES = Signal()              #
    ENCOUNTER_ACTIVATE = Signal(int)            # db_index
    FEATURE_COMMIT = Signal(str, int)           # TABLE_NAME, db_index
    FEATURE_DELETE = Signal(str, int)           # TABLE_NAME, db_index
    FEATURE_INSPECT = Signal(str, int)          # TABLE_NAME, db_index
    FOOTNOTE_COMMIT = Signal(int)               # db_index
    FOOTNOTE_DELETE = Signal(int)               # db_index
    GENRE_COMMIT = Signal(int)                  # db_index
    GENRE_DELETE = Signal(int)                  # db_index
    GUARD_COMMIT = Signal(int)                  # db_index
    GUARD_DELETE = Signal(int)                  # db_index
    GUARD_INSPECT = Signal(int)                 # db_index
    GUARD_POPUP = Signal(int)                   # db_index
    INSCRIPTION_COMMIT = Signal(int)            # db_index
    INSCRIPTION_DELETE = Signal(int)            # db_index
    MINSTREL_COMMIT = Signal(int)               # db_index
    MINSTREL_CREATE = Signal(int)               # db_index
    MINSTREL_DELETE = Signal(int)               # db_index
    MINSTREL_INSPECT = Signal(int)              # db_index
    PAGE_COMMIT = Signal(int)                   # db_index
    PAGE_DELETE = Signal(int)                   # db_index
    TAB_RENAME = Signal(str, int, str)          # table_name, db_index, name
    TREASURE_COMMIT = Signal(int)               # db_index
    TREASURE_DELETE = Signal(int)               # db_index
    TREASURE_INSPECT = Signal(int)              # db_index
    PRESENTER_SET = Signal(int)                 # db_index
    PRESENTER_ADD = Signal(int)                 # db_index
    PRESENTER_BACKGROUND = Signal(int)          # db_index
    PRESENTER_REMOVE = Signal(int)              # db_index
    IMAGE_POPUP = Signal(int)                   # db_index
    MUSIC_ADD = Signal(int, int)                # minstrel_db_index, treasure_db_index
    MUSIC_CONTINUE = Signal(int)                # minstrel_db_index
    MUSIC_DIRECT = Signal(int)                  # treasure_db_index
    MUSIC_NOW_PLAYING = Signal(int)             # title
    CITADEL_SHOW = Signal()                     #
    CITADEL_LOADED = Signal()                   #
    REFRESH = Signal()

    def __init__(self):
        super().__init__()
        self.FEATURE_COMMIT.connect(self.feature_commit)
        self.FEATURE_DELETE.connect(self.feature_delete)
        self.FEATURE_INSPECT.connect(self.feature_inspect)
        self.logger = logging.getLogger(self.__class__.__name__)

    def feature_commit(self, table_name: str, db_index: int):
        match table_name:
            case 'book': self.BOOK_COMMIT.emit(db_index)
            case 'encounter': self.ENCOUNTER_COMMIT.emit(db_index)
            case 'footnote': self.FOOTNOTE_COMMIT.emit(db_index)
            case 'genre': self.GENRE_COMMIT.emit(db_index)
            case 'guard': self.GUARD_COMMIT.emit(db_index)
            case 'inscription': self.INSCRIPTION_COMMIT.emit(db_index)
            case 'minstrel': self.MINSTREL_COMMIT.emit(db_index)
            case 'page': self.PAGE_COMMIT.emit(db_index)
            case 'treasure': self.TREASURE_COMMIT.emit(db_index)

    def feature_delete(self, table_name: str, db_index: int):
        match table_name:
            case 'book': self.BOOK_DELETE.emit(db_index)
            case 'encounter': self.ENCOUNTER_DELETE.emit(db_index)
            case 'footnote': self.FOOTNOTE_DELETE.emit(db_index)
            case 'genre': self.GENRE_DELETE.emit(db_index)
            case 'guard': self.GUARD_DELETE.emit(db_index)
            case 'inscription': self.INSCRIPTION_DELETE.emit(db_index)
            case 'minstrel': self.MINSTREL_DELETE.emit(db_index)
            case 'page': self.PAGE_DELETE.emit(db_index)
            case 'treasure': self.TREASURE_DELETE.emit(db_index)

    def feature_inspect(self, table_name: str, db_index: int):
        match table_name:
            case 'book': self.BOOK_INSPECT.emit(db_index)
            case 'encounter': self.ENCOUNTER_INSPECT.emit(db_index)
            case 'guard': self.GUARD_INSPECT.emit(db_index)
            case 'minstrel': self.MINSTREL_INSPECT.emit(db_index)
            case 'treasure': self.TREASURE_INSPECT.emit(db_index)


SIGNALS = SignalManager()
