---
name: nemovideo
description: >-
  Create, edit, preview, inspect, and export editable videos with the NemoVideo
  MCP tools. Use when a user wants to make or change a video, import or generate
  media, save a Draft Protocol V3 timeline, watch or inspect the result, export
  a finished file, or check NemoVideo credits.
---

# NemoVideo MCP workflow

Use this skill for ordinary NemoVideo project work. For reusable text,
graphics, effect presets, or other Platform reference material, use
`platform-reference-materials` instead.

When authoring or modifying a Draft Protocol V3 template beyond the invariants
below, invoke `$draft-v3-authoring`. Extract the exact element structure,
timeline rule, and edit/repair procedure needed for the requested change, then
return to this workflow for saving, inspection, preview, or export. If that
Skill is not available, use only the invariants below and do not invent detailed
element syntax; ask the user to install the companion Skill for advanced edits.

## Standard workflow

1. Call `create_video_project` and retain its `project_id`, `session_id`, and
   `version`.
2. Import user media with `upload_asset`, or create new media with
   `generate_video` or `generate_audio` only when requested. Use every returned
   media URL exactly; never construct one from a filename.
3. Author the complete Draft Protocol V3 template and call `save_v3_draft`
   with the last observed version as `base_version`.
4. Call `preview_video` when the user should watch the saved draft. Use
   `get_project_frame` only to inspect a particular visual result yourself.
5. Call `render_video`, then poll `get_render_status`, only when the user asks
   for a downloadable video file.

Before a partial edit, call `get_video_project` and preserve unrelated tracks,
clips, expressions, plugins, and user-authored content. `save_v3_draft`
replaces the complete template.

## Draft V3 invariants

- The root is `<draft fps width height duration>` and its direct children are
  typed `<track id type>` elements containing uniquely identified
  `<clip id in out>` elements.
- Time values are milliseconds. Clips on the same track must not overlap; use
  separate tracks for simultaneous layers.
- Put media attributes on the media child inside a clip, not on `<clip>`.
- Use only media URLs returned by NemoVideo tools. Do not copy Cicada-local
  paths, invent CDN URLs, or translate a returned URL into another scheme.
- Preserve advanced V3 constructs already present. Do not simplify a draft by
  deleting bindings, data carriers, render bodies, motion, animation, Lottie,
  or Three.js elements merely because the edit is small.

## Billed actions and retries

`generate_video` and `generate_audio` spend credits. Use one caller-stable
`idempotency_key` for one logical generation and reuse that same key only when
retrying the same request. A new key represents a new billed operation.

Video and music generation may be asynchronous. Poll
`get_generation_status` with the returned generation identifier and type until
it succeeds or reaches a terminal failure. Do not report generated media as
placed in the project until a saved draft references it.

Use `get_credits` only for balance or quota questions. Do not interpret a
successful generation request as proof that an export or timeline edit exists.

## Failure handling

- Missing OAuth scope: tell the user to reconnect and approve the required
  permission; do not retry unchanged.
- Insufficient credits or plan restriction: report the returned limitation and
  let the user decide whether to top up or upgrade.
- Validation failure: correct the template or input before retrying.
- Version conflict: reload the project, preserve the user's intended change,
  and save against the new version.
- Unavailable Gateway: report that the operation did not complete; never claim
  a project, generation, save, render, or publication succeeded from a request
  attempt alone.

## Completion check

State separately what was generated, what was saved to the editable draft,
what was previewed, and what was exported. Claim only outcomes proven by the
corresponding tool result.
