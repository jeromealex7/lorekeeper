import json
import re
import requests

from .constants import TYPES
from .guard import Guard
from src.model import Inscription, Keep, Trait, Treasure
from src.settings import PATHS, SIGNALS

PROPERTIES = (('Perception', 'perception'), ('Languages', 'languages'), ('Skills', 'skills'),
              ('Str', 'strength'), ('Dex', 'dexterity'), ('Con', 'constitution'), ('Int', 'intelligence'),
              ('Wis', 'wisdom'), ('Cha', 'charisma'), ('Items', 'items'), ('AC', 'armor_class'),
              ('Fort', 'fortitude'), ('Ref', 'reflex'), ('Will', 'will'), ('Resistances', 'resistances'),
              ('Weaknesses', 'weaknesses'), ('Immunities', 'immunities'), ('Speed', 'speed'),
              ('HP', 'hit_points'))
REGEX_ABILITIES = re.compile(r'<span class="hanging-indent"><b>(?:<a.*?>)?(.*?)(?:</b>|</a>)+\s*'
                             r'(?:<span class=\'action\' title=\'(.*?)\' .*?</span>)?(?:\s*</b>)?(.*?)</span>'
                             r'(?!<span class="hanging-indent"><b>(?:Critical Success|Success|Failure|Critical Failure)'
                             r'</b>)')
REGEX_IMAGE = re.compile(r'<a target="_blank" href="(Images\\Monsters\\.*?\.png)">')
REGEX_NAME_LEVEL = re.compile(r'<h1 class="title"><a href="Monsters\.aspx\?ID=\d+">(.*?)</a>'
                              r'<span style="margin-left:auto; margin-right:0">Creature (\d+)</span></h1>')
REGEX_PROPERTY = re.compile(fr'<b>((?!{"|".join(f"(?:{prop[0]})" for prop in PROPERTIES)})[^<]*?)</b>\s*(.*?)[\s,;]*<')
REGEX_REMOVE_HTML = re.compile(r'</?(?:a|u|span).*?>')
REGEX_REMOVE_MAP = re.compile(r'\[.*?]')
REGEX_SIZE = re.compile(r'<span class="traitsize"><a href="/Rules\.aspx\?ID=445">(.*?)</a></span>')
REGEX_SPELLS = re.compile(r'<b>((?:Divine|Occult|Arcane|Primal).*?(?:Spell|Ritual)s?)</b>(.*?)(?:<span|$|<br />)')
REGEX_SPLIT = re.compile(r'<b>Perception</b>(.*?)<b>AC</b>(.*?)<b>Speed</b>(.*?)$', re.DOTALL)
REGEX_TRAITS = re.compile(r'<span class="trait"><a href="/Traits\.aspx\?ID=\d+">(.*?)</a></span>')
REGEX_TYPE = re.compile(f'Recall Knowledge - ({"|".join(TYPES)})')


def read_entry(title: str, text: str) -> str:
    try:
        result = re.search(fr'<b>{title}</b>\s*(.*?)[\s,;]*(?:</br|<b|<hr />|<br />)', text).groups()[0]
    except AttributeError:
        return ''
    return REGEX_REMOVE_HTML.sub('', result).strip()


def read_aon(index: int) -> dict[str, str | int | list]:
    url = fr'https://2e.aonprd.com/Monsters.aspx?ID={index}'
    answer = requests.get(url)
    text = answer.text
    data = {'gender': 2}

    try:
        general, defensive, offensive = REGEX_SPLIT.search(text).groups()
        name, level = REGEX_NAME_LEVEL.search(text).groups()
        data['name'] = name
        data['level'] = int(level)
        data['size'] = REGEX_SIZE.search(text).groups()[0]
    except (AttributeError, ValueError):
        return {}
    data['_traits'] = ['_hidden', 'Archives of Nethys'] + [match.groups()[0] for match in REGEX_TRAITS.finditer(text)]
    try:
        data['info'] = re.search(fr'{name}</h1>(.*?)<br />', text).groups()[0]
    except AttributeError:
        data['info'] = ''
    for title, prop in PROPERTIES:
        data[prop] = read_entry(title, text)
    try:
        data['type'] = REGEX_TYPE.search(text).groups()[0]
    except AttributeError:
        data['type'] = 'Humanoid'
    try:
        data['_image'] = f'https://2e.aonprd.com/{REGEX_IMAGE.search(text).groups()[0]}'
    except AttributeError:
        data['_image'] = ''
    try:
        hp_str, *comment = re.split('[,;]', data['hit_points'], 1)
        data['hit_points_comment'] = comment[0].strip() if comment else ''
        data['hit_points'] = int(hp_str.strip())
    except ValueError:
        data['hit_points'] = 0
    try:
        perception_str, *senses = re.split('[,;]', data['perception'], 1)
        data['senses'] = senses[0].strip() if senses else ''
        data['perception'] = int(perception_str.strip())
    except ValueError:
        data['perception'] = 0
    will_str, *saves = re.split(';', data['will'], 1)
    data['saves'] = saves[0].strip() if saves else ''
    data['will'] = will_str.strip()
    data['text'] = url
    abilities = []
    for ability_type, part in (('general', general), ('defensive', defensive), ('offensive', offensive)):
        for match in REGEX_ABILITIES.finditer(part):
            name, actions, ability_text = match.groups()
            match actions:
                case 'Single Action': actions = '1 action'
                case 'Two Actions': actions = '2 actions'
                case 'Three Actions': actions = '3 actions'
                case 'Reaction': actions = 'reaction'
                case 'Free Action': actions = 'free action'
                case None: actions = ''
            ability = {'name': name, 'type': ability_type, 'actions': actions,
                       'text': REGEX_REMOVE_MAP.sub('', REGEX_REMOVE_HTML.sub('', ability_text)).strip()}
            abilities.append(ability)
        if ability_type == 'offensive':
            break
        for match in REGEX_PROPERTY.finditer(part):
            name, ability_text = match.groups()
            if name in (a['name'] for a in abilities):
                continue
            ability = {'name': name, 'type': ability_type, 'actions': '', 'text': ability_text}
            abilities.append(ability)
    for match in REGEX_SPELLS.finditer(text):
        name, ability_text = match.groups()
        ability = {'name': name, 'type': 'offensive', 'actions': '',
                   'text': REGEX_REMOVE_MAP.sub('', REGEX_REMOVE_HTML.sub('', ability_text)).strip()}
        abilities.append(ability)
    data['abilities'] = json.dumps(abilities)
    return data


def import_monsters(keep: Keep, count: int = None, download_images: bool = True):
    data_path = PATHS['scrape'].joinpath('pathfinder.json')
    if data_path.exists():
        aon_data_list = json.loads(data_path.read_text())
    else:
        aon_data_list = list(filter(None, (read_aon(index) for index in range(5))))
        data_path.write_text(json.dumps(aon_data_list))
    SIGNALS.PROGRESS_RANGE.emit(0, len(aon_data_list) - 1)
    for index, aon_data in enumerate(aon_data_list):
        SIGNALS.PROGRESS_SET.emit(index)
        image_url = aon_data.pop('_image')
        if download_images and image_url:
            treasure = Treasure.read_url(keep, image_url)
            if treasure:
                treasure['name'] = aon_data['name']
                aon_data['_treasure'] = treasure.commit()
                inscription_aon = Inscription(keep)
                inscription_aon['name'] = 'Archives of Nethys'
                inscription_aon['_treasure'] = treasure.db_index
                inscription_aon.commit()
                inscription_hidden = Inscription(keep)
                inscription_hidden['name'] = '_hidden'
                inscription_hidden['_treasure'] = treasure.db_index
                inscription_hidden.commit()
                treasure.commit()
        guard = Guard.new(keep)
        guard.update(aon_data)
        guard_index = guard.commit()
        while aon_data['_traits']:
            trait = Trait(keep)
            trait['name'] = aon_data['_traits'].pop(0)
            trait['_guard'] = guard_index
            trait.commit()
        if count and index >= count:
            break
