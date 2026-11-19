# Changelog

## 0.2.0 (2026-11-19)

### Added
- `codio mirror sync`: restores gitignored library mirrors at the commit pinned in `repos.yml` (new `ref` field). It clones missing mirrors at that ref, pins mirrors that have none and reports drift; `--update` pulls and re-pins. `codio sync` is now its alias and also clones what is missing. `codio clone` records the ref. Mirrors committed in the parent repo as submodules are flagged with a warning.
- Docs: how to restore mirrors and move submodule mirrors out of git.

## 0.1.1

Earlier releases (0.1.0, 0.1.1); see the git history.
