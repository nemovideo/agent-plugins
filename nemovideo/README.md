# NemoVideo

Turn a prompt into an **editable** video draft, preview it inside the
conversation, and export the finished file — without leaving your editor.

NemoVideo drafts are Draft Protocol V3 markup rather than an opaque render, so
"change the title colour" is a markup edit, not a full regeneration.

> **Availability** — this plugin is published ahead of the public MCP endpoint.
> Until `https://www.nemovideo.com/mcp` is serving, installing it will connect
> but find no server.

## What this plugin contains

| Component | What it does |
|-|-|
| `skills/nemovideo` | The ordinary project workflow: create a project, import or generate media, save, preview, export, and read credits — and when to hand the whole job to NemoVideo's own agent instead |
| `skills/draft-v3-authoring` | Draft Protocol V3 itself — timelines, clips, tracks, subtitles, transitions, editable data and render components, and repairing a save that failed validation |
| `skills/platform-reference-materials` | Reusable reference materials: create, attach, preview, publish, roll back, unpublish |
| `mcp.json` / `.mcp.json` | Declares the NemoVideo remote MCP server (Streamable HTTP) — same content, one file name per host |

There is no bundled runtime: no local command, no npm or pip dependency, no
background process. The plugin is a manifest plus documentation, so it works on
every platform the host runs on.

The three skills are copies. They are authored and versioned in the
`nemo-skills` repository and imported by `scripts/sync-skills.py`, which records
the versions it took in `skills-source.json`. Edit them upstream and re-run the
script; a change made here would be overwritten on the next import.

## Install

### Cursor

**From the Cursor marketplace** — open **Customize** in the sidebar, find
NemoVideo, and click install.

**With an install link** — [Add to Cursor](https://cursor.com/install-mcp?name=nemovideo&config=eyJ1cmwiOiJodHRwczovL3d3dy5uZW1vdmlkZW8uY29tL21jcCJ9)

### Claude Code

Add this repository as a marketplace, then install the plugin from it:

```bash
claude plugin marketplace add nemovideo/agent-plugins
claude plugin install nemovideo@nemovideo-agent-plugins
```

Restart the session to load it. `claude plugin details nemovideo` should report
three skills and one MCP server.

### Manually, without the plugin

Add this to `~/.cursor/mcp.json` for every project, or `.cursor/mcp.json` for one
project (in Claude Code, `claude mcp add --transport http nemovideo https://www.nemovideo.com/mcp`):

```json
{
  "mcpServers": {
    "nemovideo": {
      "url": "https://www.nemovideo.com/mcp"
    }
  }
}
```

The manual route gives you the tools but not the skills. Install the plugin to
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
| `delegate_to_nemo_agent` | Hand the whole video task to NemoVideo's own agent | `agent:chat` |
| `get_nemo_agent_turn` | Read a delegated turn: its events, the tools it ran, whether it stopped | `agent:chat` |
| `cancel_nemo_agent_turn` | Cancel a delegated turn that is still running | `agent:chat` |

The three `agent:chat` tools appear only when the connected account granted that
scope, so most sessions will not see them and the skill falls back to authoring
the draft directly. When they are available, describing a video is usually
better than writing the markup yourself: NemoVideo's agent plans the video,
authors and saves the draft, places or generates the media, and checks its own
result. Author the draft yourself for an edit you can already express exactly.

To give that agent reference media — a reference image, an opening frame, a
source video to extend — upload it with `upload_asset` and pass the `file_id`
and `mime_type` it returns in the delegate call's `attachments`, then say in the
request what each one is for — the agent reads the roles off that text. The
`asset_url` from the same upload is for the other path: writing the draft
yourself with `save_v3_draft`.

`preview_video` returns an interactive player through the
[MCP Apps extension](https://modelcontextprotocol.io/extensions/apps/overview),
which Cursor renders inline. On a host that cannot render app UI — Claude Code
included — the same tool still returns a usable text result.

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

See [LICENSE](https://github.com/nemovideo/agent-plugins/blob/main/LICENSE). The
NemoVideo service reached through this plugin is additionally governed by the
Terms of Use and Privacy Policy linked above.
