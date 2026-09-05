# Schema

Answer each of these, in your own words.

- Table by table: what columns and types does each one have?
- Which relationships are one-to-many, and which are many-to-many?
- Which constraints are enforced by the database, and which by application code — and why did you draw the line there?
- What did you deliberately denormalise?
- What would break first if this had 100x the data?

# Schema

This document describes the database structure used by the application and where
data-integrity and business rules are enforced.

## users

Stores all application users. Managers and technicians share the same table and
are distinguished by their role.

| Column | Type | Purpose |
|---|---|---|
| id | INTEGER | Primary key |
| email | VARCHAR | Login email |
| password_hash | VARCHAR | Hashed password |
| role | VARCHAR/ENUM | `MANAGER` or `TECHNICIAN` |
| is_active | BOOLEAN | Whether the account can currently log in |
| created_at | TIMESTAMP | Account creation time |

The email is used to identify the account during login.

## vehicles

Stores fleet vehicles and their maintenance configuration.

| Column | Type | Purpose |
|---|---|---|
| id | INTEGER | Primary key |
| registration_number | VARCHAR | Vehicle registration number |
| make | VARCHAR | Vehicle manufacturer |
| model | VARCHAR | Vehicle model |
| current_odometer | INTEGER | Latest accepted odometer reading |
| service_date_interval_days | INTEGER | Number of days between services |
| service_mileage_interval | INTEGER | Mileage interval between services |
| last_service_date | DATE | Date of the most recently completed service |
| last_service_odometer | INTEGER | Odometer at the most recently completed service |
| service_due_since | TIMESTAMP | Tracks when the current maintenance cycle became due |
| is_archived | BOOLEAN | Whether the vehicle is archived |
| created_at | TIMESTAMP | Vehicle creation time |
| updated_at | TIMESTAMP | Last update time |

Current odometer and last-service values are kept on the vehicle because they are
frequently required for due-status calculations.

## service_records

Stores maintenance jobs for vehicles.

| Column | Type | Purpose |
|---|---|---|
| id | INTEGER | Primary key |
| vehicle_id | INTEGER | Vehicle being serviced |
| description | TEXT | Description of the required work |
| status | VARCHAR/ENUM | `DUE`, `BOOKED`, `IN_SERVICE`, or `COMPLETED` |
| scheduled_date | DATE | Planned service date |
| created_by | INTEGER | User who created the record |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |

Each service record belongs to exactly one vehicle.

## service_technicians

Association table connecting technicians to service records.

| Column | Type | Purpose |
|---|---|---|
| id | INTEGER | Primary key |
| service_id | INTEGER | Service record being assigned |
| technician_id | INTEGER | Assigned technician |
| assigned_by | INTEGER | Manager who made the assignment |
| assigned_at | TIMESTAMP | Assignment time |

This creates a many-to-many relationship between services and technicians.

A service can have multiple technicians and a technician can be assigned to multiple
services.

## odometer_readings

Stores odometer history rather than keeping only the latest reading.

| Column | Type | Purpose |
|---|---|---|
| id | INTEGER | Primary key |
| vehicle_id | INTEGER | Vehicle associated with the reading |
| reading | INTEGER | Odometer value |
| recorded_at | TIMESTAMP | Time the reading was recorded |
| recorded_by | INTEGER | User who submitted the reading |
| source | VARCHAR | Source of the reading, such as manual or CSV |

Lower readings are rejected by the application so that an odometer value cannot
move backwards.

## service_events

Stores the immutable service timeline.

| Column | Type | Purpose |
|---|---|---|
| id | INTEGER | Primary key |
| service_id | INTEGER | Related service |
| event_type | VARCHAR | Type of event |
| old_value | TEXT | Previous value when applicable |
| new_value | TEXT | New value when applicable |
| note | TEXT | Optional event note |
| actor_id | INTEGER | User who performed the action |
| created_at | TIMESTAMP | Event time |

Events are appended rather than edited or deleted so the service history remains
traceable.

## audit_events

Stores audit information for important application actions.

| Column | Type | Purpose |
|---|---|---|
| id | INTEGER | Primary key |
| actor_id | INTEGER | User responsible for the action |
| action | VARCHAR | Action being recorded |
| entity_type | VARCHAR | Type of affected entity |
| entity_id | INTEGER | Identifier of the affected entity |
| details | TEXT/JSON | Additional action details |
| created_at | TIMESTAMP | Time of the action |

## alert_dismissals

Stores manager dismissals of overdue alerts.

| Column | Type | Purpose |
|---|---|---|
| id | INTEGER | Primary key |
| vehicle_id | INTEGER | Vehicle associated with the alert |
| service_cycle_key | VARCHAR | Identifies the maintenance cycle |
| dismissed_by | INTEGER | Manager who dismissed the alert |
| dismissed_at | TIMESTAMP | Time of dismissal |

The cycle key allows an alert to reappear for a later maintenance cycle.

## Relationships

### One-to-many

- User → Service Records
- User → Odometer Readings
- User → Service Events
- Vehicle → Service Records
- Vehicle → Odometer Readings
- Vehicle → Alert Dismissals
- Service Record → Service Events

### Many-to-many

- Service Records ↔ Technicians

The `service_technicians` table represents the many-to-many relationship.

## Database constraints vs application rules

The database is responsible for basic relational integrity and data storage
constraints such as primary keys, foreign keys, required fields and uniqueness
constraints where defined.

Application code is responsible for rules that depend on the current user or
business state.

Examples include:

- Only managers can create/archive/restore vehicles.
- Only managers can create services and manage technician assignments.
- Technicians can only access services assigned to them.
- Service transitions must follow:

  `DUE → BOOKED → IN_SERVICE → COMPLETED`

- Archived vehicles cannot be used for new services.
- Odometer readings cannot decrease.
- Only managers can dismiss overdue alerts.
- CSV rows are validated individually so valid rows can still be processed when
  another row is rejected.

These rules belong in application code because they depend on the authenticated
user and current state rather than being simple static database constraints.

## Deliberate denormalisation

The `vehicles` table stores:

- `current_odometer`
- `last_service_date`
- `last_service_odometer`
- `service_due_since`

Some of these values could be derived from historical records, but storing the
current values directly makes due calculations and common vehicle queries faster
and simpler.

The historical service and odometer records are still retained.

## What would break first at 100x the data?

The first likely bottlenecks would be service-list and dashboard queries because
they involve filtering, sorting, pagination and joins across multiple tables.

The append-only `service_events` table would also grow quickly.

At larger scale, I would add targeted indexes to frequently filtered/sorted
columns, profile the dashboard and service queries, and consider partitioning or
archiving older event data if measurement showed it was necessary.

Pagination, filtering and sorting would remain server-side so the frontend would
not need to load the entire history.