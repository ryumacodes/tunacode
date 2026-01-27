# Dependency Layers

Generated: 2026-01-27

## Layer Order (topological)

```
ui
core
infrastructure
tools
lsp
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
| core | tools | 18 |
| core | types | 24 |
| exceptions | types | 1 |
| infrastructure | configuration | 1 |
| infrastructure | constants | 1 |
| lsp | utils | 1 |
| tools | configuration | 4 |
| tools | constants | 3 |
| tools | exceptions | 4 |
| tools | lsp | 1 |
| tools | types | 2 |
| tools | utils | 1 |
| ui | core | 51 |
| utils | configuration | 2 |
| utils | types | 1 |
