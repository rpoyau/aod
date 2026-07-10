# Transition and Rebaseline Graph

```text
PROJECT-STABLE PAYLOAD + ORDERED DELTA = ROOT CANDIDATE

AUTHORING --candidate_ready--> REVIEW
REVIEW --blocking_findings--> FEEDBACK
FEEDBACK --revision_authorized--> AUTHORING
REVIEW --no_blockers + authority--> GO
GO --rebaseline_in_child_bundle--> AUTHORING(next goal)
```

Every arrow emits one immutable successor bundle. The parent bundle is not embedded recursively. The last authorized stable **payload** is embedded; the lineage parent remains a filename/SHA-256 relation.

At GO, the current bundle remains frozen. In the next successor bundle, the GO candidate becomes `stable/payload/`, the delta is reset, and new authoring begins from that rebaselined state.
