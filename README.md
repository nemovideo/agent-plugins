# NemoVideo agent plugins

Distribution packages that connect [NemoVideo](https://www.nemovideo.com) to
Model Context Protocol hosts. Each plugin bundles the skills an agent needs with
the declaration of the remote MCP server that does the work.

The MCP server itself is a hosted service; this repository carries only the
manifests, skills and brand assets used to install and drive it.

## Plugins

| Plugin | Description |
|-|-|
| [`nemovideo`](./nemovideo) | Create, edit, preview and export videos. One skill plus twelve MCP tools. |

## Repository layout

This is a Cursor multi-plugin repository. `.cursor-plugin/marketplace.json` at
the root lists every plugin; each plugin lives in its own directory with its own
manifest, so plugins version and ship independently.

```text
.cursor-plugin/marketplace.json   # lists all plugins
nemovideo/                        # one plugin
├── .cursor-plugin/plugin.json
├── mcp.json
├── skills/
├── assets/
└── README.md
scripts/validate.py               # submission checklist self-check
```

## Validating a change

`scripts/validate.py` checks every plugin in the repository against the Cursor
plugin submission checklist: manifest validity, name format, logo path, skill
frontmatter, variable declarations, and the absence of symlinks or credential
literals.

```bash
python3 scripts/validate.py
```

It exits non-zero on any failure, so it can gate a commit or a CI job.

## License

See [LICENSE](./LICENSE).
