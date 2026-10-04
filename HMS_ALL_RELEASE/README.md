# CityCare - Easy to Run / Easy to Explain

This folder contains the complete combined Release 1 + Release 2 + Release 3 project.

## Run

Open terminal in this folder and run:

    python main.py

On Windows you can also use:

    py main.py

No external package is required.

## What each file means

- `main.py` = menu. It takes input from the user and calls Hospital methods.
- `hospital.py` = business logic. This is where booking, admission, billing, labs, surgery, blood bank, etc. happen.
- `models.py` = OOP classes such as Patient, Doctor, Nurse, Bill, Ward, LabTest, Surgery.
- `errors.py` = custom errors such as WardFullError and ResourceConflictError.

## Easy OOP explanation

### 1. Inheritance
`Doctor`, `Nurse` and `Receptionist` are different types of `Staff`. They reuse the common Staff code.

### 2. Polymorphism
Each staff class has its own `calc_salary()` method. Hospital payroll can call the same method for every staff member.

### 3. Abstraction
`PaymentPolicy`, `LabTest` and `Command` define common methods for their child classes.

### 4. Composition
A Patient contains a `PatientStatus` object. This is important for OPD -> IPD because the same Patient object keeps the same ID and history while only its status changes.

### 5. Encapsulation
Patient, Bill, Ward and Hospital objects keep their own data and methods.

## Simple project flow

    User -> main.py -> Hospital -> Model object

Example:

    Book appointment
    -> main.py gets Patient ID, Doctor ID, date and time
    -> Hospital.book() checks rules
    -> Appointment object is created
    -> Appointment is stored in Hospital

## Releases included

This is one combined project, not separate Release 2 and Release 3 folders. It contains the Release 1 base system plus Release 2 and Release 3 features.

Release 2 includes patient status composition, ward transfer, insurance strategies, doctor leave/rescheduling, booking conflicts/cancellation, discharge state machine, ICU emergency handling, prescription safety, nurse coverage, undo and reports.

Release 3 includes lab tests, health packages, surgery scheduling, payroll, blood bank, bed lifecycle, ambulance, diet/visitors, referrals/follow-ups/ratings and advanced search/timeline.

## Important for explaining the project

Do not try to explain all 1,000+ lines. Explain the design in layers:

1. `main.py` is only the user interface.
2. `Hospital` is the main controller.
3. `models.py` contains the objects.
4. Release 2 adds business rules.
5. Release 3 adds new modules without changing the basic flow.

Start with the Patient -> PatientStatus example because it clearly explains why composition was used instead of inheritance.

## Simple input validation

The terminal input now uses easy validation rules:

- Patient ID: `P001`, `P002`, ... (generated automatically during registration)
- Doctor ID: `D001`, `D002`, ...
- Nurse ID: `N001`, `N002`, ...
- Receptionist ID: `R001`, `R002`, ...
- Appointment ID: `A001`, `A002`, ...
- Bill ID: `B001`, `B002`, ...
- Test ID: `T001`, `T002`, ...
- Name: letters and spaces only, for example `Meera Rao`
- Phone: 10 digits starting from 6-9, for example `9876543210`

The program shows the dummy format directly in the input prompt. Lowercase IDs such as `d001` are also accepted and converted to uppercase.


## Validation

The project now includes a separate `validation.py` file.

It provides simple reusable validation for:

- Patient IDs: `P001`
- Doctor IDs: `D001`
- Nurse IDs: `N001`
- Names: `Meera Rao`
- Phone numbers: `9876543210`
- Age: `0` to `120`
- Positive numbers
- Fixed menu choices

Example:

```python
from validation import get_id, get_name, get_phone

pid = get_id("Patient ID", "P")
name = get_name("Patient name")
phone = get_phone()
```

The functions keep asking until valid input is entered.
