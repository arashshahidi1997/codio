# Search for libraries

## Basic capability search

```bash
codio discover "signal-processing"
```

Codio searches capability tags, library names, and summaries. Results are ranked by priority tier and match quality.

## Filter by language

```bash
codio discover "plotting" --language python
```

## Interpret the output

```
Query: plotting
Recommendation: wrap — Library 'matplotlib-mirror' is available with policy 'wrap'.

Candidates (2):
  matplotlib-mirror [tier1] — Capability match: plotting
  plotly-utils [tier3] — Summary match
```

The recommendation tells you the suggested implementation strategy based on the top candidate's project profile.

## Filter the library list

Before discovery, you can browse what's registered:

```bash
codio list --kind internal
codio list --priority tier1
codio list --capability graphs
codio list --language python --kind external_mirror
```

Filters can be combined. Each filter narrows the result set.

## Discovery decision outcomes

| Decision | When to use |
|----------|-------------|
| `existing` | Internal code already solves the problem |
| `wrap` | External library needs a project adapter |
| `direct` | External library can be used as-is |
| `new` | No suitable prior art exists |
