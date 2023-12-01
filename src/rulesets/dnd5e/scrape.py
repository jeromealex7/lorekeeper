from collections import defaultdict
import json

import requests
import re

from .constants import ALIGNMENTS, SIZES, TYPES
from src.model import Inscription, Keep, Trait, Treasure
from src.rulesets import RULESET
from src.settings import PATHS, SIGNALS

REGEX_ABILITY = re.compile(r'<p><em><strong>(?P<ability_name>.*?)\.?<\/strong><\/em>\s*(?P<ability_text>.*?)\s*<\/p>')
URL = r'https://gist.githubusercontent.com/tkfu/9819e4ac6d529e225e9fc58b358c3479/raw/d4df8804c25a662efc42936db60cfbc0a5b19db8/srd_5e_monsters.json'


def get_data() -> list[dict]:
    data_path = PATHS['scrape'].joinpath('dnd5e.json')
    if data_path.exists():
        return json.loads(data_path.read_text())
    answer = requests.get(URL)
    data = answer.json()
    data_path.write_text(json.dumps(data))
    return data


def read_entry(entry: dict) -> tuple[str | None, dict[str, str | int]]:
    guard = {}
    entry = defaultdict(str, **entry)

    guard['name'] = entry['name']
    meta = entry['meta'].lower()
    for size in SIZES:
        if size.lower() in meta:
            guard['size'] = size.capitalize()
            break
    for type_ in TYPES:
        if type_.lower() in meta:
            guard['type'] = type_.capitalize()
            break
    for alignment in sorted(ALIGNMENTS, key=lambda a: len(a), reverse=True):
        if alignment.lower() in meta:
            guard['alignment'] = alignment.capitalize()
            break
    try:
        guard['subtype'] = re.search(r'\(.*?\)', meta).group()
    except AttributeError:
        guard['subtype'] = ''
    guard['armor_class'] = entry['Armor Class'].strip()
    try:
        guard['hit_dice'] = re.search(r'\d+d\d+', entry['Hit Points']).group()
    except AttributeError:
        guard['hit_dice'] = entry['Hit Points']
    guard['speed'] = entry['Speed'].strip()
    guard['strength'] = int(entry['STR'])
    guard['dexterity'] = int(entry['DEX'])
    guard['constitution'] = int(entry['CON'])
    guard['intelligence'] = int(entry['INT'])
    guard['wisdom'] = int(entry['WIS'])
    guard['charisma'] = int(entry['CHA'])
    guard['saves'] = re.sub('[A-Z]+', lambda m: m.group().capitalize(), entry['Saving Throws'])
    guard['skills'] = entry['Skills']
    guard['senses'] = re.sub('(?:,\s*)?Passive Perception \d+', '', entry['Senses'],
                             flags=re.IGNORECASE)
    guard['languages'] = entry['Languages'].replace('--', '-')
    guard['challenge'] = entry['Challenge'].split(' ')[0]
    guard['damage_immunities'] = entry['Damage Immunities'].lower()
    guard['damage_resistances'] = entry['Damage Resistances'].lower()
    guard['damage_vulnerabilities'] = entry['Damage Vulnerabilities'].lower()
    guard['condition_immunities'] = entry['Condition Immunities'].lower()
    image = entry['img_url']
    abilities = []
    for ability_type, ability_name in (('passive', 'Traits'), ('action', 'Actions'),
                                       ('reaction', 'Reactions'), ('legendary', 'Legendary Actions')):
        for match in REGEX_ABILITY.finditer(entry[ability_name]):
            match_dict = match.groupdict()
            abilities.append({'title': match_dict['ability_name'] or '', 'text': match_dict['ability_text'] or '',
                              'type': ability_type, 'priority': int('Multiattack' in match_dict['ability_name'])})
    guard['abilities'] = json.dumps(abilities)
    return image, guard


def import_monsters(keep: Keep, count: int | None = None, download_images: bool = True):
    entry_list = get_data()
    SIGNALS.PROGRESS_RANGE.emit(0, len(entry_list) - 1)
    for index, entry in enumerate(entry_list):
        if count and index >= count:
            break
        try:
            url, data = read_entry(entry)
            if download_images and url:
                treasure = Treasure.read_url(keep, url)
                if treasure:
                    treasure['name'] = data['name']
                    data['_treasure'] = treasure.commit()
                    inscription = Inscription(keep)
                    inscription['name'] = 'Monster Manual'
                    inscription['_treasure'] = treasure.db_index
                    inscription.commit()
        except Exception as err:
            print(err, entry)
            continue
        else:
            guard = RULESET.GUARD_TYPE.new(keep)
            guard.update(data)
            trait = Trait(keep)
            trait['name'] = 'Monster Manual'
            trait['_guard'] = guard.commit()
            trait.commit()
        finally:
            SIGNALS.PROGRESS_SET.emit(index)
