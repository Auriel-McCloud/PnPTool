"""Bootstrap the first (or an additional) GM account. There is no self-registration by design.

Usage:
    python scripts/create_gm.py --username sl --password "correct horse battery staple"
"""

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import GraphDatabase

from app.auth.security import hash_password
from app.config import settings


def create_gm(username: str, password: str) -> None:
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with driver.session() as session:
            existing = session.run("MATCH (g:GMUser {username: $username}) RETURN g", username=username).single()
            if existing is not None:
                print(f"GMUser '{username}' existiert bereits.")
                return

            session.run(
                "CREATE (g:GMUser {id: $id, username: $username, passwordHash: $password_hash, createdAt: datetime()})",
                id=str(uuid.uuid4()),
                username=username,
                password_hash=hash_password(password),
            )
            print(f"GMUser '{username}' angelegt.")
    finally:
        driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap a GM account")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    create_gm(args.username, args.password)
