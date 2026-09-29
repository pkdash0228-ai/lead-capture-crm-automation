# Interview demo script

1. Start the application with `uvicorn app.main:app --reload` and open `/`.
2. Submit a lead using an uppercase email and show that it is normalized in the dashboard.
3. Submit the same email again with different capitalization; show the duplicate response and activity log entry.
4. Import `sample_data/sample_leads.csv` and explain the per-row import summary.
5. Open `/dashboard` and point out lead status/source counters, search/filter controls, and recent email/intake activity.
6. Open `/docs` to demonstrate the CRUD, import, stats, and logs APIs.
7. Explain that SMTP credentials come from environment variables. Without them, leads are still saved and email failures appear in the activity log.
