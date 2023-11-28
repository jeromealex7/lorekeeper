DEFAULT_ABILITIES = """
name;title;type;priority;text
Sneak Attack;Sneak Attack (1/Turn);passive;0;[Name] deals an extra {Extra Damage:2d6} damage when [he/she/it] hits a target with a weapon attack and has advantage on the attack roll, or when the target is within 5 feet of an ally of [name] that isn't incapacitated and [name] doesn't have disadvantage on the attack roll.
Reckless;Reckless;passive;0;At the start of  [his/her/its] turn, [name] can gain advantage on all melee weapon attack rolls during that turn, but attack rolls against [him/her/it] have advantage until the start of [his/her/its] turn.
Devotion;Devotion;passive;0;[Name] has advantage on saving throws against being charmed or frightened.
Spellcasting;Spellcasting;passive;0;[Name] is a {Level:3rd}-level spellcaster. [His/Her/Its] spellcasting ability modifier is {Ability Name:Intelligence} (spell save DC [8+prof+{Ability Shorthand:int}], [+prof+{Ability Shorthand}] to hit with spell attacks). [He/She/It] has the following {Spell List:wizard} spells prepared:
Brave;Brave;passive;0;[Name] has advantage on saving throws against being frightened.
Brute;Brute;passive;0;A melee weapon deals one extra die of ist damage when [name] hits with it (included in the attack).
Shield Bash;Shield Bash;action;0;<i>Melee Weapon Attack:</i> [+prof+str] to hit, reach 5 ft., one creature. <i>Hit:</i> 2d4[+str] bludgeoning damage. If the target is a Medium or smaller creature, it must succeed on a DC [10+prof+str] Strength saving throw or be knocked prone.
Parry;Parry;reaction;0;[Name] adds [prof] to [his/her/its] AC against one melee attack that would hit [him/her/it]. To do so, [name] must see the attacker and be wielding a melee weapon.
Leadership;Leadership (Recharges after a Short or Long Rest);action;0;For 1 minute, [name] can utter a special command or warning whenever a nonhostile creature that it can see within 30 feet of [him/her/it] makes an attack roll or a saving throw. The creature can add a d4 to its roll provided it can hear and understand [name]. A creature can benefit from only one Leadership die at a time. This effect ends if [name] is incapacitated.
Keen Senses;Keen Senses;passive;0;[Name] has advantage on Wisdom (Perception) checks.
Cunning Action;Cunning Action;bonus;0;On each of [his/her/its] turns, [name] can use a bonus action to take the Dash, Disengage or Hide action.
Pack Tactics;Pack Tactics;passive;0;[Name] has advantage on an attack roll against a creature if at least one of [name]'s allies is within 5 feet of the creature and the ally isn't incapacitated.
Shadow Stealth;Shadow Stealth;bonus;0;When in dim light or darkness, [name] can use the Hide action as a bonus action.
Rampage;Rampage;bonus;0;When [name] reduces a creature to 0 hit points with a melee attack on [his/her/its] turn, [name] can take a bonus action to move up to half [his/her/its] speed and make a bite attack.
Nimble Escape;Nimble Escape;bonus;0;[Name] can take the Disengage and the Hide action as a bonus action on each of [his/her/its] turns.
Aggressive;Aggressive;bonus;0;As a bonus action, [name] can move up to [his/her/its] speed toward a hostile creature [he/she/it] can see.
Low Cunning;Low Cunning;bonus;0;[Name] can take the Disengage action as a bonus action on each of [his/her/its] turns.
Second Wind;Second Wind (Recharges after a Long or Short Rest);bonus;0;As a bonus action, [name] can regain {Hit Points:20} hit points.
Indomitable;Indomitable (2/Day);passive;0;[Name] rerolls a failed saving throw.
Melee Attack;{Attack Name};action;0;<i>Melee Weapon Attack:</i> [+prof+{Ability:str}] to hit, reach {Reach:5} ft., one target. <i>Hit:</i> {Damage:1d8}[+{Ability}] {Damage Type:slashing} damage.
Ranged Attack;{Attack Name};action;0;<i>Ranged Weapon Attack:</i> [+prof+{Ability:dex}] to hit, range {Range:80/320} ft., one target. <i>Hit:</i> {Damage:1d8}[+{Ability}] {Damage Type:piercing} damage.
Uncanny Dodge;Uncanny Dodge;reaction;0;[Name] halves the damage that it takes from an attack that hits [him/her/it]. [Name] must be able to see the attacker.
Lightfooted;Lightfooted;bonus;0;[Name] can take the Dash or Disengage action as a bonus action on each of [his/her/its] turns.
Survivor;Survivor;passive;0;[Name] regains {Hit Points:10} hit points at the start of [his/her/its] turn if [he/she/it] has at least 1 hit point but fewer hit points than half [his/her/its] hit point maximum.
Weapon Attack;Weapon Attack;legendary;1;[Name] makes a weapon attack.
Command Ally;Command Ally;legendary;0;[Name] targets one ally [he/she/it] can see within 30 feet of [him/her/it]. If the target can see and hear [name], the target can make one weapon attack as a reaction and gains advantage on the attack roll.
Damage Transfer;Damage Transfer;passive;0;While grappling a creature, [name] takes only half the damage dealt to [him/her/it], and the creature [he/she/it] is grappling takes the other half.
Spider Climb;Spider Climb;passive;0;[Name] can climb difficult surfaces, including upside down on ceilings, without needing to make an ability check.
Evasion;Evasion;passive;0;If [name] is subjected to an effect that allows it to make a Dexterity saving throw to take only half damage, [he/she/it] instead takes no damage if it succeeds on the saving throw, and only half damage if it fails.
Sunlight Sensitivity;Sunlight Sensitivity;passive;0;While in sunlight, [name] has disadvantage on attack rolls, as well as on Wisdom (Perception) checks that rely on sight.
Dagger;Dagger;action;0;<i>Melee or Ranged Weapon Attack:</i> [+prof+finesse] to hit, reach 5 ft. or range 20/60 ft., one target. <i>Hit</i>: 1d4[+finesse] piercing damage.
Legendary Resistance;Legendary Resistance;passive;0;If [name] fails a saving throw, it can choose to succeed instead.
"""