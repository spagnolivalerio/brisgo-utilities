from typing import List

from env.cards import Card, CARD_RANKS, compare_cards
from .opponent import Opponent


class RuleBasedOpponentV3(Opponent):

    LOAD_NAMES = {"ace", "three"}

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
            non_briscola_win = [
                i for i in winning
                if hand[i].suit != briscola_suit and not self._is_load(hand[i])
            ]
            if non_briscola_win:
                return min(non_briscola_win, key=lambda i: self._win_cost(hand[i]))

            load_win = [
                i for i in winning
                if hand[i].suit != briscola_suit and self._is_load(hand[i])
            ]
            if load_win and self._allow_load_response(table_card, briscola_suit):
                return min(load_win, key=lambda i: self._win_cost(hand[i]))

            briscola_win = [
                i for i in winning
                if hand[i].suit == briscola_suit and not self._is_load(hand[i])
            ]
            if briscola_win and points_on_table >= 5:
                return min(briscola_win, key=lambda i: self._win_cost(hand[i]))

        return self._discard(hand, briscola_suit)

    def _discard(self, hand: List[Card], briscola_suit: str) -> int:
        non_briscola = [i for i, c in enumerate(hand) if c.suit != briscola_suit]
        if non_briscola:
            return min(non_briscola, key=lambda i: self._discard_cost(hand[i], briscola_suit))
        return min(range(len(hand)), key=lambda i: self._discard_cost(hand[i], briscola_suit))

    def _wins(self, card: Card, table_card: Card, briscola_suit: str) -> bool:
        return compare_cards(table_card, card, briscola_suit) == 1

    def _is_load(self, card: Card) -> bool:
        return card.name in self.LOAD_NAMES

    def _allow_load_response(self, table_card: Card, briscola_suit: str) -> bool:
        return table_card.suit != briscola_suit

    def _win_cost(self, card: Card) -> tuple:
        return (card.points, CARD_RANKS[card.name])

    def _discard_cost(self, card: Card, briscola_suit: str) -> tuple:
        is_briscola = 1 if card.suit == briscola_suit else 0
        is_load = 1 if self._is_load(card) else 0
        return (is_load, card.points, is_briscola, CARD_RANKS[card.name])

    def _lead_cost(self, card: Card, briscola_suit: str) -> tuple:
        is_briscola = 1 if card.suit == briscola_suit else 0
        is_load = 1 if self._is_load(card) else 0
        return (is_briscola, is_load, card.points, CARD_RANKS[card.name])
