from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from heapq import heappush, heappop


# ---------- People ----------

class Person(ABC):
    def __init__(self, pid, name, phone=""):
        self.id = pid
        self.name = name
        self.phone = phone

    def __str__(self):
        return f"{self.id} - {self.name}"


class Staff(Person, ABC):
    def __init__(self, pid, name, phone="", spec=""):
        super().__init__(pid, name, phone)
        self.spec = spec
        self.off = set()
        self.appts = []
        self.shifts = set()

    @abstractmethod
    def calc_salary(self, month, data):
        pass


class Doctor(Staff):
    def calc_salary(self, month, data):
        return 80000 + data.get("consult", 0) * 200 + data.get("surgery", 0) * 2000


class Nurse(Staff):
    def calc_salary(self, month, data):
        return 30000 + data.get("night", 0) * 500


class Receptionist(Staff):
    def calc_salary(self, month, data):
        return 22000 + data.get("ot", 0) * 150


class SeniorDoctor(Doctor):
    pass


# ---------- Patient status using composition ----------

class PatientStatus:
    def __init__(self, kind="OPD"):
        self.kind = kind

    def __str__(self):
        return self.kind


class Patient(Person):
    def __init__(self, pid, name, phone="", bg="", status="OPD"):
        super().__init__(pid, name, phone)
        self.bg = bg
        self.status = PatientStatus(status)
        self.allergies = set()
        self.prescriptions = []
        self.admissions = []
        self.bills = []
        self.events = []
        self.followups = []
        self.ratings = {}
        self.diet = None
        self.visitors = []

    @property
    def kind(self):
        return self.status.kind

    def set_status(self, kind):
        self.status.kind = kind


# ---------- Appointments ----------

@dataclass
class Appointment:
    aid: str
    patient: Patient
    doctor: Doctor
    day: date
    time: str
    status: str = "BOOKED"
    fee: float = 500
    paid: float = 200

    def key(self):
        return f"{self.day} {self.time}"


# ---------- Beds / wards ----------

@dataclass
class Bed:
    bid: str
    ward: str
    state: str = "AVAILABLE"  # AVAILABLE, OCCUPIED, CLEANING, MAINTENANCE
    patient_id: str = ""

    def assign(self, pid):
        self.state = "OCCUPIED"
        self.patient_id = pid

    def discharge(self):
        self.state = "CLEANING"
        self.patient_id = ""


class Ward:
    def __init__(self, name, rate, beds):
        self.name = name
        self.rate = rate
        self.beds = [Bed(f"{name[:2].upper()}{i+1}", name) for i in range(beds)]

    def free_bed(self):
        for b in self.beds:
            if b.state == "AVAILABLE":
                return b
        return None

    def counts(self):
        out = {"AVAILABLE": 0, "OCCUPIED": 0, "CLEANING": 0, "MAINTENANCE": 0}
        for b in self.beds:
            out[b.state] += 1
        return out


@dataclass
class StayRecord:
    ward: str
    frm: date
    to: date | None = None


# ---------- Billing / insurance ----------

@dataclass
class BillItem:
    name: str
    amount: float
    kind: str = "OTHER"
    source: str = ""


class Bill:
    def __init__(self, bid, patient):
        self.id = bid
        self.patient = patient
        self.items = []
        self.paid = 0
        self.insurance = None

    def has_item(self, source):
        return any(getattr(x, "source", "") == source for x in self.items)

    def add(self, name, amount, kind="OTHER", source=""):
        self.items.append(BillItem(name, float(amount), kind, source))

    @property
    def total(self):
        return sum(x.amount for x in self.items)

    @property
    def balance(self):
        return max(0, self.total - self.paid)

    def show_details(self):
        print("\n========== PATIENT BILL ==========")
        print(f"Bill ID : {self.id}")
        print(f"Patient : {self.patient.id}")
        print(f"Name    : {self.patient.name}")
        print("----------------------------------")

        if not self.items:
            print("No charges found.")
        else:
            for item in self.items:
                print(f"{item.name:<30} ₹{item.amount:>8.2f}")

        print("----------------------------------")
        print(f"Total   : ₹{self.total:.2f}")
        print(f"Paid    : ₹{self.paid:.2f}")
        print(f"Balance : ₹{self.balance:.2f}")
        print("==================================")

    def __str__(self):
        return f"{self.id}: {self.patient.name} ₹{self.total:.2f} balance ₹{self.balance:.2f}"


class PaymentPolicy(ABC):
    @abstractmethod
    def calculate_payable(self, bill):
        pass


class SelfPay(PaymentPolicy):
    def calculate_payable(self, bill):
        return bill.total


class Government(PaymentPolicy):
    def calculate_payable(self, bill):
        ward_items = [x for x in bill.items if x.kind == "WARD"]
        ward = sum(x.amount for x in ward_items)
        if any(not x.name.startswith("General") for x in ward_items):
            from errors import ClaimRejectedError
            raise ClaimRejectedError("Government scheme allows only General ward.")
        if ward > 50000:
            from errors import ClaimRejectedError
            raise ClaimRejectedError("Government scheme rejects ward charges above ₹50,000.")
        return bill.total


class PrivateInsurance(PaymentPolicy):
    def __init__(self, limit=100000):
        self.limit = limit

    def calculate_payable(self, bill):
        covered = 0
        for x in bill.items:
            if x.kind != "MEDICINE":
                covered += x.amount * 0.8
        covered = min(covered, self.limit)
        return max(0, bill.total - covered)


class Corporate(PaymentPolicy):
    def calculate_payable(self, bill):
        payable = 0
        for x in bill.items:
            if x.kind == "CONSULT":
                payable += 0
            else:
                payable += x.amount * 0.3
        return payable


# ---------- Prescriptions ----------

@dataclass
class Prescription:
    med: str
    cat: str
    override: bool = False
    reason: str = ""


# ---------- Discharge state machine ----------

class Discharge:
    states = ["ADMITTED", "UNDER_TREATMENT", "DISCHARGE_REQUESTED", "APPROVED", "BILLED", "DISCHARGED"]
    allowed = {
        "ADMITTED": {"UNDER_TREATMENT"},
        "UNDER_TREATMENT": {"DISCHARGE_REQUESTED"},
        "DISCHARGE_REQUESTED": {"APPROVED"},
        "APPROVED": {"BILLED"},
        "BILLED": {"DISCHARGED"},
    }

    def __init__(self):
        self.state = "ADMITTED"

    def move(self, new, role):
        from errors import InvalidTransitionError
        if new not in self.allowed.get(self.state, set()):
            raise InvalidTransitionError(f"{self.state} -> {new} is not allowed.")
        if new == "APPROVED" and role != "SeniorDoctor":
            raise InvalidTransitionError("Only a SeniorDoctor can approve discharge.")
        if new == "BILLED" and role != "Billing":
            raise InvalidTransitionError("Only billing staff can mark BILLED.")
        self.state = new


# ---------- Labs / composite packages ----------

class LabTest(ABC):
    def __init__(self, tid, patient, doctor):
        self.id = tid
        self.patient = patient
        self.doctor = doctor
        self.status = "ORDERED"
        self.abnormal = False

    @abstractmethod
    def price(self):
        pass

    @abstractmethod
    def generate_report(self):
        pass


class BloodTest(LabTest):
    def price(self): return 400
    def generate_report(self):
        return "haemoglobin, WBC, platelets with normal ranges"


class XRay(LabTest):
    def price(self): return 800
    def generate_report(self): return "body part, findings text"


class MRI(LabTest):
    def __init__(self, tid, patient, doctor, approved=False):
        super().__init__(tid, patient, doctor)
        self.approved = approved

    def price(self): return 6500
    def generate_report(self): return "body part, findings text"


class ECG(LabTest):
    def price(self): return 300
    def generate_report(self): return "heart rate, rhythm"


class HealthPackage:
    discounts = {"Basic": .10, "Executive": .15, "Senior Citizen": .20}

    def __init__(self, name):
        self.name = name
        self.parts = []

    def add(self, item):
        self.parts.append(item)

    def price(self):
        total = sum(x.price() for x in self.parts)
        return total * (1 - self.discounts.get(self.name, 0))


# ---------- Surgery ----------

@dataclass
class Surgery:
    sid: str
    patient: Patient
    surgeon: Doctor
    anaesthetist: Doctor
    nurses: list
    theatre: str
    start: datetime
    end: datetime
    kind: str
    fee: float


# ---------- Blood bank ----------

@dataclass
class BloodUnit:
    group: str
    collected: date
    units: int = 1

    def valid(self, day):
        return day <= self.collected + timedelta(days=42)


# ---------- Ambulance ----------

@dataclass
class Ambulance:
    aid: str
    kind: str
    distance: float = 0
    state: str = "AVAILABLE"
    patient_id: str = ""

    def charge(self):
        rate = 15 if self.kind == "Basic" else 40
        return max(500, self.distance * rate)


# ---------- Diet / visitors / referrals ----------

@dataclass
class Diet:
    name: str
    daily: float


@dataclass
class Referral:
    rid: str
    patient: Patient
    from_doc: Doctor
    spec: str
    status: str = "PENDING"


@dataclass
class Notification:
    patient_id: str
    text: str


# ---------- Commands ----------

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class SimpleCommand(Command):
    def __init__(self, run, back):
        self.run = run
        self.back = back

    def execute(self):
        return self.run()

    def undo(self):
        return self.back()
