# Draft V3 MCP authoring reference

Read only the sections needed for the requested edit. The saved value is one
complete XML-like Draft V3 template.

## Document and timeline

The root is `<draft fps="30" width="1920" height="1080" duration="6000">`.
Its direct children are `<track id="..." type="...">` elements. Supported
track roles include video, image, text, graphics, effect, audio, voice, bgm,
and sfx. Every track and clip needs a stable unique ID.

Each `<clip id="..." in="0" out="3000">` uses composition time in
milliseconds. Clips on the same track must not overlap. Sequential clips may
abut (`first.out === second.in`); simultaneous background, title, sticker, or
effect layers belong on separate tracks. Later tracks paint above earlier ones.

For media, place the media element inside the clip. Use the exact URL returned
by NemoVideo, including an `asset://...` URL from `upload_asset`. Source ranges
belong on the clip as `source-start` and `source-end` when trimming is needed.

## Targeted edits

Treat IDs as anchors. Find the smallest affected track or clip, change only the
requested attributes or children, and then submit the entire preserved
template. When changing duration, reconcile the root duration and every
affected clip boundary; do not silently truncate unrelated later content.

Before removing a track or clip, distinguish an explicit deletion request from
a replacement or restyle request. A restyle should retain timing, identity, and
unrelated children whenever the format allows it.

## Cuts and transitions

A plain cut needs adjacent clips with no overlap. A `<transition>` belongs at
the cut point between the two specific adjacent clips and consumes source
handles from each side; it does not justify overlapping their composition
ranges. Put `<transitions>` as a direct child of `<draft>`, after the tracks,
never inside a track. `from-clip` and `to-clip` reference the adjacent
video clip IDs; `in` is the cut point and `duration` is milliseconds.

For a requested 500 ms cross-dissolve at 3000 ms, use the exact built-in type:

```xml
<transitions>
  <transition type="glsl_cross_dissolve" from-clip="first-clip-id" to-clip="second-clip-id" in="3000" duration="500" />
</transitions>
```

The two clips still abut at 3000 ms. The renderer uses source handles rather
than overlapping their composition ranges. Confirm that the outgoing and
incoming sources have enough material beyond their trims; if that cannot be
established from the existing clip/source metadata, ask whether to shorten the
transition or adjust the trims. If the user did not request a transition, keep
the cut plain and omit the whole `<transitions>` block.

`get_project_frame` accepts `frame`, a zero-based frame index, not milliseconds.
Convert with `frame = floor(milliseconds / 1000 * fps)`. At 30 fps, use frame
`89` (the last frame before the 3000 ms cut), frame `98` (within the 500 ms
transition), and frame `105` (at/after its 3500 ms end). For a plain cut,
choose one actual frame index on each side in the same way.

## Text and subtitles

Plain static text or a subtitle can be a styled text element inside a text
clip. Keep each subtitle cue aligned to its requested speech interval, readable
inside the safe area, and on a dedicated text track when it overlaps video.
Reuse a `<styles>` class for repeated subtitle styling instead of duplicating
the same declarations in every cue. `<styles>` is the recommended first child
of the text track, and its single-class selectors are track-scoped. Reference
one class name with `class="..."`; inline style may override individual cues.
Keep per-cue text and timing local. A concrete two-cue structure is:

```xml
<track id="subtitle-track" type="text">
  <styles>
    .subtitle-box { left: 6%; top: 80%; width: auto; height: auto }
    .subtitle-text { color: #fff; font-size: 2.4em; font-weight: 700; text-shadow: 0 0.06em 0.16em rgba(0,0,0,0.72) }
  </styles>
  <clip id="subtitle-1" class="subtitle-box" in="800" out="1800">
    <div class="subtitle-text">First supplied cue</div>
  </clip>
  <clip id="subtitle-2" class="subtitle-box" in="3600" out="4700">
    <div class="subtitle-text">Second supplied cue</div>
  </clip>
</track>
```

Place this track after the video track so the captions paint above the video.
Preserve an unrelated overlay's existing relative order unless the user asks
whether captions should appear above or below that overlay.

Do not invent transcript timing. If exact word timing is unavailable through
the provided project or user input, ask for it or clearly use the user's
approved coarse timing.

## Editable render components

For a graphic whose text, colors, dimensions, placement, toggles, or motion
must remain editable, put those values in `<data type="json">` and consume them
from a sibling `<render>` body. Keep expressions and bindings intact during a
small edit. A bare static subtitle does not need a full-frame render wrapper;
that wrapper can create a misleading full-canvas selection box.

Use `<component>` for repeated reusable visual structure. Prefer existing
component, style, and data names over introducing near-duplicates.

## Effects and animation

Preserve existing color, effect, beauty, motion, GSAP, Anime, Lottie, Three.js,
and render constructs unless the user asks to change them. Use the smallest
mechanism that meets the request: ordinary CSS/render interpolation for simple
property motion, Lottie for supplied Lottie animation, and Three.js only for an
explicitly editable 3D scene or model. Do not translate these constructs into
generated video merely to simplify the template.

For frame-sensitive animation, convert the requested inspection time to a
frame index and check representative start, middle, and end frames.

## Repair checklist

On validation failure, use the returned error location and verify:

- root attribute names and positive numeric values;
- direct track nesting and valid track type;
- unique IDs and non-overlapping clips on each track;
- `in < out` and ranges within the draft duration;
- media URLs copied exactly from tool results;
- referenced style, data, component, asset, and expression names exist;
- XML-like tags and quoted attributes are balanced.

Repair only the implicated structure, reload first if the project version has
advanced, then save the complete template again.
