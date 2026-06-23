# Sécurisation de Messages SQS avec LocalStack

Mini Projet - Sécurisation d'un service de messagerie cloud AWS SQS  
en environnement local avec LocalStack.

---

## Description

Simulation et sécurisation d'un service de messagerie cloud AWS SQS  
en environnement local avec LocalStack. Le projet implémente :
- Chiffrement des messages via **KMS (AES-256)**
- Signature des messages avec **SHA-256**
- Contrôle d'accès (producteur autorisé vs étranger non autorisé)
- Stockage sécurisé dans **S3**
- Dashboard de visualisation

---

## Technologies
- Python
- AWS SQS / KMS / S3 (LocalStack)
- Docker & Docker Compose
- Boto3

---

## Services LocalStack utilisés
- **SQS** — File de messages
- **KMS** — Chiffrement AES-256
- **IAM** — Contrôle d'accès
- **S3** — Stockage sécurisé

---

## Installation

### Prérequis
- Docker & Docker Compose
- Un compte LocalStack

### Configuration
Créer un fichier `.env` :
LOCALSTACK_TOKEN=ton_token_ici

### Lancer le projet
```bash
docker-compose up
```
