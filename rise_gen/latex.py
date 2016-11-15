import re
from rise_gen.util import num_to_word

def monster_latex(creature):
    """Generate LaTeX necessary to create a monster from the given creature"""
    # bracket doubling looks crazy within this string
    # so we use <> in place of {}
    # and then substitute those at the end
    text = "\n".join(filter(lambda s: s, [
        "\\begin<monsection>{name}<{level}>".format(
            name=name(creature), level=creature.level),
        *indent_list(4, [
            "\\begin<spellcontent>",
            *indent_list(4, [
                "\\begin<spelltargetinginfo>",
                *indent_list(4, [
                    senses(creature),
                    movement(creature),
                    size(creature),
                ]),
                "\\end<spelltargetinginfo>",
                "\\begin<spelleffects>",
                *indent_list(4, [
                    defenses(creature),
                    attacks(creature),
                    attributes(creature),
                ]),
                "\\end<spelleffects>",
            ]),
            "\\end<spellcontent>",
            "\\begin<spellfooter>",
            *indent_list(4, [
                languages(creature),
                levels(creature),
                encounter(creature),
                abilities(creature),
            ]),
            "\\end<spellfooter>",
        ]),
        "\\end<monsection>",
        traits(creature),
        adept_points(creature),
    ])).replace('<', '{').replace('>', '}')

    # convert + and - to \plus and \minus
    text = re.sub(r'\+(\d)', r'\plus\1', text)
    text = re.sub(r'([^-])-(\d)', r'\1\minus\2', text)
    return text

def abilities(creature):
    relevant_abilities = list(filter(
        lambda ability: not ability.has_tag('monster_trait') and not ability.has_tag('sense'),
        creature.visible_abilities
    ))
    if not relevant_abilities:
        return None
    return "\\pari \\mb<Abilities> " + ", ".join(sorted(
        [str(ability) for ability in relevant_abilities]
    )).capitalize()

_vowels = set(['a', 'e', 'i', 'u'])
def adept_points(creature):
    if not 'adept' in creature.levels:
        return None
    count = max(creature.level, creature.intelligence // 2, creature.perception // 2, creature.willpower // 2)
    return "\\parhead<Adept Points> {a_an} {name} has {count} adept {point}. {it_they} one hour after being spent.".format(
        a_an="An" if creature.name[0] in _vowels else "A",
        name=creature.name,
        count=num_to_word(count),
        point="point" if count == 1 else "points",
        it_they="It returns" if count == 1 else "They return",
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

def encounter(creature):
    return "\\pari \\mb<Encounter> {}".format(creature.encounter or "")

def indent(spaces):
    return " " * spaces

def indent_list(spaces, strings):
    return [indent(spaces) + s if s else None
            for s in strings]

def languages(creature):
    if creature.languages is None:
        return None
    return "\\pari \\mb<Languages> " + ", ".join([
        language.capitalize() for language in creature.languages
    ])

def levels(creature):
    return "\\pari \\mb<Levels> {levels} [{monster_type}]".format(
        levels=", ".join([
            "{class_name} {level}".format(
                class_name='\\textbf<{}>'.format(class_name.capitalize()) if class_name == creature.base_class.name else class_name.capitalize(),
                level=creature.levels[class_name])
            for class_name in sorted(creature.classes.keys())
        ]),
        monster_type=creature.monster_type.name.capitalize(),
    )


def movement(creature):
    # skip land speed to ensure it is in front
    speed_strings = list(filter(None,
                                ["{} ft.\\ {} speed".format(value, name)
                                       if value is not None and name != 'land' else None
                                       for name, value in creature.speeds.items()
                                 ]))
    if creature.land_speed is not None:
        speed_strings.insert(0, "{} ft.\\ land speed".format(creature.land_speed))
    return "\\pari \\mb<Movement> {}".format(", ".join(speed_strings))

def name(creature):
    if ',' in creature.name:
        parts = creature.name.split(', ')
        if len(parts) != 2:
            raise Exception("Invalid compound creature name '{}'".format(creature.name))
        return "[{}]<{}>".format(parts[1].title(), parts[0].title())
    else:
        return "<{}>".format(creature.name.title())

def senses(creature):
    return "\\pari \\mb<Senses> " + ", ".join(sorted(
        [str(ability) for ability in filter(
            lambda ability: ability.has_tag('sense'),
            creature.visible_abilities
        )])
    ).capitalize()

def size(creature):
    return "\\pari \\mb<Size> {size}; \\mb<Reach> {reach} ft.".format(size=creature.size.capitalize(), reach=creature.reach)

def traits(creature):
    return "\\parhead<Traits> " + ", ".join(
        [name.title() for name in sorted(
            [str(ability) for ability in filter(
                lambda ability: ability.has_tag('monster_trait'),
                creature.visible_abilities
            )])
        ]
    )
