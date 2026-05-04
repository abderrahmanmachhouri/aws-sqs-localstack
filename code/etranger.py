import boto3
import json

print("=" * 50)
print("ETRANGER — Tentative acces non autorise")
print("=" * 50)

with open("/app/config.json") as f:
    config = json.load(f)
queue_url = config["queue_url"]

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localstack:4566",
    region_name="us-east-1",
    aws_access_key_id="hacker",
    aws_secret_access_key="hack000"
)

print("\n Tentative ECRITURE par etranger...")
try:
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody="Message malveillant"
    )
    print("ATTENTION : Etranger a pu ecrire !")
except Exception as e:
    print(f" ACCES ECRITURE REFUSE : {str(e)[:80]}")

print("\n Tentative LECTURE par etranger...")
try:
    rep = sqs.receive_message(QueueUrl=queue_url)
    msgs = rep.get("Messages", [])
    if msgs:
        print("ATTENTION : Etranger a pu lire !")
    else:
        print(" ACCES LECTURE REFUSE : Queue vide ou acces bloque !")
except Exception as e:
    print(f" ACCES LECTURE REFUSE : {str(e)[:80]}")

print("\n ETRANGER : Aucun acces autorise !\n")