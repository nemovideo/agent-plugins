#!/usr/bin/env python3
"""Import the canonical NemoVideo skills from the nemo-skills repository.

The skills are authored and versioned in nemo-skills; this repository only
redistributes them for Model Context Protocol hosts. Editing the copies here
would fork them, so this script overwrites them from a nemo-skills build and
records what it took, letting a reviewer see which upstream version shipped.

It reads the built archives rather than the source tree because the build is
what enforces version numbering and the manifest checks:

    cd <nemo-skills> && node scripts/build-openai-skills.mjs

Only SKILL.md and references/ are copied. agents/openai.yaml is deliberately
left behind: it is the OpenAI Apps dependency manifest, no MCP host here reads
it, and it hardcodes the development endpoint that this repository must not
advertise. The server this plugin talks to is declared in mcp.json instead.

Usage:
    python3 scripts/sync-skills.py [--nemo-skills PATH] [--check]

--check reports drift without writing, for use in CI or before a release.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "nemovideo"
SKILLS_DEST = PLUGIN / "skills"
LOCK = PLUGIN / "skills-source.json"

DEFAULT_NEMO_SKILLS = Path.home() / "Project/nemo-mega-x-monorepo/nemo-skills"
BUILD_SUBDIR = Path("dist/openai-skills")

# Everything the plugin distributes. A skill absent from a build is an error
# rather than a silent omission: a partial skill set changes agent behaviour.
EXPECTED = ("nemovideo", "draft-v3-authoring", "platform-reference-materials")

# The plugin-level archive bundles all three; the per-skill archives are what we
# unpack, so the bundle must not be mistaken for one of them.
ARCHIVE = re.compile(r"^(?P<name>[a-z0-9-]+)-(?P<version>v\d+\.\d+\.\d+)\.zip$")

COPY_ROOT = "SKILL.md"
COPY_DIRS = ("references",)


def discover(build_dir: Path) -> dict[str, tuple[Path, str]]:
    """Map each expected skill to its archive and version."""
    if not build_dir.is_dir():
        sys.exit(
            f"no build at {build_dir}\n"
            f"run: cd {build_dir.parents[1]} && node scripts/build-openai-skills.mjs"
        )

    found: dict[str, tuple[Path, str]] = {}
    for archive in sorted(build_dir.glob("*.zip")):
        match = ARCHIVE.match(archive.name)
        if match and match["name"] in EXPECTED:
            found[match["name"]] = (archive, match["version"])

    missing = [name for name in EXPECTED if name not in found]
    if missing:
        sys.exit(f"build is missing: {', '.join(missing)}")
    return found


def extract(archive: Path, into: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.namelist():
            # Refuse traversal: these archives are trusted today, but this file
            # is the seam where an untrusted one would enter.
            if member.startswith("/") or ".." in Path(member).parts:
                sys.exit(f"unsafe path in {archive.name}: {member}")
        bundle.extractall(into)


def wanted(root: Path) -> list[Path]:
    """Paths inside an extracted skill that belong in this repository."""
    paths = [root / COPY_ROOT]
    for directory in COPY_DIRS:
        if (root / directory).is_dir():
            paths.extend(sorted(p for p in (root / directory).rglob("*") if p.is_file()))
    return paths


def differs(src_root: Path, dst_root: Path) -> bool:
    src_files = {p.relative_to(src_root) for p in wanted(src_root)}
    dst_files = set()
    if dst_root.is_dir():
        dst_files = {p.relative_to(dst_root) for p in dst_root.rglob("*") if p.is_file()}
    if src_files != dst_files:
        return True
    return any(
        not filecmp.cmp(src_root / rel, dst_root / rel, shallow=False) for rel in src_files
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nemo-skills", type=Path, default=DEFAULT_NEMO_SKILLS)
    parser.add_argument("--check", action="store_true", help="report drift, write nothing")
    args = parser.parse_args()

    archives = discover(args.nemo_skills / BUILD_SUBDIR)
    versions = {name: version for name, (_, version) in archives.items()}

    with tempfile.TemporaryDirectory() as tmp:
        staged: dict[str, Path] = {}
        for name, (archive, _) in archives.items():
            root = Path(tmp) / name
            extract(archive, root)
            if not (root / COPY_ROOT).is_file():
                sys.exit(f"{archive.name} has no {COPY_ROOT}")
            staged[name] = root

        drifted = [name for name, root in staged.items() if differs(root, SKILLS_DEST / name)]
        recorded = json.loads(LOCK.read_text())["skills"] if LOCK.is_file() else {}
        if recorded != versions:
            drifted.append("skills-source.json")

        if args.check:
            if drifted:
                print("out of date: " + ", ".join(sorted(set(drifted))))
                return 1
            print("up to date with " + ", ".join(f"{n} {v}" for n, v in sorted(versions.items())))
            return 0

        for name, root in staged.items():
            dest = SKILLS_DEST / name
            shutil.rmtree(dest, ignore_errors=True)
            for path in wanted(root):
                target = dest / path.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)

    LOCK.write_text(
        json.dumps(
            {
                "comment": (
                    "Generated by scripts/sync-skills.py. The skills under "
                    "nemovideo/skills/ are copies from nemo-skills; edit them there."
                ),
                "source": "nemo-skills",
                "skills": versions,
            },
            indent=2,
        )
        + "\n"
    )

    for name, version in sorted(versions.items()):
        print(f"  {name} {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
