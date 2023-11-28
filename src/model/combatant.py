from .feature import Feature


class Combatant(Feature):
    TABLE_NAME = 'combatant'
    _encounter: int
    _guard: int
    name: str
    index: int
    token: str
    notes: str
    type: str
    initiative: str
    initiative_roll: str
    hit_points: str
    maximum_hit_points: str
    maximum_hit_points_roll: str
    label: str
    power: str
    show: int
