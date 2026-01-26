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

