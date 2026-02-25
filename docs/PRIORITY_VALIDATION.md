# Priority Validation Feature

## Problem
The `priority` array in `config.yml` can become empty or corrupted, causing routers to not appear in the UI or execute in the wrong order.

## Solution
Automatic validation and reconstruction of priority arrays on both load and save operations.

## How It Works

### On Load
When the config is loaded, `validateAndFixPriorities()` checks:
1. If `priority` is not an array, it creates an empty array
2. Finds all router names (excluding the 'priority' key itself)
3. Adds any missing routers to the priority array
4. Logs reconstruction to console for debugging

### On Save
Before saving, the same validation runs to ensure the config is always consistent.

## Example

**Before (corrupt config.yml):**
```yaml
routers:
  handlers:
    priority: []  # Empty!
    quick:
      enabled: true
    echo:
      enabled: true
```

**After (auto-fixed):**
```yaml
routers:
  handlers:
    priority: [quick, echo]  # Reconstructed!
    quick:
      enabled: true
    echo:
      enabled: true
```

## Console Output
When reconstruction happens, you'll see:
```
Reconstructed handlers priority: added quick, echo
```

## Test Coverage
- ✅ Reconstruct empty handlers priority
- ✅ Reconstruct empty semantic priority  
- ✅ Fix corrupt priority (null/undefined)
- ✅ Validate before save
- ✅ Preserve existing priority order

## Code Location
- Implementation: `webui/src/components/config-editor.ts` - `validateAndFixPriorities()`
- Tests: `webui/src/test/config-editor.test.ts` - "priority validation" suite
