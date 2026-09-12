---
name: neev-cli
description: Manage NeevCloud sandboxes from the command line with neev-cli — install and sign in, pick an organization and project, create and pause sandboxes, and run files, commands, and processes inside them. Use when setting up NeevCloud, troubleshooting authorization errors, or driving sandboxes from a shell or CI.
metadata:
  author: neevcloud
  version: "1.0.0"
---

# neev-cli

`neev-cli` is the command-line interface for NeevCloud. Use it to sign in, choose the organization and project you are working in, and manage sandboxes end to end.

## Install

macOS and Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/NeevCloudAI/neev-cli/main/install.sh | sh
```

The script detects the OS and architecture, verifies the release checksum, and installs to `/usr/local/bin`, or `~/.local/bin` if that is not writable. Pin a version with `NEEV_CLI_VERSION=v0.8.1`, or change the destination with `NEEV_CLI_INSTALL_DIR`.

On Windows there is no install script. Download `neev-cli_windows_amd64.zip` (or `arm64`) from https://github.com/NeevCloudAI/neev-cli/releases/latest, extract it, and add the folder to `PATH`. Do not invent a one-line installer.

Verify with `neev-cli version`.

## Two Credentials

This is the most common source of authorization errors. The two credentials are not interchangeable.

| Credential | Covers |
|---|---|
| API key (`sk-nc-…`) | Sandboxes — creating, pausing, resuming, deleting, and all work inside them |
| Personal Access Token (`pat-nc-…`) | The account — which organizations and projects exist, plus billing and AI runtime |

You need the PAT once, to establish which org and project you are in. After that an API key drives sandboxes.

If `neev-cli org list` fails but `neev-cli sandbox list` works, the PAT is missing. If it is the other way round, the API key is missing.

## Sign In

```bash
neev-cli auth login       # prompts for the pat-nc-… token; input is hidden on a TTY
neev-cli auth status      # exits non-zero when signed out
neev-cli auth logout
```

**Never put a token on the command line.** There is deliberately no `--token` flag, because a secret in `argv` leaks into shell history and `ps`. For CI, pipe it:

```bash
echo "$NEEV_API_TOKEN" | neev-cli auth login --token-stdin
```

Or skip login entirely and set `NEEV_API_TOKEN` for a single invocation.

**If you are an agent: do not run `auth login` on the user's behalf.** Stop and ask them to run it themselves, then continue once `auth status` succeeds.

## Choose an Organization and Project

Most commands need both. A context saves the pair so you can stop passing flags.

```bash
neev-cli context list                              # orgs and projects you can use, fetched live
neev-cli context set dev <org-id> <project-id>     # save and make current
neev-cli context current
neev-cli context use <name>
```

An explicit `--org-id` / `--project-id` always overrides the current context. Never guess these values — list them and ask.

## Sandbox Lifecycle

```bash
neev-cli sandbox create
neev-cli sandbox list
neev-cli sandbox get <id>
neev-cli sandbox pause <id>       # stops compute billing, preserves the disk
neev-cli sandbox resume <id>
neev-cli sandbox delete <id>
neev-cli sandbox metrics <id>

neev-cli sandbox template list
neev-cli sandbox template get <template-id>
```

Sandboxes provision asynchronously. A new sandbox is `Pending` before it is `Ready`; wait for `Ready` before running anything in it.

Address a sandbox by its id, not its name.

## Snapshots

```bash
neev-cli sandbox snapshot create --sandbox-id <id>
neev-cli sandbox snapshot list
neev-cli sandbox snapshot get <snapshot-id>
neev-cli sandbox snapshot delete <snapshot-id>
neev-cli sandbox restore --sandbox-id <id> --snapshot-id <snap>
neev-cli sandbox fork --sandbox-id <id>
```

## Work Inside a Sandbox

These need the API key:

```bash
export NEEV_API_KEY="sk-nc-..."
```

### Files

Paths are relative to the workspace. **Absolute paths are rejected with a 400** — the workspace is confined. Use `src/app.py`, never `/workspace/src/app.py`.

```bash
neev-cli sandbox fs write --sandbox-id <id> src/app.py --from-file ./app.py
neev-cli sandbox fs read  --sandbox-id <id> src/app.py
neev-cli sandbox fs list  --sandbox-id <id> src
```

### Commands

Use `exec` for anything that finishes on its own.

```bash
neev-cli sandbox exec --sandbox-id <id> -- python --version
neev-cli sandbox exec --sandbox-id <id> --stream -- npm install
neev-cli sandbox exec --sandbox-id <id> -it -- bash
```

Unlike the files API, commands accept absolute paths.

### Long-Running Processes

A dev server must not run through `exec` — it never returns. Start it detached instead.

```bash
neev-cli sandbox process start --sandbox-id <id> -- npm run dev
neev-cli sandbox process list  --sandbox-id <id>
neev-cli sandbox process logs  --sandbox-id <id> --process-id <pid> -f
neev-cli sandbox process get   --sandbox-id <id> --process-id <pid> --wait
neev-cli sandbox process kill  --sandbox-id <id> --process-id <pid>
neev-cli sandbox process kill-all --sandbox-id <id>
```

`logs` supports `-f` to follow, `--tail N`, and `-o json`. `get --wait` blocks until the process exits.

## What the CLI Cannot Do

**Exposing a port for a preview URL has no CLI command.** To reach a server running inside a sandbox from a browser, use the SDK — see the `neev-sdk` skill — or call the API directly.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `--api-key is required` on `exec`, `fs`, or `process` | Set `NEEV_API_KEY`. This is the sandbox key, not the PAT |
| `org list` or `context list` fails, sandboxes work | Not signed in. Run `neev-cli auth login` |
| Commands hang inside a sandbox, installs time out | Egress is deny-all by default. See the `neev-sdk` skill |
| A file write returns 400 | An absolute path. Use a path relative to the workspace |
| Commands fail right after create | The sandbox is still `Pending`. Wait for `Ready` |
