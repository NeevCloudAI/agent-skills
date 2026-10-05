---
name: neev-sandbox-mcp
description: Connect an agent — Claude Code, Cursor, Codex, Claude Desktop, or any MCP client — to the NeevCloud sandbox MCP server so it gets a sandbox as native tools, without the API key ever passing through chat, then work in that sandbox safely. Use when asked to set up, configure, or troubleshoot the sandbox MCP server, or when working in a NeevCloud sandbox over MCP.
metadata:
  author: neevcloud
  version: "1.0.0"
---

# neev-sandbox-mcp

The sandbox MCP server gives an agent one NeevCloud sandbox as native tools: run commands, read and write files, manage processes, snapshot and roll back, pause and resume. It needs one URL and a project API key, and nothing else: no CLI, no SDK, no Personal Access Token and no sign-in. Do not install or ask for any of them to set this up.

Full reference: https://docs.ai.neevcloud.com/agentic-studio/overview/sandbox-mcp-server.md

## The Connection

| Setting | Value |
|---|---|
| URL | `https://mcp.sandboxes.as-south-1.ai.neevcloud.com/mcp` — the region in the hostname is the sandbox's region |
| Transport | Streamable HTTP. The server holds no session |
| `Authorization` | `Bearer sk-nc-…`, a **project API key**. `x-api-key: sk-nc-…` also works |
| `x-sandbox-name` | Which sandbox this connection works in. Omitted, it is `default` |

Only the API key is used. A Personal Access Token (`pat-nc-…`) is for the separate account MCP server, does not work here, and is never needed for this setup.

A sandbox name is lowercase letters, digits and hyphens, starts with a letter, ends with a letter or digit, and is at most 63 characters. One URL serves every sandbox; changing sandboxes means changing the header, not the URL.

## Keep the Key Out of Chat and Out of Files

Never ask the user to paste the API key into chat, and never write its value into a config file. Every supported agent reads it from an environment variable, so the config only ever holds a reference.

For Claude Desktop, skip to its section below: it does not read the shell environment, so the key goes in a headers file instead.

1. Check that `NEEV_API_KEY` is set and non-empty without printing it, for example `test -n "$NEEV_API_KEY" && echo set`.
2. If it is not set, stop. Ask the user to create a project API key in the NeevCloud console and export `NEEV_API_KEY` in their shell profile, then restart the agent so it inherits the variable. A `.env` file is not enough: these agents read the environment they were launched from.
3. Ask which sandbox name to use, or propose one from the project directory name. Never reuse a name that may belong to someone else's sandbox in the same project.

## Configure the Agent

Write the config for the agent you are running in. Each form below keeps the key in the environment.

**Claude Code** — `.mcp.json` in the project root. `${NEEV_API_KEY}` is expanded when the server starts, so the file is safe to commit. Do not use `claude mcp add --header` for the key: it stores the header literally.

```json
{
  "mcpServers": {
    "neev-sandbox": {
      "type": "http",
      "url": "https://mcp.sandboxes.as-south-1.ai.neevcloud.com/mcp",
      "headers": {
        "Authorization": "Bearer ${NEEV_API_KEY}",
        "x-sandbox-name": "my-agent"
      }
    }
  }
}
```

**Cursor** — `.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` for every project.

```json
{
  "mcpServers": {
    "neev-sandbox": {
      "url": "https://mcp.sandboxes.as-south-1.ai.neevcloud.com/mcp",
      "headers": {
        "Authorization": "Bearer ${env:NEEV_API_KEY}",
        "x-sandbox-name": "my-agent"
      }
    }
  }
}
```

**Codex** — `~/.codex/config.toml`.

```toml
[mcp_servers.neev-sandbox]
url = "https://mcp.sandboxes.as-south-1.ai.neevcloud.com/mcp"
bearer_token_env_var = "NEEV_API_KEY"
http_headers = { "x-sandbox-name" = "my-agent" }
```

**Claude Desktop** — its config file only starts local stdio servers, so bridge to the HTTP server with [`mcp-remote`](https://www.npmjs.com/package/mcp-remote), which needs Node.js. Desktop does not inherit the shell environment, so the key cannot come from `NEEV_API_KEY`. Keep it in a headers file instead, out of the config and out of the process list.

1. Create `~/.neevcloud/sandbox-mcp.headers` with a placeholder, and make it readable only by the user (`chmod 600` on macOS and Linux):

   ```
   Authorization: Bearer <paste your sk-nc- key here>
   x-sandbox-name: my-agent
   ```

2. Ask the user to open the file in an editor and replace the placeholder with their key. Never write the key yourself.
3. Add the server to `claude_desktop_config.json` (`~/Library/Application Support/Claude/` on macOS, `%APPDATA%\Claude\` on Windows), merged into any existing `mcpServers`. The path must be absolute, because `~` is not expanded:

   ```json
   {
     "mcpServers": {
       "neev-sandbox": {
         "command": "npx",
         "args": [
           "-y", "mcp-remote@latest",
           "https://mcp.sandboxes.as-south-1.ai.neevcloud.com/mcp",
           "--transport", "http-only",
           "--header-file", "/Users/me/.neevcloud/sandbox-mcp.headers"
         ]
       }
     }
   }
   ```

4. Ask the user to quit Claude Desktop completely and reopen it. Closing the window is not enough.

**Any other MCP client** — point it at the URL with the two headers above, and use its own environment-variable reference for the key. If it has none, tell the user the config will hold the key in plain text and let them write that value in themselves.

If a server named `neev-sandbox` is already configured, show the user the difference and ask before replacing it.

## Verify

The agent picks up a new MCP server only after a restart or reload. After that:

1. List the server's tools. Work from that list rather than from memory, since the tools offered can change.
2. Call `get_sandbox`. If it reports that no such sandbox exists, setup is done: the sandbox is created on first use, below.
3. An authentication error means the key is missing, wrong, or a PAT. Re-check `NEEV_API_KEY` in the environment the agent was launched from.

## Working Over MCP

- **Create on first use.** `create_sandbox` takes no arguments and creates the sandbox this connection names. Creation is asynchronous: if the next call says it is not ready, poll `get_sandbox` and wait, and never create a second one.
- **Phases.** `Ready`: run commands. `Paused`: carry on, the next call wakes it. `Pending`, `NotReady`, `Unknown`: still starting, wait a few seconds. `RestoreFailed`: it will not recover, so delete it and create a new one.
- **Paths are relative** to the workspace. File tools reject absolute paths.
- **No internet by default.** If an install hangs, outbound access is closed. No tool can change that. Ask the user to allow the hosts through the API or the SDK.
- **Long-running work** goes through `process_start`, which returns at once, then `process_logs` and `process_get`. `exec` waits for the program to finish.
- **Pause and resume keep running processes**, and so does a rollback, as of the snapshot. Check with `process_get` before restarting something.
- **Snapshot before anything risky** with `create_snapshot`, wait until it has finished, and `rollback_sandbox` if it goes wrong. A rollback discards everything since the snapshot.

## Ask Before

- Creating a sandbox. It holds quota for as long as it exists.
- `delete_sandbox`. It is permanent, and files and processes are gone.
- `rollback_sandbox`. Work since the snapshot cannot be recovered.
- `expose_port`. It puts a server on a public preview URL.
- Raising the idle or lifetime limits with `update_sandbox_timeout`.

A sandbox is only removed by `delete_sandbox`, or by a lifetime limit set to delete it. Pausing stops compute billing but keeps the quota.
