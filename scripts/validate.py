#!/usr/bin/env python3
"""Check every plugin here against the Cursor plugin submission checklist.

Also checks that the Claude Code manifests mirror the Cursor ones, since the
same plugin ships to both hosts from duplicated manifests that can drift.

Run from the repository root: python3 scripts/validate.py
Exits non-zero on any failure so it can gate a commit or CI job.
"""

import json
import os
import re
import sys

MARKETPLACE_MANIFEST = ".cursor-plugin/marketplace.json"
PLUGIN_MANIFEST = ".cursor-plugin/plugin.json"
MCP_CONFIG = "mcp.json"
CLAUDE_MARKETPLACE_MANIFEST = ".claude-plugin/marketplace.json"
CLAUDE_PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
CLAUDE_MCP_CONFIG = ".mcp.json"
SKILLS_DIR = "skills"
SKILL_FILE = "SKILL.md"

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


def check_name(value: str, label: str) -> None:
    if re.fullmatch(NAME_PATTERN, value):
        ok(f"{label} '{value}' is lowercase kebab-case")
    else:
        bad(f"{label} '{value}' must be lowercase kebab-case and start/end alphanumeric")


def check_description(value: str, label: str) -> None:
    if DESCRIPTION_MIN <= len(value) <= DESCRIPTION_MAX:
        ok(f"{label} description present ({len(value)} chars)")
    else:
        bad(f"{label} description length {len(value)} outside {DESCRIPTION_MIN}-{DESCRIPTION_MAX}")


def check_relative_paths(manifest: dict, label: str) -> None:
    for key, value in manifest.items():
        if isinstance(value, str) and not value.startswith("http"):
            if value.startswith("/") or ".." in value:
                bad(f"{label} field '{key}' uses an absolute or escaping path: {value}")
    ok(f"{label} has no absolute or '..' paths")


def check_marketplace() -> list[dict]:
    print(f"== {MARKETPLACE_MANIFEST} ==")
    manifest = json.load(open(MARKETPLACE_MANIFEST))
    ok("valid JSON")

    check_name(manifest.get("name", ""), "marketplace name")

    owner = manifest.get("owner") or {}
    if owner.get("name"):
        ok(f"owner '{owner['name']}' declared")
    else:
        bad("owner.name is required")

    entries = manifest.get("plugins") or []
    if entries:
        ok(f"{len(entries)} plugin entr(y/ies) listed")
    else:
        bad("plugins array is required and must not be empty")

    names = [entry.get("name", "") for entry in entries]
    if len(names) == len(set(names)):
        ok("plugin names are unique")
    else:
        bad(f"duplicate plugin names: {[n for n in names if names.count(n) > 1]}")

    return entries


def check_plugin(entry: dict) -> None:
    source = entry.get("source") or entry.get("name", "")
    print(f"== plugin '{entry.get('name', '?')}' at {source}/ ==")

    if source.startswith("/") or ".." in source:
        bad(f"source '{source}' must be a relative in-repo path")
        return
    if not os.path.isdir(source):
        bad(f"source directory '{source}' not found")
        return

    manifest_path = os.path.join(source, PLUGIN_MANIFEST)
    if not os.path.isfile(manifest_path):
        bad(f"{manifest_path} not found")
        return
    manifest = json.load(open(manifest_path))
    ok(f"{manifest_path} is valid JSON")

    if manifest.get("name") != entry.get("name"):
        bad(f"manifest name '{manifest.get('name')}' differs from marketplace entry '{entry.get('name')}'")
    else:
        ok("manifest name matches the marketplace entry")

    check_name(manifest.get("name", ""), "plugin name")
    check_description(manifest.get("description", ""), "plugin")
    check_relative_paths(manifest, "plugin manifest")

    logo = manifest.get("logo", "")
    if not logo:
        ok("no logo declared (optional)")
    elif logo.startswith(("/", "http")) or ".." in logo:
        bad(f"logo '{logo}' must be a relative in-repo path")
    else:
        logo_path = os.path.join(source, logo)
        if os.path.isfile(logo_path):
            ok(f"logo '{logo}' exists ({os.path.getsize(logo_path)} bytes)")
        else:
            bad(f"logo '{logo}' not found at {logo_path}")

    if not os.path.isfile(os.path.join(source, "README.md")):
        bad(f"{source}/README.md is required to document usage and configuration")
    else:
        ok("README.md present")

    check_mcp(source, manifest)
    check_skills(source)


def check_mcp(source: str, manifest: dict) -> None:
    path = os.path.join(source, MCP_CONFIG)
    if not os.path.isfile(path):
        ok(f"no {MCP_CONFIG} (plugin ships no MCP server)")
        return

    servers = json.load(open(path)).get("mcpServers", {})
    ok(f"{MCP_CONFIG} is valid JSON, declares {len(servers)} server: {', '.join(servers)}")

    used: set[str] = set()
    for entry in servers.values():
        used |= set(re.findall(VARIABLE_PATTERN, json.dumps(entry)))
        if "url" not in entry and "command" not in entry:
            bad("a server entry has neither 'url' nor 'command'")

    declared = set((manifest.get("variables") or {}).get("properties", {}))
    undeclared = used - declared
    if undeclared:
        bad(f"{MCP_CONFIG} uses variables not declared in the manifest: {sorted(undeclared)}")
    else:
        ok("every ${VAR} used in mcp.json is declared in the manifest")


def check_skills(source: str) -> None:
    root = os.path.join(source, SKILLS_DIR)
    if not os.path.isdir(root):
        ok(f"no {SKILLS_DIR}/ (plugin ships no skills)")
        return

    count = 0
    for dirpath, _, filenames in os.walk(root):
        if SKILL_FILE not in filenames:
            continue
        count += 1
        path = os.path.join(dirpath, SKILL_FILE)
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
        ok(f"{count} skill(s) discovered")
    else:
        bad(f"{root}/ exists but contains no {SKILL_FILE}")


def check_hygiene() -> None:
    print("== repository hygiene ==")
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


def check_claude_mirror(entries: list[dict]) -> None:
    """The Claude Code manifests must say the same thing as the Cursor ones.

    Claude Code reads `.claude-plugin/` and `.mcp.json`; Cursor reads
    `.cursor-plugin/` and `mcp.json`. The pairs are hand-maintained copies, so a
    version bump or a server URL change applied to only one host is silent
    breakage for the other. The only field allowed to differ is the marketplace
    entry's `source`, which Claude Code requires to be a "./"-prefixed path.
    """
    print(f"== {CLAUDE_MARKETPLACE_MANIFEST} (Claude Code mirror) ==")
    if not os.path.isfile(CLAUDE_MARKETPLACE_MANIFEST):
        bad(f"{CLAUDE_MARKETPLACE_MANIFEST} not found; the plugin would not install in Claude Code")
        return

    claude_market = json.load(open(CLAUDE_MARKETPLACE_MANIFEST))
    cursor_market = json.load(open(MARKETPLACE_MANIFEST))
    ok("valid JSON")

    for key in ("name", "owner", "metadata"):
        if claude_market.get(key) != cursor_market.get(key):
            bad(f"marketplace '{key}' differs between the Cursor and Claude Code manifests")
    claude_entries = {entry.get("name"): entry for entry in claude_market.get("plugins") or []}
    if set(claude_entries) != {entry.get("name") for entry in entries}:
        bad(f"Claude Code marketplace lists {sorted(claude_entries)}, Cursor lists {sorted(e.get('name') for e in entries)}")
        return
    ok("marketplace header and plugin list match the Cursor manifest")

    for entry in entries:
        name = entry.get("name", "?")
        source = entry.get("source") or name
        claude_entry = claude_entries[name]

        if claude_entry.get("source") != f"./{source.lstrip('./')}":
            bad(f"'{name}' Claude Code source must be './{source.lstrip('./')}', got '{claude_entry.get('source')}'")
        else:
            ok(f"'{name}' source is a './'-prefixed path as Claude Code requires")

        differing = [
            key
            for key in set(entry) | set(claude_entry)
            if key != "source" and entry.get(key) != claude_entry.get(key)
        ]
        if differing:
            bad(f"'{name}' marketplace entry differs on {sorted(differing)} between the two hosts")
        else:
            ok(f"'{name}' marketplace entry otherwise matches the Cursor entry")

        check_mirrored_file(
            os.path.join(source, PLUGIN_MANIFEST),
            os.path.join(source, CLAUDE_PLUGIN_MANIFEST),
            required=True,
        )
        check_mirrored_file(
            os.path.join(source, MCP_CONFIG),
            os.path.join(source, CLAUDE_MCP_CONFIG),
            required=False,
        )


def check_mirrored_file(cursor_path: str, claude_path: str, required: bool) -> None:
    if not os.path.isfile(cursor_path):
        if os.path.isfile(claude_path):
            bad(f"{claude_path} exists but {cursor_path} does not")
        elif required:
            bad(f"{cursor_path} not found")
        return
    if not os.path.isfile(claude_path):
        bad(f"{claude_path} not found; Claude Code does not read {cursor_path}")
        return
    if json.load(open(cursor_path)) == json.load(open(claude_path)):
        ok(f"{claude_path} mirrors {cursor_path}")
    else:
        bad(f"{claude_path} has drifted from {cursor_path}")


def main() -> int:
    entries = check_marketplace()
    for entry in entries:
        check_plugin(entry)
    check_claude_mirror(entries)
    check_hygiene()
    print(f"\nRESULT: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
