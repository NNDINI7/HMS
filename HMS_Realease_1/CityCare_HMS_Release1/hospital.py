from abc import ABC, abstractmethod
from datetime import date
from enum import Enum
import itertools


class HospitalError(Exception):
    pass


class PatientNotFoundError(HospitalError):
    pass


class DoctorNotAvailableError(HospitalError):
    pass


class WardFullError(HospitalError):
    pass


class InvalidOperationError(HospitalError):
    pass


class Billable(ABC):
    @abstractmethod
    def calculate_bill(self):
        pass


class Person(ABC):
    hospital_name = "CityCare Hospital"

    _ids = {
        "P": itertools.count(1),
        "D": itertools.count(1),
        "N": itertools.count(1),
        "R": itertools.count(1),
    }

    def __init__(self, person_id, name, age, gender, phone):
        self.person_id = person_id
        self.name = name
        self.age = age
        self.gender = gender
        self.phone = phone

    @classmethod
    def make_id(cls, prefix):
        return f"{prefix}{next(Person._ids[prefix]):03d}"

    @property
    def age(self):
        return self.__age

    @age.setter
    def age(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError("Age must be a number.")
        if not 0 <= value <= 120:
            raise ValueError("Age must be between 0 and 120.")
        self.__age = value

    @property
    def gender(self):
        return self.__gender

    @gender.setter
    def gender(self, value):
        value = str(value).strip().title()
        if value not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other.")
        self.__gender = value

    @property
    def phone(self):
        return self.__phone

    @phone.setter
    def phone(self, value):
        value = str(value)
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("Phone must contain exactly 10 digits.")
        self.__phone = value

    @abstractmethod
    def get_details(self):
        pass

    @abstractmethod
    def get_role(self):
        pass

    def __eq__(self, other):
        return isinstance(other, Person) and self.person_id == other.person_id

    def __str__(self):
        return f"{self.person_id} - {self.name}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.person_id!r}, {self.name!r})"


class Medicine:
    def __init__(self, name, dosage, days):
        self.name = name
        self.dosage = dosage
        self.days = int(days)
        if self.days <= 0:
            raise ValueError("Medicine days must be greater than 0.")

    def charge(self):
        return 50 * self.days

    def __str__(self):
        return f"{self.name} ({self.dosage}, {self.days} days)"

    def __repr__(self):
        return f"Medicine({self.name!r}, {self.dosage!r}, {self.days})"


class Ward:
    def __init__(self, ward_type, total_beds, charge_per_day):
        self.ward_type = ward_type
        self.total_beds = int(total_beds)
        self.charge_per_day = float(charge_per_day)
        self.beds = {}

    def available_beds(self):
        return self.total_beds - len(self.beds)

    def is_full(self):
        return self.available_beds() == 0

    def assign_bed(self, patient):
        if self.is_full():
            raise WardFullError(f"{self.ward_type} ward is full.")
        for n in range(1, self.total_beds + 1):
            if n not in self.beds:
                self.beds[n] = patient
                return n
        raise WardFullError("No bed is available.")

    def release_bed(self, bed_no):
        self.beds.pop(bed_no, None)

    def __len__(self):
        return len(self.beds)

    def __contains__(self, patient):
        return patient in self.beds.values()

    def __str__(self):
        return f"{self.ward_type} Ward - ₹{self.charge_per_day:.0f}/day"

    def __repr__(self):
        return f"Ward({self.ward_type!r}, {self.total_beds}, {self.charge_per_day})"


class Patient(Person, Billable):
    def __init__(self, person_id, name, age, gender, phone, blood_group, medical_history=None):
        super().__init__(person_id, name, age, gender, phone)
        self.blood_group = self.validate_blood_group(blood_group)
        self.medical_history = medical_history or []
        self.prescriptions = []
        self.appointments = []

    @staticmethod
    def validate_blood_group(value):
        value = str(value).strip().upper()
        valid = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
        if value not in valid:
            raise ValueError("Blood group must be one of A+, A-, B+, B-, AB+, AB-, O+, O-.")
        return value

    @classmethod
    def from_string(cls, text):
        name, age, gender, phone, blood_group = [x.strip() for x in text.split(",")]
        return OutPatient(
            Person.make_id("P"), name, age, gender, phone, blood_group
        )

    @property
    def blood_group(self):
        return self.__blood_group

    @blood_group.setter
    def blood_group(self, value):
        valid = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
        value = str(value).strip().upper()
        if value not in valid:
            raise ValueError(
                "Blood group must be one of: A+, A-, B+, B-, AB+, AB-, O+, O-."
            )
        self.__blood_group = value

    def get_role(self):
        return "Patient"

    def get_details(self):
        return (
            f"{self.person_id} | {self.name} | Age: {self.age} | "
            f"Gender: {self.gender} | Phone: {self.phone} | "
            f"Blood: {self.blood_group}"
        )

    def __str__(self):
        return f"{self.person_id} - {self.name} ({self.get_role()})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.person_id!r}, {self.name!r})"


class OutPatient(Patient):
    def calculate_bill(self, doctor_fee=0):
        med_charge = sum(m.charge() for p in self.prescriptions for m in p.medicines)
        amount = doctor_fee + med_charge
        if self.age >= 60:
            amount *= 0.90
        return amount

    def get_role(self):
        return "Outpatient"


class InPatient(Patient):
    def __init__(self, *args, ward=None, bed_number=None, admission_date=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ward = ward
        self.bed_number = bed_number
        self.admission_date = admission_date

    def calculate_bill(self, doctor_fee=0):
        if not self.ward or not self.admission_date:
            return 0

        days = max(1, (date.today() - self.admission_date).days)
        ward_charge = days * self.ward.charge_per_day
        med_charge = sum(m.charge() for p in self.prescriptions for m in p.medicines)
        amount = ward_charge + doctor_fee + med_charge
        amount *= 1.05  # 5% service tax
        if self.age >= 60:
            amount *= 0.90
        return amount

    def get_role(self):
        return "Inpatient"

    def get_details(self):
        base = super().get_details()
        bed = f"{self.ward.ward_type}-{self.bed_number}" if self.ward else "Not admitted"
        return base + f" | Bed: {bed}"


class Doctor(Person):
    def __init__(self, person_id, name, age, gender, phone, specialisation,
                 consultation_fee, available_slots=None):
        super().__init__(person_id, name, age, gender, phone)
        self.specialisation = specialisation
        self.consultation_fee = float(consultation_fee)
        self.available_slots = available_slots or []

    def get_role(self):
        return "Doctor"

    def get_details(self):
        return (
            f"{self.person_id} | Dr. {self.name} | {self.specialisation} | "
            f"Fee: ₹{self.consultation_fee:.0f} | Slots: {', '.join(self.available_slots)}"
        )

    def __str__(self):
        return f"{self.person_id} - Dr. {self.name} ({self.specialisation})"

    def __repr__(self):
        return f"Doctor({self.person_id!r}, {self.name!r}, {self.specialisation!r})"


class SeniorDoctor(Doctor):
    def can_approve_discharge(self):
        return True

    def get_role(self):
        return "Senior Doctor"


class Nurse(Person):
    def __init__(self, person_id, name, age, gender, phone, shift, assigned_ward):
        super().__init__(person_id, name, age, gender, phone)
        self.shift = shift
        self.assigned_ward = assigned_ward

    def get_role(self):
        return "Nurse"

    def get_details(self):
        return (
            f"{self.person_id} | Nurse {self.name} | Shift: {self.shift} | "
            f"Ward: {self.assigned_ward}"
        )


class Receptionist(Person):
    def get_role(self):
        return "Receptionist"

    def get_details(self):
        return f"{self.person_id} | Receptionist {self.name} | Phone: {self.phone}"


class Ambulance:
    def __init__(self, amb_id, driver, phone):
        self.amb_id = amb_id
        self.driver = driver
        self.phone = phone

    def get_details(self):
        return f"Ambulance {self.amb_id} | Driver: {self.driver} | Phone: {self.phone}"

    def __str__(self):
        return self.get_details()


class AppointmentStatus(Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Appointment:
    _count = itertools.count(1)

    def __init__(self, patient, doctor, slot):
        self.appointment_id = f"A{next(self._count):03d}"
        self.patient = patient
        self.doctor = doctor
        self.slot = slot
        self.status = AppointmentStatus.SCHEDULED

    def __str__(self):
        return (
            f"{self.appointment_id} | {self.patient.name} | Dr. {self.doctor.name} | "
            f"{self.slot} | {self.status.value}"
        )

    def __repr__(self):
        return f"Appointment({self.appointment_id!r}, {self.patient.person_id!r}, {self.doctor.person_id!r}, {self.slot!r})"


class Prescription:
    _count = itertools.count(1)

    def __init__(self, doctor, patient, medicines):
        self.prescription_id = f"RX{next(self._count):03d}"
        self.doctor = doctor
        self.patient = patient
        self.medicines = medicines

    def __str__(self):
        meds = ", ".join(str(m) for m in self.medicines)
        return f"{self.prescription_id} | Dr. {self.doctor.name} | {meds}"


class Bill:
    _count = itertools.count(1)

    def __init__(self, patient, line_items, total):
        self.bill_id = f"B{next(self._count):03d}"
        self.patient = patient
        self.line_items = line_items
        self.total = total

    def __lt__(self, other):
        return self.total < other.total

    def __add__(self, other):
        return self.total + other.total

    def __str__(self):
        lines = [f"Bill ID: {self.bill_id}", f"Patient: {self.patient.name}"]
        lines += [f"- {name}: ₹{amount:.2f}" for name, amount in self.line_items]
        lines.append(f"TOTAL: ₹{self.total:.2f}")
        return "\n".join(lines)

    def __repr__(self):
        return f"Bill({self.bill_id!r}, {self.patient.person_id!r}, {self.total!r})"


def print_all(people):
    # Duck typing: every object only needs get_details().
    for person in people:
        print(person.get_details())


class Hospital:
    hospital_name = Person.hospital_name

    def __init__(self):
        self.patients = []
        self.doctors = []
        self.nurses = []
        self.receptionists = []
        self.wards = []
        self.appointments = []
        self.bills = []
        self.ambulances = []

    @staticmethod
    def is_valid_phone(phone):
        return str(phone).isdigit() and len(str(phone)) == 10

    def register_patient(self, name, age, gender, phone, blood_group):
        # Object-level validation happens in Person/Patient.
        pid = Person.make_id("P")
        p = OutPatient(pid, name, age, gender, phone, blood_group)
        self.patients.append(p)
        return p

    def search_patient(self, patient_id):
        for p in self.patients:
            if p.person_id == patient_id:
                return p
        raise PatientNotFoundError(f"Patient {patient_id} was not found.")

    def _find_doctor(self, doctor_id):
        for d in self.doctors:
            if d.person_id == doctor_id:
                return d
        raise HospitalError(f"Doctor {doctor_id} was not found.")

    def _find_ward(self, ward_type):
        for w in self.wards:
            if w.ward_type.lower() == ward_type.lower():
                return w
        raise HospitalError(f"Ward {ward_type} was not found.")

    def book_appointment(self, patient_id, doctor_id, slot):
        p = self.search_patient(patient_id)
        d = self._find_doctor(doctor_id)

        if slot not in d.available_slots:
            raise DoctorNotAvailableError("This slot is not available for the doctor.")

        for a in self.appointments:
            if (a.doctor == d and a.slot == slot and
                    a.status == AppointmentStatus.SCHEDULED):
                raise DoctorNotAvailableError("This doctor is already booked for this slot.")

        a = Appointment(p, d, slot)
        self.appointments.append(a)
        p.appointments.append(a)
        return a

    def cancel_appointment(self, appointment_id):
        for a in self.appointments:
            if a.appointment_id == appointment_id:
                if a.status == AppointmentStatus.COMPLETED:
                    raise InvalidOperationError("A completed appointment cannot be cancelled.")
                a.status = AppointmentStatus.CANCELLED
                return
        raise InvalidOperationError("Appointment not found.")

    def admit_patient(self, patient_id, ward_type):
        p = self.search_patient(patient_id)

        if isinstance(p, InPatient):
            raise InvalidOperationError("Patient is already admitted.")

        w = self._find_ward(ward_type)
        bed = w.assign_bed(p)

        # Change the patient to an inpatient while keeping the same object data.
        p.__class__ = InPatient
        p.ward = w
        p.bed_number = bed
        p.admission_date = date.today()
        return p

    def discharge_patient(self, patient_id):
        p = self.search_patient(patient_id)

        if not isinstance(p, InPatient):
            raise InvalidOperationError("An outpatient cannot be discharged.")

        # In a real hospital this could require SeniorDoctor approval.
        if p.ward:
            p.ward.release_bed(p.bed_number)

        p.ward = None
        p.bed_number = None
        p.admission_date = None
        p.__class__ = OutPatient

    def add_prescription(self, patient_id, doctor_id, medicines):
        p = self.search_patient(patient_id)
        d = self._find_doctor(doctor_id)
        pr = Prescription(d, p, medicines)
        p.prescriptions.append(pr)
        return pr

    def generate_bill(self, patient_id):
        p = self.search_patient(patient_id)

        # Use consultation fees from the patient's appointments.
        fees = []
        for a in p.appointments:
            if a.status != AppointmentStatus.CANCELLED:
                fees.append(a.doctor.consultation_fee)

        doctor_fee = sum(fees)

        med_charge = sum(
            m.charge()
            for pr in p.prescriptions
            for m in pr.medicines
        )

        items = []

        if isinstance(p, InPatient):
            days = max(1, (date.today() - p.admission_date).days)
            ward_charge = days * p.ward.charge_per_day
            subtotal = ward_charge + doctor_fee + med_charge
            tax = subtotal * 0.05
            discount = (subtotal + tax) * 0.10 if p.age >= 60 else 0
            total = subtotal + tax - discount

            items.append((f"{p.ward.ward_type} ward ({days} day/s)", ward_charge))
            items.append(("Doctor visits", doctor_fee))
            items.append(("Medicines", med_charge))
            items.append(("Service tax 5%", tax))
            if discount:
                items.append(("Senior citizen discount 10%", -discount))
        else:
            subtotal = doctor_fee + med_charge
            discount = subtotal * 0.10 if p.age >= 60 else 0
            total = subtotal - discount

            items.append(("Doctor consultation", doctor_fee))
            items.append(("Medicines", med_charge))
            if discount:
                items.append(("Senior citizen discount 10%", -discount))

        bill = Bill(p, items, total)
        self.bills.append(bill)
        return bill

    def load_sample_data(self):
        # Three wards required by Release 1.
        self.wards = [
            Ward("General", 10, 1000),
            Ward("ICU", 4, 8000),
            Ward("Private", 5, 3500),
        ]

        self.doctors = [
            Doctor(Person.make_id("D"), "Amit Sharma", 45, "Male", "9876500001",
                   "Cardiology", 1000, ["10:00", "11:00", "12:00"]),
            Doctor(Person.make_id("D"), "Neha Patil", 39, "Female", "9876500002",
                   "Orthopaedics", 800, ["10:00", "13:00", "15:00"]),
            SeniorDoctor(Person.make_id("D"), "Raj Mehta", 55, "Male", "9876500003",
                         "General", 700, ["09:00", "11:00", "16:00"]),
        ]

        self.nurses = [
            Nurse(Person.make_id("N"), "Priya Joshi", 30, "Female", "9876500011",
                  "Morning", "General"),
            Nurse(Person.make_id("N"), "Karan Singh", 34, "Male", "9876500012",
                  "Night", "ICU"),
        ]

        self.receptionists = [
            Receptionist(Person.make_id("R"), "Meena Verma", 29, "Female", "9876500021")
        ]

        sample = [
            ("Ravi", 34, "Male", "9876543210", "O+"),
            ("Anita", 62, "Female", "9876543211", "A+"),
            ("Vikram", 48, "Male", "9876543212", "B+"),
            ("Sneha", 27, "Female", "9876543213", "AB+"),
            ("Mohan", 70, "Male", "9876543214", "O-"),
        ]

        for data in sample:
            self.register_patient(*data)

        # A sample prescription and appointment make billing easy to test.
        first_patient = self.patients[0].person_id
        first_doctor = self.doctors[0].person_id

        self.book_appointment(first_patient, first_doctor, "10:00")
        self.add_prescription(
            first_patient, first_doctor,
            [Medicine("Paracetamol", "500 mg", 3)]
        )

        self.ambulances.append(Ambulance("AMB001", "Ramesh", "9876500099"))

    def print_all(self, people):
        print_all(people)
