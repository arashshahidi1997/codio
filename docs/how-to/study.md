# Study and compare libraries

## Structured analysis of a single library

```bash
codio study mne-python
```

Returns strengths, caveats, entry points, and integration guidance derived from registry metadata.

## Compare multiple libraries

```bash
codio compare mne-python scipy-signal --query "EEG filtering"
```

Codio compares shared and distinguishing capabilities across the named libraries and provides a recommendation.

## When to study vs. discover

- Use `codio discover` when you have a problem and want to find candidate libraries.
- Use `codio study` when you already know a library name and want structured analysis.
- Use `codio compare` when choosing between known alternatives.

## Write a curated note after study

If the study reveals important context, capture it as a curated note:

```
docs/reference/codelib/libraries/<library-name>.md
```

Update the profile to point to it:

```yaml
profiles:
  mne-python:
    curated_note: docs/reference/codelib/libraries/mne-python.md
```
