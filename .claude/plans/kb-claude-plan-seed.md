---
title: plan — kb-claude adoption checkpoints
link: kb-claude-plan-seed
type: plans
ontological_relations:
  - relates_to: [[kb-claude-overview]]
  - relates_to: [[kb-claude-code-touchpoints]]
tags:
  - kb-claude
  - planning
  - roadmap
created_at: 2025-12-09T19:54:08Z
updated_at: 2025-12-09T19:54:08Z
uuid: b9d4d55d-4137-4520-ad3b-002203d266b1
---
Near-term steps to operationalize the knowledge base.
- Wire the kb-claude CLI into the workflow and document install steps alongside `.venv`/`uv`.
- Automate `kb-claude manifest` regeneration in CI or pre-commit once the CLI is available.
- Add semantic search or graph export once core validation and manifest generation are stable.
