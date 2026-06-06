import re
from difflib import get_close_matches

CARD_ALIASES = {
    # Suspects
    "scarlet": "Scarlet",
    "scarlett": "Scarlet",
    "miss scarlet": "Scarlet",
    "miss scarlett": "Scarlet",
    "miss_scarlet": "Scarlet",
    "miss_scarlett": "Scarlet",

    "mustard": "Mustard",
    "colonel mustard": "Mustard",
    "col mustard": "Mustard",
    "colonel_mustard": "Mustard",

    "white": "White",
    "mrs white": "White",
    "miss white": "White",
    "mrs_white": "White",

    "green": "Green",
    "mr green": "Green",
    "mister green": "Green",
    "reverend green": "Green",
    "rev green": "Green",
    "mr_green": "Green",

    "peacock": "Peacock",
    "mrs peacock": "Peacock",
    "miss peacock": "Peacock",
    "mrs_peacock": "Peacock",

    "plum": "Plum",
    "professor plum": "Plum",
    "prof plum": "Plum",
    "professor_plum": "Plum",

    # Weapons
    "rope": "Rope",

    "knife": "Knife",
    "dagger": "Knife",

    "candlestick": "Candlestick",
    "candle stick": "Candlestick",

    "revolver": "Revolver",
    "gun": "Revolver",
    "pistol": "Revolver",

    "lead pipe": "Lead Pipe",
    "leadpipe": "Lead Pipe",

    "wrench": "Wrench",
    "spanner": "Wrench",

    # Rooms
    "kitchen": "Kitchen",

    "ballroom": "Ballroom",

    "conservatory": "Conservatory",

    "dining room": "Dining Room",
    "diningroom": "Dining Room",

    "billiard room": "Billiard Room",
    "billiards room": "Billiard Room",
    "billiardroom": "Billiard Room",

    "library": "Library",

    "lounge": "Lounge",

    "hall": "Hall",

    "study": "Study",
}


def normalize_card_name(name: str) -> str:
    name = name.lower().strip()

    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name)

    if name in CARD_ALIASES:
        return CARD_ALIASES[name]

    match = get_close_matches(
        name,
        CARD_ALIASES.keys(),
        n=1,
        cutoff=0.8
    )

    if match:
        return CARD_ALIASES[match[0]]

    raise ValueError(f"Unknown card: {name}")