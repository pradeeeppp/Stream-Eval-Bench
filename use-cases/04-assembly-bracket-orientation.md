# 04 — Assembly assistant: was the earlier part installed the right way round?

## User need
Accurate assembly history when hand hides detail.

## Stream script
* **E1:** install bracket once, orientation obscured → `orientation=unknown`.
* **E2:** two other operations complete (preserve).
* **E3:** alternate view of *original* install: marked face inward; instruction says outward → non-compliant.

## Expected response
> “Earlier bracket had marked face inward; conflicts with instruction.” Update orientation+compliance for that install only. Keep later ops. Do NOT claim repair done.

## Benchmark test
Which install needs review, what happened after. Failure: wrong-install blame, delete work, alternate-view-as-new-install. Note: current close-up counts as E1 evidence only if removal/reorientation ruled out.

## RQ mapping
RQ1+RQ3; closest to implemented HoloAssist tray/camera cases — good next to implement.

## To implement
- [ ] mirror `table_assembly.py` schema `{install_orientation, compliance, later_ops}`
Status: `illustrative, high-priority expansion`.
