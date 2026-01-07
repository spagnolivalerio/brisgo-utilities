import os
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, CheckConstraint, UniqueConstraint

# --------------------------------------------------
# App & DB configuration (Cloud SQL only)
# --------------------------------------------------

app = Flask(__name__)

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]
INSTANCE_CONNECTION_NAME = os.environ["INSTANCE_CONNECTION_NAME"]

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+mysqldb://{DB_USER}:{DB_PASSWORD}@/"
    f"{DB_NAME}?unix_socket=/cloudsql/{INSTANCE_CONNECTION_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --------------------------------------------------
# Models
# --------------------------------------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False, unique=True)
    name = db.Column(db.String(32), nullable=False)
    lastname = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(64), nullable=False)
    firebase_code = db.Column(db.String(50))
    friend_code = db.Column(db.String(16), nullable=False, unique=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "lastname": self.lastname,
            "nickname": self.nickname,
            "firebase_code": self.firebase_code,
            "friend_code": self.friend_code,
        }


class Friendship(db.Model):
    __tablename__ = "friendships"
    __table_args__ = (
        CheckConstraint("user_id <> friend_id", name="ck_friendships_user_friend"),
        UniqueConstraint("user_id", "friend_id", name="uq_friendships_pair"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(
        Enum("pending", "accepted", "rejected", name="friendship_status"),
        nullable=False,
        server_default="pending",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "friend_id": self.friend_id,
            "status": self.status,
        }


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    match_type = db.Column(Enum("1v1", "2v2", name="match_type"), nullable=False)
    mode = db.Column(Enum("online", "cpu", name="match_mode"), nullable=False)
    status = db.Column(Enum("finished", "aborted", name="match_status"), nullable=False)
    team1_points = db.Column(db.SmallInteger, nullable=False, server_default="0")
    team2_points = db.Column(db.SmallInteger, nullable=False, server_default="0")

    def to_dict(self):
        return {
            "id": self.id,
            "match_type": self.match_type,
            "mode": self.mode,
            "status": self.status,
            "team1_points": self.team1_points,
            "team2_points": self.team2_points,
        }


class MatchPlayer(db.Model):
    __tablename__ = "match_players"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    team_index = db.Column(Enum("team1", "team2", name="team_index"))

    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "user_id": self.user_id,
            "team_index": self.team_index,
        }


class MatchInvite(db.Model):
    __tablename__ = "match_invite"
    __table_args__ = (
        CheckConstraint("inviter_id <> invitee_id", name="ck_invite_users"),
    )

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(32), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(
        Enum("pending", "accept", "rejected", name="invite_status"),
        nullable=False,
        server_default="pending",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "inviter_id": self.inviter_id,
            "invitee_id": self.invitee_id,
            "status": self.status,
        }

# --------------------------------------------------
# Helpers & errors
# --------------------------------------------------

def parse_json(required_fields=None):
    if not request.is_json:
        abort(400, description="Expected application/json")
    payload = request.get_json()
    if required_fields:
        missing = [f for f in required_fields if f not in payload]
        if missing:
            abort(400, description=f"Missing fields: {', '.join(missing)}")
    return payload


@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(err):
    return jsonify({"error": str(err)}), err.code

# --------------------------------------------------
# Health & init
# --------------------------------------------------

@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/init")
def init_db():
    db.create_all()
    return jsonify({"status": "initialized"})

# --------------------------------------------------
# Users
# --------------------------------------------------

@app.post("/users")
def create_user():
    payload = parse_json(
        ["username", "name", "lastname", "password", "nickname", "friend_code"]
    )
    user = User(
        username=payload["username"],
        name=payload["name"],
        lastname=payload["lastname"],
        password=payload["password"],
        nickname=payload["nickname"],
        firebase_code=payload.get("firebase_code"),
        friend_code=payload["friend_code"],
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@app.get("/users")
def list_users():
    query = User.query
    if "username" in request.args:
        query = query.filter_by(username=request.args["username"])
    if "friend_code" in request.args:
        query = query.filter_by(friend_code=request.args["friend_code"])
    if "nickname" in request.args:
        query = query.filter_by(nickname=request.args["nickname"])
    return jsonify([u.to_dict() for u in query.all()])


@app.get("/users/<int:user_id>")
def get_user(user_id):
    return jsonify(User.query.get_or_404(user_id).to_dict())


@app.patch("/users/<int:user_id>")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    payload = parse_json()
    for field in payload:
        if hasattr(user, field):
            setattr(user, field, payload[field])
    db.session.commit()
    return jsonify(user.to_dict())


@app.delete("/users/<int:user_id>")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return "", 204

# --------------------------------------------------
# Friendships
# --------------------------------------------------

@app.post("/friendships")
def create_friendship():
    payload = parse_json(["user_id", "friend_id"])
    friendship = Friendship(
        user_id=payload["user_id"],
        friend_id=payload["friend_id"],
        status=payload.get("status", "pending"),
    )
    db.session.add(friendship)
    db.session.commit()
    return jsonify(friendship.to_dict()), 201


@app.get("/friendships")
def list_friendships():
    query = Friendship.query
    if "user_id" in request.args:
        uid = int(request.args["user_id"])
        query = query.filter(
            (Friendship.user_id == uid) | (Friendship.friend_id == uid)
        )
    if "status" in request.args:
        query = query.filter_by(status=request.args["status"])
    return jsonify([f.to_dict() for f in query.all()])


@app.patch("/friendships/<int:friendship_id>")
def update_friendship(friendship_id):
    friendship = Friendship.query.get_or_404(friendship_id)
    payload = parse_json(["status"])
    friendship.status = payload["status"]
    db.session.commit()
    return jsonify(friendship.to_dict())


@app.delete("/friendships/<int:friendship_id>")
def delete_friendship(friendship_id):
    friendship = Friendship.query.get_or_404(friendship_id)
    db.session.delete(friendship)
    db.session.commit()
    return "", 204

# --------------------------------------------------
# Matches
# --------------------------------------------------

@app.post("/matches")
def create_match():
    payload = parse_json(["match_type", "mode", "status"])
    match = Match(**payload)
    db.session.add(match)
    db.session.commit()
    return jsonify(match.to_dict()), 201


@app.get("/matches")
def list_matches():
    query = Match.query
    for field in ["status", "match_type"]:
        if field in request.args:
            query = query.filter_by(**{field: request.args[field]})
    return jsonify([m.to_dict() for m in query.all()])


@app.patch("/matches/<int:match_id>")
def update_match(match_id):
    match = Match.query.get_or_404(match_id)
    payload = parse_json()
    for field in payload:
        if hasattr(match, field):
            setattr(match, field, payload[field])
    db.session.commit()
    return jsonify(match.to_dict())


@app.delete("/matches/<int:match_id>")
def delete_match(match_id):
    match = Match.query.get_or_404(match_id)
    db.session.delete(match)
    db.session.commit()
    return "", 204

# --------------------------------------------------
# Match players
# --------------------------------------------------

@app.post("/match-players")
def create_match_player():
    payload = parse_json(["match_id", "user_id"])
    mp = MatchPlayer(**payload)
    db.session.add(mp)
    db.session.commit()
    return jsonify(mp.to_dict()), 201


@app.get("/match-players")
def list_match_players():
    query = MatchPlayer.query
    for field in ["match_id", "user_id"]:
        if field in request.args:
            query = query.filter_by(**{field: int(request.args[field])})
    return jsonify([p.to_dict() for p in query.all()])

# --------------------------------------------------
# Match invites
# --------------------------------------------------

@app.post("/match-invites")
def create_match_invite():
    payload = parse_json(["room_id", "inviter_id", "invitee_id"])
    invite = MatchInvite(**payload)
    db.session.add(invite)
    db.session.commit()
    return jsonify(invite.to_dict()), 201


@app.get("/match-invites")
def list_match_invites():
    query = MatchInvite.query
    for field in ["inviter_id", "invitee_id", "status"]:
        if field in request.args:
            query = query.filter_by(**{field: request.args[field]})
    return jsonify([i.to_dict() for i in query.all()])


@app.patch("/match-invites/<int:invite_id>")
def update_match_invite(invite_id):
    invite = MatchInvite.query.get_or_404(invite_id)
    payload = parse_json(["status"])
    invite.status = payload["status"]
    db.session.commit()
    return jsonify(invite.to_dict())


@app.delete("/match-invites/<int:invite_id>")
def delete_match_invite(invite_id):
    invite = MatchInvite.query.get_or_404(invite_id)
    db.session.delete(invite)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
