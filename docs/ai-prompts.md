# AI prompts

The prompts you actually used, in the order you used them, grouped by what you were trying to achieve. For each significant one: what you asked, what you got back, and what you had to correct.

Include at least one prompt that produced something wrong, and what you did about it.

If you did not use AI at all, say so here, and describe your process instead.


## <What you were trying to achieve>

### Prompt

### What you got

### What you corrected

# AI prompts

AI was used as a development and debugging assistant during this assignment. I reviewed,
tested, and corrected the generated suggestions rather than using AI output without verification.

## 1. Understanding the assignment

### Prompt

Help me understand the Fleet Maintenance assignment requirements and break them into
backend, frontend, database, authorization, service lifecycle, dashboard, CSV,
timeline, alerts, documentation, and deployment tasks.

### What you got

AI helped break the README requirements into smaller implementation tasks and highlighted
the importance of server-side authorization, lifecycle validation, pagination, CSV handling,
dashboard metrics, immutable events, and deployment documentation.

### What you corrected

I used the assignment README as the source of truth and implemented and tested the required
features against those requirements.

---

## 2. Debugging the service records implementation

### Prompt

Help me understand why the service records implementation is failing and explain the
error rather than just giving me replacement code.

### What you got

AI helped trace the problem to the way the service technician relationship was being joined.

### What you corrected

The query was corrected so that technician filtering worked without creating duplicate
SQLAlchemy aliases/joins. I then tested the filter in the application.

---

## 3. Improving the service-record UI

### Prompt

Help me add technician filtering and sorting to the service records page while keeping
the existing functionality working.

### What you got

AI suggested adding a technician filter, sort selection, and the corresponding API
query parameters.

### What you corrected

I integrated the changes into the existing frontend and tested technician filtering and
the different sort options manually.

---

## 4. Deployment debugging

### Prompt

The deployed application login is returning HTTP 500. Help me diagnose the actual cause.

### What you got

After checking the live Render logs, the traceback showed the failure occurred inside
the Passlib bcrypt backend while verifying the stored password.

### What you corrected

Instead of changing the login flow itself, I replaced the Passlib password verification
with direct bcrypt hashing/checking in `backend/app/auth.py`.

The live `/auth/login` endpoint was then tested again and returned HTTP 200.

---

## 5. Wrong/initial approach and correction

### Prompt

Help fix the deployed login failure.

### What you got

The initial investigation could have led to treating the issue as a frontend/Vercel
problem. Checking the actual backend response and Render traceback showed that the request
was reaching the backend and the failure was inside password verification.

### What you corrected

I did not change the frontend login flow. I used the server traceback to identify the
bcrypt/Passlib compatibility problem and changed only the password hashing/verification
implementation. I then redeployed and verified the endpoint successfully.

---

## 6. CSV odometer import

### Prompt

The Import Odometer CSV feature is not working in the deployed frontend. Help identify
what is wrong and fix the upload flow.

### What you got

The frontend button was not correctly connected to a file input/upload event.

### What you corrected

I connected the button to a file input, created the multipart upload request, handled
the API response, refreshed the vehicle data, and displayed the successful/rejected
row counts.

The deployed CSV import was then tested successfully.

---

## 7. Production API configuration

### Prompt

Configure the React frontend so it uses the deployed backend in production while still
working against localhost during local development.

### What you got

AI suggested using the Vite `VITE_API_URL` environment variable with a localhost fallback.

### What you corrected

The frontend was configured to use the Render backend URL through the production
environment variable, while retaining the localhost fallback for development.

---

## 8. UI refinement and debugging

### Prompt

Help improve the presentation of the dashboard, vehicle page, service records,
alerts, filters, and modals without changing the required functionality.

### What you got

AI suggested improvements to spacing, buttons, filters, dashboard presentation,
and modal layout.

### What you corrected

I applied the useful changes to the existing implementation and manually checked the
result. One button styling issue was caused by an incorrect CSS class, which was corrected
and retested.