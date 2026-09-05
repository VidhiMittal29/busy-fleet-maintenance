# Submission

Fill this in and commit it. This is the first file we open.

## Links

-  **GitHub repository:** https://github.com/VidhiMittal29/busy-fleet-maintenance
- **Live application:** https://busy-fleet-maintenance.vercel.app

## Notes for the reviewer

<Anything we should know before opening the link — e.g. your host sleeps when idle and the first
request can take up to a minute.>

The frontend is hosted on Vercel and the backend is hosted on Render's free tier.

The Render backend may sleep after a period of inactivity, so the first request after idle time may take a little longer while the service wakes up.

Demo data is already seeded in the database.

## Demo credentials


| Role       | Email                    | Password    |
|------------|-------|------------------|-------------|
| Manager    | manager@busyfleet.com    | Manager@123 |
| Technician | technician@busyfleet.com | Tech@123    |


## Stack

| Layer    | What you used         | Why                                                                       |
|----------|-----------------------|---------------------------------------------------------------------------|
| Frontend | React + Vite          | Fast, lightweight SPA for the fleet management UI                         |
| Backend  | FastAPI + SQLAlchemy  | REST API with server-side validation, role enforcement and business logic |
| Database | PostgreSQL (Supabase) | Managed PostgreSQL database with persistent cloud storage                 |
| Hosting  | Vercel + Render       | Free-tier deployment for frontend and backend                             |
## Goal checklist

Mark each honestly. Partial is fine — say what is partial.


| # | Goal                                                                   | Status| Notes                                                                 |
|---|--------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| 1 | Authentication, Manager/Technician roles and server-side authorization | Done | Login and role-based access are implemented. Manager-only actions are enforced on the backend. |
| 2 | Vehicle management and service interval configuration                  | Done | Vehicles can be created, edited, archived/restored and configured with date/mileage service intervals. |
| 3 | Service records and technician assignment                              | Done | Managers can create services and assign multiple technicians. Assigned technicians can view/update their services. |
| 4 | Service lifecycle and due/overdue logic                                | Done | Due → Booked → In Service → Completed is enforced server-side. Completion resets service counters. |
| 5 | Server-side search, filtering, sorting and pagination                  | Done | Service records support search, vehicle/status/technician filters, sorting, pagination and total counts. |
| 6 | Odometer CSV import and service-history export                         | Done | Bulk odometer import provides per-row results and rejects lower readings. Service history can be exported as CSV. |
| 7 | Dashboard and fleet reporting                                          | Done | Dashboard includes due, in-service, completed-this-week and overdue metrics, breakdowns and completion trend chart. |
| 8 | Immutable service timeline and notes                                   | Done | Service events and notes are stored as an immutable timeline. |
| 9 | Overdue alerts and dismissal                                           | Done | Overdue alerts are shown in the alert area/navigation and can be dismissed by managers. |
| 10 | Documentation, deployment and reproducible demo                       | Done | Architecture, schema, plan, decisions and AI-prompt documentation are included. The application is deployed with demo credentials provided above. |


## How much time did you actually spend?
Approximately 12 hours, including implementation, debugging, testing, documentation and deployment.

## What would you do next, with another 12 hours?
I would add a more comprehensive automated test suite, especially for role-based authorization and service-state transitions. I would also improve production observability/error reporting and add a dedicated technician-management interface for creating and managing technician accounts.

## What are you least happy with in this codebase, and why?
The application was built under a tight deadline, so some frontend components and backend logic could be refactored further for cleaner separation of concerns and better reuse. I would also add more automated coverage around edge cases such as invalid lifecycle transitions, CSV validation failures and overdue calculations.