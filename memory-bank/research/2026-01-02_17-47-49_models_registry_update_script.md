# Research – Models Registry Update Script

**Date:** 2026-01-02 17:47:49
**Owner:** user
**Phase:** Research
**Git Commit:** 9827e62
**Last Updated:** 2026-01-02 17:47:49
**Last Updated By:** user

## Goal

Find the existing script that fetches `https://models.dev/api.json` and saves it to `src/tunacode/configuration/models_registry.json` for offline bundling with the package.

---

## Findings

### Key Finding: **No such script exists**

After comprehensive research of the codebase, git history, and scripts directory, **there is NO existing script that performs step 1→2** (fetching from models.dev and saving to the bundled JSON file).

### Relevant Files & Analysis

| File | Purpose | Status |
|------|---------|--------|
| `src/tunacode/configuration/models_registry.json` | Bundled offline registry (754KB+) | Manually maintained |
| `src/tunacode/configuration/models.py` | Loads bundled JSON at runtime | Active |
| `src/tunacode/utils/models_registry.py` | **DELETED** - was runtime cache only | Removed in cdaec03 |

### Historical Context

**Deleted Module: `src/tunacode/utils/models_registry.py`**
- **Introduced:** Commit `edee671` (Aug 29, 2025) - "feat: enhance /model command with multi-source routing and models.dev integration"
- **Deleted:** Commit `cdaec03` (Oct 16, 2025) - "refactor: Delete 7 dead module files (~1446 lines)"
- **What it did:**
  - Fetched from `https://models.dev/api.json`
  - Saved to **runtime cache**: `~/.tunacode/cache/models_cache.json`
  - **NOT** to the bundled JSON file
  - Had 24-hour TTL for cache validity

**Key code from deleted module (for reference):**
```python
class ModelsRegistry:
    API_URL = "https://models.dev/api.json"
    CACHE_FILE = "models_cache.json"  # In ~/.tunacode/cache/, NOT bundled
    CACHE_TTL = timedelta(hours=24)

    def _fetch_from_api(self) -> bool:
        """Fetch models from models.dev API."""
        # Fetches and saves to ~/.tunacode/cache/models_cache.json
```

### Manual Updates

The bundled `models_registry.json` file has been manually updated:
- **Commit `f59dedd`** (Dec 19, 2025): "chore: update models registry from models.dev"
  - Only 1 line changed (JSON diff truncated)
  - No script mentioned in commit message
  - Appears to be manual curl/download + commit

### Search Results

| Search Pattern | Result |
|----------------|--------|
| `models.dev` in code | Only `src/tunacode/configuration/models.py` (comment reference) |
| Scripts for update | None found |
| `curl * models.dev` patterns | None found |
| Makefiles | None in project root |
| GitHub Actions | No update workflow found |

---

## Knowledge Gaps

1. **How should the bundled JSON be updated?** - Currently manual process
2. **Should this be automated?** - No CI/CD workflow exists
3. **Version tracking** - No clear process for when to update models_registry.json

---

## Recommendations

### Option 1: Create a simple update script
```bash
#!/bin/bash
# scripts/update_models_registry.sh
curl https://models.dev/api.json -o src/tunacode/configuration/models_registry.json
```

### Option 2: Python script with validation
```python
# scripts/update_models_registry.py
import json
import urllib.request
from pathlib import Path

def main():
    url = "https://models.dev/api.json"
    output = Path("src/tunacode/configuration/models_registry.json")

    with urllib.request.urlopen(url) as response:
        data = json.load(response)
        output.write_text(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
```

### Option 3: Restore the deleted module with dual-mode
- Runtime cache: `~/.tunacode/cache/` (24h TTL)
- Bundle update mode: Flag to write to `src/tunacode/configuration/`

---

## References

- [GitHub: src/tunacode/configuration/models.py](https://github.com/alchemiststudiosDOTai/tunacode/blob/9827e62/src/tunacode/configuration/models.py)
- [GitHub: src/tunacode/configuration/models_registry.json](https://github.com/alchemiststudiosDOTai/tunacode/blob/9827e62/src/tunacode/configuration/models_registry.json)
- [GitHub: Commit edee671 (models_registry.py added)](https://github.com/alchemiststudiosDOTai/tunacode/commit/edee671)
- [GitHub: Commit cdaec03 (models_registry.py deleted)](https://github.com/alchemiststudiosDOTai/tunacode/commit/cdaec03)
- [GitHub: Commit f59dedd (manual JSON update)](https://github.com/alchemiststudiosDOTai/tunacode/commit/f59dedd)
