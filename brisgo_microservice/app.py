import base64
import os
import secrets
import string
from dotenv import load_dotenv
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGBLOB

# --------------------------------------------------
# App & DB configuration (local DBMS)
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DB_USER = "valerio"
DB_PASSWORD = "root"
DB_NAME = "brisgo"
DB_HOST = "localhost"
DB_PORT = os.getenv("DB_PORT", "3306")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DEBUG"] = True

db = SQLAlchemy(app)

# --------------------------------------------------
# Models
# --------------------------------------------------

class User(db.Model):
    __tablename__ = "USERS"

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64))
    firebase_code = db.Column(db.String(50), unique=True)
    friend_code = db.Column(db.String(16), nullable=False, unique=True)
    photo = db.Column(LONGBLOB)
    cups = db.Column(db.Integer, nullable=False, server_default="0")

    def to_dict(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "firebase_code": self.firebase_code,
            "friend_code": self.friend_code,
            "cups": self.cups
        }


class Friendship(db.Model):
    __tablename__ = "FRIENDSHIPS"
    __table_args__ = (
        CheckConstraint("user_id <> friend_id", name="ck_friendships_user_friend"),
        UniqueConstraint("user_id", "friend_id", name="uq_friendships_pair"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("USERS.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("USERS.id"), nullable=False)
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
    __tablename__ = "MATCHES"

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
    __tablename__ = "MATCH_PLAYERS"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("USERS.id"), nullable=False)
    team_index = db.Column(Enum("team1", "team2", name="team_index"))

    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "user_id": self.user_id,
            "team_index": self.team_index,
        }


class MatchInvite(db.Model):
    __tablename__ = "MATCH_INVITE"
    __table_args__ = (
        CheckConstraint("inviter_id <> invitee_id", name="ck_invite_users"),
    )

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(100), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey("USERS.id"), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey("USERS.id"), nullable=False)
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


def generate_friend_code():
    letters = string.ascii_uppercase
    digits = string.digits
    while True:
        code = "".join(
            [
                secrets.choice(letters),
                secrets.choice(letters),
                secrets.choice(digits),
                secrets.choice(digits),
                secrets.choice(digits),
                secrets.choice(digits),
                secrets.choice(letters),
                secrets.choice(letters),
            ]
        )
        if not User.query.filter_by(friend_code=code).first():
            return code


def get_user_by_firebase(firebase_code):
    return User.query.filter_by(firebase_code=firebase_code).first()


@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(err):
    return jsonify({"error": str(err)}), err.code

# Health & init

@app.get("/")
def health():
    return jsonify({"status": "ok"})

# --------------------------------------------------
# Users
# --------------------------------------------------

@app.post("/login")
def login_user():
    payload = parse_json(["firebase_code", "nickname"])
    firebase_code = payload["firebase_code"]
    nickname = payload["nickname"]
    user = User.query.filter_by(firebase_code=firebase_code).first()
    if user:
        if user.nickname != nickname:
            user.nickname = nickname
            db.session.commit()
        return jsonify(
            {"firebase_code": firebase_code, "nickname": user.nickname, "created": False}
        )
    user = User(
        firebase_code=firebase_code,
        nickname=nickname,
        friend_code=generate_friend_code(),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"firebase_code": firebase_code, "nickname": nickname, "created": True}), 201


@app.post("/users")
def get_user():
    payload = parse_json(["firebase_code"])
    user = User.query.filter_by(firebase_code=payload["firebase_code"]).first()
    if not user:
        return jsonify({})
    photo_base64 = None
    if user.photo is not None:
        photo_base64 = base64.b64encode(user.photo).decode("ascii")
    return jsonify(
        {
            "id": user.id,
            "nickname": user.nickname,
            "firebase_code": user.firebase_code,
            "friend_code": user.friend_code,
            "photo_base64": photo_base64,
            "cups": user.cups
        }
    )


@app.post("/users/photo")
def update_user_photo():
    payload = parse_json(["firebase_code", "photo_base64"])
    firebase_code = payload["firebase_code"]
    try:
        photo_bytes = base64.b64decode(payload["photo_base64"], validate=True)
    except (ValueError, TypeError):
        abort(400, description="Invalid base64 in photo_base64")
    user = User.query.filter_by(firebase_code=firebase_code).first()
    if not user:
        abort(404, description="User not found")
    user.photo = photo_bytes
    db.session.commit()
    return jsonify({"firebase_code": user.firebase_code, "updated": True}), 200


@app.post("/users/nickname")
def update_user_nickname():
    payload = parse_json(["firebase_code", "nickname"])
    firebase_code = payload["firebase_code"]
    user = User.query.filter_by(firebase_code=firebase_code).first()
    if not user:
        abort(404, description="User not found")
    user.nickname = payload["nickname"]
    db.session.commit()
    return jsonify({"firebase_code": user.firebase_code, "updated": user.nickname}), 200

# --------------------------------------------------
# Friendships
# --------------------------------------------------

@app.post("/friendships/request")
def request_friendship():
    payload = parse_json(["requester_firebase_code", "addressee_firebase_code"])
    requester = get_user_by_firebase(payload["requester_firebase_code"])
    addressee = get_user_by_firebase(payload["addressee_firebase_code"])
    if not requester or not addressee:
        abort(404, description="User not found")
    if requester.id == addressee.id:
        abort(400, description="Cannot request friendship with yourself")
    existing = Friendship.query.filter_by(
        user_id=requester.id, friend_id=addressee.id
    ).first()
    if existing:
        return jsonify(existing.to_dict()), 200
    friendship = Friendship(
        user_id=requester.id,
        friend_id=addressee.id,
        status="pending",
    )
    reverse = Friendship(
        user_id=addressee.id,
        friend_id=requester.id,
        status="pending",
    )
    db.session.add(friendship)
    db.session.add(reverse)
    db.session.commit()
    return jsonify(friendship.to_dict()), 201


@app.get("/friendships/<firebase_code>")
def list_friendships(firebase_code):
    user = get_user_by_firebase(firebase_code)
    if not user:
        return jsonify([])
    friendships = Friendship.query.filter_by(
        user_id=user.id, status="accepted"
    ).all()
    friend_ids = [f.friend_id for f in friendships]
    if not friend_ids:
        return jsonify([])
    friends = User.query.filter(User.id.in_(friend_ids)).all()
    return jsonify({"friends": [u.to_dict() for u in friends]})


@app.put("/friendships/status")
def update_friendship_status():
    payload = parse_json(
        ["requester_firebase_code", "addressee_firebase_code", "status"]
    )
    requester = get_user_by_firebase(payload["requester_firebase_code"])
    addressee = get_user_by_firebase(payload["addressee_firebase_code"])
    if not requester or not addressee:
        abort(404, description="User not found")
    friendship = Friendship.query.filter_by(
        user_id=requester.id, friend_id=addressee.id
    ).first()
    if not friendship:
        return jsonify({}), 200
    new_status = payload["status"]
    if new_status not in {"pending", "accepted", "rejected"}:
        abort(400, description="Invalid status")
    friendship.status = new_status
    reverse = Friendship.query.filter_by(
        user_id=addressee.id, friend_id=requester.id
    ).first()
    if reverse:
        reverse.status = new_status
    else:
        reverse = Friendship(
            user_id=addressee.id,
            friend_id=requester.id,
            status=new_status,
        )
        db.session.add(reverse)
    db.session.commit()
    return jsonify(friendship.to_dict())

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
    app.run(host="0.0.0.0", port=8080, debug=True)
