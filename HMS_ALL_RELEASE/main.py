from datetime import date, datetime, timedelta
import re

from hospital import Hospital
from models import Doctor, Nurse, Receptionist, SeniorDoctor, Ambulance, BloodTest, XRay, MRI, ECG, HealthPackage
from errors import CityCareError


# ---------- Simple input validation ----------
def get_name(prompt="Name"):
    while True:
        name = input(f"{prompt} (e.g. Meera Rao): ").strip()
        if re.fullmatch(r"[A-Za-z][A-Za-z ]{1,39}", name):
            return " ".join(name.split())
        print("Invalid name. Use letters and spaces only.")


def get_id(prompt, prefix):
    while True:
        value = input(f"{prompt} (e.g. {prefix}001): ").strip().upper()
        if re.fullmatch(rf"{prefix}\d{{3}}", value):
            return value
        print(f"Invalid ID. Use the format {prefix}001, {prefix}002, ...")


def get_patient_id():
    return get_id("Patient ID", "P")


def get_doctor_id():
    return get_id("Doctor ID", "D")


def get_phone():
    while True:
        phone = input("Phone (10 digits, e.g. 9876543210): ").strip()
        if re.fullmatch(r"[6-9]\d{9}", phone):
            return phone
        print("Invalid phone. Enter a valid 10-digit Indian mobile number.")


def seed(h):
    if h.staff:
        return
    h.add_staff(SeniorDoctor("D001", "Meera Rao", spec="Cardiology"))
    h.add_staff(Doctor("D002", "Amit Shah", spec="Cardiology"))
    h.add_staff(Doctor("D003", "Neha Jain", spec="Neurology"))
    h.add_staff(Nurse("N001", "Riya", spec="General"))
    h.add_staff(Nurse("N002", "Pooja", spec="ICU"))
    h.add_staff( Receptionist("R001", "Anil") )
    h.ambulances.extend([
        Ambulance("AM01", "Basic", 5),
        Ambulance("AM02", "ALS", 8),
    ])


def show_menu():
    print("\n===== CityCare Hospital Management =====")
    print("1. Register patient")
    print("2. Add doctor / nurse / receptionist")
    print("3. View doctors")
    print("4. View patients")
    print("5. Search patient")
    print("6. Book appointment")
    print("7. Cancel appointment")
    print("8. Admit patient")
    print("9. Discharge patient")
    print("10. Add prescription")
    print("11. Generate bill")
    print("12. Ward occupancy")
    print("13. View bills sorted by amount")
    print("14. Transfer patient")
    print("15. Insurance claim")
    print("16. Doctor leave")
    print("17. Lab test")
    print("18. Health package")
    print("19. Schedule surgery")
    print("20. Payroll")
    print("21. Blood issue")
    print("22. Ambulance")
    print("23. Diet / visitor")
    print("24. Referral / follow-up / rating")
    print("25. Advanced search")
    print("26. Timeline")
    print("27. Reports")
    print("28. Undo last booking")
    print("0. Exit")


def main():
    h = Hospital()
    seed(h)

    while True:
        show_menu()
        ch = input("Enter choice: ").strip()

        try:
            if not ch.isdigit():
                print("Invalid choice")
                continue
            ch = int(ch)

            if ch == 0:
                print("Goodbye!")
                break

            if ch == 1:
                name = get_name()
                phone = get_phone()
                bg = input("Blood group (e.g. A+, O-, AB+): ").strip().upper()
                kind = input("OPD/IPD (e.g. OPD): ").strip().upper()
                while kind not in ("OPD", "IPD"):
                    print("Invalid type. Enter OPD or IPD.")
                    kind = input("OPD/IPD (e.g. OPD): ").strip().upper()
                p = h.add_patient(name, phone, bg, kind)
                print("Patient ID:", p.id)

            elif ch == 2:
                typ = input("Type (doctor/nurse/receptionist): ").strip().lower()
                while typ not in ("doctor", "nurse", "receptionist"):
                    print("Invalid type. Choose doctor, nurse or receptionist.")
                    typ = input("Type (doctor/nurse/receptionist): ").strip().lower()
                prefix = {"doctor": "D", "nurse": "N", "receptionist": "R"}[typ]
                sid = get_id("Staff ID", prefix)
                name = get_name("Staff name")
                spec = input("Specialisation (e.g. Cardiology): ").strip() if typ == "doctor" else ""
                if typ == "doctor":
                    st = Doctor(sid, name, spec=spec)
                elif typ == "nurse":
                    st = Nurse(sid, name)
                else:
                    st = Receptionist(sid, name)
                h.add_staff(st)
                print("Added:", st)

            elif ch == 3:
                for d in h.doctors():
                    print(d.id, d.name, d.spec)

            elif ch == 4:
                for p in h.patients.values():
                    print(p.id, p.name, p.kind, p.bg)

            elif ch == 5:
                for p in h.search(input("Patient ID/name: ")):
                    print(p.id, p.name, p.kind)

            elif ch == 6:
                pid = get_patient_id()
                did = get_doctor_id()
                day = date.fromisoformat(input("Date YYYY-MM-DD: "))
                tm = input("Time HH:MM: ")
                a = h.book(pid, did, day, tm)
                print(f"Booked {a.aid}; advance ₹{a.paid}")
                print("Appointment charge will be added to the patient's bill.")

            elif ch == 7:
                aid = get_id("Appointment ID", "A")
                print("Refund:", h.cancel(aid))

            elif ch == 8:
                pid = get_patient_id()
                ward = input("Ward: ")
                print("Bed:", h.admit(pid, ward).bid)

            elif ch == 9:
                pid = get_patient_id()
                print("Move patient through ADMITTED -> UNDER_TREATMENT -> DISCHARGE_REQUESTED -> APPROVED -> BILLED -> DISCHARGED.")
                for state, role in [
                    ("UNDER_TREATMENT", "Doctor"),
                    ("DISCHARGE_REQUESTED", "Doctor"),
                    ("APPROVED", "SeniorDoctor"),
                    ("BILLED", "Billing"),
                    ("DISCHARGED", "Billing")
                ]:
                    h.move_discharge(pid, state, role)
                print("Patient discharged.")

            elif ch == 10:
                pid = get_patient_id()
                med = input("Medicine: ")
                cat = input("Category: ")
                h.add_prescription(pid, med, cat)
                print("Prescription added.")

            elif ch == 11:
                pid = get_patient_id()
                b = h.make_bill(pid)
                b.show_details()

            elif ch == 12:
                for w, c in h.occupancy().items():
                    print(w, c)

            elif ch == 13:
                for b in sorted(h.bills.values(), key=lambda x: x.total, reverse=True):
                    print(b)

            elif ch == 14:
                pid = get_patient_id()
                ward = input("New ward: ")
                print("Bed:", h.transfer(pid, ward).bid)

            elif ch == 15:
                bid = get_id("Bill ID", "B")
                typ = input("Self-pay/Government scheme/Private insurance/Corporate tie-up: ")
                print("Patient payable:", h.claim(bid, typ))

            elif ch == 16:
                did = get_doctor_id()
                day = date.fromisoformat(input("Leave date YYYY-MM-DD: "))
                h.doctor_leave(did, day)
                print("Leave applied.")

            elif ch == 17:
                pid = get_patient_id()
                did = get_doctor_id()
                typ = input("BloodTest/XRay/MRI/ECG: ")
                tid = get_id("Test ID", "T")
                if typ == "BloodTest":
                    t = BloodTest(tid, h.patients[pid], h.staff[did])
                elif typ == "XRay":
                    t = XRay(tid, h.patients[pid], h.staff[did])
                elif typ == "MRI":
                    ok = input("Doctor approved? y/n: ").lower() == "y"
                    t = MRI(tid, h.patients[pid], h.staff[did], ok)
                else:
                    t = ECG(tid, h.patients[pid], h.staff[did])
                h.add_lab(t)
                print("Price:", t.price(), "| Report:", t.generate_report())
                print("Lab charge will be added to the patient's bill.")

            elif ch == 18:
                name = input("Package (Basic/Executive/Senior Citizen): ")
                p = HealthPackage(name)
                print("Enter test IDs separated by comma:")
                for tid in input().split(","):
                    tid = tid.strip()
                    if tid in h.lab:
                        p.add(h.lab[tid])
                print("Package price:", p.price())

            elif ch == 19:
                print("Use schedule_surgery() from hospital.py for surgery objects.")
                print("It checks Major/IPD and resource conflicts.")

            elif ch == 20:
                month = input("Month: ")
                for x in h.payroll(month):
                    print(x)

            elif ch == 21:
                pid = get_patient_id()
                bg = input("Patient blood group: ")
                units = int(input("Units: "))
                h.blood_issue(pid, bg, units)
                print("Blood issued.")

            elif ch == 22:
                typ = input("Basic/ALS: ")
                km = float(input("Distance km: "))
                pid = get_patient_id()
                a = h.dispatch_ambulance(typ, km, pid)
                print("Dispatched:", a.aid, "Charge:", a.charge())
                print("Ambulance charge will be added to the patient's bill.")

            elif ch == 23:
                pid = get_patient_id()
                x = input("diet/visitor: ").lower()
                if x == "diet":
                    h.set_diet(pid, input("Regular/Diabetic/Liquid/Low-salt: "))
                else:
                    name = input("Visitor name: ")
                    h.add_visitor(pid, name, datetime.now(), input("Doctor approved? y/n: ").lower() == "y")
                print("Done.")

            elif ch == 24:
                print("Use refer(), add_followup() and rate_doctor() from hospital.py.")

            elif ch == 25:
                name = input("Name partial (blank all): ")
                bg = input("Blood group (blank all): ")
                kind = input("OPD/IPD (blank all): ").upper()
                for p in h.advanced_search(name=name, bg=bg, kind=kind):
                    print(p.id, p.name, p.kind, p.bg)

            elif ch == 26:
                pid = get_patient_id()
                for t, msg in h.timeline(pid):
                    print(t, "-", msg)

            elif ch == 27:
                print("Revenue:", h.revenue_report())
                print("Doctor earnings:", h.doctor_earnings())
                print("Ward report:")
                for x in h.bed_report():
                    print(x)

            elif ch == 28:
                print(h.undo())

            else:
                print("Invalid choice")

        except CityCareError as e:
            print(f"Error: {e}")
        except (KeyError, ValueError) as e:
            print(f"Error: invalid input ({e})")


if __name__ == "__main__":
    main()
