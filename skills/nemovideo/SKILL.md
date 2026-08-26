---
name: nemovideo
description: Create, edit, preview and export videos with the NemoVideo MCP server. Use when the user wants to make or change a video, generate video/music/sound-effect/speech clips, import media into a video project, watch or inspect a draft, export a finished video file, or check their NemoVideo credit balance.
---

# NemoVideo

NemoVideo turns a prompt into an **editable** video project. The draft is Draft
Protocol V3 markup that you write and rewrite, not an opaque blob, so an edit is
a markup change rather than a full regeneration.

The `nemovideo` MCP server is remote and account-bound. The first tool call
triggers an OAuth sign-in; every tool then acts on the connected account only.

## Standard workflow

1. `create_video_project` — returns `project_id`, `session_id`, `version: 0`.
   Do this before anything that writes a draft. Keep all three; later tools
   reject a `session_id` from a different project.
2. `upload_asset` — once per piece of media the draft references. Returns
   `asset_url`; use that exact string in the draft.
3. `generate_video` / `generate_audio` — only when the user needs new footage,
   music, a sound effect, or narration. These are billed. Skip them for drafts
   built from uploaded media, text, and shapes.
4. `save_v3_draft` — validates and persists the whole `main_template`. Pass the
   `version` you last saw as `base_version`.
5. `preview_video` — the user watches the saved draft. Use
   `get_project_frame` instead when *you* need to check the layout.
6. `render_video` then `get_render_status` — only when the user wants a
   downloadable file. Requires a Starter plan or above.

## Draft Protocol V3 essentials

One `<draft fps width height duration>` root; `duration`, `in` and `out` are
milliseconds. It holds `<track id>` elements, each holding `<clip id in out>`
elements whose content is ordinary HTML. Clip ids are unique across all tracks,
and clips within a track should not overlap.

```xml
<draft fps="30" width="1280" height="720" duration="5000">
  <track id="text">
    <clip id="hello" in="0" out="5000"><div>Hello world</div></clip>
  </track>
</draft>
```

Media is referenced only by the `asset://` URL that `upload_asset` returned, for
example `<img src="asset://image/my-photo" />`. Do not build an `asset://` URL
by hand: the stored filename can differ from the uploaded one.

Beyond static markup the protocol supports `:prop="expr"` bindings, `*if` and
`*for`, `{expr}` interpolation, `<data>` and `<styles>` carriers, `<script>` and
`<render lang="jsx">`, and the `<lottie>`, `<motion>`, `<anime>`, `<gsap>` and
`<three>` plugins. When editing an existing draft, preserve the constructs
already in it — deleting expressions and plugins to write plain markup silently
degrades the project. A `<script>` body may not loop unboundedly and may not
mention `fetch`, `document`, `window`, `process`, `require`, `eval` or
`Function`; prefer an expression wherever one would do.

`save_v3_draft` replaces the entire template, so read the current one with
`get_video_project` before a partial edit.

## Preview, frame, and render are three different things

| Need | Tool | Costs credits | Produces a file |
|-|-|-|-|
| User watches the draft | `preview_video` | No | No |
| You verify your own layout | `get_project_frame` | No | No |
| User wants a video file | `render_video` | Plan required | Yes |

`get_project_frame` takes a **frame index**, not milliseconds: multiply seconds
by the draft's `fps`. Never describe a video or send a single frame in place of
calling `preview_video` when the user asked to watch it. Both read what
`save_v3_draft` last stored, so save first.

## Billing and idempotency

`generate_video` and `generate_audio` consume credits and require a
caller-stable `idempotency_key`. **Reuse the same key when retrying the same
user request** — a new key on a retry charges the account twice. Use
`get_credits` when the user asks about credits, balance, or remaining quota.

`generate_video` and `generate_audio` with `kind=music` return immediately;
poll `get_generation_status` with the matching `generation_type` until the
status is terminal — `succeeded`, or any of `failed`, `canceled`, `cancelled`
and `timed_out`. `kind=sound_effect` and `kind=speech` complete in the initial
call and have no status to poll.

One `generate_video` call produces at most 15 seconds. Cover a longer sequence
with several clips rather than one long request.

## Handling failures

- `insufficient_scope` — the account did not grant that permission at sign-in.
  Tell the user to reconnect and approve it; do not retry.
- Insufficient credits (402) or plan required (403) — a deterministic refusal.
  Relay the message and tell the user to top up or upgrade at
  https://www.nemovideo.com/pricing ; retrying cannot succeed.
- A request the model cannot satisfy (422), such as a clip longer than the
  15-second limit — relay the constraint and offer a request that fits, for
  example several shorter clips. Retrying the same arguments cannot succeed.
- Version conflict on save — re-read with `get_video_project` and resave using
  the returned `version`, keeping the user's intent.
- A draft rejected by validation — fix the markup against the rules above.
  Do not resubmit the same template unchanged.

## Tools

| Tool | Purpose |
|-|-|
| `get_credits` | Credit balance: available, frozen, total granted, total consumed |
| `create_video_project` | New project plus its first editing session |
| `get_video_project` | Current draft, resolver context, and `version` |
| `save_v3_draft` | Validate and persist the full draft with optimistic locking |
| `preview_video` | Play the saved draft for the user |
| `get_project_frame` | One rendered frame as an image, for self-checking |
| `upload_asset` | Import a file into the project and get its `asset://` URL |
| `generate_video` | Billed text-to-video generation |
| `generate_audio` | Billed music, sound effect, or speech generation |
| `get_generation_status` | Progress and result of a video or music generation |
| `render_video` | Start an export to a video file |
| `get_render_status` | Export progress and the download URL |
