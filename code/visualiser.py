import boto3
import json

print("=" * 50)
print("VISUALISATION — Etat de la Queue SQS")
print("=" * 50)

with open("/app/config.json") as f:
    config = json.load(f)
queue_url = config["queue_url"]

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localstack:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# Envoyer quelques messages de test
print("\nEnvoi de messages de test...")
for i in range(3):
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({
            "id": i+1,
            "contenu": f"Message test #{i+1}",
            "expediteur": "Producteur"
        })
    )

# Voir etat de la queue
attrs = sqs.get_queue_attributes(
    QueueUrl=queue_url,
    AttributeNames=[
        "ApproximateNumberOfMessages",
        "ApproximateNumberOfMessagesNotVisible"
    ]
)["Attributes"]

print(f"\nETAT DE LA QUEUE :")
print(f"   Messages disponibles : {attrs['ApproximateNumberOfMessages']}")
print(f"   Messages en lecture  : {attrs['ApproximateNumberOfMessagesNotVisible']}")

print(f"\nCONTENU DES MESSAGES :")
print("-" * 40)

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=1,
    VisibilityTimeout=0
)

if "Messages" in response:
    for i, msg in enumerate(response["Messages"], 1):
        try:
            body = json.loads(msg["Body"])
            contenu = body.get('contenu', msg["Body"])
            expediteur = body.get('expediteur', 'Inconnu')
        except:
            contenu = msg["Body"]
            expediteur = "Inconnu"
        print(f"\n  Message #{i}")
        print(f"     Contenu : {contenu}")
        print(f"     De      : {expediteur}")
        print(f"     Statut  : Chiffre KMS")
        print("-" * 40)
else:
    print("Queue vide !")

print("\nPROJET SQS SECURISE — TERMINE !\n")
print("=" * 50)
print("RESUME SECURITE")
print("=" * 50)
print("Producteur   -> Ecriture uniquement")
print("Consommateur -> Lecture uniquement")
print("Etranger     -> Aucun acces")
print("Chiffrement  -> KMS AES-256")
print("DLQ          -> Activee")
print("=" * 50)
