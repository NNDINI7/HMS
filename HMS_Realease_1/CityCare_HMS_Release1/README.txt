CITYCARE HOSPITAL MANAGEMENT SYSTEM - RELEASE 1
================================================

Requirements:
- Python 3.10 or newer
- Standard library only
- No database/files are used for data storage.
- All data exists in memory while the program runs.

HOW TO RUN
----------
1. Open this folder in a terminal.
2. Run:

   python main.py

3. Use the terminal menu.

SAMPLE DATA
-----------
The application starts with:
- 3 doctors
- 2 nurses
- 3 wards
- 5 patients
- 1 receptionist
- sample appointment and prescription
- 1 ambulance

MAIN FILES
----------
main.py
    Terminal menu and user interaction.

hospital.py
    OOP model, validation, billing, hospital operations and exceptions.

IMPORTANT
---------
Because Release 1 requires in-memory storage, data is reset whenever the program
is restarted. No JSON, database or other storage file is used.

BILLING
-------
OPD:
    consultation fee + ₹50 per medicine per day
    age 60+ gets 10% final discount

IPD:
    days x ward charge
    + doctor visit fee
    + medicine charges
    + 5% service tax
    age 60+ gets 10% final discount
