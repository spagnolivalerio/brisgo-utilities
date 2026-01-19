DROP DATABASE IF EXISTS brisgo;
CREATE DATABASE brisgo;
USE brisgo;

CREATE TABLE USERS (
  id            INTEGER PRIMARY KEY AUTO_INCREMENT,
  nickname      VARCHAR(64) DEFAULT NULL,
  firebase_code VARCHAR(50) DEFAULT NULL UNIQUE,
  friend_code   VARCHAR(16) NOT NULL UNIQUE, 
  photo         LONGBLOB DEFAULT NULL, 
  cups          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE FRIENDSHIPS (
  id          INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id     INTEGER NOT NULL,
  friend_id   INTEGER NOT NULL,
  status      ENUM ('pending', 'accepted', 'rejected') DEFAULT 'pending',
  CHECK       (user_id <> friend_id),
  UNIQUE      (user_id, friend_id),
  FOREIGN KEY (user_id) REFERENCES USERS(id),
  FOREIGN KEY (friend_id) REFERENCES USERS(id)
);

CREATE TABLE MATCHES (
  id           INTEGER PRIMARY KEY AUTO_INCREMENT,
  match_type   ENUM ('1v1', '2v2') NOT NULL,
  mode         ENUM ('online', 'cpu') NOT NULL,      
  status       ENUM  ('finished', 'aborted') NOT NULL,    
  team1_points SMALLINT NOT NULL DEFAULT 0,
  team2_points SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE MATCH_PLAYERS (
  id          INTEGER PRIMARY KEY AUTO_INCREMENT,
  match_id    INTEGER NOT NULL,
  user_id     INTEGER NOT NULL,
  team_index  ENUM ('team1', 'team2'),            
  FOREIGN KEY (match_id) REFERENCES MATCHES(id),
  FOREIGN KEY (user_id) REFERENCES USERS(id)
);

CREATE TABLE MATCH_INVITE (
  id          INTEGER PRIMARY KEY AUTO_INCREMENT,
  room_id     VARCHAR(100) NOT NULL,
  inviter_id  INTEGER NOT NULL,
  invitee_id  INTEGER NOT NULL,
  status      ENUM ('pending', 'accept', 'rejected') DEFAULT 'pending',    
  CHECK       (inviter_id <> invitee_id),
  FOREIGN KEY (inviter_id) REFERENCES USERS(id),
  FOREIGN KEY (invitee_id) REFERENCES USERS(id)
);

-- Seed data
INSERT INTO USERS (nickname, firebase_code, friend_code, photo, cups) VALUES
  ('Vale',  'fb_001', 'FRIEND001', NULL, 12),
  ('Marta', 'fb_002', 'FRIEND002', NULL, 8),
  ('Luca',  'fb_003', 'FRIEND003', NULL, 3),
  ('Giulia','fb_004', 'FRIEND004', NULL, 20);

INSERT INTO FRIENDSHIPS (user_id, friend_id, status) VALUES
  (1, 2, 'accepted'),
  (1, 3, 'pending'),
  (2, 4, 'rejected');

INSERT INTO MATCHES (match_type, mode, status, team1_points, team2_points) VALUES
  ('1v1', 'online', 'finished', 5, 3),
  ('2v2', 'cpu',    'aborted',  1, 0);

INSERT INTO MATCH_PLAYERS (match_id, user_id, team_index) VALUES
  (1, 1, 'team1'),
  (1, 2, 'team2'),
  (2, 3, 'team1'),
  (2, 4, 'team2');

INSERT INTO MATCH_INVITE (room_id, inviter_id, invitee_id, status) VALUES
  ('room_abc', 1, 2, 'accept'),
  ('room_xyz', 3, 4, 'pending');
