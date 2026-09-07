---
name: platform-reference-materials
description: >-
  Create, preview, attach, update, publish, roll back, or unpublish reusable
  NemoVideo Platform reference materials. Use when a user wants a reusable
  text, graphics, or effect preset, a shared visual treatment, or a versioned
  Platform material that can be placed in editable Draft Protocol V3 projects.
---

# Platform reference materials

Use this workflow for reusable V3 clip material on `text`, `graphics`, or
`effect` tracks. Plain uploaded or generated footage belongs in the media
library and is not a Platform reference material.

**If `create_platform_resources` is not in your tool list, this account has
not been granted Platform access.** The tools are registered only when the
token carries the Platform scopes, and those scopes are granted only to
accounts with a Platform creator role, so re-authorizing does not change the
outcome. Stop, tell the user which capability is missing, and do not work
around it.

Material comes first. Author it, create it, preview it, and only then place it
in a video. Do not build a video and then try to carve material out of its
saved draft: a Platform resource is authored on its own, not extracted from a
clip.

## Write material that stands on its own

Material plays inside a throwaway 1920x1080, 30 fps draft with nothing else on
the canvas, and later inside a clip on someone else's timeline. It has to
carry everything it needs:

- Size and place it in absolute pixels on a 1920x1080 canvas -- position,
  width, height, font-size, colour -- in inline `style`. A Platform body is
  clip child markup, so there is no track-level `<styles>` sheet and no CSS
  `@keyframes` to lean on. Unstyled text renders 16px at the top-left.
- Start on screen. Anything positioned off-canvas at the first frame shows
  nothing unless an animation brings it in.
- Animate with the engine clock, not CSS keyframes or framer-motion arrays.
  `<motion :animate="{ ... }">` is evaluated every frame with `t` (ms since
  the clip started), `frame`, `fps` and `progress` in scope, and the builtins
  `interpolate(t, [inMs, ...], [out, ...], { extrapolateRight: 'clamp' })`,
  `spring({ frame, fps, config })` and `kf(t, [[ms, value], ...])`. Keys x,
  y, scale, rotate, skew and blur fold into transform/filter; other keys pass
  through as CSS. `{ x: [0, -600] }` and a `:transition` attribute are not
  this engine and produce no motion at all.
- Engine content is welcome: `<render lang="jsx">` for vector glyph text,
  components, bound attributes. Declare `duration_ms` when the material has a
  pace; the preview plays exactly that long.

## Discover existing material

When the user asks what already exists, call `search_resources` without a
project ID to search PUBLIC resources and the caller's own reusable USER
resources; supply a project ID only for PROJECT resources. It returns ranked
metadata only: keep its exact resource ID, resource version ID, positive
version, and content digest unchanged. A search hit is not a body and does not
attach or publish anything. `preview_platform_resource` and
`attach_platform_resource` accept only Platform resources the caller may
manage; do not send an arbitrary search hit to either tool.

## Create independently and check

1. Author only the clip's child markup. Do not wrap it in `<draft>`, `<track>`,
   `<clip>`, or `<use>`. Anything a V3 clip can hold is material; the one
   exclusion is a fragment that is only a media reference (a bare `<video>`,
   `<img>` or audio element belongs in the media library).
2. Call `create_platform_resources` with an `items` array. Give every distinct
   item a recognizable title, description, usage guidance, tags, the correct
   `type_key`, the body from step 1, `duration_ms` when it has a pace, and a
   distinct `idempotency_key`. Reuse a key only to retry that same item.
   Inspect every returned `items[]` entry: proceed only for entries whose `ok`
   is true and whose `resource` is present, and report each sibling `error`
   separately; a top-level `ok: true` does not mean every batch item
   succeeded.
3. Watch it before going further. Call `preview_platform_resource` with the
   returned resource ID, resource version ID, and version. It plays the
   material on its own: no project is created and nothing is saved. Fix by
   appending a version (see Update) rather than by attaching something you
   have not looked at.

   Ask the user once, before the first preview of a session, which result
   they want, and keep the answer: `preview_mode: widget` returns an inline
   player; `preview_mode: page` returns a read-only workspace link that plays
   the same thing. The link names the resource only: it opens on the newest
   version the user may read and the page has a version switcher, so give it
   once and tell the user it keeps working after every appended version; do
   not paste a new link per iteration. Whether a player renders at all, and
   whether a dozen of them make the conversation unusable, are facts about the
   user's client that no tool result reports, so do not choose for them.
4. Stop after showing the preview. Do not create a project, attach, place, or
   publish in the same turn. Wait for a new user message that explicitly
   confirms this exact previewed version before continuing.

## Place in a video

Only after the user explicitly confirms the exact previewed version in a new
message, and the material belongs in an actual video:

1. Call `create_video_project` when the user needs a project for it.
2. Call `attach_platform_resource` with the complete `resource_id`,
   `resource_version_id`, `version`, and `content_digest` returned for that
   exact immutable version. Use a stable attachment idempotency key and reuse
   it only to retry that same attachment.
3. Use the returned `track_type` for the host track and copy the returned
   `use_node` exactly inside a timed `<clip>`, as that clip's direct and only
   content element. Do not rewrite, shorten, or hand-author the node.
4. Call `save_v3_draft` with the complete template and current base version,
   then call `preview_video` so the user can verify the placed material.

Creation commits immutable resource versions but does not publish, attach,
save, preview, render, or export anything by itself. If creation or attachment
fails, do not silently inline a second copy of the body and do not claim the
material is reusable or placed.

## Update an existing resource

Read the material back first. Call `get_platform_resource` with the resource
ID: it returns the newest version the account may read -- body, title, tags,
and the update coordinates (resource version ID, version,
`resource_revision`) -- which may be a version the creator edited on the
workspace page since this conversation last saw it. Base the update on what it
returns, never on a body remembered from earlier.

To append a version, call `create_platform_resources` again with the item's
`update` object. Pass the exact `resource_id`, `base_resource_version_id`,
`base_version`, and `expected_resource_revision` from that current state; the
item still includes all creation fields, including its new body. This update
revision is not the publication mutation field named `expected_revision`. Do
not create a second resource merely because the material changed. Existing
projects remain pinned to their earlier immutable versions until deliberately
attached and saved with the new version.

After creating a new version, repeat the attach, save, and preview sequence
with the new returned version triple and digest before describing the update
as verified in a project.

## Publish and publication changes

Publishing changes the deployment's public `CATALOG`; it is separate from
creating or previewing a resource.

- Before `publish_platform_resource`, confirm that the user wants this exact
  version published, use `list_resource_publications` to obtain the current
  revision, and require the asynchronous cover state to be `CONTENT_READY`.
- Pass the exact resource version and expected revision. A conflict or pending
  cover means nothing was published; refresh state instead of guessing.
- Before each publish, rollback, or unpublish mutation, call
  `list_resource_publications` again and pass that freshly observed
  `expected_revision`; do not reuse a revision from an earlier mutation.
- Use `rollback_platform_resource` only when the user explicitly requests the
  previous published version and a previous version exists.
- Use `unpublish_platform_resource` only when the user explicitly requests
  removal from the current deployment catalog. Unpublishing does not delete
  immutable resource versions.

Never describe create, attach, save, preview, or cover completion as a public
publication. Report the final resource version, project placement, preview, and
publication state as separate outcomes.
