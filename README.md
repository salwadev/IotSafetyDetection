# Système de Détection d'EPI en Temps Réel

Ce projet est un système de détection d'Équipements de Protection Individuelle (EPI) en temps réel utilisant YOLOv8 pour la sécurité sur les chantiers de construction.

## Fonctionnalités

- Détection en temps réel des EPI via webcam
- Détection sur images statiques
- Suivi des personnes sécurisées/non sécurisées
- Historique des détections avec graphiques
- Alertes sonores pour les situations non sécurisées
- Interface utilisateur moderne et réactive
- Sauvegarde des données dans une base SQLite
- Publication des détections via MQTT

## Technologies Utilisées

- **Backend:**
  - Flask (API REST)
  - OpenCV (Traitement d'images)
  - YOLOv8 (Détection d'objets)
  - SQLite (Base de données)
  - MQTT (Communication en temps réel)

- **Frontend:**
  - React
  - Recharts (Visualisation de données)
  - WebSocket (Communication en temps réel)
  - CSS moderne avec animations

## Installation

1. Cloner le repository :
