# Plan

Answer each of these, in your own words.

- How did you break the work into sessions?
- What order did you build in, and why that order?
- What did you estimate versus what it actually took?
- What did you cut when you ran short?

## How did you break the work into sessions?

I divided the work into a few practical sessions:

1. Read the assignment carefully and break the requirements into backend, frontend,
   database, documentation, and deployment tasks.
2. Build the database models and backend APIs first.
3. Add authentication and server-side role enforcement.
4. Implement vehicles, service records, assignments, lifecycle rules, due/overdue logic,
   timeline events, CSV import/export, dashboard and alerts.
5. Build the React interface around the working API and refine the main screens.
6. Test the manager and technician workflows and fix issues found during testing.
7. Deploy the backend and frontend, then debug production-specific issues.
8. Complete the required documentation and submission file.

## What order did you build in, and why that order?

I built the backend/data layer first because the frontend depends on the API contracts,
database relationships, authorization rules and lifecycle logic.

After the core backend worked, I built the main frontend workflows. I then added the
secondary features such as filtering, sorting, dashboard presentation, alerts and
CSV interactions.

Deployment came after the main application was working locally so that production
debugging was focused on deployment-specific issues rather than unfinished core
functionality.

## What did you estimate versus what it actually took?

I initially expected the implementation to be relatively straightforward once the main
data model and API structure were in place. In practice, more time was needed for
debugging the service/technician query, refining the UI, validating role-specific
behavior, and getting authentication and CSV import working correctly in the deployed
environment.

The deployment/debugging stage took longer than expected because the production
environment exposed a bcrypt compatibility issue that was not present during local
testing.

## What did you cut when you ran short?

I prioritized the assignment requirements and cut non-essential polish rather than
core functionality.

I did not build a dedicated technician-management screen or extensive automated test
coverage. I also kept some frontend/backend areas simpler than I would in a longer
production project.

The focus was to deliver the required fleet, service, authorization, reporting,
timeline, alert, CSV, documentation, and deployment functionality within the deadline.