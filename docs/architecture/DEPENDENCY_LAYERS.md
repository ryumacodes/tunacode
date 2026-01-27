# Dependency Layers

Generated: 2026-01-27

## LSP Feedback Collected

- **LSP modules detected - beta feature feedback needed**
  - Modules: 3 total
  - Details: tunacode.tools.lsp.client, tunacode.tools.lsp.servers, tunacode.tools.lsp

## Layer Order (topological)

```
ui
core
infrastructure
tools
utils
configuration
constants
exceptions
types
```

## Layer-to-Layer Imports

| From | To | Count |
|------|----|-------|
| configuration | constants | 6 |
| configuration | exceptions | 1 |
| configuration | types | 4 |
| core | configuration | 14 |
| core | constants | 5 |
| core | exceptions | 4 |
| core | infrastructure | 1 |
| core | tools | 17 |
| core | types | 23 |
| exceptions | types | 1 |
| infrastructure | configuration | 1 |
| infrastructure | constants | 1 |
| tools | configuration | 6 |
| tools | constants | 3 |
| tools | exceptions | 4 |
| tools | types | 1 |
| tools | utils | 2 |
| ui | core | 49 |
| utils | configuration | 2 |
| utils | types | 1 |
