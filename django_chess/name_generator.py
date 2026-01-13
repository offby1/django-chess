"""Generate human-readable game names from random words."""

import random

ADJECTIVES = [
    "happy", "clever", "swift", "gentle", "brave", "kind", "wise", "calm",
    "bright", "cool", "mighty", "noble", "quick", "bold", "fair", "keen",
    "proud", "grand", "wild", "pure", "rare", "warm", "vast", "eager"
]

COLORS = [
    "blue", "red", "green", "golden", "silver", "purple", "orange", "amber",
    "jade", "ruby", "pearl", "ivory", "coral", "azure", "crimson", "emerald"
]

NOUNS = [
    "panda", "dolphin", "eagle", "tiger", "dragon", "phoenix", "wizard",
    "knight", "castle", "river", "mountain", "ocean", "forest", "meadow",
    "valley", "storm", "comet", "star", "moon", "sun", "cloud", "thunder",
    "hawk", "wolf", "bear", "lion", "falcon", "raven", "fox", "deer"
]


def generate_game_name() -> str:
    """
    Generate a human-readable game name from 3-4 random words.

    Format: [Adjective] [Color] [Noun] or [Adjective] [Adjective] [Noun]

    Examples:
    - "brave golden dragon"
    - "clever swift eagle"
    - "gentle blue dolphin"
    """
    # 50% chance of including a color, otherwise use two adjectives
    if random.random() < 0.5:
        parts = [
            random.choice(ADJECTIVES),
            random.choice(COLORS),
            random.choice(NOUNS)
        ]
    else:
        parts = [
            random.choice(ADJECTIVES),
            random.choice(ADJECTIVES),
            random.choice(NOUNS)
        ]

    return " ".join(parts)
