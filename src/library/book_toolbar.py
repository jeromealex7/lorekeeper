from PySide2 import QtWidgets

from src.model import Book, Keep
from src.widgets import BuildingToolbar


class BookToolbar(BuildingToolbar):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=Book, parent=parent)

    @staticmethod
    def get_icon_name(type_: str) -> str:
        return type_
