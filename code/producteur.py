import boto3
import json
import hashlib

print("=" * 50)
print("PRODUCTEUR — Envoi de messages")
print("=" * 50)

with open("/app/config.json") as f:
    config = json.load(f)
queue_url = config["queue_url"]

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localstack:4566",
    region_name="us-east-1",
    aws_access_key_id="producteur",
    aws_secret_access_key="prod123"
)

messages = [
    {"id": 1, "contenu": "Message confidentiel 1", "expediteur": "Producteur"},
    {"id": 2, "contenu": "Donnees sensibles 2",    "expediteur": "Producteur"},
    {"id": 3, "contenu": "Rapport secret 3",        "expediteur": "Producteur"},
]

print("\nEnvoi des messages...\n")
for msg in messages:
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(msg),
        MessageAttributes={
            "Expediteur":  {"StringValue": "Producteur", "DataType": "String"},
            "Chiffrement": {"StringValue": "KMS-AES256", "DataType": "String"}
        }
    )
    print(f"OK Message {msg['id']} envoye | ID: {response['MessageId']}")

print("\nPRODUCTEUR : Tous les messages envoyes !\n")

# Créer une signature du message
def signer_message(contenu):
    signature = hashlib.sha256(contenu.encode()).hexdigest()
    return signature

# Lors de l'envoi
contenu = json.dumps(msg)
signature = signer_message(contenu)

sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=contenu,
    MessageAttributes={
        "Signature": {
            "StringValue": signature,
            "DataType": "String"
        },
        "Chiffrement": {
            "StringValue": "KMS-AES256",
            "DataType": "String"
        }
    }
)
print(f"OK Message envoye avec signature : {signature[:20]}...")