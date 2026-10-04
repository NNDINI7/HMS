# CityCare Viva / Demo Notes

## 30-second explanation

CityCare is a command-line hospital management system built using Python and OOP. `main.py` handles user input, `Hospital` handles business operations, and `models.py` contains reusable classes. Release 2 adds advanced hospital rules and Release 3 adds labs, surgery, payroll, blood bank, ambulance and patient services.

## Five OOP concepts to remember

- Inheritance: Doctor is a Staff.
- Polymorphism: Doctor/Nurse/Receptionist calculate salary differently.
- Abstraction: LabTest and PaymentPolicy define common methods.
- Composition: Patient has PatientStatus, so OPD can become IPD without replacing the Patient object.
- Encapsulation: objects keep their own data and operations.

## How to run for demo

1. Open the `easy_citycare` folder in VS Code.
2. Open Terminal.
3. Run `python main.py`.
4. Demo data is already available in the menu.
5. Start with option 4 to view patients and option 3 to view doctors.
6. Then demonstrate appointment booking, admission, billing, lab tests and reports.

## If asked why there are multiple files

I separated the project so each file has one responsibility. This makes the code easier to maintain than putting every class and every menu operation into one very large file.
