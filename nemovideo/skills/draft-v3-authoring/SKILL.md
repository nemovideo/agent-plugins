---
name: draft-v3-authoring
description: >-
  Author, inspect, or modify NemoVideo Draft Protocol V3 templates through the
  NemoVideo MCP server. Use for timeline edits, clips, tracks, subtitles,
  transitions, editable data/render components, or targeted repair of a save
  validation error.
---

# Draft V3 authoring through NemoVideo MCP

Use this skill for the structure and editing craft of a Draft V3 template. Use
`$nemovideo` for project creation, media generation, rendering, credits, and the
overall completion report. If `$nemovideo` is not installed, limit the workflow
to editing an existing project whose `project_id` is supplied; do not invent
the missing creation, generation, render, export, or credit tools. Ask the user
to install the companion NemoVideo Skill for those operations.

## Exact MCP boundary

Use only these exact calls for this editing loop:

- `get_video_project({ project_id })`
- `save_v3_draft({ project_id, session_id, main_template, base_version })`
- `get_project_frame({ project_id, frame })`
- `preview_video({ project_id })`

Never call or invent `get_project`, `apply_project_xml`,
`render_project_preview`, or another generic editor API. `main_template` is the
complete Draft V3 document. There is no `<add>` wrapper or incremental patch
format: changing an existing project means preserving its complete template,
editing that document, and saving the complete result.

## Editing loop

1. Before changing an existing project, call `get_video_project`. Retain its
   current complete template and version.
2. Read `references/draft-v3-mcp-authoring.md` for the requested element or
   timeline operation. Preserve unrelated tracks, clips, IDs, expressions,
   plugins, styles, data carriers, and user-authored content.
3. Construct the complete replacement template and call `save_v3_draft` with
   the last observed `base_version`. A save is a write, not a patch.
4. After a successful save, call `get_project_frame` with frame indexes for
   representative moments that can expose timing, placement, transition, or
   layering mistakes. Convert milliseconds with
   `frame = floor(milliseconds / 1000 * fps)`.
5. If the frames are sound, call `preview_video` so the user can watch the
   editable result. Render a downloadable file only when separately requested.

For a new project, begin at step 2. Derive canvas and duration from user intent,
the chosen output format, and verified media metadata; use media URLs returned
by the media tools exactly.

## Hard gates

- Time is milliseconds. Root attributes are `fps`, `width`, `height`, and
  `duration`; direct children are typed tracks.
- IDs are stable and unique. Clips on the same track must not overlap. Put
  simultaneous layers on separate tracks, in paint order.
- Use returned media URLs exactly, including `asset://` URLs. Never invent a
  CDN URL or reuse a local path.
- A partial edit preserves unrelated content. `save_v3_draft` receives the
  complete template, so omission is deletion.
- For editable graphics, keep user-editable values in `<data type="json">`
  and project them from `<render>`. Do not flatten an existing editable
  component into baked media or hard-coded values.
- A transition belongs at a requested cut between adjacent clips; do not add
  decorative transitions without user intent.

## Validation and repair

If `save_v3_draft` reports validation errors, do a targeted repair of the named
element, attribute, timing range, or reference. Preserve the rest of the
template and retry with the correct current version. If a version conflict is
reported, reload with `get_video_project`, reapply the intended change to that
new complete template, and save against its version.

Do not claim an edit succeeded until the save result proves it. Do not claim
visual correctness until representative frames or the preview have been
checked.
