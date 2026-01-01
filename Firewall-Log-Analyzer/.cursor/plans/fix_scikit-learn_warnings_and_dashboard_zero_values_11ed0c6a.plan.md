---
name: Fix Scikit-Learn Warnings and Dashboard Zero Values
overview: "Fix two issues: (1) Suppress scikit-learn version mismatch warnings in training scripts by adding warning filter to feature_normalizer.py, and (2) Fix dashboard showing zeros by ensuring proper date range calculation for 24h statistics and using timezone-aware datetime."
todos:
  - id: fix-sklearn-warnings
    content: Add warning filter to feature_normalizer.py to suppress scikit-learn version mismatch warnings in training scripts
    status: pending
  - id: fix-datetime-deprecation
    content: Replace datetime.utcnow() with datetime.now(timezone.utc) in alert_service.py
    status: pending
  - id: fix-dashboard-daterange
    content: Fix 24h statistics calculation in dashboard.py to use actual current time instead of alert bucket end time
    status: pending
  - id: test-warnings
    content: Test training scripts to verify warnings are suppressed
    status: pending
    dependencies:
      - fix-sklearn-warnings
  - id: test-dashboard
    content: Test dashboard API and frontend to verify values are displayed correctly
    status: pending
    dependencies:
      - fix-datetime-deprecation
      - fix-dashboard-daterange
---

#Fix Scikit-Learn Warnings and Dashboard Zero Values

## Issues Identified

1. **Scikit-learn warnings in training scripts**: Warnings appear when running training scripts because `FeatureNormalizer.load()` is called directly, bypassing the warning filter in `model_loader.py`.
2. **Dashboard showing zeros**: Dashboard cards show "0" for threat counts and total logs because:

- Date range calculation uses `bucket_end` (floored to 5-minute boundaries) instead of current time
- `datetime.utcnow()` is used in `alert_service.py` (deprecated, should use timezone-aware)
- The 24h statistics query may not match actual last 24 hours from "now"

## Implementation Plan

### 1. Fix Scikit-Learn Warnings

**File**: `ml_engine/features/feature_normalizer.py`Add warning suppression at the top of the file (after imports, before class definition):

```python
import warnings

# Suppress scikit-learn version mismatch warnings (models trained with 1.5.2, runtime may be 1.8.0+)
# This is safe as scikit-learn maintains backward compatibility for model loading
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
```

**Location**: After line 26 (after `logger = logging.getLogger(__name__)`)**Why**: This ensures warnings are suppressed when `FeatureNormalizer.load()` is called directly by training scripts, not just when loaded via `model_loader.py`.

### 2. Fix Dashboard Zero Values

**File**: `backend/app/services/alert_service.py`**Change 1**: Replace deprecated `datetime.utcnow()` with timezone-aware datetime:

- Line 62: `now = datetime.utcnow()` → `now = datetime.now(timezone.utc)`
- Line 152: `datetime.utcnow()` → `datetime.now(timezone.utc)`
- Line 176: `now = datetime.utcnow()` → `now = datetime.now(timezone.utc)`

**Change 2**: Add timezone import at top:

- Add `timezone` to imports: `from datetime import datetime, timedelta, timezone`

**File**: `backend/app/routes/dashboard.py`**Change**: Fix 24h statistics to use actual last 24 hours from current time, not from alert bucket:

```python
# Get 24h statistics - use actual last 24 hours from now, not from alert bucket
now = datetime.now(timezone.utc)
start_24h = now - timedelta(hours=24)
query_24h = {
    "timestamp": {
        "$gte": start_24h,
        "$lte": now
    }
}
```

**Location**: Replace lines 99-105 with the above code.**Why**: The alert bucket's `end_date` is floored to 5-minute boundaries, which means "last 24 hours" could be from 24h ago to 5 minutes ago, missing recent logs. Using actual current time ensures accurate 24h statistics.

### 3. Verify Data Flow

**Check**: Ensure the frontend correctly displays the data:

- `frontend/src/pages/Dashboard.jsx` already handles null/undefined values with `|| 0` fallbacks (lines 170, 221, etc.)
- The issue is likely backend returning zeros due to date range mismatch

## Testing

1. **Scikit-learn warnings**: Run training scripts and verify no warnings appear:
   ```bash
               cd ml_engine
               PYTHONPATH=.. python3 -m ml_engine.training.train_anomaly_detector
   ```




2. **Dashboard values**: 

- Check if logs exist in database for last 24 hours
- Verify API response: `GET /api/dashboard/summary` should show correct `total_logs_24h`
- Check browser console for API errors
- Verify threat counts match actual detections

## Files to Modify

1. `ml_engine/features/feature_normalizer.py` - Add warning filter
2. `backend/app/services/alert_service.py` - Fix datetime.utcnow() deprecation
3. `backend/app/routes/dashboard.py` - Fix 24h statistics date range