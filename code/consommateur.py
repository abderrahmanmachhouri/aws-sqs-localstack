import boto3
import json
import hashlib

print("=" * 50)
print("CONSOMMATEUR — Lecture des messages")
print("=" * 50)

with open("/app/config.json") as f:
    config = json.load(f)
queue_url = config["queue_url"]

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localstack:4566",
    region_name="us-east-1",
    aws_access_key_id="consommateur",
    aws_secret_access_key="cons456"
)

print("\nLecture des messages...\n")
for i in range(3):
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        MessageAttributeNames=["All"],
        WaitTimeSeconds=2
    )
    if "Messages" in response:
        msg = response["Messages"][0]
        body = json.loads(msg["Body"])
        attrs = msg.get("MessageAttributes", {})

        print(f"Message recu :")
        print(f"   Contenu     : {body['contenu']}")
        print(f"   Expediteur  : {body['expediteur']}")
        print(f"   Chiffrement : {attrs.get('Chiffrement', {}).get('StringValue', 'KMS-AES256')}")

        # Verifier signature si elle existe
        if "Signature" in attrs:
            sig_recue = attrs["Signature"]["StringValue"]
            sig_calc = hashlib.sha256(msg["Body"].encode()).hexdigest()
            if sig_recue == sig_calc:
                print(f"   Signature   : OK !")
            else:
                print(f"   Signature   : ALERTE message modifie !")
        else:
            print(f"   Signature   : Non presente")

        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=msg["ReceiptHandle"]
        )
        print(f"   Supprime apres lecture\n")

print("CONSOMMATEUR : Lecture terminee !\n")