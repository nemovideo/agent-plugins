# NemoVideo for Cursor

Turn a prompt into an **editable** video draft, preview it inside the
conversation, and export the finished file — without leaving Cursor.

NemoVideo drafts are Draft Protocol V3 markup rather than an opaque render, so
"change the title colour" is a markup edit, not a full regeneration.

## What this plugin contains

| Component | What it does |
|-|-|
| `skills/nemovideo` | Teaches the agent the correct authoring order, the Draft Protocol V3 rules, and how to handle billing, retries and version conflicts |
| `mcp.json` | Declares the NemoVideo remote MCP server (Streamable HTTP) |

There is no bundled runtime: no local command, no npm or pip dependency, no
background process. The plugin is a manifest plus documentation, so it works on
every platform Cursor runs on.

## Install

**From the Cursor marketplace** — open **Customize** in the sidebar, find
NemoVideo, and click install.

**With an install link** — [Add to Cursor](https://cursor.com/install-mcp?name=nemovideo&config=eyJ1cmwiOiJodHRwczovL2Rldi5uZW1vdmlkZW8uYWkvbWNwIn0%3D)

**Manually** — add this to `~/.cursor/mcp.json` for every project, or
`.cursor/mcp.json` for one project:

```json
{
  "mcpServers": {
    "nemovideo": {
      "url": "https://dev.nemovideo.ai/mcp"
    }
  }
}
```

The manual route gives you the tools but not the skill. Install the plugin to
get both.

## Signing in

The server is remote and account-bound. The first tool call opens a browser
sign-in; every tool afterwards acts only on the connected account.

Authentication is standard OAuth 2.1 with PKCE and dynamic client registration,
so there is nothing to paste and no API key to manage:

- Protected resource metadata (RFC 9728) — `/.well-known/oauth-protected-resource/mcp`
- Authorization server metadata (RFC 8414) — `/.well-known/oauth-authorization-server`
- Dynamic client registration (RFC 7591) — `POST /oauth/register`
- Authorization code + PKCE (`S256` required)

Access tokens last one hour; refresh tokens last 30 days and rotate on every
use. Revoke access at any time from your NemoVideo account settings, or with
`POST /oauth/revoke`.

## Tools

| Tool | Purpose | Scope |
|-|-|-|
| `get_credits` | Credit balance: available, frozen, granted, consumed | `billing:read` |
| `create_video_project` | New project plus its first editing session | `workspace:write` |
| `get_video_project` | Current draft, resolver context, and `version` | `video:read` |
| `save_v3_draft` | Validate and persist the full draft, with optimistic locking | `workspace:write` |
| `preview_video` | Play the saved draft for the user | `video:read` |
| `get_project_frame` | One rendered frame as an image, for self-checking | `video:read` |
| `upload_asset` | Import a file into the project and get its `asset://` URL | `asset:write` |
| `generate_video` | Billed text-to-video generation | `video:generate` |
| `generate_audio` | Billed music, sound effect, or speech generation | `audio:generate` |
| `get_generation_status` | Progress and result of a generation | `video:read` / `audio:read` |
| `render_video` | Start an export to a video file | `render:write` |
| `get_render_status` | Export progress and the download URL | `render:read` |

`preview_video` returns an interactive player through the
[MCP Apps extension](https://modelcontextprotocol.io/extensions/apps/overview),
which Cursor renders inline. On a host that cannot render app UI the same tool
still returns a usable text result.

## Known limitations

- `upload_asset` needs a **server-reachable** `download_url`. A file that only
  exists on your machine has to be published somewhere first.
- `render_video` requires a Starter plan or above. `preview_video` and
  `get_project_frame` are free.
- `generate_video` and `generate_audio` consume credits. Insufficient credits
  (402) and plan-required (403) are deterministic refusals — retrying cannot
  succeed.
- One `generate_video` call produces at most 15 seconds. Cover longer sequences
  with several clips.

## Support

- Product and pricing — <https://www.nemovideo.com>
- Terms of Use — <https://www.nemovideo.com/nemovideo-terms-of-use>
- Privacy Policy — <https://www.nemovideo.com/nemovideo-privacy-policy>

## License

See [LICENSE](./LICENSE). The NemoVideo service reached through this plugin is
additionally governed by the Terms of Use and Privacy Policy linked above.
