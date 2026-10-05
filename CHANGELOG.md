# Changelog

## Unreleased

- `neev-sandbox-mcp` — connecting an agent to the sandbox MCP server. Writes the Claude Code, Cursor, or Codex config with the API key read from the environment, verifies the connection, and covers creating on first use, phases, and the actions to ask about first.

## 1.0.0

Initial release.

- `neev-cli` — installing and signing in, choosing an organization and project, the sandbox lifecycle, and running files, commands, and processes from a shell or CI. Covers the two credentials and when each applies, and that signing in is optional because `NEEV_API_TOKEN` authenticates a command on its own.
- `neev-sdk` — building against NeevCloud from TypeScript or Python: sandboxes, files, commands, processes, exposing a port for a preview URL, and controlling what a sandbox can reach on the network.
- Plugin manifests for Claude Code, Codex, and Cursor, plus the generic `.agents` and `.plugin` discovery paths, so the repo installs as a plugin as well as through the skills CLI.
