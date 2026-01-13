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


def generate_game_name(seed: int | None = None) -> str:
    """
    Generate a human-readable game name from 3-4 random words.

    Format: [Adjective] [Color] [Noun] or [Adjective] [Adjective] [Noun]

    Args:
        seed: Optional seed for random number generator. If provided, the same
              seed will always generate the same name (useful for game UUIDs).

    Examples:
    - "brave golden dragon"
    - "clever swift eagle"
    - "gentle blue dolphin"
    """
    # Create a new random instance to avoid affecting global state
    rng = random.Random(seed)

    # 50% chance of including a color, otherwise use two adjectives
    if rng.random() < 0.5:
        parts = [
            rng.choice(ADJECTIVES),
            rng.choice(COLORS),
            rng.choice(NOUNS)
        ]
    else:
        parts = [
            rng.choice(ADJECTIVES),
            rng.choice(ADJECTIVES),
            rng.choice(NOUNS)
        ]

    return " ".join(parts)
