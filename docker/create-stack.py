#!/usr/bin/env python3
"""
Create the Jarvis (Onyx) stack in Portainer via API.

Usage:
  python docker/create-stack.py --user admin --password YOUR_PASSWORD

Or with environment variables:
  PORTAINER_USERNAME=admin PORTAINER_PASSWORD=xxx python docker/create-stack.py
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import ssl

BASE = "https://portainer.fabioviana.app.br/api"
ENDPOINT_ID = 1
STACK_NAME = "jarvis"
STACK_FILE = os.path.join(os.path.dirname(__file__), "docker-stack.yml")

# Environment variables for the Portainer stack
ENV_VARS = [
    {"name": "DOMAIN", "value": "jarvis.fabioviana.app.br"},
    {"name": "IMAGE_TAG", "value": "latest"},
    {"name": "REGISTRY", "value": "byfabioviana"},
    {"name": "AUTH_TYPE", "value": "basic"},
    {"name": "POSTGRES_USER", "value": "postgres"},
    {"name": "POSTGRES_PASSWORD", "value": "923e87fa759a52f0181644871eb0ae95"},
    {"name": "USER_AUTH_SECRET", "value": "7250ede5050f82825a8b145c42c7d3aa6a56684014070c9de1ab07b4d8636bb3"},
    {"name": "ENCRYPTION_KEY_SECRET", "value": "d8213bdadbf7c8e481e7b2ccd73bdff56da3ab0b22e75055058ce255a8b01aa3"},
    {"name": "OPENROUTER_API_KEY", "value": os.environ.get("OPENROUTER_API_KEY", "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")},
    {"name": "MINIO_ROOT_USER", "value": "minioadmin"},
    {"name": "MINIO_ROOT_PASSWORD", "value": "3OpuDRDCZ4-BJEbm1iWqHe7O"},
    {"name": "S3_AWS_ACCESS_KEY_ID", "value": "minioadmin"},
    {"name": "S3_AWS_SECRET_ACCESS_KEY", "value": "3OpuDRDCZ4-BJEbm1iWqHe7O"},
    {"name": "OPENSEARCH_ADMIN_PASSWORD", "value": "StrongPassword123!"},
    {"name": "LOG_LEVEL", "value": "info"},
    {"name": "ENABLE_CRAFT", "value": "false"},
]

ctx = ssl.create_default_context()


def api(method, path, data=None, jwt=None):
    headers = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}", data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP {e.code} {method} {path}: {e.read().decode()}", flush=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create Jarvis stack in Portainer")
    parser.add_argument("--user", default=os.environ.get("PORTAINER_USERNAME", "admin"))
    parser.add_argument("--password", default=os.environ.get("PORTAINER_PASSWORD", ""))
    args = parser.parse_args()

    if not args.password:
        print("ERROR: Provide --password or set PORTAINER_PASSWORD env var")
        sys.exit(1)

    # 1. Authenticate
    print("-> Authenticating with Portainer...", flush=True)
    result = api("POST", "/auth", {"username": args.user, "password": args.password})
    jwt = result["jwt"]
    print("   OK", flush=True)

    # 2. Check if stack already exists
    print("-> Checking existing stacks...", flush=True)
    stacks = api("GET", "/stacks", jwt=jwt)
    for s in stacks:
        print(f"   Found: ID={s['Id']} Name={s['Name']}", flush=True)
        if s["Name"] == STACK_NAME:
            print(f"   Stack '{STACK_NAME}' already exists (ID={s['Id']}). Use Portainer UI to update.", flush=True)
            print(f"\n   Set GitHub secret: gh secret set PORTAINER_STACK_ID --repo byfabioviana/onyx --body \"{s['Id']}\"")
            return

    # 3. Read stack file
    print(f"-> Reading {STACK_FILE}...", flush=True)
    with open(STACK_FILE, "r", encoding="utf-8") as f:
        stack_content = f.read()
    print(f"   {len(stack_content)} bytes", flush=True)

    # 4. Create stack
    print(f"-> Creating stack '{STACK_NAME}'...", flush=True)
    payload = {
        "Name": STACK_NAME,
        "StackFileContent": stack_content,
        "SwarmID": "",  # will be auto-detected
        "Env": ENV_VARS,
    }

    # Get swarm ID
    swarm_info = api("GET", f"/endpoints/{ENDPOINT_ID}/docker/swarm", jwt=jwt)
    payload["SwarmID"] = swarm_info["ID"]
    print(f"   Swarm ID: {swarm_info['ID']}", flush=True)

    result = api(
        "POST",
        f"/stacks/create/swarm/string?endpointId={ENDPOINT_ID}",
        data=payload,
        jwt=jwt,
    )
    stack_id = result["Id"]
    print(f"\nSUCCESS! Stack '{STACK_NAME}' created with ID={stack_id}", flush=True)
    print(f"\nSet GitHub secret:")
    print(f"  gh secret set PORTAINER_STACK_ID --repo byfabioviana/onyx --body \"{stack_id}\"")


if __name__ == "__main__":
    main()
