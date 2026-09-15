#!/usr/bin/env python3
"""Fetch pre-intake data from Jira ProForma form.

Calls /jira/epic/{epic_key}/preintake-data to retrieve onboarding information
captured in the pre-intake workflow phase.

Output: JSON object with pre-intake fields
"""
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

import yaml


def find_repo_root():
    p = Path.cwd()
    while p != p.parent:
        if (p / "catalog-info.yaml").exists():
            return p
        p = p.parent
    return None


def main():
    root = find_repo_root()
    if not root:
        print(json.dumps({"error": "catalog-info.yaml not found"}), file=sys.stderr)
        sys.exit(1)

    auth_path = Path(os.path.expanduser("~/.config/publishing-house/auth.json"))
    if not auth_path.exists():
        print(json.dumps({"error": "~/.config/publishing-house/auth.json not found"}), file=sys.stderr)
        sys.exit(1)

    creds = json.loads(auth_path.read_text())
    api_key = creds.get("credential", "")
    central = creds.get("central", "").rstrip("/")
    if not api_key or not central:
        print(json.dumps({"error": "Missing credential or central in auth.json"}), file=sys.stderr)
        sys.exit(1)

    spec_path = root / "publishing-house" / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text()) or {} if spec_path.exists() else {}
    project = spec.get("project", {})

    epic_key = project.get("jira_ticket", "")
    if not epic_key:
        print(json.dumps({"error": "project.jira_ticket missing in spec.yaml"}), file=sys.stderr)
        sys.exit(1)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(
            f"{central}/api/v1/jira/epic/{epic_key}/preintake-data",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = json.loads(r.read().decode())

        # Output as JSON
        print(json.dumps(data, indent=2))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(json.dumps({"error": "No pre-intake data found for this epic"}), file=sys.stderr)
        else:
            print(json.dumps({"error": f"HTTP {e.code}: {e.reason}"}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Failed to fetch pre-intake data: {e}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
