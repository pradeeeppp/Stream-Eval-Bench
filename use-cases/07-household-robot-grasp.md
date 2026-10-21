# 07 — Household robotics: did it pick the spoon first try?

## User need
Did robot pick requested spoon on attempt 1?

## Stream script
* **E1:** reach into cluttered drawer, gripper+object hidden → `grasp=unknown, success=unknown`.
* **E2:** later actions may change held object (keep current possession separate).
* **E3:** wrist-cam of *original* attempt: spoon in gripper.

## Expected response
Update attempt-1 to successful spoon grasp, keep single attempt. Later holding may differ.

## Benchmark test
Object + success for correct attempt, current possession separate.

## Candidate footage
DROID (external + wrist). Use visualizer to find grasps/drawer interactions; screen for info gain. Check terms.

## RQ mapping
RQ1 (attempt identity), RQ3 (history vs current possession).
Status: `illustrative`.
