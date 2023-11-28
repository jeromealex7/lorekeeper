import inspect
import re
from typing import get_type_hints, TypeVar

from .feature import Feature
from src.model import Combatant

Keep = TypeVar('Keep')


class Guard(Feature):
    TABLE_NAME = 'guard'
    TAG_TABLE_NAME = 'trait'
    REGEX_BRACKET = re.compile(r'\[([^\]]*?)\]')
    REGEX_GENDERED = re.compile(r'([^\/]*)\/([^\/]*)\/([^\/]*)')
    REGEX_HTML = re.compile(r'<.*?>')
    REGEX_ROLL = re.compile(r'(\d+d\d+)\s*?[+-]0')

    def __init__(self, keep: Keep, db_index: int = 0, name: str = None, data: dict = None):
        super().__init__(keep=keep, db_index=db_index, name=name, data=data)
        self.property_regex = re.compile(rf'(?<!\w)({"|".join(self.get_properties())})(?!\w)',
                                         re.IGNORECASE)

    def commit(self) -> int:
        self['traits'] = ', '.join(self.get_tags())
        return super().commit()

    @classmethod
    def get_default_data(cls, data: dict = None) -> dict[str, str | int]:
        return {'name': '', 'gender': 0, 'type': '', '_treasure': 0, 'short_name': '', 'traits': ''} | \
               super().get_default_data()

    def get_tags(self) -> list[str]:
        df = self.keep.buildings['trait'].df
        return df[df['_guard'] == self.db_index]['name'].values.tolist()

    @staticmethod
    def get_icon_name(type_: str) -> str:
        return ''

    def get_properties(self) -> list[str]:
        result = []
        for name, method in inspect.getmembers(self.__class__):
            try:
                if not isinstance(method, property):
                    continue
                fget = method.fget
                if get_type_hints(fget).get('return') == int:
                    result.append(name)
            except (NameError, TypeError):
                continue
        result += list(self.keys())
        return result

    def parse(self, text: str) -> str:

        def parse_bracket(content: str) -> str:
            prefix = ''.join(self.REGEX_HTML.findall(content))
            content = self.REGEX_HTML.sub('', content)
            if self.REGEX_GENDERED.findall(content):
                return self.REGEX_GENDERED.sub(lambda match: match.groups()[self['gender']], content)
            content = content.replace(' ', '')
            if not content:
                return ''
            format_ = '+d' if content and content[0] in ('+', '-') else ''
            upper = content[0].isupper()

            def replace(word: str) -> str:
                word = word.lower()
                if word == 'name':
                    short_name = s.lower() if (s := self['short_name'].strip()) else self['name']
                    return f'the {short_name}' if self['gender'] == 2 else short_name
                if hasattr(self, word):
                    return str(getattr(self, word))
                return self.get(word)
            content = self.property_regex.sub(lambda match: replace(match.groups()[0]), content)
            try:
                result = str(format(eval(content), format_))
            except (NameError, SyntaxError, ValueError):
                result = content
            if upper:
                result = result.capitalize()
            return prefix + result
        return self.REGEX_ROLL.sub(lambda match: match.groups()[0],
                                   self.REGEX_BRACKET.sub(lambda match: parse_bracket(match[1]), text))

    @property
    def icon_name(self) -> str:
        return self.get_icon_name(self['type'])

    def to_combatant(self) -> Combatant:
        return Combatant(keep=self.keep, db_index=0)
