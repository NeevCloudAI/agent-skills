---
name: neev-sdk
description: Build on NeevCloud sandboxes from TypeScript or Python with the official SDKs — create sandboxes, write and upload files, run commands and processes, expose a port to get a public preview URL, control outbound network access, snapshot and roll back, and read the audit trail. Use when writing application or agent code against NeevCloud rather than driving it from a shell.
metadata:
  author: neevcloud
  version: "1.0.0"
---

# neev-sdk

Official NeevCloud SDKs: `@neevcloud/sdk` for TypeScript and JavaScript, `neevai` for Python. This skill matches version 0.8.1 of both. They expose the same surface, in camelCase and snake_case respectively.

## Install

```bash
npm install @neevcloud/sdk
```

```bash
pip install neevai
```

Do not install `@neevcloud/sdk@beta`: that tag points at an older pre-release.

The JS package needs a server-side runtime with global `fetch` — Node 18+, Bun, Deno, or an edge runtime. **There is no browser build**: an API key must never ship to a browser. The Python package needs Python 3.10+.

## Authentication

Three environment variables, and no PAT — you supply the organization and project directly rather than discovering them.

| Variable | Required |
|---|---|
| `NEEV_API_KEY` | Yes. A project API key created with **Resource Type: Sandboxes** |
| `NEEV_ORG_ID` | Yes |
| `NEEV_PROJECT_ID` | Yes |

```typescript
import { Neev } from "@neevcloud/sdk";
const neev = new Neev();               // reads the environment
```

```python
from neevai import NeevAI
neev = NeevAI()                        # reads the environment
```

Never hard-code the key or print it. Read it from the environment.

## Create a Sandbox

Provisioning is asynchronous. Always wait for `Ready`; `waitUntilReady()` also waits until the sandbox can be reached.

```typescript
const sandbox = await neev.sandboxes.create({});
await sandbox.waitUntilReady();
```

```python
sandbox = neev.sandboxes.create({})
sandbox.wait_until_ready()
```

Omit the template to get the platform default, or pass `sandbox_template_id`. List what is available with `neev.templates`.

Fetch an existing one with `neev.sandboxes.get("<id or name>")`: a sandbox can be addressed by its id or its name wherever an id is accepted.

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

`files.write` switches to a resumable chunked upload above 1 MiB, so large writes work. To move a local file without holding it in memory, use `files.uploadFile(localPath, remotePath)` / `files.downloadFile(remotePath, localPath)` (Node only in JS), or `files.upload_file` / `files.download_file` in Python. A failed download leaves no partial file.

## Run a Command

For anything that finishes on its own.

```typescript
const result = await sandbox.exec(["ls", "-la"]);
console.log(result.exitCode, result.stdout);
```

```python
result = sandbox.exec(["ls", "-la"])
print(result.exit_code, result.stdout)
```

To see output as it arrives, stream it. **A stream does nothing until you iterate it** — awaiting it or calling it without a loop never runs the command.

```typescript
for await (const event of sandbox.exec(["npm", "install"], { stream: true })) {
  if (event.type === "stdout" || event.type === "stderr") process.stdout.write(event.data);
  if (event.type === "exit") console.log("exit", event.exitCode);
}
```

```python
for event in sandbox.exec_stream(["npm", "install"]):
    if event["type"] in ("stdout", "stderr"):
        print(event["data"], end="")
    elif event["type"] == "exit":
        print("exit", event["exit_code"])
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
const url = await sandbox.getUrl({ port: 3000 });   // exposes if needed, waits until it answers

await sandbox.listPorts();
await sandbox.revokePort(3000);
```

```python
port = sandbox.expose_port(3000)
print(port.preview_url)
url = sandbox.get_url(3000)                          # exposes if needed, waits until it answers

sandbox.list_ports()
sandbox.revoke_port(3000)
```

Rules that catch people out:

- **The server must listen on `0.0.0.0`, not `127.0.0.1`.** A loopback-bound server is unreachable even once the port is exposed.
- The URL has no authentication. Treat it as a secret and revoke the port when done.
- The URL contains a slug, and the slug is the only thing gating it. Omit `slug` and a random one is generated. To choose one, pass exactly 8 lowercase letters and digits: `exposePort(3000, { slug: "a1b2c3d4" })` / `expose_port(3000, slug="a1b2c3d4")`.
- Exposing an already-exposed port returns the same URL and changes nothing, unless you pass a different slug: that **rotates** the URL, and the old one stops working.
- While the sandbox is paused the URL does not serve. After a resume, the server that was running is running again.
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

```python
sandbox = neev.sandboxes.create({
    "egress": {
        "mode": "allow_list",
        "allow": [{"host": "registry.npmjs.org", "ports": [443], "protocol": "TCP"}],
    },
})
```

Change it on a running sandbox with `update`, which applies live with no restart. `egress` **replaces** the whole policy. `egress_add` and `egress_remove` edit the allow-list in place: they cannot be combined with `egress`, and `egress_add` is rejected while the mode is `deny_all`, so switch to `allow_list` with `egress` first.

```typescript
await sandbox.update({ egress_add: { allow: [{ host: "pypi.org", ports: [443] }] } });
```

```python
sandbox.update({"egress_add": {"allow": [{"host": "pypi.org", "ports": [443]}]}})
```

Host names match exactly: `api.github.com` does not also allow `github.com`, and wildcards are rejected. To open all outbound traffic, pass `allowInternet: true` to `create` or `update` (`allow_internet=True` in Python). Inside an `egress` object, `allow_internet` only applies in `allow_list` mode; `deny_all` ignores it. Prefer an allow list. Common hosts: `registry.npmjs.org` for npm, `pypi.org` and `files.pythonhosted.org` for pip, `proxy.golang.org` and `sum.golang.org` for Go, `github.com` and `codeload.github.com` to clone.

**Widening egress changes what code in the sandbox can reach. If you are an agent, ask before doing it.**

## Snapshots, Rollback and Fork

A snapshot captures memory and files together.

```typescript
const snap = await sandbox.snapshot({ name: "before-migration", waitUntilReady: true });
await sandbox.rollback(snap.id);          // same sandbox, back to the snapshot
const copy = await sandbox.fork("attempt-b");   // a second sandbox from the live state
```

```python
snap = sandbox.snapshot({"name": "before-migration"})
# wait until neev.sandboxes.get_snapshot(snap.id).status == "Ready" before rolling back
sandbox.rollback(snap.id)
copy = sandbox.fork("attempt-b")
```

A rollback brings back the files, memory and processes that were running when the snapshot was taken, and discards everything since. It cannot be undone. **If you are an agent, ask before rolling back.**

## Audit Trail

Read what ran inside a sandbox: program names (never arguments), process and file operations, the credential each was made under, and how it ended. Records come newest first, one page at a time.

```typescript
const trail = await sandbox.audit({ limit: 50 });
for (const r of trail.records) console.log(r.at, r.tool, r.command, r.outcome);
const older = trail.next_cursor ? await sandbox.audit({ cursor: trail.next_cursor }) : null;
```

```python
trail = sandbox.audit(limit=50)
for r in trail.records:
    print(r.at, r.tool, r.command, r.outcome)
older = sandbox.audit(cursor=trail.next_cursor) if trail.next_cursor else None
```

## A Typical Flow

```typescript
const sandbox = await neev.sandboxes.create({
  egress: { mode: "allow_list", allow: [{ host: "registry.npmjs.org" }] },
});
await sandbox.waitUntilReady();

await sandbox.files.write("package.json", packageJsonText);   // your file contents
await sandbox.files.write("server.js", serverSource);
const install = await sandbox.exec(["npm", "install"]);
if (install.exitCode !== 0) throw new Error(install.stderr);

await sandbox.processes.start("node", { args: ["server.js"] });
const url = await sandbox.getUrl({ port: 3000 });
console.log(url);
```

## Lifecycle and Cost

Compute is billed while a sandbox runs. Pause it to stop compute billing — memory, files and running processes are kept and come back on resume. Delete is permanent and unrecoverable.

```typescript
await sandbox.pause();
await sandbox.resume();
await sandbox.keepalive();                                  // reset the idle timer
await sandbox.updateTimeout({ idle_timeout_seconds: 1800 }); // change the idle window
await sandbox.delete();
```

```python
sandbox.pause()
sandbox.resume()
sandbox.keepalive()
sandbox.update_timeout({"idle_timeout_seconds": 1800})
sandbox.delete()
```

## Errors

A failed call raises an `APIError` subclass (`NotFoundError`, `PermissionDeniedError`, `RateLimitError`, …). Branch on `error.code`, the API's machine-readable code such as `not_found` or `sandbox_quota_exceeded`, never on the message text. `error.scope` names the limit a quota refusal hit.

**Creating, pausing, and deleting sandboxes are billable, stateful actions. If you are an agent, ask before creating or deleting.**
