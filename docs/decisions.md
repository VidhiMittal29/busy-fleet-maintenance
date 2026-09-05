# Decisions

Log the decisions that actually shaped this codebase — the ones where a real alternative existed and
you picked one. At least five entries. For each: what you chose, what you rejected, and why. At least
one entry must be a decision you later reversed — say what changed your mind. It can be any entry
below, not necessarily the last one; add a **Later reversed:** line to whichever one it is.


## Decision 1

- **Chose:** FastAPI + SQLAlchemy + PostgreSQL for the backend and database.
- **Rejected:** Building the application entirely on the frontend or using a simpler
  in-memory/local database.
- **Why:** The assignment requires server-side authorization, validation, persistent
  fleet/service history, filtering, pagination, and relational data. A relational
  backend was a better fit.

## Decision 2

- **Chose:** JWT-based authentication with Manager and Technician roles enforced on
  the server.
- **Rejected:** Relying only on frontend route/button restrictions.
- **Why:** The assignment explicitly requires server-side enforcement, so hiding
  controls in the UI alone would not be sufficient.

## Decision 3

- **Chose:** Store service events/timeline entries as separate immutable records.
- **Rejected:** Keeping only the latest service status and overwriting previous changes.
- **Why:** The assignment requires an immutable timeline showing creation, status changes,
  assignment changes, and notes.

## Decision 4

- **Chose:** Determine whether a vehicle is due when either its date interval or mileage
  interval is reached.
- **Rejected:** Requiring both conditions to be reached.
- **Why:** The assignment states that a service becomes due when either interval is reached.

## Decision 5

- **Chose:** Implement service-record search, filtering, sorting and pagination on the
  backend.
- **Rejected:** Loading the entire service list into React and filtering/sorting it only
  in the browser.
- **Why:** The assignment specifically requires these operations to be server-side and
  also requires total counts for pagination.

## Decision 6

- **Chose:** Support multiple technicians per service through a service-technician
  association table.
- **Rejected:** Allowing only one technician field on a service record.
- **Why:** The assignment allows multiple technicians to be assigned to the same service
  and requires managers to control those assignments.

## Decision 7

- **Chose:** Use CSV bulk import for odometer readings with per-row success/rejection
  results.
- **Rejected:** Rejecting the complete file when one row is invalid.
- **Why:** The assignment explicitly requires valid rows to still be applied when other
  rows are rejected.

## Decision 8

- **Chose:** Deploy the frontend on Vercel and backend on Render, using Supabase
  PostgreSQL for the database.
- **Rejected:** Keeping the application entirely local for submission.
- **Why:** The assignment requires a live URL and a publicly accessible demo. These
  services provided a practical free-tier deployment path.

## Decision 9

- **Chose:** Initially use Passlib's bcrypt integration for password hashing.
- **Rejected initially:** Direct use of the bcrypt library.
- **Why:** Passlib provided a conventional password-hashing abstraction and was simple
  to integrate initially.
- **Later reversed:** After deployment, login returned HTTP 500 on Render. The server
  traceback showed the failure inside the Passlib bcrypt backend under the deployed
  Python environment. I replaced the Passlib verification/hashing calls with direct
  bcrypt usage and verified that live login returned HTTP 200.