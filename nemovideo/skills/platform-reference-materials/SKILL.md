---
name: platform-reference-materials
description: >-
  Create, attach, preview, publish, roll back, or unpublish reusable NemoVideo
  Platform reference materials. Use when a user wants a reusable text,
  graphics, or effect preset, a shared visual treatment, or a versioned
  Platform material that can be placed in editable Draft Protocol V3 projects.
---

# Platform reference materials

Use this workflow for reusable V3 clip material on `text`, `graphics`, or
`effect` tracks. Plain uploaded or generated footage belongs in the media
library and is not a Platform reference material.

## Create and place material

1. Author only the clip's child markup. Do not wrap it in `<draft>`, `<track>`,
   `<clip>`, or `<use>`.
2. Call `create_platform_resources`. Give every distinct item a recognizable
   title, description, usage guidance, tags, the correct `track_type`, and a
   distinct `idempotency_key`. Reuse a key only to retry that same item.
   Inspect every returned `items[]` entry: proceed only for entries whose
   `ok` is true and whose `resource` is present. Report each sibling `error`
   separately; a top-level `ok: true` does not mean that every batch item
   succeeded.
3. Call `create_video_project` when the user also wants an example or working
   project for the material.
4. Call `attach_platform_resource` with the complete `resource_id`,
   `resource_version_id`, `version`, and `content_digest` returned for that
   exact immutable version. Use a stable attachment idempotency key.
5. Use the returned `track_type` for the host track and copy the returned
   `use_node` exactly inside a timed `<clip>`. Do not rewrite, shorten, or
   hand-author the node.
6. Call `save_v3_draft` with the complete template and current base version,
   then call `preview_video` so the user can verify the placed material.

Creation commits immutable resource versions but does not publish, attach,
save, preview, render, or export anything by itself. If creation or attachment
fails, do not silently inline a second copy of the body and do not claim the
material is reusable or placed.

## Update an existing resource

To append a version, use `create_platform_resources` with its `update` object.
Pass the exact `resource_id`, `base_resource_version_id`, `base_version`, and
`expected_resource_revision` from the current resource state. This update
revision is not the publication mutation field named `expected_revision`. Do
not create a second resource merely because the material changed. Existing
projects remain pinned to their earlier immutable versions until deliberately
updated.

After creating a new version, repeat the attach, save, and preview sequence with
the new returned version triple and digest before describing the update as
verified in a project.

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
