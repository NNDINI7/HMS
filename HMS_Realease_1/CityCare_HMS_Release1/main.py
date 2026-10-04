from hospital import (
    Hospital, PatientNotFoundError, DoctorNotAvailableError,
    WardFullError, InvalidOperationError, HospitalError
)


def show_people(h):
    print("\n--- People ---")
    h.print_all(h.patients + h.doctors + h.nurses + h.receptionists)


def read_age():
    while True:
        value = input("Age: ").strip()
        try:
            age = int(value)
            if 0 <= age <= 120:
                return age
            print("Invalid age. Enter a value between 0 and 120.")
        except ValueError:
            print("Invalid age. Enter a number between 0 and 120.")


def read_gender():
    while True:
        value = input("Gender (Male/Female/Other): ").strip().title()
        if value in ("Male", "Female", "Other"):
            return value
        print("Invalid gender. Please enter Male, Female, or Other.")


def read_phone():
    while True:
        value = input("Phone (10 digits): ").strip()
        if Hospital.is_valid_phone(value):
            return value
        print("Invalid phone. Phone must contain exactly 10 digits.")


def read_blood_group():
    valid = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
    while True:
        value = input("Blood group: ").strip().upper()
        if value in valid:
            return value
        print("Invalid blood group. Valid groups: A+, A-, B+, B-, AB+, AB-, O+, O-.")


def show_patients(h):
    print("\n--- Patients ---")
    if not h.patients:
        print("No patients registered.")
        return
    for p in h.patients:
        print(p.get_details())


def show_doctors(h):
    print("\n--- Doctors ---")
    for d in h.doctors:
        print(d.get_details())


def show_wards(h):
    print("\n--- Wards ---")
    for w in h.wards:
        print(w)
        print(f"  Occupied: {len(w)}/{w.total_beds}")
        print(f"  Available: {w.available_beds()}")


def get_patient(h):
    pid = input("Patient ID: ").strip().upper()
    return h.search_patient(pid)


def get_doctor(h):
    did = input("Doctor ID: ").strip().upper()
    for d in h.doctors:
        if d.person_id == did:
            return d
    raise HospitalError("Doctor not found.")


def book_appointment(h):
    p = get_patient(h)
    d = get_doctor(h)
    slot = input(f"Slot {d.available_slots}: ").strip()
    a = h.book_appointment(p.person_id, d.person_id, slot)
    print("Appointment booked:", a)


def cancel_appointment(h):
    aid = input("Appointment ID: ").strip().upper()
    h.cancel_appointment(aid)
    print("Appointment cancelled.")


def admit_patient(h):
    p = get_patient(h)
    wt = input("Ward type (General/ICU/Private): ").strip().title()
    h.admit_patient(p.person_id, wt)
    print("Patient admitted successfully.")


def discharge_patient(h):
    p = get_patient(h)
    h.discharge_patient(p.person_id)
    print("Patient discharged successfully.")


def add_prescription(h):
    p = get_patient(h)
    d = get_doctor(h)
    meds = []
    print("Enter medicines. Leave name empty when done.")
    while True:
        name = input("Medicine name: ").strip()
        if not name:
            break
        dose = input("Dosage (e.g. 500 mg): ").strip()
        days = int(input("Number of days: "))
        from hospital import Medicine
        meds.append(Medicine(name, dose, days))

    if not meds:
        print("No medicines entered.")
        return

    pr = h.add_prescription(p.person_id, d.person_id, meds)
    print("Prescription added:", pr)


def generate_bill(h):
    p = get_patient(h)
    bill = h.generate_bill(p.person_id)
    print("\n--- BILL ---")
    print(bill)
    print("Total: ₹", f"{bill.total:.2f}")


def search_patient(h):
    p = get_patient(h)
    print(p.get_details())


def menu():
    h = Hospital()
    h.load_sample_data()

    while True:
        print("\n" + "=" * 48)
        print("        CITYCARE HOSPITAL - HMS")
        print("=" * 48)
        print("1. Register patient")
        print("2. View patients")
        print("3. View doctors")
        print("4. View wards")
        print("5. View all people")
        print("6. Book appointment")
        print("7. Cancel appointment")
        print("8. Admit patient")
        print("9. Discharge patient")
        print("10. Add prescription")
        print("11. Generate bill")
        print("12. Search patient")
        print("0. Exit")

        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                print("\n--- Register Patient ---")
                name = input("Name: ").strip()
                while not name:
                    print("Name cannot be empty.")
                    name = input("Name: ").strip()

                age = read_age()
                gender = read_gender()
                phone = read_phone()
                blood_group = read_blood_group()

                p = h.register_patient(name, age, gender, phone, blood_group)
                print("Patient registered:", p)
            elif choice == "2":
                show_patients(h)
            elif choice == "3":
                show_doctors(h)
            elif choice == "4":
                show_wards(h)
            elif choice == "5":
                show_people(h)
            elif choice == "6":
                book_appointment(h)
            elif choice == "7":
                cancel_appointment(h)
            elif choice == "8":
                admit_patient(h)
            elif choice == "9":
                discharge_patient(h)
            elif choice == "10":
                add_prescription(h)
            elif choice == "11":
                generate_bill(h)
            elif choice == "12":
                search_patient(h)
            elif choice == "0":
                print("Thank you for using CityCare HMS.")
                break
            else:
                print("Please choose a valid menu option.")

        except (HospitalError, ValueError) as e:
            print("Error:", e)
        except Exception as e:
            # Keeps the terminal app safe from unexpected bad input.
            print("Something went wrong. Please try again.", e)


if __name__ == "__main__":
    menu()
