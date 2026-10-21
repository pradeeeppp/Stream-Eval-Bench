Typical use cases: understanding an earlier event from later evidence
A relatable way to introduce the benchmark is: “You see something happen, then a replay or another camera shows a detail you missed. Can an AI update its account of that event without thinking it happened twice or confusing it with what is happening now?”
The scenarios below are illustrative benchmark designs, not verified examples from the candidate datasets. They share one requirement: later footage provides evidence about an identifiable earlier occurrence. A new view of the current state alone does not necessarily establish what happened in the past.
1. Sports companion: who actually touched the ball?
User need: A viewer wants an accurate account of a match despite fast action, occlusion and replays.
First observation: A wide shot shows one shot on goal. A defender partly blocks the view, so the assistant cannot confidently identify who made the final touch. Play then continues.
Later evidence: A slow-motion replay of that same shot clearly shows a touch by player #8. The replay arrives after another passage of play.
Expected response: “The replay shows that #8 made the final touch on the earlier shot. That is the same attempt, not another shot.” Update the touch attribution; preserve the shot’s identity, original time, count and place in the match sequence. Do not treat the replay position as the current ball position.
Benchmark test: Ask who touched the ball before and after the replay, how many attempts have occurred, and what was last observed in live play. Failure means guessing early, missing the new detail, counting an extra attempt, or overwriting the current situation with replay content.
2. Multi-camera incident review: which bag was picked up?
User need: A monitoring operator wants one consistent incident record when camera views arrive at different times.
First observation: Camera A shows someone picking up a bag near a doorway, but the bag is obscured. A second person picks up another bag soon afterward.
Later evidence: Delayed footage from camera B shows the first pickup from a clearer angle and reveals a red tag on that bag. Capture timestamps or overlapping actions establish that the footage concerns the first pickup.
Expected response: “The bag in the first pickup had a red tag.” Update only that event’s bag description. Preserve two distinct pickups, their order and the record of the second person. Do not infer ownership, theft or intent from a pickup alone.
Benchmark test: Require the model to attach the tag detail to the correct pickup among similar candidates. Vary the delay and number of intervening pickups. Failure means merging two events, creating a third pickup, or assigning the new detail to the wrong person.
3. Cooking assistant: which ingredient went into the bowl?
User need: A cook wants the assistant to keep an accurate preparation history when hands or containers block the camera.
First observation: The cook adds one spoonful from an unreadable container. The assistant records one addition but leaves the ingredient unresolved. Stirring and another ingredient addition follow.
Later evidence: A delayed side-camera clip of the original spoonful reveals the container label and its connection to that transfer: the ingredient was sugar.
Expected response: “That earlier spoonful was sugar.” Update the ingredient field for the first addition; retain its quantity as one spoonful, its original position in the recipe and the later actions. Do not count the replay as another spoonful or claim the bowl’s current contents are visible if they are not.
Benchmark test: Ask what was added in the first step, how many additions occurred and which step was last observed. Include a control where a container label is visible only later, without evidence linking it to the earlier transfer; that case should remain unresolved.
4. Assembly assistant: was the earlier part installed the right way round?
User need: A worker or inspector wants an accurate assembly history even when a hand hides a critical installation detail.
First observation: A worker installs a bracket once, but its orientation is obscured. The worker then completes two other operations.
Later evidence: An alternate view of the original installation shows that the bracket’s marked face was inward. A task-specific instruction establishes that it should have faced outward.
Expected response: “The earlier bracket installation had the marked face inward; that conflicts with the assembly instruction.” Update the orientation and instruction-compliance fields for that installation. Preserve the completed later operations and avoid claiming that a repair has already occurred.
Benchmark test: Ask which installation needs review and which operations happened afterward. Failure means attributing the issue to a different installation, deleting completed work, or treating the alternate view as a new installation. A current close-up is evidence about the earlier installation only if intervening removal or reorientation has been ruled out.
5. Remote assistance: was the connector latched before the next step?
User need: A remote helper needs to revise its assessment of a past manipulation while still following the worker’s ongoing task.
First observation: A worker inserts a connector, but a hand hides the latch. The assistant records insertion while leaving latch engagement unconfirmed. The worker moves to a cable-routing step.
Later evidence: A delayed close-up of that same insertion shows the latch engaging. The worker’s current activity continues in a separate live view.
Expected response: “The close-up confirms that the earlier connector insertion latched successfully. The current step is cable routing.” Update latch status for the earlier insertion and retain the current-step record. Do not ask the worker to repeat an already completed insertion.
Benchmark test: Score both the historical update and recognition of the ongoing action. Failure means updating correctly but losing the current task, repeating an unnecessary instruction, or interpreting the delayed close-up as current activity. Concurrent-action tests require visible live input, such as a second feed or split-screen; hidden events should not be scored as observable.
6. Traffic incident review
User need: A transport analyst wants to reconstruct the order of actions in a road encounter.
First observation: A dashcam view leaves it unclear whether a pedestrian entered the road before or after a vehicle began turning.
Later evidence: An overhead recording of the same interval arrives later and reveals that the pedestrian entered first.
Expected response: Revise the order of the two actions while retaining one encounter and its original time. The evidence establishes visible sequence; it does not by itself establish legal fault.
Benchmark test: Temporal-order revision without duplicating the encounter or confusing it with a later crossing.
Candidate footage: WTS provides overhead and vehicle views of staged traffic scenarios. Inspect its gallery for candidate pairs; this scenario is illustrative, not a verified clip. Check access and redistribution terms before releasing footage.
WTS dataset and gallery
7. Household robotics
User need: A person asks whether a household robot picked up the requested spoon on its first attempt.
First observation: The robot reaches into a cluttered drawer, but the gripper and selected object are hidden.
Later evidence: A wrist-camera recording of that original attempt reveals the spoon in the gripper.
Expected response: Update the earlier attempt to a successful spoon grasp, preserving a single attempt. Later actions may change what the robot currently holds.
Benchmark test: Update object identity and action success for the correct attempt while keeping current possession separate.
Candidate footage: DROID includes external and wrist camera recordings of robot manipulation. Use its visualizer to find grasps, placements, and drawer interactions; screen pairs for actual information gain.
DROID dataset and visualizer
8. Meetings and collaborative work
User need: A meeting participant asks who handed the prototype to whom during an earlier discussion.
First observation: Two participants reach across a table, obscuring the handover in the room view.
Later evidence: A synchronized participant-camera recording of that moment identifies the giver and recipient.
Expected response: Correct the participant roles in the original handover without adding another handover or disrupting the later discussion. Visible transfer does not establish agreement with a proposal.
Benchmark test: Participant-role correction and association to the right interaction.
Candidate footage: The AMI Meeting Corpus includes synchronized room and individual camera views. Look for visible object exchanges; a qualifying handover pair still needs clip-level verification.
AMI Meeting Corpus
9. Dance and movement coaching
User need: A dance coach asks which foot initiated the turn in the dancer’s second repetition.
First observation: A front view makes the foot sequence ambiguous.
Later evidence: A side recording of the same repetition shows which foot moved first.
Expected response: Update the movement description for repetition two, preserving the number and order of repetitions and leaving repetition three unchanged.
Benchmark test: Fine-grained movement interpretation under repeated, visually similar actions. The target is observable movement, not a clinical assessment.
Candidate footage: AIST/AIST++ provides multi-view dance footage, with nine camera views in the underlying AIST data. Select pairs where the additional angle resolves a specific ambiguity.
AIST++ project
AIST Dance Video Database
10. Surgical skills training
User need: An instructor reviewing a simulated procedure asks which instrument received the needle in an earlier transfer.
First observation: Overlapping instruments obscure the transfer.
Later evidence: A second camera view of the same gesture reveals the receiving instrument.
Expected response: Correct instrument attribution while retaining one transfer and the original gesture sequence. Do not infer clinical safety or overall competence from this observation alone.
Benchmark test: Tool-role correction in fine-grained procedural video.
Candidate footage: JIGSAWS contains stereo video, kinematics, and gesture annotations for simulated surgical tasks. Its narrow stereo baseline may provide too little new information; verify that the second view actually resolves the ambiguity.
JIGSAWS dataset
11. Retail checkout
User need: A checkout reviewer asks which product variant was placed on the tray.
First observation: A carton is placed on the tray with its identifying label hidden.
Later evidence: A delayed close-up recording of the original placement reveals the variant.
Expected response: Update the identity of the already-counted item without creating an extra placement or billed item.
Benchmark test: Attribute refinement with stable item and event counts.
Candidate footage: AI City Challenge 2022 checkout data is a starting point for the retail domain, but its checkout task is single-view and is not a ready-made paired-view source. A suitable alternative or controlled recording is needed for this scenario.
AI City Challenge 2022 data
Official challenge paper
12. Parcel handling and logistics
User need: A warehouse operator asks which trolley received a parcel during its original loading.
First observation: The worker’s body hides the trolley label as the parcel is loaded.
Later evidence: A second recording of that loading reveals the destination as trolley B.
Expected response: Correct the destination of the original loading, preserving one loading event and any subsequent transfers. Seeing the parcel on trolley B now is insufficient evidence of its original destination.
Benchmark test: Destination correction while distinguishing historical location from current location.
Collection route: No ready-made source was verified for this example. Record synchronized views of controlled parcel transfers with readable parcel and trolley identifiers.
13. Laboratory experiments
User need: A researcher reviewing an experiment asks which marked vial received an earlier pipette transfer.
First observation: A hand blocks the target vial during the transfer.
Later evidence: A delayed overhead recording of the same transfer reveals vial B.
Expected response: Update the target of that transfer while preserving the transfer count and experimental order. Do not infer chemical identity or transferred volume unless those facts are supplied by evidence.
Benchmark test: Target-object correction; retain uncertainty when the new view still does not identify the vial.
Collection route: No ready-made source was verified for this example. Use a controlled demonstration with clearly marked vials and synchronized views.
14. Screen recordings and software workflows
User need: A collaborator asks which filename and destination were selected during an earlier export.
First observation: A low-resolution screen share makes the export dialog unreadable.
Later evidence: A higher-resolution recording of that same interval arrives later and reveals the selected filename and destination.
Expected response: Update the recorded export details without counting a second export. The dialog alone does not prove that the file still exists or that the operation completed successfully.
Benchmark test: Text-detail refinement with stable action identity, separating selected settings from observed completion and current state.
Collection route: No ready-made source was verified for this example. Capture synchronized high- and low-quality versions of a controlled workflow and release the clearer segment later.

