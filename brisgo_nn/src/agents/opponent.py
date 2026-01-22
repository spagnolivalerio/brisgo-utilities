import random
from typing import List
from env.cards import Card

class Opponent:

    def play(self, hand: List[Card], table_card: Card, briscola_suit: str) -> int:
        raise NotImplementedError
    
class RandomOpponent(Opponent):

    def play(self, hand: List[Card], table_card: Card, briscola_suit: str) -> int:
        assert len(hand) > 0, "Opponent hand is empty"
        return random.randrange(len(hand))


