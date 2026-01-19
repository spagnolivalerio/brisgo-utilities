from typing import List

from env.cards import Card, BRISCOLA_RANK, compare_cards
from .opponent import Opponent


class RuleBasedOpponentV2(Opponent):

    def play(self, hand: List[Card], table_card: Card, briscola_suit: str) -> int:
        assert len(hand) > 0, "Opponent hand is empty"

        if table_card is None:
            return self._lead(hand, briscola_suit)

        return self._respond(hand, table_card, briscola_suit)

    def _lead(self, hand: List[Card], briscola_suit: str) -> int:
        non_briscola = [i for i, c in enumerate(hand) if c.suit != briscola_suit]
        if non_briscola:
            return min(non_briscola, key=lambda i: self._lead_cost(hand[i], briscola_suit))
        return min(range(len(hand)), key=lambda i: self._lead_cost(hand[i], briscola_suit))

    def _respond(self, hand: List[Card], table_card: Card, briscola_suit: str) -> int:
        points_on_table = table_card.points
        winning = [i for i, c in enumerate(hand) if self._wins(c, table_card, briscola_suit)]

        if winning:
            winning_non_briscola = [
                i for i in winning if hand[i].suit != briscola_suit
            ]
            if winning_non_briscola:
                choice = min(winning_non_briscola, key=lambda i: self._win_cost(hand[i]))
                if points_on_table == 0 and hand[choice].points >= 10:
                    return self._discard(hand, briscola_suit)
                return choice

            winning_briscola = [i for i in winning if hand[i].suit == briscola_suit]
            choice = min(winning_briscola, key=lambda i: self._briscola_spend_cost(hand[i]))
            if self._should_use_briscola(points_on_table, hand[choice], len(hand)):
                return choice

        return self._discard(hand, briscola_suit)

    def _discard(self, hand: List[Card], briscola_suit: str) -> int:
        non_briscola = [i for i, c in enumerate(hand) if c.suit != briscola_suit]
        if non_briscola:
            return min(non_briscola, key=lambda i: self._discard_cost(hand[i], briscola_suit))
        return min(range(len(hand)), key=lambda i: self._discard_cost(hand[i], briscola_suit))

    def _wins(self, card: Card, table_card: Card, briscola_suit: str) -> bool:
        return compare_cards(table_card, card, briscola_suit) == 1

    def _win_cost(self, card: Card) -> tuple:
        return (card.points, BRISCOLA_RANK[card.name])

    def _briscola_spend_cost(self, card: Card) -> tuple:
        return (BRISCOLA_RANK[card.name], card.points)

    def _discard_cost(self, card: Card, briscola_suit: str) -> tuple:
        is_briscola = 1 if card.suit == briscola_suit else 0
        return (card.points, is_briscola, BRISCOLA_RANK[card.name])

    def _lead_cost(self, card: Card, briscola_suit: str) -> tuple:
        is_briscola = 1 if card.suit == briscola_suit else 0
        return (is_briscola, card.points, BRISCOLA_RANK[card.name])

    def _should_use_briscola(self, points_on_table: int, card: Card, hand_size: int) -> bool:
        threshold = 5
        if hand_size <= 2:
            threshold = 2
        if card.points >= 10:
            threshold += 2
        if points_on_table >= threshold:
            return True
        if hand_size <= 2 and card.points <= 2 and points_on_table > 0:
            return True
        return False
