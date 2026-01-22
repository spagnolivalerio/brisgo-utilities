from typing import List

from env.cards import Card, CARD_RANKS, compare_cards
from .opponent import Opponent


class RuleBasedOpponent(Opponent):

    def play(self, hand: List[Card], table_card: Card, briscola_suit: str) -> int:
        assert len(hand) > 0, "Opponent hand is empty"

        if table_card is None:
            return self._lead(hand, briscola_suit)

        return self._respond(hand, table_card, briscola_suit)

    def _lead(self, hand: List[Card], briscola_suit: str) -> int:
        non_briscola = [i for i, c in enumerate(hand) if c.suit != briscola_suit]
        if non_briscola:
            return min(non_briscola, key=lambda i: self._discard_cost(hand[i], briscola_suit))
        return min(range(len(hand)), key=lambda i: self._discard_cost(hand[i], briscola_suit))

    def _respond(self, hand: List[Card], table_card: Card, briscola_suit: str) -> int:
        points_on_table = table_card.points
        winning = [i for i, c in enumerate(hand) if self._wins(c, table_card, briscola_suit)]

        if winning:
            non_briscola_win = [
                i for i in winning if hand[i].suit != briscola_suit
            ]
            if non_briscola_win:
                return min(non_briscola_win, key=lambda i: self._win_cost(hand[i]))

            # Only briscola can win: spend them only if worth the points.
            if points_on_table >= 5:
                return min(winning, key=lambda i: self._win_cost(hand[i]))

        return self._discard(hand, briscola_suit)

    def _discard(self, hand: List[Card], briscola_suit: str) -> int:
        non_briscola = [i for i, c in enumerate(hand) if c.suit != briscola_suit]
        if non_briscola:
            return min(non_briscola, key=lambda i: self._discard_cost(hand[i], briscola_suit))
        return min(range(len(hand)), key=lambda i: self._discard_cost(hand[i], briscola_suit))

    def _wins(self, card: Card, table_card: Card, briscola_suit: str) -> bool:
        return compare_cards(table_card, card, briscola_suit) == 1

    def _win_cost(self, card: Card) -> tuple:
        return (card.points, CARD_RANKS[card.name])

    def _discard_cost(self, card: Card, briscola_suit: str) -> tuple:
        is_briscola = 1 if card.suit == briscola_suit else 0
        return (card.points, is_briscola, CARD_RANKS[card.name])
