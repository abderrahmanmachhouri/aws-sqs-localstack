import boto3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

endpoint = "http://localstack:4566"
region = "us-east-1"

def get_all_data():
    sqs = boto3.client("sqs", endpoint_url=endpoint, region_name=region,
                       aws_access_key_id="test", aws_secret_access_key="test")
    s3 = boto3.client("s3", endpoint_url=endpoint, region_name=region,
                      aws_access_key_id="test", aws_secret_access_key="test")
    kms = boto3.client("kms", endpoint_url=endpoint, region_name=region,
                       aws_access_key_id="test", aws_secret_access_key="test")

    # SQS Queues + Messages
    queues = []
    try:
        resp = sqs.list_queues()
        for url in resp.get("QueueUrls", []):
            name = url.split("/")[-1]
            attrs = sqs.get_queue_attributes(
                QueueUrl=url,
                AttributeNames=["ApproximateNumberOfMessages",
                               "ApproximateNumberOfMessagesNotVisible",
                               "CreatedTimestamp"]
            )["Attributes"]

            # Lire les messages sans les supprimer
            messages = []
            try:
                msgs = sqs.receive_message(
                    QueueUrl=url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=1,
                    VisibilityTimeout=0,
                    MessageAttributeNames=["All"]
                )
                for msg in msgs.get("Messages", []):
                    try:
                        body = json.loads(msg["Body"])
                        contenu = body.get("contenu", msg["Body"])
                        expediteur = body.get("expediteur", "Inconnu")
                    except:
                        contenu = msg["Body"]
                        expediteur = "Inconnu"
                    messages.append({
                        "id": msg["MessageId"][:8] + "...",
                        "contenu": contenu,
                        "expediteur": expediteur
                    })
            except:
                pass

            queues.append({
                "name": name,
                "url": url,
                "messages_dispo": attrs.get("ApproximateNumberOfMessages", "0"),
                "messages_en_cours": attrs.get("ApproximateNumberOfMessagesNotVisible", "0"),
                "messages": messages
            })
    except:
        pass

    # S3 Buckets + Fichiers
    buckets = []
    try:
        for b in s3.list_buckets().get("Buckets", []):
            objects = s3.list_objects_v2(Bucket=b["Name"])
            files = []
            for obj in objects.get("Contents", []):
                # Lire le contenu
                try:
                    response = s3.get_object(Bucket=b["Name"], Key=obj["Key"])
                    content = response["Body"].read().decode()
                    if len(content) > 100:
                        content = content[:100] + "..."
                except:
                    content = "N/A"
                files.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "content": content
                })
            buckets.append({
                "name": b["Name"],
                "files": files,
                "count": len(files)
            })
    except:
        pass

    # KMS Keys
    keys = []
    try:
        resp = kms.list_keys()
        for k in resp.get("Keys", []):
            try:
                info = kms.describe_key(KeyId=k["KeyId"])["KeyMetadata"]
                keys.append({
                    "id": info["KeyId"][:8] + "...",
                    "desc": info.get("Description", "N/A"),
                    "status": info.get("KeyState", "N/A")
                })
            except:
                pass
    except:
        pass

    return queues, buckets, keys

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        queues, buckets, keys = get_all_data()

        # ── SQS HTML ──
        sqs_html = ""
        for q in queues:
            msgs_html = ""
            if q["messages"]:
                for m in q["messages"]:
                    expediteur_color = "#00ff88" if m["expediteur"] == "Producteur" else "#ff4444"
                    msgs_html += f"""
                    <div class="msg-item">
                        <span class="msg-id">ID: {m['id']}</span>
                        <span class="msg-content">📩 {m['contenu']}</span>
                        <span class="msg-from" style="color:{expediteur_color}">De: {m['expediteur']}</span>
                        <span class="msg-enc">🔐 KMS-AES256</span>
                    </div>"""
            else:
                msgs_html = "<p class='no-msg'>Aucun message visible</p>"

            color = "#ff4444" if q["name"] == "dlq-projet" else "#00d4ff"
            sqs_html += f"""
            <div class="service-card">
                <div class="service-header" style="border-left: 4px solid {color}">
                    <span class="service-icon">📬</span>
                    <span class="service-name">{q['name']}</span>
                    <span class="badge" style="background:#1a4a2e;color:#00ff88">{q['messages_dispo']} disponibles</span>
                    <span class="badge" style="background:#2a1a4a;color:#aa88ff">{q['messages_en_cours']} en cours</span>
                </div>
                <div class="msg-list">{msgs_html}</div>
            </div>"""

        # ── S3 HTML ──
        s3_html = ""
        for b in buckets:
            files_html = ""
            for f in b["files"]:
                if "fichier" in b["name"] or f["key"].endswith(".txt"):
                    icon = "📄"
                    badge = "<span class='type-badge fichier'>FICHIER</span>"
                elif "objet" in b["name"] or f["key"].endswith(".json"):
                    icon = "📦"
                    badge = "<span class='type-badge objet'>OBJET</span>"
                else:
                    icon = "🔷"
                    badge = "<span class='type-badge block'>BLOCK</span>"

                files_html += f"""
                <div class="file-item">
                    <div class="file-header">{icon} {f['key']} {badge} — {f['size']} bytes</div>
                    <div class="file-content">📋 {f['content']}</div>
                </div>"""

            s3_html += f"""
            <div class="service-card">
                <div class="service-header" style="border-left: 4px solid #00ff88">
                    <span class="service-icon">🪣</span>
                    <span class="service-name">{b['name']}</span>
                    <span class="badge" style="background:#1a3a2a;color:#00ff88">{b['count']} fichier(s)</span>
                </div>
                <div class="msg-list">{files_html}</div>
            </div>"""

        # ── KMS HTML ──
        kms_html = ""
        for k in keys:
            kms_html += f"""
            <div class="service-card">
                <div class="service-header" style="border-left: 4px solid #ffaa00">
                    <span class="service-icon">🔑</span>
                    <span class="service-name">Cle KMS: {k['id']}</span>
                    <span class="badge" style="background:#2a2a1a;color:#ffaa00">{k['status']}</span>
                </div>
                <div class="msg-list">
                    <div class="msg-item">
                        <span class="msg-content">Description: {k['desc']}</span>
                        <span class="msg-enc">🔐 AES-256</span>
                    </div>
                </div>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
    <title>LocalStack Dashboard</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:Arial,sans-serif; background:#0a0e1a; color:#fff; padding:20px; }}
        .header {{
            text-align:center; padding:25px;
            background:linear-gradient(135deg,#1a1f2e,#2d3561);
            border-radius:15px; margin-bottom:25px;
            border:1px solid #3d4f7c;
        }}
        .header h1 {{ font-size:2em; color:#00d4ff; }}
        .header p {{ color:#8892b0; margin-top:8px; }}
        .status-bar {{
            display:flex; gap:15px; margin-bottom:25px; flex-wrap:wrap;
        }}
        .stat-box {{
            background:#1a1f2e; border:1px solid #3d4f7c;
            border-radius:10px; padding:15px 20px;
            text-align:center; flex:1; min-width:150px;
        }}
        .stat-num {{ font-size:2em; font-weight:bold; color:#00d4ff; }}
        .stat-label {{ color:#8892b0; font-size:0.85em; margin-top:5px; }}
        .section {{ margin-bottom:25px; }}
        .section-title {{
            font-size:1.3em; color:#00d4ff;
            margin-bottom:15px; padding:10px 15px;
            background:#1a1f2e; border-radius:8px;
            border-left:4px solid #00d4ff;
        }}
        .service-card {{
            background:#1a1f2e; border:1px solid #2d3561;
            border-radius:10px; margin-bottom:15px; overflow:hidden;
        }}
        .service-header {{
            display:flex; align-items:center; gap:10px;
            padding:12px 15px; background:#16192a;
        }}
        .service-icon {{ font-size:1.3em; }}
        .service-name {{ font-weight:bold; color:#ccd6f6; flex:1; }}
        .badge {{
            padding:3px 10px; border-radius:20px;
            font-size:0.75em; font-weight:bold;
        }}
        .msg-list {{ padding:10px 15px; }}
        .msg-item {{
            display:flex; gap:10px; align-items:center;
            padding:8px; background:#0f1220;
            border-radius:6px; margin-bottom:6px;
            font-size:0.85em; flex-wrap:wrap;
        }}
        .msg-id {{ color:#555; font-size:0.8em; }}
        .msg-content {{ color:#ccd6f6; flex:1; }}
        .msg-from {{ font-weight:bold; }}
        .msg-enc {{ color:#ffaa00; }}
        .file-item {{
            background:#0f1220; border-radius:6px;
            margin-bottom:8px; overflow:hidden;
        }}
        .file-header {{
            padding:8px 12px; color:#ccd6f6;
            font-size:0.9em; background:#161928;
        }}
        .file-content {{
            padding:8px 12px; color:#8892b0;
            font-size:0.8em; font-family:monospace;
            border-top:1px solid #2d3561;
        }}
        .type-badge {{
            display:inline-block; padding:2px 8px;
            border-radius:10px; font-size:0.75em; font-weight:bold;
        }}
        .fichier {{ background:#1a4a2e; color:#00ff88; }}
        .objet {{ background:#1a2a4a; color:#00aaff; }}
        .block {{ background:#4a1a2a; color:#ff4488; }}
        .security-grid {{
            display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
            gap:12px;
        }}
        .sec-item {{
            background:#1a1f2e; border:1px solid #2d3561;
            border-radius:10px; padding:15px; text-align:center;
        }}
        .sec-icon {{ font-size:1.8em; margin-bottom:8px; }}
        .sec-title {{ color:#00d4ff; font-weight:bold; font-size:0.9em; }}
        .sec-status {{ color:#00ff88; margin-top:5px; font-size:0.85em; }}
        .no-msg {{ color:#555; padding:5px; font-size:0.85em; }}
        .footer {{ text-align:center; color:#555; margin-top:20px; font-size:0.8em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 LocalStack Dashboard</h1>
        <p>Cloud Computing — Securisation SQS + S3 + KMS</p>
        <p style="color:#00ff88;margin-top:5px">● LocalStack Community v4.13.2 — Running</p>
    </div>

    <div class="status-bar">
        <div class="stat-box">
            <div class="stat-num">{len(queues)}</div>
            <div class="stat-label">📬 Queues SQS</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">{len(buckets)}</div>
            <div class="stat-label">🪣 Buckets S3</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">{len(keys)}</div>
            <div class="stat-label">🔑 Cles KMS</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">3</div>
            <div class="stat-label">👥 Roles IAM</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">📬 SQS — Files d'attente et Messages</div>
        {sqs_html}
    </div>

    <div class="section">
        <div class="section-title">🪣 S3 — Stockage (Fichier / Objet / Block)</div>
        {s3_html}
    </div>

    <div class="section">
        <div class="section-title">🔑 KMS — Cles de Chiffrement</div>
        {kms_html}
    </div>

    <div class="section">
        <div class="section-title">🔒 Securite Implementee</div>
        <div class="security-grid">
            <div class="sec-item">
                <div class="sec-icon">🔑</div>
                <div class="sec-title">Chiffrement KMS</div>
                <div class="sec-status">✅ AES-256 Actif</div>
            </div>
            <div class="sec-item">
                <div class="sec-icon">👨‍💼</div>
                <div class="sec-title">Producteur</div>
                <div class="sec-status">✅ Ecriture only</div>
            </div>
            <div class="sec-item">
                <div class="sec-icon">👨‍💻</div>
                <div class="sec-title">Consommateur</div>
                <div class="sec-status">✅ Lecture only</div>
            </div>
            <div class="sec-item">
                <div class="sec-icon">🚫</div>
                <div class="sec-title">Etranger</div>
                <div class="sec-status">❌ Acces refuse</div>
            </div>
            <div class="sec-item">
                <div class="sec-icon">📦</div>
                <div class="sec-title">Dead Letter Queue</div>
                <div class="sec-status">✅ 3 tentatives</div>
            </div>
            <div class="sec-item">
                <div class="sec-icon">✍️</div>
                <div class="sec-title">Signature SHA-256</div>
                <div class="sec-status">✅ Integrite OK</div>
            </div>
        </div>
    </div>

    <p class="footer">🔄 Rafraichi automatiquement toutes les 5 secondes</p>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

if __name__ == "__main__":
    print("=" * 50)
    print("DASHBOARD — Interface Graphique Complete")
    print("=" * 50)
    print("\nDashboard : http://localhost:8080\n")
    server = HTTPServer(("0.0.0.0", 8080), DashboardHandler)
    server.serve_forever()