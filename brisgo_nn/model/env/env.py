import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from env.cards import Deck, Card, compare_cards
from agents.opponent import RandomOpponent

class BriscolaEnv(gym.Env):

    metadata = {"render_modes": ["human"]}

    def __init__(self, opponent=None):
        super().__init__()

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(26,),
            dtype=np.float32
        )
        self.leader = ""  # Who starts the trick
        self.action_space = spaces.Discrete(3)

        self.opponent = opponent if opponent is not None else RandomOpponent()

        self.deck = None
        self.briscola_suit = None

        self.agent_hand = []
        self.opponent_hand = []
        self.table_card = None

        self.agent_points = 0
        self.opponent_points = 0
        self.step_count = 0
    
    def change_opponent(self, opponent):

        self.opponent = opponent if opponent is not None else RandomOpponent()
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.deck = Deck()
        self.deck.shuffle()

        # Draw briscola
        briscola_card = self.deck.draw()
        self.briscola_suit = briscola_card.suit
        self.deck.put_back(briscola_card)

        # Deal cards
        self.agent_hand = [self.deck.draw() for _ in range(3)]
        self.opponent_hand = [self.deck.draw() for _ in range(3)]

        self.agent_points = 0
        self.opponent_points = 0
        self.step_count = 0

        # Decide who starts the first hand
        self.leader = "agent" if random.random() < 0.5 else "opponent"
        self.table_card = None

        # If opponent starts, he plays immediately
        if self.leader == "opponent":
            opp_idx = self.opponent.play(
                self.opponent_hand,
                table_card=None,
                briscola_suit=self.briscola_suit
            )
            self.table_card = self.opponent_hand.pop(opp_idx)

        return self._get_state(), {}
 
    def step(self, action: int):
        reward = 0.0
        terminated = False
        truncated = False

        if action >= len(self.agent_hand):
            return self._get_state(), -10.0, False, False, {}

        agent_card = self.agent_hand.pop(action)

        # Trick solving
        if self.table_card is not None:
            # Opponent opened, agent responds
            first_card = self.table_card
            second_card = agent_card
            first_player = "opponent"
        else:
            # Agent opens, opponent responds
            first_card = agent_card
            opp_idx = self.opponent.play(
                self.opponent_hand,
                table_card=agent_card,
                briscola_suit=self.briscola_suit
            )
            second_card = self.opponent_hand.pop(opp_idx)
            first_player = "agent"

        # Decide winner
        winner_first = (compare_cards(first_card, second_card, self.briscola_suit) == 0)
        if winner_first:
            winner = first_player
        else:
            winner = "agent" if first_player == "opponent" else "opponent"

        # Assign points
        hand_points = first_card.points + second_card.points

        if winner == "agent":
            self.agent_points += hand_points
            reward += hand_points
        else:
            self.opponent_points += hand_points
            reward -= hand_points

        # Clear table and set leader
        self.table_card = None
        self.leader = winner

        # Draw cards (winner first)
        if len(self.deck) > 0:
            if winner == "agent":
                self.agent_hand.append(self.deck.draw())
                self.opponent_hand.append(self.deck.draw())
            else:
                self.opponent_hand.append(self.deck.draw())
                self.agent_hand.append(self.deck.draw())

        self.step_count += 1

        # Terminal condition
        if (
            len(self.deck) == 0
            and len(self.agent_hand) == 0
            and len(self.opponent_hand) == 0
        ):
            terminated = True
            if self.agent_points > self.opponent_points:
                reward += 100.0
            else:
                reward -= 100.0
            return self._get_state(), reward, terminated, truncated, {}

        # Opponent opens next hand (ONLY if he has cards)
        if self.leader == "opponent" and len(self.opponent_hand) > 0:
            opp_idx = self.opponent.play(
                self.opponent_hand,
                table_card=None,
                briscola_suit=self.briscola_suit
            )
            self.table_card = self.opponent_hand.pop(opp_idx)

        return self._get_state(), reward, terminated, truncated, {}

    def _get_state(self):
        state = []

        # --- Normalized step ---
        state.append(self.step_count / 20.0)

        # --- Normalized points ---
        state.append(self.agent_points / 120.0)

        # --- Agent hand (3 cards max) ---
        for i in range(3):
            if i < len(self.agent_hand):
                state.extend(self._encode_card(self.agent_hand[i]))
            else:
                state.extend([0.0] * 6)

        # --- Table card ---
        if self.table_card is not None:
            state.extend(self._encode_card(self.table_card))
        else:
            state.extend([0.0] * 6)

        assert len(state) == 26, f"State length is {len(state)}, expected 26"

        return np.array(state, dtype=np.float32)

    def _encode_card(self, card: Card):
        name_norm = card.name_id / 9.0
        is_briscola = 1.0 if card.suit == self.briscola_suit else 0.0
        suit_oh = self._encode_suit(card.suit)
        return [name_norm, is_briscola] + suit_oh

    def _encode_suit(self, suit: str):
        suits = ["batons", "cups", "coins", "swords"]
        return [1.0 if suit == s else 0.0 for s in suits]
    
    def render(self):
        print(f"Briscola: {self.briscola_suit}")
        print(f"Agent hand: {self.agent_hand}")
        print(f"Opponent hand: {len(self.opponent_hand)} cards")
        print(f"Points: agent={self.agent_points}, opp={self.opponent_points}")
    
