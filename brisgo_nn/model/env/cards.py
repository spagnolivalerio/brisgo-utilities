import random

SUITS = ["batons", "cups", "coins", "swords"]

CARD_NAMES = [
    "ace", "two", "three", "four", "five",
    "six", "seven", "jack", "knight", "king"
]

CARD_POINTS = {
    "ace": 11,
    "three": 10,
    "king": 4,
    "knight": 3,
    "jack": 2,
    "two": 0,
    "four": 0,
    "five": 0,
    "six": 0,
    "seven": 0,
}

class Card:

    def __init__(self, name: str, suit: str):
        assert name in CARD_NAMES
        assert suit in SUITS

        self.name = name
        self.suit = suit
        self.points = CARD_POINTS[name]
        self.name_id = CARD_NAMES.index(name)

    def __repr__(self):
        return f"{self.name.capitalize()} of {self.suit.capitalize()}"

class Deck:

    def __init__(self):
        self.cards = [
            Card(name, suit)
            for suit in SUITS
            for name in CARD_NAMES
        ]

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card:
        assert len(self.cards) > 0, "Deck is empty"
        return self.cards.pop(0)

    def put_back(self, card: Card):
        # Put a card on the back of the deck (used for the briscola)
        self.cards.append(card)

    def __len__(self):
        return len(self.cards)

BRISCOLA_RANK = {
    "ace": 9,
    "three": 8,
    "king": 7,
    "knight": 6,
    "jack": 5,
    "seven": 4,
    "six": 3,
    "five": 2,
    "four": 1,
    "two": 0,
}

def compare_cards(first_card: Card, second_card: Card, briscola_suit: str) -> int:

    if first_card.suit == second_card.suit:
        return 0 if BRISCOLA_RANK[first_card.name] > BRISCOLA_RANK[second_card.name] else 1

    if first_card.suit == briscola_suit:
        return 0
    if second_card.suit == briscola_suit:
        return 1

    return 0
