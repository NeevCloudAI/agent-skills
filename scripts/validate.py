#!/usr/bin/env python3
"""Validate the skills repo: skill frontmatter, manifest JSON, and one version everywhere.

Run with no arguments to check the tree. Pass a tag (e.g. v1.0.0) to also require that
the tag matches the declared version, which is what the release workflow does.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# The version every manifest and skill must agree on.
SOURCE_OF_TRUTH = ROOT / ".claude-plugin" / "plugin.json"
# Manifests carrying a "version" that must match.
VERSIONED_MANIFESTS = [
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".plugin/plugin.json",
]
# Manifests that must parse but carry no version.
OTHER_MANIFESTS = [
    ".cursor-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
]

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load_json(rel: str):
    """Parse one manifest, recording a readable error rather than raising."""
    path = ROOT / rel
    if not path.exists():
        fail(f"{rel}: missing")
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{rel}: invalid JSON — {exc}")
        return None


def skill_frontmatter(path: pathlib.Path) -> dict:
    """Pull the YAML frontmatter block off a SKILL.md without a YAML dependency.

    Only the flat keys and the one nested `metadata` block are read, which is all the
    skills registry needs and all we assert on.
    """
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        fail(f"{path.relative_to(ROOT)}: no YAML frontmatter block")
        return {}
    out, section = {}, None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            key, _, value = line.partition(":")
            value = value.strip()
            section = key.strip() if not value else None
            if value:
                out[key.strip()] = value.strip('"').strip("'")
        elif section:
            key, _, value = line.strip().partition(":")
            out[f"{section}.{key.strip()}"] = value.strip().strip('"').strip("'")
    return out


source = load_json(str(SOURCE_OF_TRUTH.relative_to(ROOT)))
version = (source or {}).get("version")
if not version:
    fail(f"{SOURCE_OF_TRUTH.relative_to(ROOT)}: no version to check the others against")

for rel in VERSIONED_MANIFESTS:
    data = load_json(rel)
    if data is not None and version and data.get("version") != version:
        fail(f"{rel}: version {data.get('version')!r} does not match {version!r}")

for rel in OTHER_MANIFESTS:
    load_json(rel)

skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
if not skills:
    fail("skills/: no SKILL.md found")

for path in skills:
    rel = path.relative_to(ROOT)
    fm = skill_frontmatter(path)
    if not fm:
        continue
    name = fm.get("name")
    if not name:
        fail(f"{rel}: frontmatter has no name")
    elif name != path.parent.name:
        fail(f"{rel}: name {name!r} does not match its directory {path.parent.name!r}")
    if not fm.get("description"):
        fail(f"{rel}: frontmatter has no description")
    declared = fm.get("metadata.version")
    if version and declared != version:
        fail(f"{rel}: metadata.version {declared!r} does not match {version!r}")

# A release tag has to name the version it ships.
if len(sys.argv) > 1:
    tag = sys.argv[1]
    if tag != f"v{version}":
        fail(f"tag {tag!r} does not match the declared version {version!r} (expected v{version})")

if errors:
    print("validation failed:\n" + "\n".join(f"  - {e}" for e in errors), file=sys.stderr)
    sys.exit(1)

print(f"ok — version {version}, {len(skills)} skills: {', '.join(p.parent.name for p in skills)}")
