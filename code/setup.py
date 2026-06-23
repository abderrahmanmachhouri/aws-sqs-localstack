import boto3
import json

print("=" * 50)
print("SETUP — Creation de l'infrastructure SQS")
print("=" * 50)

endpoint = "http://localstack:4566"
region = "us-east-1"

def client(service):
    return boto3.client(
        service,
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

kms = client("kms")
print("\n Creation cle KMS...")
key = kms.create_key(Description="Cle SQS projet")
key_id = key["KeyMetadata"]["KeyId"]
print(f"OK Cle KMS : {key_id}")

sqs = client("sqs")
print("\n Creation Dead Letter Queue...")
dlq = sqs.create_queue(QueueName="dlq-projet")
dlq_url = dlq["QueueUrl"]
dlq_arn = sqs.get_queue_attributes(
    QueueUrl=dlq_url,
    AttributeNames=["QueueArn"]
)["Attributes"]["QueueArn"]
print(f"OK DLQ : {dlq_url}")

print("\n Creation Queue Securisee...")
queue = sqs.create_queue(
    QueueName="queue-securisee",
    Attributes={
        "KmsMasterKeyId": key_id,
        "RedrivePolicy": json.dumps({
            "deadLetterTargetArn": dlq_arn,
            "maxReceiveCount": "3"
        }),
        "MessageRetentionPeriod": "86400",
        "VisibilityTimeout": "30"
    }
)
queue_url = queue["QueueUrl"]
print(f"OK Queue : {queue_url}")

with open("/app/config.json", "w") as f:
    json.dump({"key_id": key_id, "queue_url": queue_url}, f)
print("Config sauvegardee !")

print("\nSETUP TERMINE !\n")

# Politique IAM — Seulement Producteur et Consommateur
producteur_arn = "arn:aws:iam::000000000000:user/producteur"
consommateur_arn = "arn:aws:iam::000000000000:user/consommateur"

policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AutoriserProducteur",
            "Effect": "Allow",
            "Principal": {"AWS": producteur_arn},
            "Action": ["sqs:SendMessage"],
            "Resource": "*"
        },
        {
            "Sid": "AutoriserConsommateur",
            "Effect": "Allow",
            "Principal": {"AWS": consommateur_arn},
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes"
            ],
            "Resource": "*"
        },
        {
            "Sid": "BloquerTousLesAutres",
            "Effect": "Deny",
            "Principal": {"AWS": "*"},
            "Action": "sqs:*",
            "Resource": "*",
            "Condition": {
                "ArnNotLike": {
                    "aws:PrincipalArn": [
                        producteur_arn,
                        consommateur_arn
                    ]
                }
            }
        }
    ]
}

sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={"Policy": json.dumps(policy)}
)
print("OK Politique d'acces appliquee !")

# Creer les utilisateurs IAM
iam = client("iam")
print("\n Creation utilisateurs IAM...")

iam.create_user(UserName="producteur")
iam.create_access_key(UserName="producteur")
print("OK Utilisateur 'producteur' cree !")

iam.create_user(UserName="consommateur")
iam.create_access_key(UserName="consommateur")
print("OK Utilisateur 'consommateur' cree !")