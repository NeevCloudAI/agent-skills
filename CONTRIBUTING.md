# Contributing

These skills describe a product that changes, so the thing that matters most is that every command and method in them is real.

## Ground rules

- **Verify before writing.** Take command flags from `--help` or the cobra tree, and SDK signatures from the published docs or the OpenAPI spec. Do not write either from memory.
- **Document what ships.** If a feature is merged but not enabled in any environment, it does not belong in a skill yet.
- **Say what an agent cannot guess.** The valuable content is the traps — which credential a call needs, that ports are private until exposed, that a sandbox holds quota until deleted. Anything discoverable from `--help` is worth less.
- **Link, do not duplicate.** Point at the documentation for install steps and long explanations, so a skill installed months ago still routes to current instructions.

## Making a change

1. Edit the skill under `skills/<name>/SKILL.md`.
2. Run the checks:

   ```bash
   python3 scripts/validate.py
   npx -y skills list .
   ```

3. Open a pull request. CI runs both of the above.

## Releasing

Versions are kept in lockstep: every manifest and both skills carry the same version, and `scripts/validate.py` fails if they drift.

1. Bump the version in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `.plugin/plugin.json`, and the `metadata.version` in each `skills/*/SKILL.md`.
2. Add a `CHANGELOG.md` entry.
3. Merge that to `main`.
4. Tag it and push the tag:

   ```bash
   git tag -a v1.1.0 -m "v1.1.0"
   git push origin v1.1.0
   ```

The release workflow validates that the tag matches the declared version, re-runs the checks, and creates the GitHub release from the tag message. Nothing publishes on a push to `main`.
