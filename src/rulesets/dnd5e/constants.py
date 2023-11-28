ABILITIES = ('Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma')
ALIGNMENTS = ('Lawful Good', 'Lawful Neutral', 'Lawful Evil', 'Neutral Good', 'Neutral', 'Neutral Evil',
              'Chaotic Good', 'Chaotic Neutral', 'Chaotic Evil', 'Any', 'Unaligned')
CHALLENGES = """
level;1/8;1/4;1/2;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20
1;1:2;1:1;3:1;5:1;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-
2;1:3;1:2;1:1;3:1;6:1;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-
3;1:5;1:2;1:1;2:1;4:1;6:1;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-
4;1:8;1:4;1:2;1:1;2:1;4:1;6:1;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-;-
5;1:12;1:8;1:4;1:2;1:1;2:1;3:1;5:1;6:1;-;-;-;-;-;-;-;-;-;-;-;-;-;-
6;1:12;1:9;1:5;1:2;1:1;2:1;2:1;4:1;5:1;6:1;-;-;-;-;-;-;-;-;-;-;-;-;-
7;1:12;1:12;1:6;1:3;1:1;1:1;2:1;3:1;4:1;5:1;-;-;-;-;-;-;-;-;-;-;-;-;-
8;1:12;1:12;1:7;1:4;1:2;1:1;2:1;3:1;3:1;4:1;6:1;-;-;-;-;-;-;-;-;-;-;-;-
9;1:12;1:12;1:8;1:4;1:2;1:1;1:1;2:1;3:1;4:1;5:1;6:1;-;-;-;-;-;-;-;-;-;-;-
10;1:12;1:12;1:10;1:5;1:2;1:1;1:1;2:1;2:1;3:1;4:1;5:1;6:1;-;-;-;-;-;-;-;-;-;-
11;0;0;0;1:6;1:3;1:2;1:1;2:1;2:1;2:1;3:1;4:1;5:1;6:1;-;-;-;-;-;-;-;-;-
12;0;0;0;1:8;1:3;1:2;1:1;1:1;2:1;2:1;3:1;3:1;4:1;5:1;6:1;-;-;-;-;-;-;-;-
13;0;0;0;1:9;1:4;1:2;1:2;1:1;1:1;2:1;2:1;3:1;3:1;4:1;5:1;6:1;-;-;-;-;-;-;-
14;0;0;0;1:10;1:4;1:3;1:2;1:1;1:1;2:1;2:1;3:1;3:1;4:1;4:1;5:1;6:1;-;-;-;-;-;-
15;0;0;0;1:12;1:5;1:3;1:2;1:1;1:1;1:1;2:1;2:1;3:1;3:1;4:1;5:1;5:1;6:1;-;-;-;-;-
16;0;0;0;0;1:5;1:3;1:2;1:1;1:1;1:1;2:1;2:1;2:1;3:1;4:1;4:1;5:1;5:1;6:1;-;-;-;-
17;0;0;0;0;1:7;1:4;1:3;1:2;1:1;1:1;1:1;2:1;2:1;2:1;3:1;3:1;4:1;4:1;5:1;6:1;-;-;-
18;0;0;0;0;1:7;1:5;1:3;1:2;1:1;1:1;1:1;2:1;2:1;2:1;3:1;3:1;4:1;4:1;5:1;6:1;6:1;-;-
19;0;0;0;0;1:8;1:5;1:3;1:2;1:2;1:1;1:1;1:1;2:1;2:1;2:1;3:1;3:1;4:1;4:1;5:1;6:1;6:1;-
20;0;0;0;0;1:9;1:6;1:4;1:2;1:2;1:1;1:1;1:1;1:1;2:1;2:1;2:1;3:1;3:1;4:1;4:1;5:1;5:1;6:1
"""
CONDITIONS = ('Blinded', 'Charmed', 'Deafened', 'Exhaustion', 'Frightened', 'Grappled', 'Incapacitated',
              'Invisible', 'Paralyzed', 'Petrified', 'Poisoned', 'Prone', 'Restrained', 'Stunned', 'Unconscious')
DAMAGE_TYPES = ('Acid', 'Bludgeoning', 'Cold', 'Fire', 'Force', 'Lightning', 'Necrotic', 'Piercing', 'Poison',
                'Psychic', 'Radiant', 'Slashing', 'Thunder', 'Non-Silvered', 'Non-Adamantine', 'Non-Magical')
GENDERS = ('Male', 'Female', 'Other')
SIZES = ('Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Gargantuan')
SKILLS = (('Acrobatics', 'Dexterity'), ('Animal Handling', 'Wisdom'), ('Arcana', 'Intelligence'),
          ('Athletics', 'Strength'), ('Deception', 'Charisma'), ('History', 'Intelligence'), ('Insight', 'Wisdom'),
          ('Intimidate', 'Charisma'), ('Investigate', 'Intelligence'), ('Medicine', 'Wisdom'),
          ('Nature', 'Intelligence'), ('Perception', 'Wisdom'), ('Performance', 'Charisma'),
          ('Persuasion', 'Charisma'), ('Religion', 'Intelligence'), ('Sleight of Hand', 'Dexterity'),
          ('Stealth', 'Dexterity'), ('Survival', 'Wisdom'))
TYPES = ('Aberration', 'Beast', 'Celestial', 'Construct', 'Dragon', 'Elemental', 'Fey', 'Fiend', 'Giant',
         'Humanoid', 'Monstrosity', 'Ooze', 'Plant', 'Swarm', 'Undead')
XP_TABLE = {
    '1/8': 10,
    '1/4': 25,
    '1/2': 50,
    '1': 100,
    '2': 200,
    '3': 450,
    '4': 700,
    '5': 1100,
    '6': 1800,
    '7': 2300,
    '8': 2900,
    '9': 3900,
    '10': 5000,
    '11': 5900,
    '12': 7200,
    '13': 8400,
    '14': 10000,
    '15': 11500,
    '16': 13000,
    '17': 15000,
    '18': 18000,
    '19': 20000,
    '20': 25000,
}
