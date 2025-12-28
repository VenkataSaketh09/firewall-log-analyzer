# Dashboard Page Setup Guide

## Overview
The Dashboard page has been successfully created with all required features as per the Frontend Development Guide.

## Installation

First, install all required dependencies:

```bash
cd frontend
npm install
```

## Required Dependencies

The following dependencies have been added to `package.json`:

- **react-router-dom**: For routing
- **axios**: For API calls
- **recharts**: For charts and visualizations
- **react-icons**: For icons
- **dayjs**: For date formatting
- **tailwindcss**: For styling (dev dependency)
- **postcss** & **autoprefixer**: For Tailwind CSS (dev dependencies)

## Environment Configuration

Create a `.env` file in the `frontend` directory:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Project Structure

```
frontend/src/
├── components/
│   ├── common/
│   │   ├── SummaryCard.jsx
│   │   └── AlertCard.jsx
│   ├── charts/
│   │   ├── LogsOverTimeChart.jsx
│   │   ├── SeverityDistributionChart.jsx
│   │   ├── EventTypesChart.jsx
│   │   └── ProtocolUsageChart.jsx
│   ├── tables/
│   │   └── TopIPsTable.jsx
│   └── timeline/
│       └── RecentActivityTimeline.jsx
├── pages/
│   └── Dashboard.jsx
├── services/
│   ├── api.js
│   └── dashboardService.js
├── hooks/
│   └── useAutoRefresh.js
├── utils/
│   ├── constants.js
│   ├── dateUtils.js
│   └── formatters.js
├── App.jsx
└── main.jsx
```

## Features Implemented

### ✅ Dashboard Page (`/dashboard`)

1. **Header Section**
   - System status indicator
   - Manual refresh button
   - Last updated timestamp

2. **Summary Cards**
   - Total Logs (24h)
   - Active Threats
   - Security Score
   - System Health

3. **Active Alerts List**
   - Severity-based color coding
   - Threat type badges
   - Description and timestamps

4. **Threat Summary**
   - By Type: Brute Force, DDoS, Port Scan
   - By Severity: Critical, High, Medium, Low

5. **Charts**
   - Logs Over Time (Line Chart)
   - Severity Distribution (Pie Chart)
   - Event Types (Bar Chart)
   - Protocol Usage (Bar Chart)

6. **Top Source IPs Table**
   - Top 10 IPs with statistics
   - Severity breakdown
   - Last seen timestamps

7. **Recent Activity Timeline**
   - Last 50 logs
   - Color-coded by severity
   - Relative timestamps

8. **Auto-Refresh**
   - Automatic refresh every 30 seconds
   - Manual refresh button
   - Loading states

## API Integration

The Dashboard integrates with the following backend endpoints:

- `GET /api/dashboard/summary` - Dashboard summary data
- `GET /api/logs/stats/summary` - Log statistics
- `GET /api/logs` - Recent logs for timeline

## Color Coding

Severity colors are defined in `src/utils/constants.js`:
- **CRITICAL**: Red (#dc2626)
- **HIGH**: Orange (#ea580c)
- **MEDIUM**: Yellow (#eab308)
- **LOW**: Green (#22c55e)

## Running the Application

1. Make sure the backend is running on `http://localhost:8000`
2. Start the frontend development server:

```bash
npm run dev
```

3. Navigate to `http://localhost:5173/dashboard` (or the port shown in terminal)

## Responsive Design

The Dashboard is fully responsive with:
- Mobile-friendly grid layouts
- Responsive charts
- Adaptive table layouts
- Touch-friendly buttons

## Next Steps

To complete the full application, you'll need to create:
- Logs Page (`/logs`)
- Threats Page (`/threats`)
- Reports Page (`/reports`)
- Settings Page (`/settings`) - Optional
- Navigation sidebar
- Authentication (if required)

## Notes

- All API calls are handled through the centralized `api.js` service
- Error handling is implemented with user-friendly messages
- Loading states are shown during data fetching
- The Dashboard auto-refreshes every 30 seconds
- All timestamps are formatted using dayjs with relative time support

