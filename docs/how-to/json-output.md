# Use JSON output for scripting

Most codio commands accept `--json` to produce machine-readable output.

## Examples

```bash
codio list --json
codio get schema-tools --json
codio validate --json
codio vocab --json
codio discover "graphs" --json
codio study networkx --json
codio compare lib-a lib-b --json
```

## Pipe to jq

```bash
codio list --json | jq '.[].name'
codio discover "validation" --json | jq '.recommended_decision'
codio validate --json | jq '.errors'
```

## Use in scripts

```bash
if codio validate --json | jq -e '.valid' > /dev/null; then
  echo "Registry is consistent"
else
  echo "Registry has errors"
  codio validate --json | jq '.errors[]'
fi
```
