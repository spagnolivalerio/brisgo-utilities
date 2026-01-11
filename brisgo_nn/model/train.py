import random
import numpy as np
from model import DQN, ReplayBuffer

import torch
import torch.nn as nn
import torch.optim as optim

from env.env import BriscolaEnv
from agents.opponent import RandomOpponent
from agents.rule_based_agent_v1 import RuleBasedOpponent

AGENT = "rule_based"

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
        device="cpu"
    ):
        self.env = env
        self.device = device

        self.state_dim = env.observation_space.shape[0]
        self.num_actions = env.action_space.n

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
    if name in {"rule", "rule_based", "rulebased"}:
        return RuleBasedOpponent()
    if name in {"random", "rnd"}:
        return RandomOpponent()
    raise ValueError(f"Unknown opponent: {name}")

def make_env(opponent_name: str):
    opponent = get_opponent(opponent_name)
    return BriscolaEnv(opponent=opponent)

if __name__ == "__main__":

    env = make_env(AGENT)
    trainer = DQNTrainer(env)

    trainer.train(episodes=500000)

    torch.save(trainer.q_net.state_dict(), "dqn_briscola.pth")
