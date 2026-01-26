## DQN perfomances

The rule-based opponents are different agents that use deterministic rules and strategies, more or less conservative, following classic heuristics of the game of briscola.

| name | random | rule based v1 | rule based v2 | rule based v3 |
| --- | --- | --- | --- | --- |
| dqn_random_agent | 90% | 39% | 39.5% | 40% |
| dqn_rule_based_v2 | 81% | 63.3 | 65.5% | 66% |
| dqn_opponents_pool | 70% | 66% | 65% | 62% |
| dqn_augmented | 66.2 % | 62.3% | 62.8% | 66.8% |

Strategy notes:
- v1: conservative discard, wins with non-briscola when possible, uses briscola only if table points >= 5.
- v2: avoids winning zero-point hands with high-value cards; uses briscola based on a points threshold that drops late in the hand.
- v3: load-aware (ace/three), avoids spending loads, plays loads only if the table card is not briscola; uses briscola to win only with >= 5 points on the table.
