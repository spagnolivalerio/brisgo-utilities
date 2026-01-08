import os
import torch
from torch import nn
from flask import Flask, jsonify, request
from google.cloud import storage

class DQN(nn.Module):
    def __init__(self, state_dim: int, num_actions: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, num_actions)
        )

    def forward(self, x):
        return self.net(x)


STATE_DIM = 26
NUM_ACTIONS = 3

BUCKET_NAME = "brisgo_agent_bucket"        
MODEL_FILES = {
    "medium": ("dqn_briscola.pth", "/tmp/dqn_briscola.pth"),
    "hard": ("dqn_briscola_hard.pth", "/tmp/dqn_briscola_hard.pth"),
}

def download_weights(blob_name, local_path):
    if os.path.exists(local_path):
        return  

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)

def load_model(blob_name, local_path):
    download_weights(blob_name, local_path)
    model = DQN(state_dim=STATE_DIM, num_actions=NUM_ACTIONS)
    state_dict = torch.load(local_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model

app = Flask(__name__)
MODEL_CACHE = {}

def get_model(difficulty):
    if difficulty not in MODEL_FILES:
        return None
    if difficulty not in MODEL_CACHE:
        blob_name, local_path = MODEL_FILES[difficulty]
        MODEL_CACHE[difficulty] = load_model(blob_name, local_path)
    return MODEL_CACHE[difficulty]

@app.route("/act", methods=["POST"])
def act():
    payload = request.get_json(silent=True)
    if not payload or "state" not in payload or "difficulty" not in payload:
        return jsonify({"error": "Missing 'state' or 'difficulty' in JSON body"}), 400

    difficulty = payload["difficulty"]
    if difficulty not in MODEL_FILES:
        return jsonify({"error": "'difficulty' must be 'medium' or 'hard'"}), 400

    state = payload["state"]
    if not isinstance(state, list) or len(state) != STATE_DIM:
        return jsonify({"error": f"'state' must be a list of length {STATE_DIM}"}), 400

    try:
        state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
    except (TypeError, ValueError):
        return jsonify({"error": "'state' must be a list of numbers"}), 400

    model = get_model(difficulty)
    with torch.no_grad():
        q_values = model(state_t)
        action = int(torch.argmax(q_values, dim=1).item())

    return jsonify({"action": action})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
