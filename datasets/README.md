# New-dataset candidate records

Start with [the expansion/admission protocol](../docs/DATASET_EXPANSION.md) and
copy [candidate.template.json](candidate.template.json) for each proposed episode.
The template contains placeholders and is not a real or admitted sample.

No new cross-dataset episodes are admitted in this directory yet. Existing
HoloAssist diagnostic data remain in their original experiment directories.

For future collection, store candidate records in a source/version-specific
directory, retain rejected/deferred records and never mix unreviewed candidates
with scored test labels. Keep original recording identifiers for split grouping.
Do not fill a field by inferring an old hidden fact from a later changed state.

Allowed admission states are `candidate`, `screened`, `prefix_labeled`,
`link_verified`, `adjudicated`, `pilot_admitted`, `released`, `deferred`, and
`rejected`. Missing checks remain null, not true. Changing the status string is
not a validation procedure; an episode needs the recorded reviews and checks.

Construction tracks: `delayed_delivery`, `natural_later_evidence`,
`delayed_alternate_view`, `controlled_reveal`. Event-link labels: `same_event`,
`new_event`, `unrelated`, `unresolvable`. Evidence-effect labels: `confirms`,
`contradicts`, `refines`, `unresolved`, `no_new_information`. These are proposed
collection fields, not a claim that a cross-dataset scoring adapter is complete.
