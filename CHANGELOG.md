# Changelog

## Unreleased

- `neev-sdk` — updated for SDK 0.8.1. Install without `@beta`, which points at an older pre-release. Streaming `exec` examples now iterate the stream, because an un-iterated stream never runs the command. Egress changes use `update()` with `egress_add` / `egress_remove` instead of raw HTTP. Adds snapshots, rollback and fork, the audit trail, preview slugs, large-file upload, keepalive and timeouts, and error codes. Corrects two claims: `allow_internet` is not audit-logged, and processes survive a pause.
- `neev-sandbox-mcp` — connecting an agent to the sandbox MCP server. Writes the Claude Code, Cursor, or Codex config with the API key read from the environment, verifies the connection, and covers creating on first use, phases, and the actions to ask about first.

## 1.0.0

Initial release.

- `neev-cli` — installing and signing in, choosing an organization and project, the sandbox lifecycle, and running files, commands, and processes from a shell or CI. Covers the two credentials and when each applies, and that signing in is optional because `NEEV_API_TOKEN` authenticates a command on its own.
- `neev-sdk` — building against NeevCloud from TypeScript or Python: sandboxes, files, commands, processes, exposing a port for a preview URL, and controlling what a sandbox can reach on the network.
- Plugin manifests for Claude Code, Codex, and Cursor, plus the generic `.agents` and `.plugin` discovery paths, so the repo installs as a plugin as well as through the skills CLI.
