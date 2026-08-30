# Architecture

Answer each of these, in your own words, once the system has taken real shape.

- What are the moving pieces, and how do they talk to each other?
- Where does each piece run?
- What is the request path for one representative user action, end to end?
- What did you decide *not* to build, and why?

## Moving Pieces

The application has three main parts: a React frontend, a FastAPI backend
and a PostgreSQL database.

The React frontend is responsible for displaying the application and taking
input from the user. It communicates with the backend using HTTP requests
and JSON.

The FastAPI backend handles authentication, role checks, validation and the
main business logic. It receives requests from React and uses SQLAlchemy to
read and update the PostgreSQL database.

PostgreSQL stores the application's permanent data, including users,
vehicles, service records, technician assignments, odometer readings and
audit events.

The basic communication flow is:

React → FastAPI → SQLAlchemy → PostgreSQL

The response then travels back through the same layers to update the
frontend.

## Where Each Piece Runs

During development, the frontend and backend will run locally on my
computer, while PostgreSQL can run locally or through a development
database.

For deployment, I plan to host the React frontend on Vercel, the FastAPI
backend on Render and PostgreSQL on Supabase.

The browser communicates with the FastAPI backend over HTTP. The backend
is the only application component that communicates with PostgreSQL. The
frontend does not connect directly to the database.

## Representative Request Path

A representative action is a manager creating a new vehicle.

1. The manager fills in the vehicle details in the React frontend and clicks
   Save.
2. React sends a POST request containing the vehicle data to the FastAPI API.
3. FastAPI verifies the user's authentication and checks that the user has
   the MANAGER role.
4. FastAPI validates the submitted vehicle data and applies the relevant
   business rules.
5. SQLAlchemy is used to create the database record in PostgreSQL.
6. PostgreSQL saves the vehicle and returns the result.
7. FastAPI sends the saved vehicle back as a JSON response.
8. React receives the response and updates the vehicle list shown to the
   manager.

The frontend is responsible for the user interface, but authentication and
authorization are enforced by the backend so they cannot be bypassed by
modifying the frontend.

## What I Decided Not to Build

I decided not to add features such as fuel tracking, GPS tracking, parts
inventory, driver management or a separate mobile application.

These could be useful in a larger fleet management system,  but they are outside the requirements given for this project.. Adding them would increase the
scope and take time away from the core maintenance workflow.

I also decided not to add an AI-based maintenance prediction feature. The
project can already determine whether a vehicle is due or overdue using its
date and mileage intervals, so adding prediction would not solve a required
problem.

My priority is to make the required workflows reliable, secure and easy to
understand rather than adding features just to increase the feature count.