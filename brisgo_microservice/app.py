import base64
import os
import secrets
import string
from dotenv import load_dotenv
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, CheckConstraint, UniqueConstraint, or_
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
    google_photo_url = db.Column(db.String(100))
    photo = db.Column(LONGBLOB)
    cups = db.Column(db.Integer, nullable=False, server_default="0")

    def to_dict(self):
        photo_base64 = None
        if self.photo is not None:
            photo_base64 = base64.b64encode(self.photo).decode("ascii")
        return {
            "id": self.id,
            "photo": photo_base64,
            "nickname": self.nickname,
            "firebase_code": self.firebase_code,
            "friend_code": self.friend_code,
            "google_photo_url": self.google_photo_url,
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
    mode = db.Column(Enum("online", "cpu", name="match_mode"), nullable=False)
    status = db.Column(Enum("finished", "aborted", name="match_status"), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey("USERS.id"), nullable=False)
    joiner_id = db.Column(db.Integer, db.ForeignKey("USERS.id"), nullable=False)
    host_points = db.Column(db.SmallInteger, nullable=False, server_default="0")
    joiner_points = db.Column(db.SmallInteger, nullable=False, server_default="0")

    def to_dict(self):
        return {
            "id": self.id,
            "mode": self.mode,
            "status": self.status,
            "host_id": self.host_id,
            "joiner_id": self.joiner_id,
            "host_points": self.host_points,
            "joiner_points": self.joiner_points,
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
    google_photo_url = payload.get("google_photo_url")
    user = User.query.filter_by(firebase_code=firebase_code).first()
    if user:
        if user.nickname != nickname:
            user.nickname = nickname
        if google_photo_url and user.google_photo_url != google_photo_url:
            user.google_photo_url = google_photo_url
        db.session.commit()
        return jsonify(
            {"firebase_code": firebase_code, "nickname": user.nickname, "created": False}
        )
    user = User(
        firebase_code=firebase_code,
        nickname=nickname,
        friend_code=generate_friend_code(),
        google_photo_url=google_photo_url,
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


@app.post("/users/stats")
def get_user_stats():
    payload = parse_json(["firebase_code"])
    user = User.query.filter_by(firebase_code=payload["firebase_code"]).first()
    if not user:
        abort(404, description="User not found")

    def build_stats(mode):
        matches = Match.query.filter(
            Match.mode == mode,
            Match.status == "finished",
            or_(Match.host_id == user.id, Match.joiner_id == user.id),
        ).all()
        total_games = len(matches)
        wins = 0
        for match in matches:
            if match.host_id == user.id and match.host_points > match.joiner_points:
                wins += 1
            elif match.joiner_id == user.id and match.joiner_points > match.host_points:
                wins += 1
        win_rate = (wins / total_games) if total_games else 0
        return {
            "total_win": wins,
            "cups": user.cups,
            "win_rate": win_rate,
            "total_game_played": total_games,
        }

    return jsonify({"cpu": build_stats("cpu"), "online": build_stats("online")})


@app.put("/users/cups")
def add_user_cups():
    payload = parse_json(["firebase_code"])
    user = User.query.filter_by(firebase_code=payload["firebase_code"]).first()
    if not user:
        abort(404, description="User not found")
    cups_to_add = secrets.randbelow(4) + 27
    user.cups = (user.cups or 0) + cups_to_add
    db.session.commit()
    return jsonify({"firebase_code": user.firebase_code, "added": cups_to_add, "cups": user.cups}), 200

# --------------------------------------------------
# Leaderboards
# --------------------------------------------------

@app.get("/leaderboard/global")
def global_leaderboard():
    users = User.query.order_by(User.cups.desc()).all()
    return jsonify({"leaderboard": [u.to_dict() for u in users]})


@app.post("/leaderboard/friends")
def friends_leaderboard():
    payload = parse_json(["firebase_code"])
    user = get_user_by_firebase(payload["firebase_code"])
    if not user:
        abort(404, description="User not found")
    friendships = Friendship.query.filter_by(user_id=user.id, status="accepted").all()
    friend_ids = [f.friend_id for f in friendships]
    if not friend_ids:
        return jsonify({"leaderboard": []})
    friends = User.query.filter(User.id.in_(friend_ids)).order_by(User.cups.desc()).all()
    return jsonify({"leaderboard": [u.to_dict() for u in friends]})

# --------------------------------------------------
# Friendships
# --------------------------------------------------

@app.post("/friendships/request")
def request_friendship():
    payload = parse_json(["requester_firebase_code", "addressee_friend_code"])
    requester = get_user_by_firebase(payload["requester_firebase_code"])
    addressee = User.query.filter_by(friend_code=payload["addressee_friend_code"]).first()
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


@app.post("/friendships")
def list_friendships():
    payload = parse_json(["firebase_code", "status"])
    firebase_code = payload["firebase_code"]
    status = payload["status"]
    if status not in {"pending", "accepted", "rejected"}:
        abort(400, description="Invalid status")
    user = get_user_by_firebase(firebase_code)
    if not user:
        return jsonify({"friends":[]})
    friendships = Friendship.query.filter_by(
        user_id=user.id, status=status
    ).all()
    friend_ids = [f.friend_id for f in friendships]
    if not friend_ids:
        return jsonify({"friends":[]})
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
    payload = parse_json(
        ["mode", "status", "host_id", "joiner_id", "host_points", "joiner_points"]
    )
    match = Match(**payload)
    db.session.add(match)
    db.session.commit()
    return jsonify({"match": match.to_dict()}), 201

# --------------------------------------------------
# Match invites
# --------------------------------------------------

@app.post("/match-invites")
def create_match_invite():
    payload = parse_json(["inviter_firebase_code", "invitee_firebase_code", "room_id"])
    inviter = get_user_by_firebase(payload["inviter_firebase_code"])
    invitee = get_user_by_firebase(payload["invitee_firebase_code"])
    if not inviter or not invitee:
        abort(404, description="User not found")
    if inviter.id == invitee.id:
        abort(400, description="Cannot invite yourself")
    invite = MatchInvite(
        room_id=payload["room_id"],
        inviter_id=inviter.id,
        invitee_id=invitee.id,
        status="pending",
    )
    db.session.add(invite)
    db.session.commit()
    return jsonify(invite.to_dict()), 201


@app.post("/match-invites/list")
def list_match_invites():
    payload = parse_json(["firebase_code"])
    user = get_user_by_firebase(payload["firebase_code"])
    if not user:
        return jsonify([])
    invites = MatchInvite.query.filter_by(
        invitee_id=user.id, status="pending"
    ).all()
    results = []
    for invite in invites:
        data = invite.to_dict()
        inviter = User.query.get(invite.inviter_id)
        if inviter:
            inviter_data = inviter.to_dict()
            data["nickname"] = inviter_data.get("nickname")
            data["photo"] = inviter_data.get("photo")
            data["google_photo_url"] = inviter_data.get("google_photo_url")
        else:
            data["nickname"] = None
            data["photo"] = None
            data["google_photo_url"] = None
        results.append(data)
    return jsonify({"invites": results})


@app.put("/match-invites")
def update_match_invite():
    payload = parse_json(["room_id", "status"])
    invite = MatchInvite.query.filter_by(room_id=payload["room_id"]).first()
    if not invite:
        abort(404, description="Invite not found")
    invite.status = payload["status"]
    db.session.commit()
    return jsonify({"invite":invite.to_dict()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
