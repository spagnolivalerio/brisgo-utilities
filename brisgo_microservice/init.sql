DROP DATABASE IF EXISTS brisgo;
CREATE DATABASE brisgo;
USE brisgo;

CREATE TABLE USERS (
  id               INTEGER PRIMARY KEY AUTO_INCREMENT,
  nickname         VARCHAR(64) DEFAULT NULL,
  firebase_code    VARCHAR(50) DEFAULT NULL UNIQUE,
  friend_code      VARCHAR(16) NOT NULL UNIQUE, 
  photo            LONGBLOB DEFAULT NULL, 
  cups             INTEGER NOT NULL DEFAULT 0, 
  google_photo_url VARCHAR(100) DEFAULT NULL
);

CREATE TABLE FRIENDSHIPS (
  id          INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id     INTEGER NOT NULL,
  friend_id   INTEGER NOT NULL,
  status      ENUM ('pending', 'waiting', 'accepted', 'rejected') DEFAULT 'pending',
  CHECK       (user_id <> friend_id),
  UNIQUE      (user_id, friend_id),
  FOREIGN KEY (user_id) REFERENCES USERS(id ),
  FOREIGN KEY (friend_id) REFERENCES USERS(id)
);

CREATE TABLE MATCHES (
  id            INTEGER PRIMARY KEY AUTO_INCREMENT,
  createdAt     BIGINT NOT NULL DEFAULT (UNIX_TIMESTAMP()),
  mode          ENUM ('online', 'cpu') NOT NULL,      
  host_id       INTEGER  NOT NULL, 
  joiner_id     INTEGER NOT NULL,   
  host_points   SMALLINT NOT NULL DEFAULT 0,
  joiner_points SMALLINT NOT NULL DEFAULT 0,
  FOREIGN KEY (host_id) REFERENCES USERS(id),
  FOREIGN KEY (joiner_id) REFERENCES USERS(id),
  UNIQUE (createdAt, host_id, joiner_id)
);

CREATE TABLE MATCH_INVITE (
  id          INTEGER PRIMARY KEY AUTO_INCREMENT,
  room_id     VARCHAR(100) NOT NULL,
  inviter_id  INTEGER NOT NULL,
  invitee_id  INTEGER NOT NULL,
  status      ENUM ('pending', 'accept', 'rejected') DEFAULT 'pending',    
  CHECK       (inviter_id <> invitee_id),
  FOREIGN KEY (inviter_id) REFERENCES USERS(id),
  FOREIGN KEY (invitee_id) REFERENCES USERS(id),
  UNIQUE (inviter_id, invitee_id, room_id)
);

-- Seed data for stats
INSERT INTO USERS (nickname, firebase_code, friend_code, photo, cups, google_photo_url) VALUES
  ('Vale',  'fb_001', 'FRIEND001', NULL, 120, NULL),
  ('Marta', 'fb_002', 'FRIEND002', NULL, 95,  NULL),
  ('Luca',  'fb_003', 'FRIEND003', NULL, 60,  NULL),
  ('Giulia','fb_004', 'FRIEND004', NULL, 30,  NULL);

INSERT INTO MATCHES (createdAt, mode, host_id, joiner_id, host_points, joiner_points) VALUES
  (UNIX_TIMESTAMP() - 5000, 'online', 1, 2, 7, 5),
  (UNIX_TIMESTAMP() - 4000, 'online', 2, 1, 6, 8),
  (UNIX_TIMESTAMP() - 3000, 'cpu',    1, 3, 3, 6),
  (UNIX_TIMESTAMP() - 2000, 'cpu',    3, 1, 2, 9),
  (UNIX_TIMESTAMP() - 1000, 'online', 4, 1, 4, 4),
  (UNIX_TIMESTAMP() - 500,  'online', 1, 4, 9, 2);

