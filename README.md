# NeevCloud Agent Skills

Official agent skills for NeevCloud. They teach a coding agent — Claude Code, Cursor, Codex, and others — how to drive NeevCloud sandboxes with the CLI and the SDKs, including the parts that are easy to get wrong.

## Install

```bash
npx -y skills add NeevCloudAI/agent-skills -g --all
```

Check what is installed:

```bash
npx -y skills list -g --json
```

Re-run the add command to update to the latest version.

### As a plugin

If your agent supports plugin marketplaces, you can install these skills without `npx`:

```
/plugin marketplace add NeevCloudAI/agent-skills
```

Manifests are provided for Claude Code, Codex, and Cursor, plus a generic one for agents that read `.agents/plugins`. Both install paths deliver the same two skills.

## Skills

| Skill | Use it for |
|---|---|
| `neev-cli` | Installing and signing in, choosing an organization and project, sandbox lifecycle, and running files, commands, and processes from a shell or CI |
| `neev-sdk` | Building against NeevCloud from TypeScript or Python — sandboxes, files, commands, processes, preview URLs, and network egress |

## Getting Started

If you are setting up NeevCloud for the first time, the [Set Up with Your Coding Agent](https://docs.ai.neevcloud.com) guide has a prompt you can paste into your agent that installs these skills, installs the CLI, and walks you through sign-in.

## What These Skills Emphasize

They exist because a few things about NeevCloud are not guessable, and an agent that guesses gets them wrong:

- **Two credentials.** An API key covers sandboxes; a Personal Access Token covers your account. They are not interchangeable.
- **Nothing is exposed by default.** A server inside a sandbox is unreachable until you explicitly expose its port, and it must bind `0.0.0.0` to be served.
- **No internet by default.** Outbound traffic is denied until you allow it, which is almost always why a package install hangs in a fresh sandbox.
- **Workspace paths are relative.** Absolute paths in file operations are rejected.
- **Secrets stay out of chat.** Sign-in is a human step; there is deliberately no flag that takes a token on the command line.

The skills also mark the actions an agent should ask about before taking — creating or deleting sandboxes, exposing a port to the internet, and widening a sandbox's egress policy.

## Documentation

Full documentation lives at https://docs.ai.neevcloud.com.

## Contributing

These skills are generated against the real CLI and SDK surface. If one has drifted from the product, open an issue.

## Contributing

Every command and method in these skills is taken from the shipped CLI and SDKs rather than written from memory, and CI checks that the skills parse and that the registry CLI can discover them. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to make a change or cut a release.

## License

Apache-2.0. See [LICENSE](LICENSE).
