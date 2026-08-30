# Schema

Answer each of these, in your own words.

- Table by table: what columns and types does each one have?
- Which relationships are one-to-many, and which are many-to-many?
- Which constraints are enforced by the database, and which by application code — and why did you draw the line there?
- What did you deliberately denormalise?
- What would break first if this had 100x the data?

### users

This table stores everyone who can log in to the application. I kept managers
and technicians in the same table because they are both users; their role
determines what they are allowed to do.

| Column | Type | Why it is needed |
|---|---|---|
| id | UUID | Unique ID for each user |
| name | VARCHAR | Name shown in the application |
| email | VARCHAR | Used for login; should be unique |
| password_hash | VARCHAR | Stores the hashed password instead of the actual password |
| role | ENUM | Tells us whether the user is a manager or technician |
| created_at | TIMESTAMP | Records when the user account was created |

### vehicles

This table stores the vehicles in the fleet. I am also keeping the current
odometer value and the last completed service details here because they are
needed frequently when checking whether a vehicle is due for maintenance.

| Column | Type | Why it is needed |
|---|---|---|
| id | UUID | Unique ID for each vehicle |
| registration_number | VARCHAR | Vehicle registration number; should be unique |
| make | VARCHAR | Vehicle manufacturer |
| model | VARCHAR | Vehicle model |
| current_odometer | INTEGER | Latest accepted odometer reading |
| service_date_interval_days | INTEGER | Number of days after which the vehicle needs servicing |
| service_mileage_interval | INTEGER | Number of kilometres after which the vehicle needs servicing |
| last_service_date | DATE | Date of the most recently completed service |
| last_service_odometer | INTEGER | Odometer reading when the last service was completed |
| is_archived | BOOLEAN | Shows whether the vehicle is archived |
| created_at | TIMESTAMP | When the vehicle was added |
| updated_at | TIMESTAMP | When the vehicle was last updated |

### service_records

This table stores each maintenance job. A service belongs to one vehicle,
and its status tells us where the job currently is in the service process.

| Column | Type | Why it is needed |
|---|---|---|
| id | UUID | Unique ID for each service record |
| vehicle_id | UUID | Connects the service to the vehicle being serviced |
| description | TEXT | Describes what needs to be done |
| status | ENUM | Current status: Due, Booked, In Service or Completed |
| scheduled_date | DATE | Date on which the service is planned |
| created_by | UUID | Stores which user created the service record |
| created_at | TIMESTAMP | When the service record was created |
| updated_at | TIMESTAMP | When the service record was last changed |

### service_technicians

This table connects services with the technicians working on them. I used a
separate table because one service can have multiple technicians and one
technician can work on multiple services.

| Column | Type | Why it is needed |
|---|---|---|
| service_id | UUID | Identifies the service being worked on |
| technician_id | UUID | Identifies the technician assigned to it |
| assigned_by | UUID | Records who made the assignment |
| assigned_at | TIMESTAMP | Records when the technician was assigned |

The combination of `service_id` and `technician_id` should be unique so that
the same technician cannot be assigned to the same service twice.

### service_events

This table keeps a record of important actions that happen to a service.
Instead of changing old events, I will add a new event whenever something
important happens, so the service history can be traced over time.

| Column | Type | Why it is needed |
|---|---|---|
| id | UUID | Unique ID for each event |
| service_id | UUID | Identifies which service the event belongs to |
| event_type | VARCHAR | Describes what happened, such as status change or technician assignment |
| old_value | TEXT | Stores the previous value when something changes |
| new_value | TEXT | Stores the new value when something changes |
| note | TEXT | Additional information about the event |
| actor_id | UUID | Identifies the user who performed the action |
| created_at | TIMESTAMP | Records when the event happened |

### odometer_readings

This table stores the odometer readings submitted for each vehicle. I am
keeping the readings as history instead of only updating the current value
on the vehicle, so we can track when and how the odometer changed.

| Column | Type | Why it is needed |
|---|---|---|
| id | UUID | Unique ID for each reading |
| vehicle_id | UUID | Identifies which vehicle the reading belongs to |
| reading | INTEGER | The odometer value that was submitted |
| recorded_at | TIMESTAMP | When the reading was recorded |
| recorded_by | UUID | Identifies the user who submitted the reading |
| source | VARCHAR | Shows whether the reading came from manual entry or CSV upload |

### alert_dismissals

This table stores when a manager dismisses an overdue alert. The dismissal
is linked to a particular maintenance cycle instead of permanently marking
the vehicle as dismissed.

| Column | Type | Why it is needed |
|---|---|---|
| id | UUID | Unique ID for each dismissal |
| vehicle_id | UUID | Identifies the vehicle with the overdue alert |
| service_cycle_key | VARCHAR | Identifies the maintenance cycle for which the alert was dismissed |
| dismissed_by | UUID | Identifies the manager who dismissed the alert |
| dismissed_at | TIMESTAMP | Records when the alert was dismissed |

## Relationships

### One-to-many relationships

- User → Service Records: One user can create multiple service records.
- User → Service Events: One user can perform multiple actions, which are recorded as events.
- User → Odometer Readings: One user can submit multiple odometer readings.
- Vehicle → Service Records: One vehicle can have many different service records over time.
- Vehicle → Odometer Readings: One vehicle can have multiple odometer readings over time.
- Vehicle → Alert Dismissals: One vehicle can have dismissals for different maintenance cycles.
- Service Record → Service Events: A single service can have multiple events during its lifecycle.

### Many-to-many relationship

- Service Records ↔ Technicians: A single service can be assigned to multiple technicians, while one technician can be assigned to multiple services. The service_technicians table is used to connect the two.

## Constraints: Database vs Application

I am keeping basic data integrity rules in the database and business rules
in the application code. The database should act as the final safeguard
against invalid data, while the application handles rules that depend on
the user's role or the current business workflow.

### Database constraints

- User email must be unique.
- Vehicle registration number must be unique.
- Required fields should not be NULL.
- Foreign keys should make sure that referenced users, vehicles and services exist.
- The combination of service_id and technician_id should be unique so that
  the same technician cannot be assigned to the same service twice.
- Stored role and status values should only contain allowed values.

I chose the database for these rules because they should remain true no
matter where the data is coming from.

### Application constraints

- Only managers can archive or restore vehicles.
- Only managers can create, edit or delete service records.
- Technicians can only access services assigned to them.
- Service status changes must follow the allowed order:
  Due → Booked → In Service → Completed.
- Archived vehicles cannot be used for new services.
- Only managers can dismiss overdue alerts.
- Odometer CSV rows are validated individually so that valid rows can still
  be processed when other rows fail.

I put these rules in the application because they depend on the current
user, the current state of the system, or the business workflow.

Important operations that update multiple pieces of data will be performed
inside database transactions so that either all related changes succeed or
none of them are saved.

## Deliberate Denormalisation

I am keeping current_odometer, last_service_date and last_service_odometer
on the vehicles table even though some of these values can be obtained from
the historical records.

These values are used frequently when checking maintenance due status and
displaying vehicle information. Keeping the latest values directly on the
vehicle avoids repeatedly looking through the historical records.

The historical odometer readings and service records are still kept, so the
denormalisation is only for frequently accessed current values and does not
remove the history.

## What Would Break First at 100x the Data?

The services page and dashboard queries would probably be the first areas
where performance becomes an issue. They involve searching, filtering,
sorting, pagination and joins between several tables.

I would handle this by adding indexes to the columns that are frequently
searched or filtered and by keeping pagination, filtering and sorting on
the server.

The frontend should only receive the records needed for the current page
instead of loading the complete service history.

The service_events table would also grow quickly because it is append-only.
If the system became much larger, I would consider archiving or partitioning
old events after checking where the actual performance bottleneck is.

I would not add these optimisations prematurely because the assignment has a
small initial dataset and unnecessary complexity would make the application
harder to maintain.