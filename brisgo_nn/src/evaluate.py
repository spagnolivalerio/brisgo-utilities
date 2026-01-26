import argparse

import torch

from model import DQN
from env.env import BriscolaEnv
from agents.rule_based_agent_v1 import RuleBasedOpponent
from agents.rule_based_agent_v2 import RuleBasedOpponentV2
from agents.rule_based_agent_v3 import RuleBasedOpponentV3


def select_action(model, state, env, device):
    state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        q_values = model(state_t).squeeze(0)

    valid_len = len(env.agent_hand)
    if valid_len <= 0:
        return 0

    # to handle not valid actions
    mask = torch.full_like(q_values, -1e9)
    mask[:valid_len] = 0.0
    masked_q = q_values + mask
    return int(torch.argmax(masked_q).item())


def play_episode(model, opponent, device, aug=False):
    env = BriscolaEnv(opponent=opponent, aug=aug)
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


def evaluate(model, opponent, episodes, device, aug=False):
    results = {"win": 0, "loss": 0, "draw": 0}
    for _ in range(episodes):
        outcome = play_episode(model, opponent, device, aug=aug)
        results[outcome] += 1
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    episodes = 5000
    models = [
        ("opponents_pool", "weights/dqn_briscola_opponents_pool.pth", False, None),
        ("rule_based500k", "weights/rule_based_500kep.pth", False, None),
        ("random_100k", "weights/random_agent_100k.pth", False, None),
        ("aug_hard", "weights/aug_hard.pth", True, 128),
    ]

    scenarios = [
        ("rule_based", RuleBasedOpponent()),
        ("rule_based_v2", RuleBasedOpponentV2()),
        ("rule_based_v3", RuleBasedOpponentV3()),
    ]

    for model_name, model_path, aug, num_nodes in models:
        env = BriscolaEnv(aug=aug)
        state_dim = env.observation_space.shape[0]
        num_actions = env.action_space.n
        if num_nodes is None:
            model = DQN(state_dim, num_actions).to(args.device)
        else:
            model = DQN(state_dim, num_actions, num_nodes=num_nodes).to(args.device)
        model.load_state_dict(torch.load(model_path, map_location=args.device))
        model.eval()
        print(f"model: {model_name} ({model_path}) aug={aug} nodes={num_nodes or 64}")
        for name, opp in scenarios:
            results = evaluate(model, opp, episodes, args.device, aug=aug)
            win_rate = results["win"] / episodes * 100.0
            print(
                f"  {name}: win {results['win']} / {episodes} "
                f"({win_rate:.1f}%), loss {results['loss']}, draw {results['draw']}"
            )


if __name__ == "__main__":
    main()
