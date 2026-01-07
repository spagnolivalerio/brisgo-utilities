USE spagnolivalerio2$brisgo;

CREATE TABLE USERS (
  id            INTEGER PRIMARY KEY,
  username      VARCHAR(32) NOT NULL UNIQUE,
  name          VARCHAR(32) NOT NULL, 
  lastname      VARCHAR(32) NOT NULL, 
  password      VARCHAR(256) NOT NULL,
  nickname      VARCHAR(64) NOT NULL,
  firebase_code VARCHAR(50) DEFAULT NULL,
  friend_code   VARCHAR(16) NOT NULL UNIQUE
);

CREATE TABLE FRIENDSHIPS   (
  id          INTEGER PRIMARY KEY,
  user_id     INTEGER NOT NULL,
  friend_id   INTEGER NOT NULL,
  status      ENUM ('pending', 'accepted', 'rejected') DEFAULT 'pending',
  CHECK       (user_id <> friend_id),
  UNIQUE      (user_id, friend_id),
  FOREIGN KEY (user_id) REFERENCES USERS(id),
  FOREIGN KEY (friend_id) REFERENCES USERS(id)
);

CREATE TABLE MATCHES (
  id           INTEGER PRIMARY KEY,
  match_type   ENUM ('1v1', '2v2') NOT NULL,
  mode         ENUM ('online', 'cpu') NOT NULL,      
  status       ENUM  ('finished', 'aborted') NOT NULL,    
  team1_points SMALLINT NOT NULL DEFAULT 0,
  team2_points SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE MATCH_PLAYERS (
  id          INTEGER PRIMARY KEY,
  match_id    INTEGER NOT NULL,
  user_id     INTEGER NOT NULL,
  team_index  ENUM ('team1', 'team2'),            
  FOREIGN KEY (match_id) REFERENCES MATCHES(id),
  FOREIGN KEY (user_id) REFERENCES USERS(id)
);

CREATE TABLE MATCH_INVITE (
  id          INTEGER PRIMARY KEY,
  room_id     VARCHAR(32) NOT NULL,
  inviter_id  INTEGER NOT NULL,
  invitee_id  INTEGER NOT NULL,
  status      ENUM ('pending', 'accept', 'rejected') DEFAULT 'pending',    
  CHECK       (inviter_id <> invitee_id),
  FOREIGN KEY (inviter_id) REFERENCES USERS(id),
  FOREIGN KEY (invitee_id) REFERENCES USERS(id)
);
