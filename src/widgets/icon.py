from PySide2.QtGui import QIcon

from src.settings import PATHS


class Icon(QIcon):

    def __init__(self, icon_name: str):
        super().__init__(PATHS['icons'].joinpath(icon_name).with_suffix('.png').__str__())
