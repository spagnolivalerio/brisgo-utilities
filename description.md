## Purpose and Main Functionalities of the App

The app is a digital card game designed to provide both entertainment and competition through single-player and online multiplayer modes.

---

## Single-Player Mode

Users can play against a **DQN-agent opponent**.  
There are **three different difficulty levels**:

- **Easy** – Random Agent  
- **Medium** – Trained on single-agent rule-based strategy  
- **Hard** – Trained on multi-agent rule-based strategy  

The performance of the DQN can be found in the report inside the brisgo-utilities repository (see below).
---

## Multiplayer Mode

The app supports **real-time online matches** between players.  
Two types of online matches are available:

- **Public matches**, where players are paired automatically using a matchmaking system  
- **Private matches**, where players can create a game and invite a specific friend to join  

---

## Minigames

The app includes **two additional minigames** to enrich the gameplay experience.

### Hit The Suit
A minigame entirely driven by device sensors (**ROTATION_VECTOR** and **GYROSCOPE**).  
Players interact with the game by physically rotating and tilting the smartphone to hit the correct card suit.

### Memory Card Game
Players must flip cards and remember their positions to find matching pairs.  
This minigame focuses on memory and concentration and follows the traditional rules of the classic card matching game.

---

## Face Detection and Emoji Mapping

The app integrates a face detection system that analyzes a photo provided by the user using **ML Kit**.  
Facial expressions are detected from the image and mapped to a predefined set of emojis.  
During online matches, these emojis can be used to communicate emotions to the opponent.

---

## User and Game Management

The app includes:
- User authentication  
- Profile management (profile photo, nickname)  
- Friendships system  
- Player statistics and ranking system

Leaderboards are dynamically updated through backend services.

---

## Backend and Cloud Integration

Cloud-based services are used for data storage, matchmaking, and real-time communication (**GCP services and Firebase**).  
User position is localized using GPS, with reverse geocoding performed through the **Nominatim public API**.

---

## Repositories
Links to our repositories:
- app repository https://github.com/matteoventali/BrisGo   
- neural network and microservices repository https://github.com/spagnolivalerio/brisgo-utilities

## Authors
Matteo Ventali (1985026), Valerio Spagnoli (1973484), Serena Ragaglia (1941007)
