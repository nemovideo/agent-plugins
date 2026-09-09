# NemoVideo agent plugins

Distribution packages that connect [NemoVideo](https://www.nemovideo.com) to
Model Context Protocol hosts. Each plugin bundles the skills an agent needs with
the declaration of the remote MCP server that does the work.

The MCP server itself is a hosted service; this repository carries only the
manifests, skills and brand assets used to install and drive it.

## Plugins

| Plugin | Description |
|-|-|
| [`nemovideo`](./nemovideo) | Create, edit, preview and export videos, and build reusable reference materials. Three skills plus twenty-six MCP tools. |

## Repository layout

This is a multi-plugin repository for two hosts. A marketplace manifest at the
root lists every plugin; each plugin lives in its own directory with its own
manifest, so plugins version and ship independently.

Cursor and Claude Code use the same layout under different names, so each plugin
carries a manifest pair per host. The two copies say the same thing —
`scripts/validate.py` fails the build if they drift.

```text
.cursor-plugin/marketplace.json   # lists all plugins (Cursor)
.claude-plugin/marketplace.json   # lists all plugins (Claude Code)
nemovideo/                        # one plugin
├── .cursor-plugin/plugin.json    # manifest (Cursor)
├── .claude-plugin/plugin.json    # manifest (Claude Code)
├── mcp.json                      # MCP server declaration (Cursor)
├── .mcp.json                     # MCP server declaration (Claude Code)
├── skills/                       # read by both hosts
├── assets/
└── README.md
scripts/validate.py               # submission checklist self-check
```

The only permitted difference between the two marketplace manifests is the
plugin `source`, which Claude Code requires to be a `./`-prefixed path.

## Validating a change

`scripts/validate.py` checks every plugin in the repository against the Cursor
plugin submission checklist: manifest validity, name format, logo path, skill
frontmatter, variable declarations, and the absence of symlinks or credential
literals. It then checks that the Claude Code manifests still mirror the Cursor
ones, so a version bump or a server URL change applied to one host but not the
other fails here rather than silently shipping a stale plugin.

```bash
python3 scripts/validate.py
```

It exits non-zero on any failure, so it can gate a commit or a CI job.

## License

See [LICENSE](./LICENSE).
