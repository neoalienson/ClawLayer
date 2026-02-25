# Config Structure Change

## Summary

Changed the YAML configuration structure so `handlers` is at the root level while `semantic` routers remain under `routers`.

## New Structure

```yaml
# handlers at root level
handlers:
  priority: [quick, echo, command]
  quick:
    enabled: true
    patterns: [...]
  echo:
    enabled: true
  command:
    enabled: true
    prefix: 'run:'

# semantic routers under routers
routers:
  semantic:
    priority: [greeting, summarize]
    greeting:
      enabled: true
      stages: [...]
      utterances: [...]
```

## Old Structure (Still Supported)

```yaml
routers:
  handlers:
    priority: [...]
    quick: {...}
  semantic:
    priority: [...]
    greeting: {...}
```

## Changes Made

### Backend (Python)
- **config.py**: Updated parser to check root level `handlers` first, fallback to `routers.handlers` for backward compatibility

### Frontend (TypeScript)
- **config-validator.ts**: Updated to validate `handlers` at root and `semantic` under `routers`
- **handlers-tab.ts**: Updated to read from `config.handlers` instead of `config.routers.handlers`
- **config-editor.ts**: Updated all handler methods to use root-level structure

### Config File
- **config.yml**: Restructured to new format

## Backward Compatibility

The Python config parser supports both structures:
- New: `handlers` at root level
- Legacy: `routers.handlers`

## Test Results

All 49 tests pass ✓

## Benefits

- Clearer separation: handlers are fast/simple, semantic routers are complex
- More intuitive structure
- Easier to understand config hierarchy
