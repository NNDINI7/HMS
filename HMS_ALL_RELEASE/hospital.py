from datetime import date, datetime, timedelta
from abc import ABC, abstractmethod
from heapq import heappush, heappop
from functools import wraps

from errors import (
    WardFullError, ClaimRejectedError, ResourceConflictError,
    InvalidOperationError, InvalidTransitionError, AllergyAlertError,
    DrugInteractionError, NurseCoverageError, BloodUnavailableError,
    VisitorPolicyError, OutOfStockError, CityCareError
)
from models import (
    Patient, Doctor, Nurse, Receptionist, SeniorDoctor, Appointment,
    Ward, StayRecord, Bill, SelfPay, Government, PrivateInsurance, Corporate,
    Prescription, Discharge, LabTest, BloodTest, XRay, MRI, ECG, HealthPackage,
    Surgery, BloodUnit, Ambulance, Diet, Referral, Notification, Command
)


def log_action(fn):
    @wraps(fn)
    def wrap(self, *args, **kwargs):
        out = fn(self, *args, **kwargs)
        self.audit.append(f"{datetime.now():%Y-%m-%d %H:%M:%S} {fn.__name__}")
        return out
    return wrap


class Hospital:
    _one = None

    def __new__(cls, *args, **kwargs):
        if cls._one is None:
            cls._one = super().__new__(cls)
        return cls._one

    def __init__(self, name="CityCare"):
        if getattr(self, "_ready", False):
            return
        self._ready = True
        self.name = name
        self.patients = {}
        self.staff = {}
        self.appts = {}
        self.bills = {}
        self.wards = {
            "ICU": Ward("ICU", 8000, 4),
            "Private": Ward("Private", 3500, 4),
            "General": Ward("General", 1000, 6),
        }
        self.audit = []
        self.undo_stack = []
        self.notes = []
        self.lab = {}
        self.surgeries = {}
        self.blood = {g: [] for g in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]}
        self.ambulances = []
        self.referrals = {}
        self.drug_pairs = {("warfarin", "aspirin"), ("amoxicillin", "methotrexate")}
        self.diet_rates = {"Regular": 300, "Diabetic": 400, "Liquid": 250, "Low-salt": 350}
        self.meds = {}
        self.wait = []
        self.seq = {"p": 1, "a": 1, "b": 1, "l": 1, "s": 1, "r": 1}

    def _id(self, k):
        n = self.seq[k]
        self.seq[k] += 1
        return f"{k.upper()}{n:03d}"

    # ---------- Release 1 ----------

    @log_action
    def add_patient(self, name, phone="", bg="", kind="OPD"):
        pid = self._id("p")
        p = Patient(pid, name, phone, bg, kind)
        p.events.append((datetime.now(), f"Patient registered as {kind}"))
        self.patients[pid] = p
        return p

    @log_action
    def add_staff(self, st):
        self.staff[st.id] = st
        return st

    def doctors(self):
        return [x for x in self.staff.values() if isinstance(x, Doctor)]

    def nurses(self):
        return [x for x in self.staff.values() if isinstance(x, Nurse)]

    def search(self, text):
        text = text.lower()
        return [p for p in self.patients.values()
                if text in p.id.lower() or text in p.name.lower()]

    def book(self, pid, did, day, tm, fee=500):
        p, d = self.patients[pid], self.staff[did]
        if not isinstance(d, Doctor):
            raise InvalidOperationError("Selected staff member is not a doctor.")
        if day in d.off:
            raise InvalidOperationError("Doctor is unavailable on that date.")
        if tm == "13:00" or tm == "13:30":
            raise ResourceConflictError("Doctor break is 13:00-14:00.")
        for a in self.appts.values():
            if a.status == "BOOKED" and a.day == day and a.time == tm:
                if a.doctor.id == did:
                    raise ResourceConflictError("Doctor already has this slot.")
                if a.patient.id == pid:
                    raise ResourceConflictError("Patient already has a booking at this time.")
        aid = self._id("a")
        a = Appointment(aid, p, d, day, tm, fee=fee)
        self.appts[aid] = a
        d.appts.append(aid)
        p.events.append((datetime.now(), f"Appointment {aid} booked"))
        self.undo_stack.append(("booking", aid))
        return a

    def cancel(self, aid, now=None):
        a = self.appts[aid]
        if a.status in ("CANCELLED", "COMPLETED"):
            raise InvalidOperationError("Appointment is already completed/cancelled.")
        now = now or datetime.now()
        apdt = datetime.combine(a.day, datetime.strptime(a.time, "%H:%M").time())
        hrs = (apdt - now).total_seconds() / 3600
        if hrs > 24:
            refund = 200
        elif hrs >= 2:
            refund = 100
        else:
            refund = 0
        a.status = "CANCELLED"
        a.patient.events.append((datetime.now(), f"Appointment {aid} cancelled"))
        return refund

    def admit(self, pid, ward_name):
        p = self.patients[pid]
        w = self.wards[ward_name]
        b = w.free_bed()
        if not b:
            raise WardFullError(f"{ward_name} ward is full.")
        b.assign(pid)
        p.set_status("IPD")
        p.admissions.append(StayRecord(ward_name, date.today()))
        p.events.append((datetime.now(), f"Admitted to {ward_name}"))
        return b

    def discharge_bed(self, pid):
        for w in self.wards.values():
            for b in w.beds:
                if b.patient_id == pid:
                    b.discharge()
                    self.patients[pid].events.append((datetime.now(), f"Bed {b.bid} moved to CLEANING"))
                    return b
        raise InvalidOperationError("Patient has no occupied bed.")

    def clean_bed(self, bid):
        for w in self.wards.values():
            for b in w.beds:
                if b.bid == bid and b.state == "CLEANING":
                    b.state = "AVAILABLE"
                    return b
        raise InvalidOperationError("Bed is not in CLEANING state.")

    def add_prescription(self, pid, med, cat, override=False, reason=""):
        p = self.patients[pid]
        if cat.lower() in {x.lower() for x in p.allergies}:
            if not override:
                raise AllergyAlertError(f"Patient is allergic to {cat}.")
        low = med.lower()
        for old in p.prescriptions:
            pair = tuple(sorted((old.med.lower(), low)))
            if pair in {tuple(sorted(x)) for x in self.drug_pairs} and not override:
                raise DrugInteractionError(f"Dangerous interaction: {old.med} + {med}")
        if override and not reason:
            raise InvalidOperationError("Override reason is required.")
        x = Prescription(med, cat, override, reason)
        p.prescriptions.append(x)
        p.events.append((datetime.now(), f"Prescription: {med}"))
        return x

    def make_bill(self, pid):
        """Create a bill and add all services not billed before."""
        bid = self._id("b")
        b = Bill(bid, self.patients[pid])

        # Doctor appointments
        for a in self.appts.values():
            if a.patient.id == pid and a.status != "CANCELLED":
                if not b.has_item(a.aid):
                    b.add("Doctor appointment " + a.aid, a.fee, "CONSULT", a.aid)
                    b.paid += a.paid

        # Lab / MRI / X-Ray / ECG
        for t in self.lab.values():
            if t.patient.id == pid and not b.has_item(t.id):
                b.add(type(t).__name__ + " " + t.id, t.price(), "LAB", t.id)

        # Ambulance
        for a in self.ambulances:
            if a.patient_id == pid and not b.has_item(a.aid):
                b.add("Ambulance " + a.aid, a.charge(), "AMBULANCE", a.aid)

        self.bills[bid] = b
        self.patients[pid].bills.append(bid)
        return b

    def occupancy(self):
        return {w.name: w.counts() for w in self.wards.values()}

    # ---------- Scenario 1: OPD -> IPD ----------

    def opd_to_ipd(self, pid, ward="ICU"):
        p = self.patients[pid]
        b = self.admit(pid, ward)
        return b

    # ---------- Scenario 2: transfer + ward charges ----------

    def transfer(self, pid, new_ward):
        p = self.patients[pid]
        if not p.admissions:
            raise InvalidOperationError("Patient is not admitted.")
        old = p.admissions[-1]
        w = self.wards[new_ward]
        b = w.free_bed()
        if not b:
            raise WardFullError(f"{new_ward} ward is full. Patient stays in {old.ward}.")
        for ow in self.wards.values():
            for ob in ow.beds:
                if ob.patient_id == pid:
                    ob.discharge()
        old.to = date.today()
        p.admissions.append(StayRecord(new_ward, date.today()))
        b.assign(pid)
        p.events.append((datetime.now(), f"Transferred to {new_ward}"))
        return b

    def ward_bill(self, pid):
        p = self.patients[pid]
        b = self.make_bill(pid)
        for s in p.admissions:
            end = s.to or date.today()
            days = max(1, (end - s.frm).days)
            b.add(f"{s.ward} ward ({days} day)", days * self.wards[s.ward].rate, "WARD")
        return b

    # ---------- Scenario 3: insurance ----------

    def claim(self, bid, typ):
        b = self.bills[bid]
        pol = {
            "Self-pay": SelfPay(),
            "Government scheme": Government(),
            "Private insurance": PrivateInsurance(),
            "Corporate tie-up": Corporate(),
        }[typ]
        b.insurance = typ
        return pol.calculate_payable(b)

    # ---------- Scenario 4: doctor leave + observer ----------

    def doctor_leave(self, did, day):
        d = self.staff[did]
        d.off.add(day)
        for a in self.appts.values():
            if a.doctor.id != did or a.day != day or a.status != "BOOKED":
                continue
            moved = False
            for nd in self.doctors():
                if nd.id == did or nd.spec != d.spec or day in nd.off:
                    continue
                try:
                    na = self.book(a.patient.id, nd.id, day, a.time, a.fee)
                    a.status = "MOVED"
                    self.notify(a.patient.id, f"Appointment {a.aid} moved to Dr. {nd.name} ({na.time})")
                    moved = True
                    break
                except CityCareError:
                    continue
            if not moved:
                a.status = "RESCHEDULE_PENDING"
                self.notify(a.patient.id, f"Appointment {a.aid} needs rescheduling.")

    def notify(self, pid, text):
        self.notes.append(Notification(pid, text))

    # ---------- Scenario 5: booking conflicts are in book/cancel ----------

    # ---------- Scenario 6: discharge state machine ----------

    def move_discharge(self, pid, new, role):
        p = self.patients[pid]
        if not hasattr(p, "dc"):
            p.dc = Discharge()
        p.dc.move(new, role)
        if new == "DISCHARGED":
            self.discharge_bed(pid)
            p.set_status("OPD")
            p.events.append((datetime.now(), "Patient discharged"))

    # ---------- Scenario 7: ICU emergency queue ----------

    def emergency_icu(self, pid, sev, min_stay=1):
        icu = self.wards["ICU"]
        b = icu.free_bed()
        if b:
            b.assign(pid)
            self.patients[pid].set_status("IPD")
            return "ADMITTED"
        cand = []
        for x in self.patients.values():
            for bb in icu.beds:
                if bb.patient_id == x.id:
                    stay = x.admissions[-1] if x.admissions else None
                    if stay and (date.today() - stay.frm).days >= min_stay:
                        score = getattr(x, "severity", 5)
                        cand.append((score, x.id, bb))
        if cand:
            score, oldpid, oldbed = sorted(cand)[0]
            oldbed.discharge()
            self.transfer(oldpid, "Private")
            self.patients[pid].set_status("IPD")
            return f"SHIFTED {oldpid}"
        heappush(self.wait, (sev, datetime.now().timestamp(), pid))
        return "WAITING"

    # ---------- Scenario 8: handled in add_prescription ----------

    # ---------- Scenario 9: nurse coverage ----------

    def set_shift(self, nurse_id, day, shift):
        n = self.staff[nurse_id]
        key = (day, shift)
        for x in n.shifts:
            if x[0] == day:
                raise NurseCoverageError("A nurse cannot have two shifts on the same day.")
        n.shifts.add(key)

    def check_coverage(self, ward_name, day, shift):
        ns = [n for n in self.nurses() if (day, shift) in n.shifts]
        need = 1
        if ward_name == "ICU":
            occ = self.wards["ICU"].counts()["OCCUPIED"]
            need = max(1, (occ + 1) // 2)
        if len(ns) < need:
            self.notes.append(Notification("", f"Warning: {ward_name}, {shift} needs {need} nurse(s)."))

    # ---------- Scenario 10: command / undo ----------

    def undo(self):
        if not self.undo_stack:
            raise InvalidOperationError("Nothing to undo.")
        typ, aid = self.undo_stack.pop()
        if typ == "booking":
            a = self.appts[aid]
            if a.status == "COMPLETED":
                raise InvalidOperationError("Undo after billing is not allowed.")
            a.status = "CANCELLED"
            return f"Undone booking {aid}"
        raise InvalidOperationError("Undo is not available for this action.")

    # ---------- Scenario 11: reports ----------

    def revenue_report(self):
        data = {"OPD": 0, "IPD": 0, "PHARMACY": 0, "REFUND": 0}
        for b in self.bills.values():
            for x in b.items:
                if x.kind in data:
                    data[x.kind] += x.amount
        return data

    def doctor_earnings(self):
        out = []
        for d in self.doctors():
            total = 80000
            for a in self.appts.values():
                if a.doctor.id == d.id and a.status == "COMPLETED":
                    total += 200
            out.append((d.name, total))
        return sorted(out, key=lambda x: x[1], reverse=True)

    def bed_report(self):
        for w in self.wards.values():
            yield w.name, w.counts()

    def long_stays(self, days):
        for p in self.patients.values():
            if p.admissions:
                s = p.admissions[-1]
                if (date.today() - s.frm).days > days:
                    yield p

    # ---------- Release 3 Feature 1: labs ----------

    def add_lab(self, test):
        if isinstance(test, MRI) and not test.approved:
            raise InvalidOperationError("MRI requires doctor approval.")
        self.lab[test.id] = test
        test.patient.events.append((datetime.now(), f"Lab ordered: {test.id}"))
        if test.abnormal:
            self.notify(test.patient.id, f"ABNORMAL lab result: {test.id}")
        return test

    def add_lab_bill(self, bid, tid):
        b = self.bills[bid]
        t = self.lab[tid]
        if not b.has_item(tid):
            b.add(type(t).__name__ + " " + tid, t.price(), "LAB", tid)

    # ---------- Feature 2: packages ----------

    def package_bill(self, bid, pack):
        self.bills[bid].add(pack.name, pack.price(), "LAB")

    # ---------- Feature 3: surgery ----------

    def schedule_surgery(self, s):
        if s.kind == "Major" and s.patient.kind != "IPD":
            raise InvalidOperationError("Only an InPatient can be booked for Major surgery.")
        people = [s.surgeon, s.anaesthetist, *s.nurses]
        for old in self.surgeries.values():
            if not (s.end <= old.start or s.start >= old.end):
                old_people = [old.surgeon, old.anaesthetist, *old.nurses]
                if s.theatre == old.theatre or any(x.id == y.id for x in people for y in old_people):
                    if s.kind == "Emergency" and old.kind == "Minor":
                        old.status = "RESCHEDULED"
                        old.patient.events.append((datetime.now(), f"Surgery {old.sid} rescheduled for emergency"))
                        continue
                    raise ResourceConflictError("Surgery resource conflict.")
        self.surgeries[s.sid] = s
        return s

    # ---------- Feature 4: payroll ----------

    def payroll(self, month):
        out = []
        for st in self.staff.values():
            if isinstance(st, Doctor):
                data = {"consult": sum(1 for a in self.appts.values() if a.doctor.id == st.id and a.status == "COMPLETED"),
                        "surgery": sum(1 for s in self.surgeries.values() if s.surgeon.id == st.id)}
            elif isinstance(st, Nurse):
                data = {"night": sum(1 for d, sh in st.shifts if sh == "NIGHT")}
            else:
                data = {"ot": 0}
            gross = st.calc_salary(month, data)
            tax = gross * .10 if gross > 50000 else 0
            out.append({"id": st.id, "name": st.name, "gross": gross, "tax": tax, "net": gross-tax})
        return out

    # ---------- Feature 5: blood bank ----------

    def add_blood(self, group, collected, units=1):
        self.blood[group].append(BloodUnit(group, collected, units))

    def blood_issue(self, pid, group, units=1):
        compatible = {
            "A+": ["A+", "A-", "O+", "O-"], "A-": ["A-", "O-"],
            "B+": ["B+", "B-", "O+", "O-"], "B-": ["B-", "O-"],
            "AB+": list(self.blood.keys()), "AB-": ["AB-", "A-", "B-", "O-"],
            "O+": ["O+", "O-"], "O-": ["O-"]
        }[group]
        today = date.today()
        arr = []
        for g in compatible:
            for u in self.blood[g]:
                if u.units > 0 and u.valid(today):
                    arr.append(u)
        if not arr:
            raise BloodUnavailableError(f"No compatible blood. Compatible groups: {', '.join(compatible)}")
        arr.sort(key=lambda x: x.collected)
        need = units
        for u in arr:
            take = min(need, u.units)
            u.units -= take
            need -= take
            if need == 0:
                break
        if need:
            raise BloodUnavailableError("Not enough compatible blood units.")
        self.patients[pid].events.append((datetime.now(), f"Blood issued: {group} x{units}"))

    # ---------- Feature 6: bed lifecycle is in Bed/Ward ----------

    # ---------- Feature 7: ambulance ----------

    def dispatch_ambulance(self, kind, distance, pid=""):
        xs = [a for a in self.ambulances if a.kind == kind and a.state == "AVAILABLE"]
        if not xs:
            raise InvalidOperationError("No ambulance available.")
        if pid and pid not in self.patients:
            raise InvalidOperationError("Patient not found.")
        a = min(xs, key=lambda x: abs(x.distance - distance))
        a.distance = distance
        a.patient_id = pid
        a.state = "ON_TRIP"
        if pid:
            self.patients[pid].events.append((datetime.now(), f"Ambulance {a.aid} booked"))
        return a

    def ambulance_arrival(self, aid, name, phone="", bg=""):
        a = next(x for x in self.ambulances if x.aid == aid)
        p = self.add_patient(name, phone, bg, "OPD")
        b = self.make_bill(p.id)
        a.patient_id = p.id
        a.state = "AVAILABLE"
        return p

    # ---------- Feature 8: diet / visitors ----------

    def set_diet(self, pid, name):
        if name not in self.diet_rates:
            raise InvalidOperationError("Unknown diet.")
        self.patients[pid].diet = Diet(name, self.diet_rates[name])

    def add_visitor(self, pid, name, at, doctor_ok=False):
        p = self.patients[pid]
        if not (16 <= at.hour < 19):
            raise VisitorPolicyError("Visitors are allowed from 16:00 to 19:00.")
        if len(p.visitors) >= 2:
            raise VisitorPolicyError("Maximum 2 visitors per patient.")
        if p.kind == "IPD":
            in_icu = any(b.patient_id == pid and b.ward == "ICU" for b in self.wards["ICU"].beds)
            if in_icu and not doctor_ok:
                raise VisitorPolicyError("ICU visitor needs doctor approval.")
        p.visitors.append((name, at))

    # ---------- Feature 9: referrals / followups ----------

    def refer(self, pid, did, spec):
        rid = self._id("r")
        r = Referral(rid, self.patients[pid], self.staff[did], spec)
        self.referrals[rid] = r
        return r

    def add_followup(self, aid, day=None):
        a = self.appts[aid]
        if a.status != "COMPLETED":
            raise InvalidOperationError("Follow-up is only for completed appointments.")
        day = day or (a.day + timedelta(days=7))
        a.patient.followups.append((aid, day))

    def rate_doctor(self, pid, did, rating, aid):
        if not 1 <= rating <= 5:
            raise InvalidOperationError("Rating must be 1 to 5.")
        p = self.patients[pid]
        if aid in p.ratings:
            raise InvalidOperationError("Only one rating per appointment.")
        p.ratings[aid] = rating
        d = self.staff[did]
        if not hasattr(d, "ratings"):
            d.ratings = []
        d.ratings.append(rating)

    def doctor_ratings(self):
        out = []
        for d in self.doctors():
            rs = getattr(d, "ratings", [])
            out.append((d.name, sum(rs)/len(rs) if rs else 0))
        return sorted(out, key=lambda x: x[1], reverse=True)

    # ---------- Feature 10: advanced search / timeline ----------

    def advanced_search(self, name="", bg="", did="", frm=None, to=None, kind=""):
        out = []
        for p in self.patients.values():
            if name and name.lower() not in p.name.lower():
                continue
            if bg and p.bg != bg:
                continue
            if kind and p.kind != kind:
                continue
            if did and not any(a.patient.id == p.id and a.doctor.id == did for a in self.appts.values()):
                continue
            if frm or to:
                ds = [s.frm for s in p.admissions]
                if not any((not frm or d >= frm) and (not to or d <= to) for d in ds):
                    continue
            out.append(p)
        return out

    def timeline(self, pid):
        p = self.patients[pid]
        for t, msg in sorted(p.events, key=lambda x: x[0]):
            yield t, msg

    # ---------- Optional: pharmacy / roles ----------

    def add_med_stock(self, med, qty):
        self.meds[med.lower()] = self.meds.get(med.lower(), 0) + qty

    def use_med(self, med, qty):
        key = med.lower()
        if self.meds.get(key, 0) < qty:
            raise OutOfStockError(f"{med} is out of stock.")
        self.meds[key] -= qty
