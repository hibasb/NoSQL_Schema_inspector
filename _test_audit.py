from security_auditor import run_audit
from schema_inferrer import infer_schema

# Collection de test avec plusieurs vulnerabilites
BCRYPT = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LkMR8hmFmXPJ8X5Wi"

docs = [
    {"username": "alice", "password": "azerty123",  "email": "alice@test.com", "role": "admin"},
    {"username": "bob",   "password": "hunter2",    "email": "bob@test.com",   "role": "user"},
    {"username": "carol", "password": BCRYPT,        "email": "carol@test.com", "role": "user"},
]

schema = infer_schema(docs)
result = run_audit(docs, schema)

print(f"Score : {result['score']}/100")
print(f"Summary : {result['summary']}")
print()
for f in result["findings"]:
    print(f"  [{f['severity']}] {f['rule']} | champ={f['field']} | ex={f['sample']}")
