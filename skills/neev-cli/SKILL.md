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

Follow the method documented for the user's operating system at
https://docs.ai.neevcloud.com/getting-started/neev-cli.md

macOS and Linux have a one-line installer there. **Windows has no install script** — hand
the user the manual download-and-PATH steps from that page rather than inventing a
command. Do not guess at a package manager: Homebrew is not currently available.

Verify with:

```bash
neev-cli version
```

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

### Signing In Is Optional

`NEEV_API_TOKEN` takes precedence over any stored session and authenticates a command on its own, with no session and nothing written to disk. **Check the environment before asking the user for anything.**

```bash
export NEEV_API_TOKEN="pat-nc-..."
neev-cli sandbox list --org-id <org-id> --project-id <project-id>
```

Without a session there is no current context, so pass `--org-id` and `--project-id` explicitly on every command. This is the path for CI, containers, and anywhere without an interactive terminal — including a sandbox, where there is no TTY for the hidden prompt.

**If you are an agent:** use `NEEV_API_TOKEN` when it is already set. Only when no credential is present should you stop and ask the user to either export it or run `auth login` themselves. Never run `auth login` on their behalf, and never build a command that carries the token.

## Choose an Organization and Project

Most commands need both. A context saves the pair so you can stop passing flags.

```bash
neev-cli context list                              # orgs and projects you can use, fetched live
neev-cli context set dev <org-id> <project-id>     # save and make current
neev-cli context current
neev-cli context use <name>
```

Contexts need a stored session. On the `NEEV_API_TOKEN` path there is no context to save, so discover the values with `neev-cli org list` and `neev-cli project list` and pass them as flags instead.

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

Paths are passed with `--path`, never as a positional argument.

```bash
neev-cli sandbox fs write --sandbox-id <id> --path src/app.py --in ./app.py
neev-cli sandbox fs read  --sandbox-id <id> --path src/app.py            # to stdout
neev-cli sandbox fs read  --sandbox-id <id> --path src/app.py --out ./app.py
neev-cli sandbox fs list  --sandbox-id <id> --path src --recursive
```

`--in -` reads the file content from stdin. `--cwd` sets a base directory relative to the workspace root.

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

`start` returns the id under the key `process_id`, not `id`:

```json
{ "process_id": "proc_a814e6151be66db8a963fdaa68bc3ebc", "started_at": 1789200702035, "state": "running" }
```

`start` also takes `--cwd`, repeatable `--env KEY=VALUE`, and `--stdin`. `kill` takes `--signal` (SIGTERM by default; `--signal 9` for SIGKILL).

`logs` supports `-f` to follow, `--tail N`, and `-o json`. `get --wait` blocks until the process exits.

## What the CLI Cannot Do

**Exposing a port for a preview URL has no CLI command.** To reach a server running inside a sandbox from a browser, use the SDK — see the `neev-sdk` skill — or call the API directly.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `--api-key is required` on `exec`, `fs`, or `process` | Set `NEEV_API_KEY`. This is the sandbox key, not the PAT |
| `org list` or `context list` returns `401 {"code":"unauthorized","message":"missing authorization header"}` while sandboxes work | No PAT. The API key is not sent to the tenant service at all, so the error says "missing" even though a credential is set. Set `NEEV_API_TOKEN` or run `neev-cli auth login` |
| No TTY for the login prompt (CI, container, sandbox) | Do not use `auth login`. Set `NEEV_API_TOKEN` and pass `--org-id` / `--project-id` |
| Commands hang inside a sandbox, installs time out | Egress is deny-all by default. See the `neev-sdk` skill |
| `invalid_argument: path must be relative, got absolute: "..."` | An absolute path in a file operation. Use a path relative to the workspace |
| Commands fail right after create | The sandbox is still `Pending`. Wait for `Ready` |
