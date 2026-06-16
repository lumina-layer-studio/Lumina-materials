# Agent Instructions

- This repository is content-only. Do not add Lumina application code or
  Registry service deployment code here.
- Keep package artifacts immutable: changing content requires a new revision.
- Seed artifacts must be official-only.
- Validation scripts must reject path traversal, non-UTF-8 manifests, hash
  mismatch, duplicate `material_id + revision_id`, and local-only files such as
  `usage_stats.json` or `_solver_cache/`.
