def monster_latex(creature):
    """Generate LaTeX necessary to create a monster from the given creature"""
    # bracket doubling looks crazy within this string
    # so we use <> in place of {}
    # and then substitute those at the end
    return "\n".join([
        "\\begin<monsection><{name}><{level}>".format(
            name=creature.name.replace('_', ' ').title(), level=creature.level),
        ind(4) + "\\begin<spellcontent>",
            ind(8) + "\\begin<spelltargetinginfo>",
                ind(12) + senses(creature),
                ind(12) + movement(creature),
                ind(12) + size(creature),
            ind(8) + "\\end<spelltargetinginfo>",
            ind(8) + "\\begin<spelleffects>",
                ind(12) + defenses(creature),
                ind(12) + attacks(creature),
                ind(12) + attributes(creature),
            ind(8) + "\\end<spelleffects>",
        ind(4) + "\\end<spellcontent>",
        ind(4) + "\\begin<spellfooter>",
            ind(8) + levels(creature),
            ind(8) + "\\pari \\mb<Encounter>", # not going to put that in the yaml?
            ind(8) + abilities(creature),
        ind(4) + "\\end<spellfooter>",
        "\\end<monsection>",
        traits(creature),
    ]).replace('<', '{').replace('>', '}').replace('+', '\\plus').replace('-', '\\minus')

def abilities(creature):
    return "\\pari \\mb<Abilities> " + ", ".join(
        [name.capitalize() for name in sorted(
            [str(ability) for ability in filter(
                lambda ability: not ability.has_tag('monster_trait') and not ability.has_tag('sense'),
                creature.visible_abilities
            )])
        ]
    )

def traits(creature):
    return "\\parhead<Traits> " + ", ".join(
        [name.title() for name in sorted(
            [str(ability) for ability in filter(
                lambda ability: ability.has_tag('monster_trait'),
                creature.visible_abilities
            )])
        ]
    )

def attacks(creature):
    return "\\pari \\mb<Attacks> {weapon_name} +{accuracy} ({dice}+{damage_bonus}); \\mb<Strikes> {strikes}".format(
        weapon_name=creature.weapon.name.capitalize(), accuracy=creature.accuracy,
        dice=str(creature.damage_dice), damage_bonus=creature.damage_bonus,
        strikes=creature.attack_count)

def attributes(creature):
    return "\\pari \\mb<Attributes> Str {}, Dex {}, Con {}, Int {}, Per {}, Wil {}".format(
        creature.strength, creature.dexterity, creature.constitution, creature.intelligence, creature.perception, creature.willpower
    )

def defenses(creature):
    return "\\pari \\mb<HP> {hp}; \\mb<Defenses> AD {armor}, Fort {fortitude}, Ref {reflex}, Ment {mental}".format(
        hp=creature.hit_points, armor=creature.armor_defense, fortitude=creature.fortitude,
        reflex=creature.reflex, mental=creature.mental)

def ind(spaces):
    return " " * spaces

def levels(creature):
    return "\\pari \\mb<Levels> {class_name} {level} [{monster_type}]".format(
        class_name=creature.monster_class.name.capitalize(), level=creature.level,
        monster_type=creature.monster_type.name.capitalize(),
    )

def movement(creature):
    speed_strings = ["{} ft.\\ {} speed".format(value, name) for name, value in creature.speeds.items()]
    if "land" not in creature.speeds:
        speed_strings.insert(0, "{} ft.\\ land speed".format(creature.land_speed))
    return "\\pari \\mb<Movement> {}".format(", ".join(speed_strings))

def senses(creature):
    return "\\pari \\mb<Senses> " + ", ".join(
        [name.capitalize() for name in sorted(
            [str(ability) for ability in filter(
                lambda ability: ability.has_tag('sense') and not ability.has_tag('monster_trait'),
                creature.visible_abilities
            )])
        ]
    )

def size(creature):
    return "\\pari \\mb<Size> {size}; \\mb<Reach> {reach} ft.".format(size=creature.size.capitalize(), reach=creature.reach)
