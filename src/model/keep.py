import json
import os
from pathlib import Path
import sqlite3
from typing import Literal, Type
import uuid

from PySide2 import QtGui

from .banner import Banner
from .book import Book
from .building import Building
from .chart import Chart
from .combatant import Combatant
from .encounter import Encounter
from .feature import Feature
from .footnote import Footnote
from .genre import Genre
from .guard import Guard
from .inscription import Inscription
from .keyword import Keyword
from .minstrel import Minstrel
from .page import Page
from .performance import Performance
from .repertoire import Repertoire
from .sigil import Sigil
from .trait import Trait
from .treasure import Treasure
from src.settings import PATHS


class Keep:
    FEATURE_TYPES: tuple[Type[Feature], ...] = (Banner, Book, Chart, Combatant, Encounter, Footnote, Genre, Guard,
                                                Inscription, Keyword, Minstrel, Page, Performance, Repertoire, Sigil,
                                                Trait, Treasure)

    def __init__(self, name: str, ruleset: str, uuid_: str = None, treasure_index: int = 0, player_count: int = 4,
                 player_level: int = 1, custom_tokens: list[str] = None, notes: list[tuple[str, str]] = None, **_):
        self.buildings: dict[str, Building] = dict()
        self.custom_tokens: list[str] = custom_tokens or []
        self.name = name
        self.notes = notes or []
        self.ruleset = ruleset
        self.player_count = player_count
        self.player_level = player_level
        self.treasure_index = treasure_index
        self.uuid = uuid_ or uuid.uuid4().hex

        self.connection = sqlite3.connect(PATHS['keeps'].joinpath(self.uuid + '.db'))
        PATHS['inventory'] = PATHS['keeps'].joinpath(self.uuid)
        PATHS['inventory'].mkdir(exist_ok=True)
        PATHS['workbench'] = PATHS['inventory'].joinpath('workbench')
        PATHS['workbench'].mkdir(exist_ok=True)
        PATHS['custom_tokens'] = PATHS['inventory'].joinpath('tokens')
        PATHS['custom_tokens'].mkdir(exist_ok=True)

    def add_ledger(self) -> int:
        ledger = Book.new(self)
        ledger['name'] = 'Ledger'
        ledger['type'] = 'fortress_tower'
        return ledger.commit()

    def create_tables(self, if_exists: Literal['fail', 'replace', 'append'] = 'replace'):
        for feature_type in self.FEATURE_TYPES:
            if feature_type.TABLE_NAME == 'guard':
                continue
            self.buildings[feature_type.TABLE_NAME] = Building(self, feature_type)
            self.buildings[feature_type.TABLE_NAME].df.to_sql(feature_type.TABLE_NAME, self.connection,
                                                              if_exists=if_exists)

    @classmethod
    def new(cls, ruleset: str):
        keep = cls(name=ruleset.title(), ruleset=ruleset)
        keep.create_tables()
        keep.add_ledger()
        return keep

    @classmethod
    def read_config(cls, file_name: str | os.PathLike[str]):
        config = json.loads(Path(file_name).read_text())
        keep = cls(**config)
        for feature_type in keep.FEATURE_TYPES:
            if issubclass(feature_type, Guard):
                continue
            keep.buildings[feature_type.TABLE_NAME] = Building.read_keep(keep, feature_type)
        return keep

    def save(self, modified_only: bool = True):
        for building in self.buildings.values():
            building.save(modified_only=modified_only)
        self.save_config()

    def save_config(self):
        try:
            image = Treasure.read_keep(self, self.treasure_index).to_image()
        except (FileNotFoundError, KeyError):
            image = QtGui.QImage(PATHS['images'].joinpath(self.ruleset + '.png').as_posix().__str__())
        image = image.convertToFormat(QtGui.QImage.Format_ARGB32).scaled(250, 250)
        transparent_image = QtGui.QImage(image.size(), QtGui.QImage.Format_ARGB32)
        transparent_image.fill(0)
        painter = QtGui.QPainter(transparent_image)
        painter.setOpacity(.35)
        painter.drawImage(0, 0, image)
        painter.end()
        transparent_image.save(PATHS['keeps'].joinpath(self.uuid + '.png').as_posix().__str__())
        config = dict(
            name=self.name,
            custom_tokens=self.custom_tokens,
            ruleset=self.ruleset,
            uuid_=self.uuid,
            treasure_index=self.treasure_index,
            player_count=self.player_count,
            player_level=self.player_level,
            notes=self.notes
        )
        PATHS['keeps'].joinpath(self.uuid).with_suffix('.json').write_text(json.dumps(config))
