---
name: nemovideo
description: >-
  Create, edit, preview, inspect, and export editable videos with the NemoVideo
  MCP tools, either by delegating the whole job to NemoVideo's own video agent
  or by authoring the draft directly. Use when a user wants to make or change a
  video, import or generate media, save a Draft Protocol V3 timeline, watch or
  inspect the result, export a finished file, or check NemoVideo credits.
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

## Choosing between delegation and authoring

**If `delegate_to_nemo_agent` is not in your tool list, this account has not
granted delegation.** Skip to the standard workflow below and author the draft
yourself; the rest of this guide works without it.

Prefer `delegate_to_nemo_agent` when the user describes a video rather than a
specific markup change. It hands the task to NemoVideo's own agent, which plans
the video, authors and saves the draft, places or generates the media, and
checks its own result. That agent knows Draft Protocol V3, the asset pipeline,
and the generation models directly.

Author the draft yourself for a change you can already express exactly — recolor
a title, trim a clip, swap one asset. Both act on the same project, so they
combine freely in either order.

## Delegation workflow

1. Call `create_video_project`; the agent needs a project and session.
2. Call `upload_asset` for each piece of user media first, and keep the `file_id`
   and `mime_type` it returns for each one.
3. Call `delegate_to_nemo_agent` with `session_id` and a `message` describing
   the video. It returns a turn carrying its `turn_id`. Pass every piece of
   reference media as `attachments`, quoting back that `file_id` and
   `mime_type`, and say in the request what each one is for ("open on the first
   photo", "keep this character", "extend this clip"). The agent decides from
   the text which is a first frame, a style reference or a source video, so an
   attachment nothing in the text accounts for is one it has no instruction for.
   An exact opening or closing frame cannot be combined with reference material
   of any kind — not a reference image, not a source video, not a reference
   audio. Ask for one or the other in a single video; asking for both fails the
   generation outright.
4. Attachments are what let the delegated agent see a file. They are not how a
   draft references media: if you write the draft yourself with `save_v3_draft`
   instead of delegating, use the `asset_url` from the same upload.
5. Branch on `turn_state`, not on `ok` and not on prose. `running` is the normal
   first answer, because the wait budget is seconds and a turn takes minutes:
   the turn was accepted and nothing exists yet. Poll `get_nemo_agent_turn` with
   that `session_id` and `turn_id` at a human pace, relay the `text` events and
   the tools it has run, and describe no result while it runs.
6. `awaiting_input` means the agent stopped to ask something. The question is in
   the arguments of the last `ask_question` tool call. Relay it, then answer with
   another `delegate_to_nemo_agent` in the same session. **Nothing was
   finished**: do not claim a video or offer to export one. This case ends
   through the runtime's ordinary success path, which is why it is reported as
   its own state rather than left for you to spot.
7. `stopped` means every part of the turn reached a terminal status. That is not
   the same as delivered, so read `runtime_statuses` and `events` before saying
   anything to the user.

   - A `user_abort` status means the turn was cancelled. That is the
     cancellation landing, not a fault.
   - An `error` event, or a status naming a failure, means the agent did not
     deliver. Report it and do not claim a saved draft.
   - Otherwise the draft is saved. Confirm it with `get_video_project` and check
     `has_draft` before describing a video.

The status vocabulary belongs to the runtime and can grow, so `stopped` is
deliberately not "succeeded": treat a status you do not recognise as "read the
events" rather than as either outcome.

`ok` means the outcome a tool names has been achieved, not that the call reached
the server. A running turn and a turn waiting on a question both report it as
`false` with no error, and a turn keeps running after the call returns — that is
progress, not failure. Use `cancel_nemo_agent_turn` when the user abandons the
request; a generation already paid for still completes and is still charged, so
read the turn afterwards rather than assuming it stopped cleanly. If a delegate
call reports that the session already has a turn running, nothing was accepted
and there is no turn to poll.

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
