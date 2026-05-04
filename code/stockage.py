import boto3
import json

print("=" * 50)
print("STOCKAGE S3 — 3 Types de Stockage")
print("=" * 50)

endpoint = "http://localstack:4566"
region = "us-east-1"

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint,
    region_name=region,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# ═══════════════════════════════════════
# TYPE 1 — Stockage FICHIER
# ═══════════════════════════════════════
print("\n TYPE 1 : Stockage FICHIER")
print("-" * 40)

s3.create_bucket(Bucket="bucket-fichiers")

# Creer un fichier texte et l'uploader
contenu_fichier = "Ceci est un fichier texte securise !"
s3.put_object(
    Bucket="bucket-fichiers",
    Key="document.txt",
    Body=contenu_fichier.encode(),
    ServerSideEncryption="AES256"
)
print("OK Fichier 'document.txt' uploade !")

# Lire le fichier
response = s3.get_object(Bucket="bucket-fichiers", Key="document.txt")
contenu = response["Body"].read().decode()
print(f"OK Fichier lu : {contenu}")

# ═══════════════════════════════════════
# TYPE 2 — Stockage OBJET
# ═══════════════════════════════════════
print("\n TYPE 2 : Stockage OBJET")
print("-" * 40)

s3.create_bucket(Bucket="bucket-objets")

# Stocker un objet JSON
objet = {
    "id": 1,
    "nom": "Hassna",
    "module": "Cloud Computing",
    "note": "20/20"
}
s3.put_object(
    Bucket="bucket-objets",
    Key="etudiant.json",
    Body=json.dumps(objet).encode(),
    ServerSideEncryption="AES256",
    Metadata={"type": "etudiant", "annee": "2026"}
)
print("OK Objet JSON 'etudiant.json' uploade !")

# Lire l'objet
response = s3.get_object(Bucket="bucket-objets", Key="etudiant.json")
data = json.loads(response["Body"].read().decode())
print(f"OK Objet lu : {data}")

# ═══════════════════════════════════════
# TYPE 3 — Stockage BLOCK
# ═══════════════════════════════════════
print("\n TYPE 3 : Stockage BLOCK")
print("-" * 40)

s3.create_bucket(Bucket="bucket-blocks")

# Simuler stockage par blocks (multipart)
bloc_data = b"BLOCK_001: Donnees sensibles partie 1 | "
bloc_data += b"BLOCK_002: Donnees sensibles partie 2 | "
bloc_data += b"BLOCK_003: Donnees sensibles partie 3"

s3.put_object(
    Bucket="bucket-blocks",
    Key="data.block",
    Body=bloc_data,
    ServerSideEncryption="AES256"
)
print("OK Block 'data.block' uploade !")

# Lire le block
response = s3.get_object(Bucket="bucket-blocks", Key="data.block")
block_content = response["Body"].read().decode()
print(f"OK Block lu : {block_content[:50]}...")

# ═══════════════════════════════════════
# LISTER TOUS LES BUCKETS
# ═══════════════════════════════════════
print("\n LISTE DES BUCKETS S3 :")
print("-" * 40)
buckets = s3.list_buckets()["Buckets"]
for bucket in buckets:
    print(f"   Bucket : {bucket['Name']}")
    objects = s3.list_objects_v2(Bucket=bucket['Name'])
    for obj in objects.get("Contents", []):
        print(f"      Fichier : {obj['Key']} ({obj['Size']} bytes)")

print("\nSTOCKAGE S3 TERMINE !\n")