# Causal Retrospective Revision (CRR): Grounding, Verification, and Research Blueprint

## 1. The Distinctive Research Problem

In streaming video understanding, current benchmarks evaluate whether a Vision-Language Model (VLM) can **remember what happened forward in time** (temporal memory) or **detect objects and actions in newly arriving frames** (perception). 

Our research investigates a distinct, unbenchmarked cognitive capability:
> **A streaming VLM may remember an earlier event correctly, recognize newly arriving footage correctly, and reason jointly across frames—yet still fail when it must use delayed footage to revise an earlier event without changing the event's identity or corrupting other historical facts.**

### Why is this capability fundamentally distinct?

| Capability | What is evaluated | Why it does not imply Retrospective Revision |
|---|---|---|
| **Perception** | Can the model recognize an action/object in an isolated clip? | Evaluates single-clip visual encoding. No temporal memory or multi-event association. |
| **Temporal Memory** | Can the model retain a fact forward in time ($t_1 \to t_2$)? | The fact is fixed when first observed. No revision or retroactive modification is required. |
| **Joint Video QA** | Can the model answer questions when all clips are present simultaneously? | The model attends bidirectionally across all frames at once. There is no causal streaming bottleneck or prior-belief conditioning. |
| **Causal Retrospective Revision (CRR)** | When delayed footage about an earlier event $E_1$ arrives at $t_3$ (after $E_2$ has occurred), can the agent update $E_1$ while preserving $E_2$ and avoiding identity confusion? | **Requires 3 coordinated operations:** (1) Retroactive Entity Binding, (2) Selective Attribute Modification, and (3) Cross-Event Identity Invariance. |

---

## 2. The Three Failure Modes of Streaming VLMs under Retrospective Evidence

When streaming VLMs are tasked with revising historical states from delayed evidence, they exhibit three failure modes that do not appear in static or pure-chronological settings:

```
[Time t1: Event E1 (Ambiguous)]  --> Agent Memory: { E1: "ambiguous", E2: "none" }
[Time t2: Event E2 (Distinct)]   --> Agent Memory: { E1: "ambiguous", E2: "confirmed" }
[Time t3: Delayed Footage of E1] --> 
     |
     +--> Failure Mode 1: Recency Bias / Misattribution
     |    Evidence binds to E2 instead of E1: { E1: "ambiguous", E2: "corrupted" }
     |
     +--> Failure Mode 2: Anchor Inertia / Belief Rigidity
     |    Agent repeats its prior generated text: { E1: "ambiguous", E2: "confirmed" }
     |
     +--> Failure Mode 3: Cross-Event Identity Swapping
     |    Agent flips identities of E1 and E2: { E1: "E2_val", E2: "E1_val" }
```

1. **Recency Bias / Misattribution (Binding Error)**:
   Autoregressive models have a strong inductive bias toward the most recently generated or observed token context. When new evidence arrives at $t_3$, the model binds the evidence to the latest active event ($E_2$) rather than back-propagating the visual association to $E_1$.
2. **Anchor Inertia / Belief Rigidity (Self-Conditioning Bias)**:
   In external-memory streaming architectures, the agent receives its own previous step's response as input memory. Language models are trained to be internally coherent; seeing its own prior assertion creates strong inertia, causing the model to defend or repeat its earlier statement rather than overturning it.
3. **Cross-Event Identity Swapping**:
   When forced to update $E_1$, the visual representation of the new clip blends with the visual representation of $E_2$, leading to catastrophic cross-contamination between distinct entities.

---

## 3. The 4-Gate Disentanglement Protocol

To establish that a failure is genuinely caused by the **streaming revision mechanism** (and not by weak perception, unresolvable ambiguity, or lack of joint reasoning capacity), every test episode must satisfy the **4-Gate Protocol**:

```mermaid
graph TD
    A[Test Episode] --> G1[Gate 1: Standalone Perception Gate]
    G1 -- PASS --> G2[Gate 2: Static / Joint Upper-Bound Gate]
    G1 -- FAIL --> X1[Invalid: Model cannot perceive the evidence]
    
    G2 -- PASS --> G3[Gate 3: Forward Chronological Memory Gate]
    G2 -- FAIL --> X2[Invalid: Visual task too hard even in full context]
    
    G3 -- PASS --> T[Target Test: Causal Retrospective Revision]
    G3 -- FAIL --> X3[Invalid: Model lacks basic temporal memory]
    
    T -- Fails to revise / Corrupts other events --> S[VALID DISCOVERY: Isolated Streaming Revision Failure]
    T -- Succeeds perfectly --> S2[Robust Updating Control]
```

1. **Gate 1: Standalone Perception Gate ($G_{perc}$)**:
   * *Protocol*: Present the delayed footage in isolation.
   * *Requirement*: The model must correctly identify the underlying object, action, or state.
   * *Purpose*: Eliminates low-level visual perception as the failure cause.
2. **Gate 2: Static / Joint Upper-Bound Gate ($G_{joint}$)**:
   * *Protocol*: Present $E_1$, $E_2$, and the delayed footage together in a single prompt.
   * *Requirement*: The model must correctly match the evidence to $E_1$, output the true state of $E_1$, and output the true state of $E_2$.
   * *Purpose*: Proves the correspondence is physically discoverable and within the model's multi-frame reasoning capacity.
3. **Gate 3: Forward Chronological Memory Gate ($G_{chrono}$)**:
   * *Protocol*: Present $E_1$ then $E_2$ in forward chronological order without delayed revision demands.
   * *Requirement*: The model must maintain and track both events across steps without catastrophic forgetting.
   * *Purpose*: Proves the agent's memory schema and sequential interface function normally.
4. **Target Condition: Causal Retrospective Revision ($T_{rev}$)**:
   * *Protocol*: Present $E_1$ (ambiguous), then $E_2$ (confirmed), then delayed footage of $E_1$.
   * *Signature of Isolated Failure*: $G_{perc} = \text{PASS} \land G_{joint} = \text{PASS} \land G_{chrono} = \text{PASS}$, but $T_{rev} = \text{FAIL}$.

---

## 4. Audit of Current Empirical Findings in Stream-Eval-Bench

| Experiment | Setup | Gates Passed | Outcome | Diagnostic Insight |
|---|---|---|---|---|
| **Two-Clip Diagnostic** (`two_clip_diagnostic`) | HoloAssist table assembly (`earlier.mp4` & `later.mp4`). Single event tracked (`tray`). | $G_{perc}$ Pass, $G_{joint}$ Pass | Final states matched; intermediate chronological error. | **Underconstrained**: Lacked a second distinct event ($E_2$) to create binding competition. Proved simple single-variable updating can succeed. |
| **Intervening Footage** (`intervening_video`) | 9-call comparison on camera part detachment with intervening video packets. | $G_{perc}$ Pass, $G_{joint}$ Fail | Model failed in *both* Joint and Streaming conditions. | **Confounded**: Joint control failure prevents attributing the error to the streaming mechanism. |
| **Fixed Hypothesis Prototype** (`fixed_hypothesis`) | Camera & Printer episodes with dual records ($E_1, E_2$) and reveal view. | Printer: $G_{perc}$ Pass, $G_{joint}$ Pass. | **Joint answer was correct ($E_2=\text{dark}$), but Update answer failed ($E_1=\text{illuminated}$, matching reveal to wrong event $E_1$).** | **Concrete Evidence of History-Conditioned Discrepancy**: The model was 100% correct on joint image bytes, but failed when conditioned on its own prior answer! |

### The Critical Takeaway from the Printer Experiment:
In `experiments/fixed_hypothesis/`, when `qwen3-vl-235b-a22b-instruct` was given the final composite image alone (Joint), it correctly assigned the reveal to $E_2$ (`E1=unknown, E2=dark, match=E2`). 
However, when given the **exact same final image** plus its own prior response from step 1 (Update), it **misattributed the reveal to $E_1$** (`E1=illuminated, E2=unknown, match=E1`), corrupting the records!

This is direct empirical proof of **History-Conditioned Binding Interference**: the agent's prior text memory directly caused a cross-event binding failure on byte-identical visual inputs.

---

## 5. Blueprint to Scale this into an Established Novel Contribution (CVPR Submission)

To transition from exploratory prototype to a high-impact benchmark paper:

### A. Dataset & Scenario Construction (Stream-CRR Benchmark)
Construct 100–200 validated episodes across 3 domains:
1. **Egocentric Assembly / Disassembly** (HoloAssist, Ego4D): Tool usage, part removals, assembly sequences where an action is momentarily blocked by the user's hand or body, then re-observed later.
2. **Multi-Camera Surveillance / Traffic**: Object $O_1$ seen with occluded license plate at camera 1 ($t_1$); object $O_2$ enters intersection ($t_2$); camera 2 captures clear rear view of $O_1$ ($t_3$).
3. **Sports Instant Replay** (NBA, NFL): Fast-action event with initial wide view followed by an alternate slow-motion replay after play resumes.

### B. Standardized Evaluation Metrics
* **Retroactive Revision Rate (RRR)**: Fraction of ambiguous/unknown historical fields correctly updated to ground truth upon receiving delayed footage.
* **Recency Preservation Rate (RPR)**: Fraction of steps where the latest known physical state remains uncorrupted when older footage arrives.
* **Binding Accuracy (BA)**: Fraction of episodes where delayed evidence is bound to the correct historical entity index ($E_{\text{target}}$) without cross-contamination.
* **Streaming Order-Effect Gap ($\Delta_{\text{SOE}}$)**:
  $$\Delta_{\text{SOE}} = \text{Accuracy}_{\text{Joint}} - \text{Accuracy}_{\text{Streaming\_CRR}}$$
  A non-zero $\Delta_{\text{SOE}}$ when $G_{perc}$ passes quantifies the exact penalty imposed by the streaming paradigm.

### C. Evaluation Across Open-Source & Frontier VLMs
Benchmark the phenomenon across model scales:
* **Compact Open-Source VLMs**: `SmolVLM2-500M-Video`, `Qwen2.5-VL-7B-Instruct`, `InternVL-2.5-8B`.
* **Large Open-Source VLMs**: `Qwen2.5-VL-72B-Instruct`, `LLaVA-OneVision-72B`.
* **Proprietary Frontier VLMs**: `GPT-4o`, `Gemini 1.5 Pro` (using API runners).

### D. Proposed Method / Algorithmic Solution
A benchmark paper is significantly strengthened by proposing a baseline solution:
* **Decoupled Belief Tracking (DBT)**: Separate the persistent state store from the conversational chat history, using structured entity slots with explicit temporal validity intervals $[t_{\text{start}}, t_{\text{end}}]$.
* **Retrospective Attention Routing**: When an incoming packet's capture timestamp precedes the stream watermark ($t_{\text{capture}} < t_{\text{watermark}}$), route attention explicitly to the historical event slot matching that timestamp, suppressing recency bias toward $E_{\text{latest}}$.
