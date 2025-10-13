# Task T001: Fix Remaining CodeRabbit UI Polish Issues

**Feature**: Frontend Code Quality  
**Phase**: Polish  
**Parallel**: Yes (independent of other tasks)  
**Estimated Effort**: 1 hour  
**Prerequisites**: None (optional enhancement)

---

## Task Description

Fix the remaining 5 CodeRabbit issues in the citadel-shield-ui frontend. These are minor UI polish items that don't block deployment but improve code quality and user experience.

---

## Execution Flow

```
1. Fix use-roving.ts global keyboard listener (20 min)
   → Scope arrow key handling to component
   → Remove document.addEventListener
   → Return onKeyDown handler from hook
2. Fix MessagePopover hardcoded ID (10 min)
   → Use React's useId() for unique IDs
   → Update aria-labelledby reference
3. Fix use-focus-trap unstable dependency (10 min)
   → Stabilize opts?.onEscape with ref
   → Prevent unnecessary re-renders
4. Fix Admin.tsx onClick overwrite (15 min)
   → Preserve original onClick from getTabProps
   → Add useEffect for inkbar sync
5. Validate all fixes (5 min)
   → Run tsc --noEmit
   → Run eslint
   → Test locally
```

---

## Issues to Fix

### Issue #6: Global Arrow Key Hijacking (HIGH)

**File**: `src/hooks/use-roving.ts` (lines 8-22)  
**Problem**: Hook installs capturing keydown listener on document, hijacks arrow keys everywhere  
**Impact**: Arrow keys don't work properly in other parts of the app

**Current Code**:
```typescript
useEffect(() => {
  const onKey = (e: KeyboardEvent) => {
    const horiz = e.key === "ArrowRight" || e.key === "ArrowLeft";
    const vert  = e.key === "ArrowDown" || e.key === "ArrowUp";
    if (!horiz && !vert) return;
    e.preventDefault(); // Prevents ALL arrow keys everywhere!
    setIndex((i) => {
      const next = (i + (e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : -1) + count) % count;
      refs.current[next]?.focus();
      return next;
    });
  };
  document.addEventListener("keydown", onKey, true);
  return () => document.removeEventListener("keydown", onKey, true);
}, [count]);
```

**Fix Required**:
```typescript
import { useCallback } from 'react';

export function useRoving(count: number, initial = 0) {
  const [index, setIndex] = useState(initial);
  const refs = useRef<HTMLElement[]>([]);

  const onKeyDown = useCallback((e: React.KeyboardEvent) => {
    // Only handle if event is on a tab element
    const horiz = e.key === "ArrowRight" || e.key === "ArrowLeft";
    const vert  = e.key === "ArrowDown" || e.key === "ArrowUp";
    if (!horiz && !vert) return;
    
    e.preventDefault(); // Only prevents for this component
    setIndex((i) => {
      const next = (i + (e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : -1) + count) % count;
      refs.current[next]?.focus();
      return next;
    });
  }, [count]);

  const getTabProps = (i: number) => ({
    ref: (el: HTMLElement | null) => (refs.current[i] = el!),
    tabIndex: i === index ? 0 : -1,
    role: "tab",
    "aria-selected": i === index,
    onClick: () => setIndex(i),
    onKeyDown, // Attach to component, not document
  });

  return { index, setIndex, getTabProps };
}
```

---

### Issue #7: Hardcoded ID Causing Duplicates (MEDIUM)

**File**: `src/components/fiori/MessagePopover.tsx` (lines 23-27)  
**Problem**: Hardcoded `id="mp-title"` causes duplicate IDs when multiple popovers render  
**Impact**: Accessibility issues, invalid HTML

**Fix Required**:
```typescript
import { useId } from 'react';

export function MessagePopover({ children }: { children: React.ReactNode }) {
  const titleId = useId(); // Generates unique ID like ":r1:"

  return (
    <div role="dialog" aria-labelledby={titleId}>
      <h2 id={titleId}>Messages</h2>
      {children}
    </div>
  );
}
```

---

### Issue #8: Unstable Dependency in Effect (MEDIUM)

**File**: `src/hooks/use-focus-trap.ts` (line 43)  
**Problem**: Effect depends on `opts?.onEscape` which is unstable if `opts` is recreated  
**Impact**: Unnecessary re-renders, potential memory leaks

**Fix Required**:
```typescript
export function useFocusTrap(opts?: { onEscape?: (e: KeyboardEvent) => void }) {
  const onEscapeRef = useRef(opts?.onEscape);
  
  // Update ref when callback changes
  useEffect(() => {
    onEscapeRef.current = opts?.onEscape;
  }, [opts?.onEscape]);

  // Effect no longer depends on opts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onEscapeRef.current?.(e);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []); // Stable dependency array
}
```

---

### Issue #13: Overwriting Tab Props onClick (MEDIUM)

**File**: `src/pages/Admin.tsx` (lines 74-82)  
**Problem**: Button spreads `...getTabProps(idx)` then overwrites `onClick`, losing roving hook's handler  
**Impact**: Keyboard navigation (arrow keys) don't update inkbar

**Current Code**:
```typescript
<button
  {...getTabProps(idx)}
  onClick={() => {
    setActiveTab(idx);
    update();
  }}
>
  Tab {idx}
</button>
```

**Fix Required**:
```typescript
{tabs.map((tab, idx) => {
  const tabProps = getTabProps(idx);
  const originalOnClick = tabProps.onClick;
  
  return (
    <button
      key={idx}
      {...tabProps}
      onClick={(e) => {
        originalOnClick?.(e); // Call roving hook's handler first
        setActiveTab(idx);
        update();
      }}
    >
      {tab}
    </button>
  );
})}

// Also add useEffect to sync inkbar on keyboard navigation:
useEffect(() => {
  update(); // Update inkbar when roving index changes
}, [rovingIndex, update]);
```

---

## Acceptance Criteria

- [ ] All 5 CodeRabbit issues resolved
- [ ] TypeScript compilation passes (no errors)
- [ ] ESLint passes (no warnings)
- [ ] Arrow keys work properly in tabs
- [ ] Multiple MessagePopovers can render without ID conflicts
- [ ] Focus trap doesn't cause unnecessary re-renders
- [ ] Admin page inkbar follows keyboard navigation

---

## Testing Procedure

### 1. TypeScript Validation
```bash
cd /home/agent0/citadel-shield-ui
npm run type-check  # or tsc --noEmit
```

**Expected**: No type errors

### 2. Linting
```bash
npm run lint
```

**Expected**: No errors or warnings

### 3. Manual Testing
```bash
npm run dev
```

**Test Cases**:
- Navigate tabs with arrow keys → inkbar should follow
- Open multiple MessagePopovers → no console errors about duplicate IDs
- Press Escape in focus trap → should trigger callback
- Use arrow keys in tab list → should only affect tabs, not other elements

---

## Deliverables

- ✅ Fixed `src/hooks/use-roving.ts`
- ✅ Fixed `src/components/fiori/MessagePopover.tsx`
- ✅ Fixed `src/hooks/use-focus-trap.ts`
- ✅ Fixed `src/pages/Admin.tsx`
- ✅ All TypeScript errors resolved
- ✅ All ESLint warnings resolved
- ✅ Changes committed to feature-1 branch
- ✅ Changes pushed to GitHub

---

## Dependencies

**Prerequisites**: None (can be done anytime)  
**Blocks**: None (doesn't block deployment)  
**Parallel**: Can run alongside deployment/testing

---

## Next Steps

After completion:
1. Commit fixes to feature-1 branch
2. Push to GitHub
3. (Optional) Create PR to merge into main
4. Continue with T002 (Frontend Testing)

---

**Effort**: 1 hour  
**Priority**: Medium (UI polish, not blocking)  
**Status**: Ready to execute

