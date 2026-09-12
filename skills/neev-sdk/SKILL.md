---
name: neev-sdk
description: Build on NeevCloud sandboxes from TypeScript or Python with the official SDKs — create sandboxes, write files, run commands and processes, expose a port to get a public preview URL, and control outbound network access. Use when writing application or agent code against NeevCloud rather than driving it from a shell.
metadata:
  author: neevcloud
  version: "1.0.0"
---

# neev-sdk

Official NeevCloud SDKs: `@neevcloud/sdk` for TypeScript and JavaScript, `neevai` for Python.

## Install

```bash
npm install @neevcloud/sdk@beta
```

```bash
pip install neevai
```

The JS package needs a server-side runtime with global `fetch` — Node 18+, Bun, Deno, or an edge runtime. **There is no browser build**: an API key must never ship to a browser.

## Authentication

Three environment variables, and no PAT — you supply the organization and project directly rather than discovering them.

| Variable | Required |
|---|---|
| `NEEV_API_KEY` | Yes |
| `NEEV_ORG_ID` | Yes |
| `NEEV_PROJECT_ID` | Yes |

```typescript
import { Neev } from "@neevcloud/sdk";
const neev = new Neev();               // reads the environment
```

```python
from neevai import NeevAI
neev = NeevAI()
```

Never hard-code the key or print it. Read it from the environment.

## Create a Sandbox

Provisioning is asynchronous. Always wait for `Ready`.

```typescript
const sandbox = await neev.sandboxes.create({});
await sandbox.waitUntilReady();
```

```python
sandbox = neev.sandboxes.create({})
sandbox.wait_until_ready()
```

Omit the template to get the platform default, or pass `sandbox_template_id`. List what is available with `neev.templates`.

Fetch an existing one with `neev.sandboxes.get("sandbox-id")`.

## Files

Paths are relative to the workspace. **Absolute paths are rejected** — the workspace is confined.

```typescript
await sandbox.files.write("greeting.txt", "hello\n");
const text = await sandbox.files.readText("src/main.py");
const entries = await sandbox.files.list("src", { recursive: false });
```

```python
sandbox.files.write("greeting.txt", "hello\n")
text = sandbox.files.read_text("src/main.py")
entries = sandbox.files.list("src", recursive=False)
```

## Run a Command

For anything that finishes on its own.

```typescript
const result = await sandbox.exec(["ls", "-la"]);
await sandbox.exec(["npm", "install"], { stream: true });
```

```python
result = sandbox.exec(["ls", "-la"])
sandbox.exec_stream(["ls", "-la"])
```

## Long-Running Processes

A server must not run through `exec` — it never returns. Start it detached and address it by its process id.

```typescript
const proc = await sandbox.processes.start("python", { args: ["server.py"], cwd: "app" });
await sandbox.processes.list();
await sandbox.processes.logs(proc.id, { cursor: 0 });
await sandbox.processes.get(proc.id, { wait: false });
await sandbox.processes.kill(proc.id);
await sandbox.processes.killAll();
```

```python
proc = sandbox.processes.start(["python", "server.py"], cwd="app")
sandbox.processes.list()
sandbox.processes.logs(proc.id)
sandbox.processes.get(proc.id, wait=False)
sandbox.processes.kill(proc.id)
sandbox.processes.kill_all()
```

## Preview URLs

Nothing inside a sandbox is reachable from outside until you expose it. Exposing a port returns a public, credential-free URL.

```typescript
const port = await sandbox.exposePort(3000);
console.log(port.preview_url);

await sandbox.listPorts();
await sandbox.revokePort(3000);
```

```python
port = sandbox.expose_port(3000)
print(port.preview_url)

sandbox.list_ports()
sandbox.revoke_port(3000)
```

Rules that catch people out:

- **The server must listen on `0.0.0.0`, not `127.0.0.1`.** A loopback-bound server is unreachable even once the port is exposed.
- The URL has no authentication. Treat it as public and revoke the port when done.
- Exposing an already-exposed port returns the same URL and changes nothing, so it is safe to call on every run.
- Pausing the sandbox stops the URL serving. The port stays exposed; the process behind it does not restart on its own.
- Ports must be between 1 and 65535, and some are reserved by the platform.

**Exposing a port publishes a service to the internet. If you are an agent, ask before doing it.**

## Internet Access

A sandbox cannot reach the internet unless you allow it. `deny_all` is the default. If a package install hangs or a `git clone` times out in a fresh sandbox, this is why — the sandbox is not broken.

Set the policy at creation:

```typescript
const sandbox = await neev.sandboxes.create({
  egress: {
    mode: "allow_list",
    allow: [{ host: "registry.npmjs.org", ports: [443], protocol: "TCP" }],
  },
});
```

Or change it on a running sandbox, which applies live with no restart:

```bash
curl -X PATCH "$BASE_URL/api/v1beta1/orgs/$NEEV_ORG_ID/projects/$NEEV_PROJECT_ID/sandboxes/$SANDBOX_ID" \
  -H "Authorization: Bearer $NEEV_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"egress": {"mode": "allow_list", "allow": [{"host": "api.github.com"}]}}'
```

An update **replaces** the policy rather than merging into it. Send the complete set of hosts.

`allow_internet: true` opens everything and is audit-logged. Prefer an allow list. Common hosts: `registry.npmjs.org` for npm, `pypi.org` and `files.pythonhosted.org` for pip, `proxy.golang.org` and `sum.golang.org` for Go, `github.com` and `codeload.github.com` to clone.

**Widening egress changes what code in the sandbox can reach. If you are an agent, ask before doing it.**

## A Typical Flow

```typescript
const sandbox = await neev.sandboxes.create({
  egress: { mode: "allow_list", allow: [{ host: "registry.npmjs.org" }] },
});
await sandbox.waitUntilReady();

await sandbox.files.write("package.json", pkg);
await sandbox.files.write("server.js", src);
await sandbox.exec(["npm", "install"], { stream: true });

const proc = await sandbox.processes.start("node", { args: ["server.js"] });
const port = await sandbox.exposePort(3000);
console.log(port.preview_url);
```

## Lifecycle and Cost

Billing runs while a sandbox is `Ready`. Pause it to stop compute billing while keeping the disk, and resume when needed. Delete is permanent and unrecoverable.

```typescript
await sandbox.pause();
await sandbox.resume();
await sandbox.delete();
```

**Creating, pausing, and deleting sandboxes are billable, stateful actions. If you are an agent, ask before creating or deleting.**
