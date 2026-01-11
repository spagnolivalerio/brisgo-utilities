import argparse
import random

import torch

from model import DQN
from env.cards import Deck, compare_cards


SUITS = ["batons", "cups", "coins", "swords"]


def encode_card(card, briscola_suit):
    name_norm = card.name_id / 9.0
    is_briscola = 1.0 if card.suit == briscola_suit else 0.0
    suit_oh = [1.0 if card.suit == s else 0.0 for s in SUITS]
    return [name_norm, is_briscola] + suit_oh


def get_state(step_count, agent_points, agent_hand, table_card, briscola_suit):
    state = []
    state.append(step_count / 20.0)
    state.append(agent_points / 120.0)

    for i in range(3):
        if i < len(agent_hand):
            state.extend(encode_card(agent_hand[i], briscola_suit))
        else:
            state.extend([0.0] * 6)

    if table_card is not None:
        state.extend(encode_card(table_card, briscola_suit))
    else:
        state.extend([0.0] * 6)

    return torch.tensor(state, dtype=torch.float32).unsqueeze(0)


def select_model_action(model, state_t, valid_len, device):
    with torch.no_grad():
        q_values = model(state_t.to(device)).squeeze(0).cpu()

    if valid_len <= 0:
        return 0

    mask = torch.full_like(q_values, -1e9)
    mask[:valid_len] = 0.0
    masked_q = q_values + mask
    return int(torch.argmax(masked_q).item())


def prompt_human_action(hand, table_card, briscola_suit):
    print("")
    print(f"Briscola: {briscola_suit}")
    if table_card is not None:
        print(f"Table: {table_card}")
    else:
        print("Table: (empty)")
    print("Your hand:")
    for i, card in enumerate(hand):
        is_briscola = " (briscola)" if card.suit == briscola_suit else ""
        print(f"  [{i}] {card}{is_briscola}")

    while True:
        raw = input("Choose card index: ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 0 <= idx < len(hand):
                return idx
        print("Invalid choice, try again.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="dqn_briscola.pth")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    device = args.device
    model = DQN(26, 3).to(device)
    model.load_state_dict(torch.load(args.model, map_location=device))
    model.eval()

    deck = Deck()
    deck.shuffle()

    briscola_card = deck.draw()
    briscola_suit = briscola_card.suit
    deck.put_back(briscola_card)

    agent_hand = [deck.draw() for _ in range(3)]
    human_hand = [deck.draw() for _ in range(3)]

    agent_points = 0
    human_points = 0
    step_count = 0

    leader = "agent" if random.random() < 0.5 else "human"
    table_card = None

    print("You are playing against the trained agent.")
    print(f"Briscola suit: {briscola_suit}")
    print(f"Starting player: {leader}")

    while True:
        if leader == "agent":
            state_t = get_state(step_count, agent_points, agent_hand, None, briscola_suit)
            action = select_model_action(model, state_t, len(agent_hand), device)
            agent_card = agent_hand.pop(action)
            table_card = agent_card

            human_idx = prompt_human_action(human_hand, table_card, briscola_suit)
            human_card = human_hand.pop(human_idx)

            first_card = agent_card
            second_card = human_card
            first_player = "agent"
        else:
            human_idx = prompt_human_action(human_hand, None, briscola_suit)
            human_card = human_hand.pop(human_idx)
            table_card = human_card

            state_t = get_state(step_count, agent_points, agent_hand, table_card, briscola_suit)
            action = select_model_action(model, state_t, len(agent_hand), device)
            agent_card = agent_hand.pop(action)

            first_card = human_card
            second_card = agent_card
            first_player = "human"

        winner_first = (compare_cards(first_card, second_card, briscola_suit) == 0)
        if winner_first:
            winner = first_player
        else:
            winner = "agent" if first_player == "human" else "human"

        hand_points = first_card.points + second_card.points
        if winner == "agent":
            agent_points += hand_points
        else:
            human_points += hand_points

        print("")
        print(f"Hand: {first_card} vs {second_card}")
        print(f"Winner: {winner} (+{hand_points} points)")
        print(f"Score: agent={agent_points} | human={human_points}")

        table_card = None
        leader = winner
        step_count += 1

        if len(deck) > 0:
            if winner == "agent":
                agent_hand.append(deck.draw())
                human_hand.append(deck.draw())
            else:
                human_hand.append(deck.draw())
                agent_hand.append(deck.draw())

        if len(deck) == 0 and len(agent_hand) == 0 and len(human_hand) == 0:
            break

    print("")
    if agent_points > human_points:
        print("Final: agent wins.")
    elif human_points > agent_points:
        print("Final: you win.")
    else:
        print("Final: draw.")


if __name__ == "__main__":
    main()
