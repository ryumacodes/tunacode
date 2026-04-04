# Documentation Work

Documentation is a first-class citizen in this repository.

Use this workflow when creating, updating, reorganizing, or correcting
documentation. Documentation changes are not secondary cleanup. They are part
of the product and should be handled with the same care as code changes.

## Intent

The purpose of documentation work is to keep the repository legible, truthful,
and usable for future development. Good docs reduce wrong assumptions, make
architecture easier to follow, and prevent drift between what the repo says and
what the repo does.

## Working Rules

- Treat documentation as real deliverable work, not as an afterthought.
- Prefer direct, operational language over vague explanation.
- Keep docs aligned with actual repository behavior, commands, and structure.
- Update docs when behavior, workflows, or expectations change.
- Do not leave known mismatches between implementation and documentation.

## Frontmatter Requirements

Anything under `/docs` should include frontmatter at the top of the file.

At minimum, documentation should declare:

- `title`
- `when_to_read`
- `summary`

`when_to_read` should tell the reader when this document is useful. `summary`
should explain what the document covers and why it matters. This metadata is
part of the document contract, not optional decoration.

## Scope

Documentation work includes:

- workflow documentation
- architecture and module maps
- setup and run instructions
- developer guidance
- harness and validation guidance
- correction of stale, misleading, or incomplete docs

## Verification

Documentation must be verified against reality.

Do not treat a docs change as complete just because the prose sounds good.
Check that referenced commands, file names, workflows, and expectations match
the repository as it exists now.

Preferred verification includes:

- confirming referenced file names and paths exist
- confirming referenced commands are the correct commands for the repo
- checking that workflow descriptions match actual team conventions
- updating cross-references when documents move or are renamed

## Done Criteria

Documentation work is ready when all of the following are true:

- the document is clear and specific
- the guidance matches current repository reality
- file references, commands, and workflow names are correct
- related docs remain consistent with the change
- the change reduces confusion instead of adding parallel or conflicting
  guidance
