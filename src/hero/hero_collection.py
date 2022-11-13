import difflib, enum

from hero import hero_util

class TierList(enum.Enum):
    MILITARY = 'Military'
    FORTUNE = 'Fortune'
    PROVISIONS = 'Provisions'
    INSPIRATION = 'Inspiration'
    KINGDOM_POWER = 'Kingdom Power'
    MILITARY_POWER = 'Military Power'


_heros = hero_util.get_all_heros_from_api()

def create_attributes_tier_list(type: TierList, difficulty, cutoff):
    filtered_heros = filter(lambda k: (k.difficulty < difficulty), _heros)
    if type is TierList.MILITARY:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.max_military), reverse=True)
    elif type is TierList.FORTUNE:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.max_fortune), reverse=True)
    elif type is TierList.PROVISIONS:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.max_provisions), reverse=True)
    elif type is TierList.INSPIRATION:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.max_inspiration), reverse=True)
    elif type is TierList.KINGDOM_POWER:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.max_kp), reverse=True)
    elif type is TierList.MILITARY_POWER:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.max_power), reverse=True)
    return filtered_heros[:cutoff]

def create_growth_tier_list(type: TierList, difficulty, cutoff):
    filtered_heros = filter(lambda k: (k.difficulty < difficulty), _heros)
    if type is TierList.MILITARY:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.military_growth, k.max_military), reverse=True)
    elif type is TierList.FORTUNE:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.fortune_growth, k.max_fortune), reverse=True)
    elif type is TierList.PROVISIONS:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.provisions_growth, k.max_provisions), reverse=True)
    elif type is TierList.INSPIRATION:
        filtered_heros = sorted(filtered_heros, key=lambda k: (k.inspiration_growth, k.max_inspiration), reverse=True)
    return filtered_heros[:cutoff]

def hero_rank(hero_name, type: TierList):
    if type is TierList.MILITARY:
        sorted_heroes = sorted(_heros, key=lambda k: int(k.military_growth), reverse=True)
    elif type is TierList.FORTUNE:
        sorted_heroes = sorted(_heros, key=lambda k: int(k.fortune_growth), reverse=True)
    elif type is TierList.PROVISIONS:
        sorted_heroes = sorted(_heros, key=lambda k: int(k.provisions_growth), reverse=True)
    elif type is TierList.INSPIRATION:
        sorted_heroes = sorted(_heros, key=lambda k: int(k.inspiration_growth), reverse=True)
    elif type is TierList.KINGDOM_POWER:
        sorted_heroes = sorted(_heros, key=lambda k: int(k.max_kp), reverse=True)
    elif type is TierList.MILITARY_POWER:
        sorted_heroes = sorted(_heros, key=lambda k: int(k.max_power), reverse=True)

    for i, sorted_heroes in enumerate(sorted_heroes):
        if sorted_heroes.hero_name.lower() == hero_name.lower():
            return i + 1

def get_hero(hero_name):
    matches = list(filter(lambda k: (k.hero_name.lower() == hero_name.lower()), _heros))
    return matches[0] if matches else None

def hero_name_diff(command_hero_name):
    heroes = []
    for hero in _heros:
        hero_name = hero.hero_name.lower()
        heroes.append(hero_name)
    return difflib.get_close_matches(command_hero_name.lower(), heroes, cutoff=0.75)
