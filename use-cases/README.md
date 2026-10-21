# Use-Cases Library (Expandable)

Source: [`use-case.md`](../use-case.md) — 14 illustrative benchmark designs for **selective retrospective correction** in streaming video.

> Core pattern for every case: `E1 ambiguous` → `E2 intervening` → `E3 delayed evidence about E1`. Ask: can the agent update `E1` without duplicating it, confusing it with `E2`, or overwriting live state?

These are **illustrative designs, not verified clips**. Each file is a stub you can expand into a runnable `stream_eval` usecase (see `stream_eval/usecases/table_assembly.py` for reference).

## Already implemented (code-ready)

| ID | Dir file | Python usecase | Video |
|---|---|---|---|
| 00a | `00-implemented-holoassist.md` | `table_assembly_tray` | HoloAssist `z060-june-28` tray OFF→ON |
| 00b | `00-implemented-holoassist.md` | `camera_detachment`, `camera_mount_status` | HoloAssist `z176-sep-05` lens/cap |
| 00c | `00-implemented-holoassist.md` | `printer_display_tracking` | HoloAssist `R071-19July` display dark/illuminated |
| 00d | `00-implemented-holoassist.md` | `table_components_tracking` | HoloAssist table legs vs tray |

Plus 25 downloaded probes: `experiments/hf_hard_prototype/videos/` + `manifest.json` + `evaluation_results.json`.

## Illustrative (expand me)

| # | File | Domain | Ambiguity → Reveal |
|---|---|---|---|
| 01 | `01-sports-companion.md` | Sports | who touched ball → slow-mo replay shows #8 |
| 02 | `02-multicamera-bag-pickup.md` | Surveillance | which bag → cam B shows red tag on 1st pickup |
| 03 | `03-cooking-ingredient.md` | Cooking | which ingredient → side cam shows sugar label |
| 04 | `04-assembly-bracket-orientation.md` | Assembly | bracket orientation → alternate view marked-face inward |
| 05 | `05-remote-connector-latch.md` | Remote assist | latch engaged? → close-up shows latch |
| 06 | `06-traffic-order.md` | Traffic | ped before/after turn → overhead shows ped first |
| 07 | `07-household-robot-grasp.md` | Robotics | which object grasped → wrist cam shows spoon |
| 08 | `08-meeting-handover.md` | Meetings | who gave to whom → participant cam resolves roles |
| 09 | `09-dance-turn-initiation.md` | Dance | which foot started turn 2 → side view resolves |
| 10 | `10-surgical-transfer.md` | Surgery training | which instrument received needle → 2nd view |
| 11 | `11-retail-checkout-variant.md` | Retail | which variant → close-up of placement |
| 12 | `12-parcel-trolley.md` | Logistics | which trolley → 2nd recording shows trolley B |
| 13 | `13-lab-vial-transfer.md` | Lab | which vial → overhead shows vial B |
| 14 | `14-screen-export-dialog.md` | Screen workflow | filename/dest → hi-res recording of same interval |

## How to expand any file (see `_template.md`)

Each stub already has:

1. `User need`, `E1 / E2 / E3`, `Expected response`
2. `Benchmark test` — what to ask before/after + Joint/Chrono/Delayed mapping
3. `RQ mapping` — RQ1 bind, RQ2 anchor, RQ3 preserve
4. `Failure modes` — merge, duplicate, misattribute, overwrite-live
5. `Candidate footage / collection route`
6. `To implement` — timestamps, packets, schema `{earlier, latest}`, `expected_final`, controls (irrelevant-evidence, replay-of-other, new-similar-action), 4-Gate checks

Design rule from `use-case.md`: *a new view of current state alone ≠ evidence about the past.* You must establish capture-time linkage (timestamps, overlapping actions, same transfer).

## RQ cheat-sheet

* RQ1 bind: attach E3 to right E among similar candidates
* RQ2 anchor: same final frames × [no prior vs real prior vs `unknown`] — does old guess hurt?
* RQ3 preserve: keep E2 + live state, no extra count, no unsupported inference
* RQ4 policy: same frames/memory/latency budget, evidence-gated update vs naive history-concat
