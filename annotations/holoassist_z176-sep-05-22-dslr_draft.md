# HoloAssist first-pass annotation (draft)

**Status:** provisional visual pass; not adjudicated or benchmark-ready  
**Annotator:** Codex, 2026-10-27  
**Source session:** `z176-sep-05-22-dslr`  
**Video duration:** 68.096 s (source manifest)  
**Task family:** DSLR camera handling / instruction-following  
**Primary source:** [HoloAssist project and data access](https://holoassist.github.io/)  
**Dataset license stated by source:** CDLA-Permissive-2.0; verify applicable terms before redistribution.

## Provenance and limits

This first pass uses the existing 1 fps contact sheets at [page 1](../experiments/source_suitability/holo_1_page1.jpg) and [page 2](../experiments/source_suitability/holo_1_page2.jpg). The sampled source manifest records SHA-256 `3eead3bbf2fe8ebb48a1888b99d0fd55385fd13ebc3ebd361d77597ab86c86cc`, but the MP4 is not currently present in this checkout. The manifest points to an EgoIT-99K redistribution and explicitly notes that it was not byte-verified against the original HoloAssist archive.

Contact-sheet timestamps are approximate 1-second samples. They can identify candidate intervals but cannot establish exact action boundaries, brief events, speech, intent, or whether a component was fully engaged between samples. This file is a working annotation, not original HoloAssist ground truth. The original annotation files/audio and the exact video should be checked before finalizing labels.

## Episode-level first pass

The recording shows a performer handling a DSLR camera and detachable components from an overhead egocentric view. The camera and a separate small accessory are initially on the work surface. The performer picks up the DSLR, manipulates the camera body and lens, then handles what appears to be a small lens cap or accessory while continuing to inspect/operate the camera. Near the end, the view changes from the overhead workbench to a room view.

**Do not infer:** the exact camera model, lens model, whether a component is correctly installed, the performer’s goal, task success, or the instructor’s advice from these sampled frames alone.

## Coarse temporal labels

Intervals are approximate candidate spans based on sampled frames, not frame-accurate ground truth. “Unclear” is intentional where the visual evidence does not settle the event.

| ID | Approx. interval (s) | Draft label | Visible evidence | Confidence | Needs review |
|---|---:|---|---|---|---|
| E1 | 0–5 | DSLR and small accessories rest on the work surface; no hand interaction is apparent in sampled frames. | Overhead view shows camera and small items on desk. | Medium | Check unsampled motion and whether this is a task start or continuation. |
| E2 | 5–8 | Performer reaches for and lifts the DSLR. | Hands enter; camera is held in both hands by the later samples. | High for pickup; low for exact onset | Inspect source frames around 5–8 s for pickup boundary. |
| E3 | 8–12 | Performer manipulates the lens and camera body; samples suggest the lens may be detached and held separately. | At roughly 8–10 s the camera mount and a separate cylindrical object appear visible; later sample shows the object near the camera. | Low | Confirm with consecutive frames: detachment, direction of rotation, and whether the item is the lens. Do not label “lens removed” as certain yet. |
| E4 | 12–18 | Performer continues handling/inspecting the DSLR and lens; possible reattachment or repositioning. | Camera and cylindrical component appear together across samples; hand positions change. | Low | Determine whether the lens is attached, removed again, or merely rotated. Locate exact state transitions. |
| E5 | 18–36 | Performer continues operating or inspecting the camera, including turning it to view its rear display/buttons. | Camera rear is repeatedly oriented toward the wearer; hands manipulate controls. | Medium | Read display only if legible at native resolution; avoid inferring menu/task state from thumbnails. |
| E6 | 36–48 | Performer reorients and handles the camera and lens. | Camera alternates between rear and lens-facing views; hand contact continues. | Low | Inspect frames for any additional detach/reattach event and distinguish camera movement from state change. |
| E7 | 48–66 | Performer handles the DSLR body and a small component near the lens/front area; possible cap placement/removal. | Camera and a small dark object are visible separately in some samples; the object is brought near the front of the camera. | Low | Verify component identity and whether it is attached, removed, or set down. Track the same object. |
| E8 | 66–68 | View transitions from close overhead camera handling to a wider room view. | Final samples show the room and work area rather than the prior close-up. | High for view change | Check if this is a video cut/camera repositioning or a new viewpoint. |

## Candidate event graph (unconfirmed)

The best candidate for the benchmark’s event-level task is a camera-component manipulation sequence in approximately **7–18 s**. The 1 fps samples are consistent with a possible detach/inspect/reattach sequence, but do not prove the exact action or state. At this stage:

- Stable event identity: **not established** beyond “same camera-handling episode.”
- Initially unresolved claim: **not established**; samples may make the component visible throughout.
- Later evidence about the same earlier occurrence: **not established**; no clear replay or alternate view is visible in the contact sheets.
- Supported correction target: **none assigned yet**.
- Protected facts: provisional camera identity and count of manipulation episodes; exact count **not assigned**.
- Downstream decision consequence: **none assigned**.

Therefore this session is useful for practice on event segmentation and state tracking, but it is **not yet admitted** as an example of later-evidence historical revision. Do not create an artificial “later reveal” from a later physical state unless we verify the object’s identity and rule out intervening handling that could have changed the state.

## Open questions for the next annotation pass

1. What is the performer’s stated task and what does the original HoloAssist narration/action annotation say?
2. Does the video include instructor speech, and does it identify a mistake, correction, or intended camera operation?
3. Around 7–18 s, is the lens actually detached and reattached? What are the precise boundaries?
4. Around 48–66 s, is the small object a lens cap, and can its state be tracked continuously?
5. Does the final room view show the performer, instructor, or a task transition?
6. Is there any natural later observation that resolves a genuinely ambiguous earlier event? Current sampled evidence does not establish one.

## Annotation schema decisions for this draft

- Times are in source-video seconds and are approximate until frame-level review.
- A missing/unclear label means **unknown**, not “no event.”
- Labels describe visible actions/states; intent and correctness require transcript, task instruction, or independent evidence.
- Keep event occurrence, object state, evidence source, and annotation confidence separate.
- Preserve original labels in a separate field when retrieved; do not overwrite them with this project’s interpretation.

