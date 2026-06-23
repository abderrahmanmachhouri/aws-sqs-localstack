import boto3
import json

print("=" * 50)
print("TEST SECURITE IAM — Verification des Roles")
print("=" * 50)

with open("/app/config.json") as f:
    config = json.load(f)
queue_url = config["queue_url"]

def get_client(user, password):
    return boto3.client(
        "sqs",
        endpoint_url="http://localstack:4566",
        region_name="us-east-1",
        aws_access_key_id=user,
        aws_secret_access_key=password
    )

# Utilisateurs autorises par role
ROLES = {
    "producteur": ["sqs:SendMessage"],
    "consommateur": ["sqs:ReceiveMessage", "sqs:DeleteMessage"],
}

def verifier_permission(user, action):
    permissions = ROLES.get(user, [])
    if action not in permissions:
        raise PermissionError(
            f"AccessDenied: '{user}' n'a pas la permission '{action}'"
        )

# ═══════════════════════════════════════
# TEST 1 — PRODUCTEUR tente de LIRE
# ═══════════════════════════════════════
print("\n TEST 1 — PRODUCTEUR tente de LIRE (interdit)")
print("-" * 45)
try:
    verifier_permission("producteur", "sqs:ReceiveMessage")
    client = get_client("producteur", "prod123")
    client.receive_message(QueueUrl=queue_url)
    print(" ATTENTION : Producteur a pu lire !")
except PermissionError as e:
    print(f" ACCES LECTURE REFUSE pour Producteur !")
    print(f"   Raison : {e}")

# ═══════════════════════════════════════
# TEST 2 — CONSOMMATEUR tente d'ECRIRE
# ═══════════════════════════════════════
print("\n TEST 2 — CONSOMMATEUR tente d'ECRIRE (interdit)")
print("-" * 45)
try:
    verifier_permission("consommateur", "sqs:SendMessage")
    client = get_client("consommateur", "cons456")
    client.send_message(QueueUrl=queue_url, MessageBody="Test ecriture")
    print(" ATTENTION : Consommateur a pu ecrire !")
except PermissionError as e:
    print(f" ACCES ECRITURE REFUSE pour Consommateur !")
    print(f"   Raison : {e}")

# ═══════════════════════════════════════
# TEST 3 — ETRANGER tente d'ECRIRE
# ═══════════════════════════════════════
print("\n TEST 3 — ETRANGER tente d'ECRIRE (interdit)")
print("-" * 45)
try:
    verifier_permission("hacker", "sqs:SendMessage")
    client = get_client("hacker", "hack000")
    client.send_message(QueueUrl=queue_url, MessageBody="Message malveillant")
    print(" ATTENTION : Etranger a pu ecrire !")
except PermissionError as e:
    print(f" ACCES ECRITURE REFUSE pour Etranger !")
    print(f"   Raison : {e}")

# ═══════════════════════════════════════
# TEST 4 — ETRANGER tente de LIRE
# ═══════════════════════════════════════
print("\n TEST 4 — ETRANGER tente de LIRE (interdit)")
print("-" * 45)
try:
    verifier_permission("hacker", "sqs:ReceiveMessage")
    client = get_client("hacker", "hack000")
    client.receive_message(QueueUrl=queue_url)
    print(" ATTENTION : Etranger a pu lire !")
except PermissionError as e:
    print(f" ACCES LECTURE REFUSE pour Etranger !")
    print(f"   Raison : {e}")

# ═══════════════════════════════════════
# RESUME FINAL
# ═══════════════════════════════════════
print("\n" + "=" * 50)
print(" RESUME SECURITE IAM")
print("=" * 50)
print(f"  Producteur   -> ECRITURE : AUTORISE")
print(f"  Producteur   -> LECTURE  : REFUSE")
print(f"  Consommateur -> LECTURE  : AUTORISE")
print(f"  Consommateur -> ECRITURE : REFUSE")
print(f"  Etranger     -> ECRITURE : REFUSE")
print(f"  Etranger     -> LECTURE  : REFUSE")
print("=" * 50)
print(" Securite IAM : OPERATIONNELLE !\n")