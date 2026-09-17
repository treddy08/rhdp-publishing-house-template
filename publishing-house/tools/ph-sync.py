#!/usr/bin/env python3
"""Sync workflow rejections to local files. Used by intake/development skills.

Always calls /workflow-data and /workflow-state. Only syncs rejections.
workflow_id, epic_key, and jira_url are synced by create-catalog endpoint.
Rejections are synced per-reason by UUID, routed to content/infra sections.

Output: key:value pairs, one per line
  stage:intake
  workflow_id:abc-123
  epic_key:RHDPCD-456
  unresolved_rejections:2
"""
import json
import os
import re
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


def sync_rejection(spec_path, rejection):
    """Sync rejection reasons to spec.yaml by per-reason UUID.

    New reasons are routed to content or infra based on reviewerStage.
    Already-known reasons (by id) stay in their original section and get
    their resolved flag updated.
    """
    if not rejection:
        return

    reasons = rejection.get("reasons", [])
    if not reasons:
        return

    reviewer_stage = rejection.get("reviewerStage", "")
    target_section = "content" if reviewer_stage == "content_review" else "infra"

    spec_data = yaml.safe_load(spec_path.read_text()) or {}
    checklist = spec_data.setdefault("approval_checklist", {})

    known_ids = {}
    for section in ("content", "infra"):
        section_data = checklist.setdefault(section, {})
        for r in section_data.get("rejections", []):
            known_ids[r.get("id")] = (section, r)

    changed = False
    for reason in reasons:
        rid = reason.get("id")
        if not rid:
            continue
        if rid in known_ids:
            _, existing = known_ids[rid]
            if existing.get("resolved") != reason.get("resolved", False):
                existing["resolved"] = reason.get("resolved", False)
                changed = True
        else:
            section_data = checklist.setdefault(target_section, {})
            rej_list = section_data.setdefault("rejections", [])
            rej_list.append({
                "id": rid,
                "text": reason.get("text", ""),
                "resolved": reason.get("resolved", False),
                "reviewer": rejection.get("reviewerName", ""),
                "timestamp": rejection.get("timestamp", ""),
            })
            changed = True

    if changed:
        with open(spec_path, "w") as f:
            yaml.dump(spec_data, f, default_flow_style=False, sort_keys=False)


def main():
    root = find_repo_root()
    if not root:
        print(json.dumps({"error": "catalog-info.yaml not found"}))
        sys.exit(1)

    auth_path = Path(os.path.expanduser("~/.config/publishing-house/auth.json"))
    if not auth_path.exists():
        print(json.dumps({"error": "~/.config/publishing-house/auth.json not found"}))
        sys.exit(1)

    creds = json.loads(auth_path.read_text())
    api_key = creds.get("credential", "")
    central = creds.get("central", "").rstrip("/")
    if not api_key or not central:
        print(json.dumps({"error": "Missing credential or central in auth.json"}))
        sys.exit(1)

    spec_path = root / "publishing-house" / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text()) or {} if spec_path.exists() else {}
    project = spec.get("project", {})

    workflow_id = project.get("workflow_id", "")
    if not workflow_id:
        print(json.dumps({"error": "project.workflow_id missing in spec.yaml"}))
        sys.exit(1)
    epic_key = project.get("jira_ticket", "")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        req = urllib.request.Request(
            f"{central}/api/v1/projects/{workflow_id}/workflow-data",
            headers=headers,
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            wd = json.loads(r.read().decode())
    except Exception as e:
        print(json.dumps({"error": f"Failed to fetch workflow data: {e}"}))
        sys.exit(1)

    rejection = wd.get("rejection")
    stage = wd.get("stage", "intake")

    # workflow_id, epic_key, and jira_url are synced by create-catalog endpoint
    # We only read them here for output, not write them

    sync_rejection(spec_path, rejection)

    unresolved = 0
    refreshed_spec = yaml.safe_load(spec_path.read_text()) or {}
    for section in ("content", "infra"):
        for reason in refreshed_spec.get("approval_checklist", {}).get(section, {}).get("rejections", []):
            if not reason.get("resolved", False):
                unresolved += 1

    print(f"stage:{stage}")
    print(f"workflow_id:{workflow_id}")
    print(f"epic_key:{epic_key}")
    print(f"unresolved_rejections:{unresolved}")


if __name__ == "__main__":
    main()
