#!/usr/bin/env python3
"""Check this plugin against the Cursor plugin submission checklist.

Run from the repository root: python3 scripts/validate.py
Exits non-zero on any failure so it can gate a commit or CI job.
"""

import json
import os
import re
import sys

MANIFEST = ".cursor-plugin/plugin.json"
NAME_PATTERN = r"[a-z0-9]([a-z0-9.-]*[a-z0-9])?"
DESCRIPTION_MIN = 10
DESCRIPTION_MAX = 500
SKILL_FRONTMATTER_FIELDS = {"name", "description"}
FRONTMATTER_PATTERN = r"^---\n(.*?)\n---\n"
VARIABLE_PATTERN = r"\$\{([A-Za-z0-9_]+)\}"
SCANNED_SUFFIXES = (".md", ".json", ".txt")
SCANNED_NAMES = ("LICENSE",)
CREDENTIAL_PATTERN = re.compile(
    r"(?i)(bearer\s+[A-Za-z0-9._-]{20,}"
    r"|sk-[A-Za-z0-9]{16,}"
    r"|BEGIN [A-Z ]*PRIVATE KEY"
    r"|client_secret\"?\s*[:=])"
)

failures: list[str] = []


def ok(message: str) -> None:
    print(f"  PASS  {message}")


def bad(message: str) -> None:
    failures.append(message)
    print(f"  FAIL  {message}")


def check_manifest() -> dict:
    print("== manifest ==")
    manifest = json.load(open(MANIFEST))
    ok(f"{MANIFEST} is valid JSON")

    name = manifest.get("name", "")
    if re.fullmatch(NAME_PATTERN, name):
        ok(f"name '{name}' is lowercase kebab-case")
    else:
        bad(f"name '{name}' must be lowercase kebab-case and start/end alphanumeric")

    description = manifest.get("description", "")
    if DESCRIPTION_MIN <= len(description) <= DESCRIPTION_MAX:
        ok(f"description present ({len(description)} chars)")
    else:
        bad(f"description length {len(description)} outside {DESCRIPTION_MIN}-{DESCRIPTION_MAX}")

    logo = manifest.get("logo", "")
    if logo.startswith(("/", "http")) or ".." in logo:
        bad(f"logo '{logo}' must be a relative in-repo path")
    elif os.path.isfile(logo):
        ok(f"logo '{logo}' exists ({os.path.getsize(logo)} bytes)")
    else:
        bad(f"logo '{logo}' not found")

    for key, value in manifest.items():
        if isinstance(value, str) and not value.startswith("http"):
            if value.startswith("/") or ".." in value:
                bad(f"manifest field '{key}' uses an absolute or escaping path: {value}")
    ok("no absolute or '..' paths in manifest")
    return manifest


def check_mcp(manifest: dict) -> None:
    print("== mcp.json ==")
    servers = json.load(open("mcp.json")).get("mcpServers", {})
    ok(f"mcp.json is valid JSON, declares {len(servers)} server: {', '.join(servers)}")

    used: set[str] = set()
    for entry in servers.values():
        used |= set(re.findall(VARIABLE_PATTERN, json.dumps(entry)))
        if "url" not in entry and "command" not in entry:
            bad("a server entry has neither 'url' nor 'command'")

    declared = set((manifest.get("variables") or {}).get("properties", {}))
    undeclared = used - declared
    if undeclared:
        bad(f"mcp.json uses variables not declared in the manifest: {sorted(undeclared)}")
    else:
        ok("every ${VAR} used in mcp.json is declared in the manifest")


def check_skills() -> None:
    print("== skills ==")
    count = 0
    for dirpath, _, filenames in os.walk("skills"):
        if "SKILL.md" not in filenames:
            continue
        count += 1
        path = os.path.join(dirpath, "SKILL.md")
        matched = re.match(FRONTMATTER_PATTERN, open(path).read(), re.S)
        if not matched:
            bad(f"{path} is missing YAML frontmatter")
            continue
        present = {
            field
            for field in SKILL_FRONTMATTER_FIELDS
            if re.search(rf"^{field}:", matched.group(1), re.M)
        }
        if present == SKILL_FRONTMATTER_FIELDS:
            ok(f"{path} frontmatter has name + description")
        else:
            bad(f"{path} frontmatter missing {sorted(SKILL_FRONTMATTER_FIELDS - present)}")

    if count:
        ok(f"{count} skill(s) discovered under skills/")
    else:
        bad("no skills found under skills/")


def check_hygiene() -> None:
    print("== hygiene ==")
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if os.path.islink(path):
                bad(f"symlinks are not allowed in a plugin package: {path}")
            if filename.endswith(SCANNED_SUFFIXES) or filename in SCANNED_NAMES:
                found = CREDENTIAL_PATTERN.search(open(path, errors="ignore").read())
                if found:
                    bad(f"possible credential in {path}: {found.group(0)[:30]}")
    ok("no symlinks and no credential-looking literals")


def main() -> int:
    manifest = check_manifest()
    check_mcp(manifest)
    check_skills()
    check_hygiene()
    print(f"\nRESULT: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
