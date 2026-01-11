import argparse

import torch

from model import DQN
from env.env import BriscolaEnv
from agents.opponent import RandomOpponent
from agents.rule_based_agent_v1 import RuleBasedOpponent


def select_action(model, state, env, device):
    state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        q_values = model(state_t).squeeze(0)

    valid_len = len(env.agent_hand)
    if valid_len <= 0:
        return 0

    mask = torch.full_like(q_values, -1e9)
    mask[:valid_len] = 0.0
    masked_q = q_values + mask
    return int(torch.argmax(masked_q).item())


def play_episode(model, opponent, device):
    env = BriscolaEnv(opponent=opponent)
    state, _ = env.reset()
    done = False

    while not done:
        action = select_action(model, state, env, device)
        state, _, terminated, truncated, _ = env.step(action)
        done = terminated or truncated

    if env.agent_points > env.opponent_points:
        return "win"
    if env.agent_points < env.opponent_points:
        return "loss"
    return "draw"


def evaluate(model, opponent, episodes, device):
    results = {"win": 0, "loss": 0, "draw": 0}
    for _ in range(episodes):
        outcome = play_episode(model, opponent, device)
        results[outcome] += 1
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="dqn_briscola.pth")
    parser.add_argument("--episodes", type=int, default=1000)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    env = BriscolaEnv()
    state_dim = env.observation_space.shape[0]
    num_actions = env.action_space.n

    model = DQN(state_dim, num_actions).to(args.device)
    model.load_state_dict(torch.load(args.model, map_location=args.device))
    model.eval()

    scenarios = [
        ("random", RandomOpponent()),
        ("rule_based", RuleBasedOpponent()),
    ]

    for name, opp in scenarios:
        results = evaluate(model, opp, args.episodes, args.device)
        win_rate = results["win"] / args.episodes * 100.0
        print(
            f"{name}: win {results['win']} / {args.episodes} "
            f"({win_rate:.1f}%), loss {results['loss']}, draw {results['draw']}"
        )


if __name__ == "__main__":
    main()
