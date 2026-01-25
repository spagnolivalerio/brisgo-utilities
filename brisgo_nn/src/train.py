import random
import numpy as np
from model import DQN, ReplayBuffer

import torch
import torch.nn as nn
import torch.optim as optim
import argparse


from env.env import BriscolaEnv
from agents.opponent import RandomOpponent
from agents.rule_based_agent_v1 import RuleBasedOpponent
from agents.rule_based_agent_v2 import RuleBasedOpponentV2
from agents.rule_based_agent_v3 import RuleBasedOpponentV3

class DQNTrainer:
    def __init__(
        self,
        env,
        gamma=0.95,
        lr=1e-3,
        buffer_size=100_000,
        batch_size=64,
        eps_start=1.0,
        eps_end=0.05,
        eps_decay=0.999,
        device="cpu", 
        num_nodes=None,
    ):
        self.env = env
        self.device = device

        self.state_dim = env.observation_space.shape[0]
        self.num_actions = env.action_space.n

        if num_nodes: 
            self.q_net = DQN(self.state_dim, self.num_actions, num_nodes=num_nodes).to(device)
        else: 
            self.q_net = DQN(self.state_dim, self.num_actions).to(device)
            
        self.optimizer = optim.RMSprop(self.q_net.parameters(), lr=lr)
        self.loss_fn = nn.SmoothL1Loss()

        self.buffer = ReplayBuffer(buffer_size)

        self.gamma = gamma
        self.batch_size = batch_size

        self.eps = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay

    def select_action(self, state):
        if random.random() < self.eps:
            return self.env.action_space.sample()
        else:
            state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_values = self.q_net(state_t)
            return torch.argmax(q_values).item()

    def train_step(self):
        if len(self.buffer) < self.batch_size:
            return None

        batch = self.buffer.sample(self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.tensor(states, dtype=torch.float32).to(self.device)
        actions = torch.tensor(actions, dtype=torch.int64).unsqueeze(1).to(self.device)
        rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1).to(self.device)
        next_states = torch.tensor(next_states, dtype=torch.float32).to(self.device)
        dones = torch.tensor(dones, dtype=torch.float32).unsqueeze(1).to(self.device)

        q_values = self.q_net(states).gather(1, actions)

        with torch.no_grad():
            max_next_q = self.q_net(next_states).max(1, keepdim=True)[0]
            target_q = rewards + self.gamma * max_next_q * (1 - dones)

        loss = self.loss_fn(q_values, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def train(self, episodes=100000):

        rewards_history = []

        for ep in range(episodes):
            
            opponent_name = str(random.randint(1, 3))
            opponent = get_opponent(opponent_name)
            self.env.opponent = opponent
            
            state, _ = self.env.reset()
            done = False
            ep_reward = 0

            while not done:
                action = self.select_action(state)
                next_state, reward, terminated, truncated, _ = self.env.step(action)
                done = terminated or truncated

                self.buffer.add(state, action, reward, next_state, done)
                self.train_step()

                state = next_state
                ep_reward += reward

            self.eps = max(self.eps * self.eps_decay, self.eps_end)
            rewards_history.append(ep_reward)

            if ep % 100 == 0:
                avg = np.mean(rewards_history[-100:])
                print(f"Episode {ep} | avg reward (last 100): {avg:.2f} | eps: {self.eps:.3f}")

        return rewards_history

def get_opponent(name: str):
    name = name.lower().strip()
    if name in {"1"}:
        return RuleBasedOpponent()
    if name in {"2"}:
        return RuleBasedOpponentV2()
    if name in {"3"}:
        return RuleBasedOpponentV3()
    return RandomOpponent()

def make_env(opponent_name: str = None, aug: bool = False):
    if opponent_name:
        opponent = get_opponent(opponent_name)
        return BriscolaEnv(opponent=opponent, aug=aug)
    return BriscolaEnv(aug=aug)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--aug", default="False")
    args = parser.parse_args()

    aug = args.aug
    aug = True if aug == "True" else False
    env = make_env(aug=aug)

    print(f"State dim: {env.observation_space.shape[0]}")

    trainer = DQNTrainer(env, num_nodes=128 if aug else None)

    trainer.train(episodes=500000)

    torch.save(trainer.q_net.state_dict(), "aug_hard.pth")

if __name__ == "__main__":

    main()
