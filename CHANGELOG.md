# Changelog

## 1.1.0

- `neev-cli` — matched to neev-cli 0.8.x. Drops `exec --stream`, which the CLI rejects (output already streams), and replaces the deprecated `sandbox restore` with `sandbox rollback`. Adds the `create` flags, resizing and egress with `sandbox update`, `fork --name`, waiting for a snapshot before rolling back, SSH access through `ssh-config`, and output formats. Says that `exec` runs no shell, so pipes and `&&` need `sh -c`, that `update --allow` replaces the egress policy instead of adding to it, that a sandbox's state is `phase` (not `status`), and that `delete` and `rollback` with no terminal abort with exit 0 unless given `--yes`.
- `neev-sdk` — pinned to SDK 0.8.2 (`@neevcloud/sdk@^0.8.2`, `neevai>=0.8.2,<0.9`). Snapshot waits compare `status` directly and stop with an error if a snapshot fails instead of polling forever. Examples also use `rollback(snap.id)` and egress policies without `allow_internet`, which 0.8.2 supports. Also fixes examples that failed as written: listing a directory that didn't exist, reading a file that was never written, and rolling back before the snapshot was ready. The `egress_add` examples now state that the sandbox must already be in `allow_list` mode.
- `neev-sdk` — updated for SDK 0.8.1. Install without `@beta`, which points at an older pre-release. Streaming `exec` examples now iterate the stream, because an un-iterated stream never runs the command. Egress changes use `update()` with `egress_add` / `egress_remove` instead of raw HTTP. Adds snapshots, rollback and fork, the audit trail, preview slugs, large-file upload, keepalive and timeouts, and error codes. Corrects two claims: `allow_internet` is not audit-logged, and processes survive a pause.
- `neev-sandbox-mcp` — connecting an agent to the sandbox MCP server. Writes the Claude Code, Cursor, or Codex config with the API key read from the environment, verifies the connection, and covers creating on first use, phases, and the actions to ask about first.

## 1.0.0

Initial release.

- `neev-cli` — installing and signing in, choosing an organization and project, the sandbox lifecycle, and running files, commands, and processes from a shell or CI. Covers the two credentials and when each applies, and that signing in is optional because `NEEV_API_TOKEN` authenticates a command on its own.
- `neev-sdk` — building against NeevCloud from TypeScript or Python: sandboxes, files, commands, processes, exposing a port for a preview URL, and controlling what a sandbox can reach on the network.
- Plugin manifests for Claude Code, Codex, and Cursor, plus the generic `.agents` and `.plugin` discovery paths, so the repo installs as a plugin as well as through the skills CLI.
