---
title: Models Registry Workflow
summary: How the bundled model registry is sourced, refreshed, normalized, and validated for TunaCode.
read_when: Refreshing the bundled provider/model catalog, debugging registry metadata, or changing provider API contract rules.
depends_on: []
feeds_into: [configuration]
---

# Models Registry Workflow

**Primary file:** `src/tunacode/configuration/models_registry.json`

## Purpose

TunaCode ships a bundled model registry so the app can populate provider and model metadata without requiring users to manually enter API base URLs, environment variable names, or context window details.

The runtime loader lives in `src/tunacode/configuration/models.py`, but the bundled JSON is maintained separately through `scripts/update_models_registry.sh`.

## Source of Truth

The refresh script downloads the upstream registry from `https://models.dev/api.json` and writes it to:

`src/tunacode/configuration/models_registry.json`

After download, the script applies TunaCode-specific normalization so the bundled registry matches the contracts expected by the app.

## Refresh Command

Run this from the repository root:

```bash
./scripts/update_models_registry.sh
```

The script requires:

- `curl`
- `uv`

## What the Script Changes

`scripts/update_models_registry.sh` performs four steps:

1. Download the latest registry JSON from models.dev.
2. Apply explicit `api` base URL overrides for providers with stable OpenAI-compatible endpoints.
3. Remove `api` values for deployment-specific providers where the endpoint depends on a user's account, region, or cloud resource.
4. Normalize MiniMax provider contracts by setting the expected environment variables, `alchemy_api` value, and OpenAI-compatible `api` base URL.

The script also fails fast if required providers are missing from the upstream registry. That protects TunaCode from silently shipping a broken or incomplete registry update.

## Provider Contract Rules

The update script currently maintains three contract groups:

- `API_OVERRIDES`: providers that must always carry an explicit `api` value in the bundled registry.
- `OMIT_API_PROVIDERS`: providers whose endpoint must stay unset in the bundled registry because deployment details are user-specific.
- `MINIMAX_PROVIDER_CONTRACTS`: MiniMax variants that must be normalized to TunaCode's expected env-var, `alchemy_api`, and OpenAI-compatible `api` contract.

If you add support for a new provider or change how provider routing works, update both the refresh script and any code in `src/tunacode/configuration/models.py` that relies on the resulting fields.

## When to Run It

Run the refresh script when:

- pulling in newly available providers or models from models.dev
- updating provider metadata after upstream changes
- adjusting TunaCode's provider API overrides
- changing MiniMax contract handling

## Verification

After refreshing the registry, run:

```bash
uv run python scripts/check_agents_freshness.py
```

Then inspect the updated registry and any related docs for consistency before committing.

## Related Files

- `scripts/update_models_registry.sh`
- `src/tunacode/configuration/models.py`
- `src/tunacode/configuration/models_registry.json`
- `docs/modules/configuration/configuration.md`
