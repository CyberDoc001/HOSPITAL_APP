from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import (
    AppointmentForm,
    ConsultationForm,
    DoctorLoginForm,
    DoctorRegistrationForm,
    PatientForm,
)
from .models import Appointment, Doctor, MedicalRecord, Patient, Notification
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from datetime import date
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden


def landing(request):
    # Landing page should always be accessible and not automatically redirect
    # authenticated users — they may choose to log out or continue from here.
    return render(request, "patients/landing.html")


def doctor_login(request):
    if request.user.is_authenticated:
        return redirect(reverse("patients:doctor_portal") if getattr(request.user, "doctor_profile", None) else reverse("patients:dashboard"))
    if request.method == "POST":
        form = DoctorLoginForm(request.POST)
        if form.is_valid():
            surname = form.cleaned_data["surname"].strip()
            email = form.cleaned_data["email"].strip()
            doctor = Doctor.objects.filter(last_name__iexact=surname, email__iexact=email).first()
            if doctor and doctor.user:
                login(request, doctor.user)
                messages.success(request, f"Welcome Dr. {doctor.last_name}. You may now access your assigned patients.")
                return redirect(reverse("patients:doctor_portal"))
            if doctor and not doctor.user:
                # Doctor exists in clinic DB but has no linked auth user; create and link one automatically.
                if doctor.email:
                    base = doctor.email.split("@")[0]
                    username = base
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base}{counter}"
                        counter += 1
                    user = User.objects.create(username=username, first_name=doctor.first_name or "", last_name=doctor.last_name or "", email=doctor.email)
                    user.set_unusable_password()
                    user.save()
                    doctor.user = user
                    doctor.save()
                    login(request, user)
                    messages.success(request, f"Doctor account created and linked — welcome Dr. {doctor.last_name}.")
                    return redirect(reverse("patients:doctor_portal"))
                else:
                    messages.error(request, "Doctor record found but no email is set. Please link a user account via admin.")
            else:
                messages.error(request, "Doctor credentials not found. Please check your surname and email.")
    else:
        form = DoctorLoginForm()
    return render(request, "patients/doctor_login.html", {"form": form})


def get_logged_in_doctor(user):
    return getattr(user, "doctor_profile", None)


@login_required
def dashboard(request):
    patient_count = Patient.objects.count()
    appointment_count = Appointment.objects.count()
    doctor_count = Doctor.objects.count()
    latest_patients = Patient.objects.order_by("-created_at")[:5]
    upcoming_appointments = Appointment.objects.filter(status="scheduled").order_by("scheduled_at")[:5]
    user_patient = None
    if hasattr(request.user, "patient_profile"):
        user_patient = request.user.patient_profile
        # compute the user's next scheduled appointment for the dashboard (safe for templates)
        user_patient_next = user_patient.appointments.filter(status="scheduled", scheduled_at__gte=timezone.now()).order_by("scheduled_at").first()
    else:
        user_patient_next = None

    # If the logged-in user is a patient, render a simplified patient dashboard
    if hasattr(request.user, "patient_profile") and request.user.patient_profile is not None and not request.user.is_staff and not getattr(request.user, "doctor_profile", None):
        patient = request.user.patient_profile
        upcoming = patient.appointments.filter(status="scheduled", scheduled_at__gte=timezone.now()).order_by("scheduled_at")
        prescriptions = patient.medical_records.filter(record_type="prescription").order_by("-created_at")
        lab_reports = patient.medical_records.filter(record_type="lab_report").order_by("-created_at")
        bills = patient.bills.order_by("-created_at")
        notifications = patient.notifications.order_by("-sent_at")[:10]
        return render(request, "patients/patient_dashboard.html", {
            "patient": patient,
            "upcoming": upcoming,
            "prescriptions": prescriptions,
            "lab_reports": lab_reports,
            "bills": bills,
            "notifications": notifications,
        })

    return render(request, "patients/dashboard.html", {
        "patient_count": patient_count,
        "appointment_count": appointment_count,
        "doctor_count": doctor_count,
        "latest_patients": latest_patients,
        "upcoming_appointments": upcoming_appointments,
        "user_patient": user_patient,
        "user_patient_next": user_patient_next,
    })


@login_required
def patient_list(request):
    # Patients may only see their own profile
    if hasattr(request.user, "patient_profile") and request.user.patient_profile is not None and not request.user.is_staff and not getattr(request.user, "doctor_profile", None):
        return redirect(reverse("patients:patient_portal"))
    doctor = get_logged_in_doctor(request.user)
    if doctor and not request.user.is_staff:
        patients = Patient.objects.filter(primary_physician=doctor).select_related("primary_physician").order_by("last_name", "first_name")
    else:
        patients = Patient.objects.select_related("primary_physician").all()
    return render(request, "patients/patient_list.html", {"patients": patients})


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    # Prevent patients from viewing other patients' details
    if hasattr(request.user, "patient_profile") and request.user.patient_profile is not None and not request.user.is_staff and not getattr(request.user, "doctor_profile", None):
        if request.user.patient_profile.pk != patient.pk:
            messages.error(request, "Access denied: you may only view your own profile.")
            return redirect(reverse("patients:patient_portal"))
    doctor = get_logged_in_doctor(request.user)
    if doctor and not request.user.is_staff and patient.primary_physician_id != doctor.id:
        messages.error(request, "Access denied: you may only view patients assigned to you.")
        return redirect(reverse("patients:doctor_patient_list"))
    next_appointment = patient.appointments.filter(status="scheduled", scheduled_at__gte=timezone.now()).order_by("scheduled_at").first()
    appointment_history = patient.appointments.order_by("-scheduled_at")
    completed_appointments = patient.appointments.filter(status__in=["checked_in", "completed"]).exists()
    has_lab_tests = patient.medical_records.filter(record_type="lab_report").exists()
    has_prescriptions = patient.medical_records.filter(record_type="prescription").exists()

    journey_steps = [
        {"label": "Patient Registration", "completed": True},
        {"label": "Book Appointment", "completed": appointment_history.exists()},
        {"label": "Visit Doctor", "completed": completed_appointments},
        {"label": "Lab Tests (if needed)", "completed": has_lab_tests},
        {"label": "Receive Results", "completed": has_lab_tests or has_prescriptions},
        {"label": "Get Prescription", "completed": has_prescriptions},
        {"label": "Pay Bills", "completed": completed_appointments or has_prescriptions},
        {"label": "Collect Medication / Follow-up", "completed": next_appointment is not None or has_prescriptions},
    ]
    return render(request, "patients/patient_detail.html", {
        "patient": patient,
        "next_appointment": next_appointment,
        "appointment_history": appointment_history,
        "journey_steps": journey_steps,
    })


@login_required
def appointment_list(request):
    # Patients may only see their own appointments
    if hasattr(request.user, "patient_profile") and request.user.patient_profile is not None and not request.user.is_staff and not getattr(request.user, "doctor_profile", None):
        patient = request.user.patient_profile
        appointments = patient.appointments.order_by("-scheduled_at")
    else:
        # Doctors see appointments assigned to them; staff see all
        doctor = get_logged_in_doctor(request.user)
        if doctor and not request.user.is_staff:
            appointments = Appointment.objects.filter(doctor=doctor).select_related("patient", "doctor").order_by("-scheduled_at")
        else:
            appointments = Appointment.objects.select_related("patient", "doctor").order_by("-scheduled_at")
    return render(request, "patients/appointment_list.html", {"appointments": appointments})


@login_required
def doctor_appointment_list(request):
    # List appointments assigned to doctors; allow filtering by doctor via GET param
    # Prevent regular patients from accessing doctor appointment listing
    if hasattr(request.user, "patient_profile") and request.user.patient_profile is not None and not request.user.is_staff and not getattr(request.user, "doctor_profile", None):
        return redirect(reverse("patients:patient_portal"))
    doctor_id = request.GET.get("doctor")
    if doctor_id:
        appointments = Appointment.objects.filter(doctor_id=doctor_id).select_related("patient", "doctor").order_by("scheduled_at")
    else:
        appointments = Appointment.objects.filter(status="scheduled").select_related("patient", "doctor").order_by("scheduled_at")
    doctors = Doctor.objects.all()
    return render(request, "patients/doctor_appointments.html", {"appointments": appointments, "doctors": doctors})


@login_required
def doctor_patient_list(request):
    doctor = get_logged_in_doctor(request.user)
    if doctor is None:
        messages.error(request, "Access denied: doctor account required.")
        return redirect(reverse("patients:dashboard"))
    patients = Patient.objects.filter(primary_physician=doctor).order_by("last_name", "first_name")
    return render(request, "patients/doctor_patient_list.html", {"doctor": doctor, "patients": patients})


@login_required
def doctor_patient_detail(request, pk):
    doctor = get_logged_in_doctor(request.user)
    if doctor is None:
        messages.error(request, "Access denied: doctor account required.")
        return redirect(reverse("patients:dashboard"))
    patient = get_object_or_404(Patient, pk=pk)
    if patient.primary_physician_id != doctor.id:
        messages.error(request, "You are not assigned to this patient.")
        return redirect(reverse("patients:doctor_patient_list"))
    upcoming = patient.appointments.filter(status="scheduled", scheduled_at__gte=timezone.now(), doctor=doctor).order_by("scheduled_at")
    records = patient.medical_records.order_by("-created_at")
    return render(request, "patients/doctor_patient_detail.html", {"doctor": doctor, "patient": patient, "upcoming": upcoming, "records": records})


@login_required
def consultation(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    doctor = get_logged_in_doctor(request.user)
    if not request.user.is_staff and (doctor is None or appointment.doctor_id != doctor.id):
        messages.error(request, "Access denied: you may only consult your assigned appointments.")
        return redirect(reverse("patients:dashboard"))
    patient = appointment.patient
    if request.method == "POST":
        form = ConsultationForm(request.POST)
        if form.is_valid():
            diagnosis = form.cleaned_data.get("diagnosis")
            prescriptions = form.cleaned_data.get("prescriptions")
            lab_requests = form.cleaned_data.get("lab_requests")
            consultation_notes = form.cleaned_data.get("consultation_notes")
            next_appointment_dt = form.cleaned_data.get("next_appointment")
            next_doctor = form.cleaned_data.get("next_doctor")

            if diagnosis:
                MedicalRecord.objects.create(patient=patient, record_type="consultation", description=diagnosis)

            if consultation_notes:
                MedicalRecord.objects.create(patient=patient, record_type="consultation", description=consultation_notes)

            if prescriptions:
                # create a prescription medical record
                MedicalRecord.objects.create(patient=patient, record_type="prescription", description=prescriptions)

            if lab_requests:
                MedicalRecord.objects.create(patient=patient, record_type="lab_report", description=lab_requests)

            if next_appointment_dt:
                Appointment.objects.create(patient=patient, doctor=next_doctor, scheduled_at=next_appointment_dt, status="scheduled", reason="Follow-up")

            # create a notification for patient
            Notification.objects.create(patient=patient, message=f"New consultation completed. Please check your profile for details.")

            appointment.status = "completed"
            appointment.save()
            messages.success(request, "Consultation saved and patient notified.")
            return redirect(reverse("patients:appointment_list"))
    else:
        form = ConsultationForm()
    return render(request, "patients/consultation.html", {"appointment": appointment, "patient": patient, "form": form})


@login_required
def medical_record_list(request):
    # Patients can only view their own medical records
    if hasattr(request.user, "patient_profile") and request.user.patient_profile is not None and not request.user.is_staff and not getattr(request.user, "doctor_profile", None):
        patient = request.user.patient_profile
        records = MedicalRecord.objects.select_related("patient").filter(patient=patient).order_by("-created_at")
    else:
        doctor = get_logged_in_doctor(request.user)
        if doctor and not request.user.is_staff:
            records = MedicalRecord.objects.select_related("patient").filter(patient__primary_physician=doctor).order_by("-created_at")
        else:
            records = MedicalRecord.objects.select_related("patient").all()
    return render(request, "patients/record_list.html", {"records": records})


@login_required
def patient_portal(request):
    # Personal patient portal: if user has a linked Patient profile, show patient-specific info
    if not hasattr(request.user, "patient_profile") or request.user.patient_profile is None:
        messages.error(request, "No patient profile is associated with your account.")
        return redirect(reverse("patients:dashboard"))
    patient = request.user.patient_profile
    next_appointment = patient.appointments.filter(status="scheduled", scheduled_at__gte=timezone.now()).order_by("scheduled_at").first()
    notifications = patient.notifications.all()[:10]
    return render(request, "patients/patient_portal.html", {"patient": patient, "next_appointment": next_appointment, "notifications": notifications})


@login_required
def admin_portal(request):
    # Simple admin portal for staff users
    if not request.user.is_staff:
        messages.error(request, "Access denied: admin/staff only.")
        return redirect(reverse("patients:dashboard"))
    patient_count = Patient.objects.count()
    appointment_count = Appointment.objects.count()
    doctor_count = Doctor.objects.count()
    recent_patients = Patient.objects.order_by("-created_at")[:5]
    return render(request, "patients/admin_portal.html", {"patient_count": patient_count, "appointment_count": appointment_count, "doctor_count": doctor_count, "recent_patients": recent_patients})


@login_required
def patient_appointments(request):
    # show only this patient's appointments
    if not hasattr(request.user, "patient_profile") or request.user.patient_profile is None:
        messages.error(request, "No patient profile is associated with your account.")
        return redirect(reverse("patients:patient_portal"))
    patient = request.user.patient_profile
    appointments = patient.appointments.order_by("-scheduled_at")
    return render(request, "patients/patient_appointments.html", {"appointments": appointments})


@login_required
def patient_book_appointment(request):
    if not hasattr(request.user, "patient_profile") or request.user.patient_profile is None:
        messages.error(request, "No patient profile is associated with your account.")
        return redirect(reverse("patients:patient_portal"))
    patient = request.user.patient_profile
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.patient = patient
            appt.status = "scheduled"
            appt.save()
            messages.success(request, "Appointment booked successfully.")
            return redirect(reverse("patients:patient_appointments"))
    else:
        # prefill doctor choices; remove patient field for patient-facing form
        form = AppointmentForm()
        # hide patient field if present in form fields
        if "patient" in form.fields:
            del form.fields["patient"]
    return render(request, "patients/patient_book_appointment.html", {"form": form})


@login_required
def patient_notifications(request):
    if not hasattr(request.user, "patient_profile") or request.user.patient_profile is None:
        messages.error(request, "No patient profile is associated with your account.")
        return redirect(reverse("patients:patient_portal"))
    patient = request.user.patient_profile
    notifications = patient.notifications.order_by("-sent_at")
    return render(request, "patients/patient_notifications.html", {"notifications": notifications})


@login_required
def doctor_portal(request):
    # Doctor dashboard: show today's appointments and quick access to consultations
    # Require the user to have an associated `Doctor` profile (registered doctor)
    doctor = getattr(request.user, "doctor_profile", None)
    if doctor is None:
        messages.error(request, "Access denied: doctor account required.")
        return redirect(reverse("patients:dashboard"))
    today = date.today()
    todays_appts = Appointment.objects.filter(scheduled_at__date=today, doctor=doctor).select_related("patient", "doctor").order_by("scheduled_at")
    # include list of all NUAM CARE doctors for quick reference
    doctors = Doctor.objects.all()
    return render(request, "patients/doctor_portal.html", {"appointments": todays_appts, "doctor": doctor, "doctors": doctors})


@login_required
@require_POST
def approve_appointment(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Staff only")
    appt = get_object_or_404(Appointment, pk=pk)
    appt.status = "scheduled"
    appt.save()
    messages.success(request, "Appointment approved.")
    return redirect(reverse("patients:manage_appointments"))


@login_required
def manage_patients(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied: staff only.")
        return redirect(reverse("patients:dashboard"))
    patients = Patient.objects.order_by("last_name", "first_name")
    return render(request, "patients/manage_patients.html", {"patients": patients})


@login_required
def manage_doctors(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied: staff only.")
        return redirect(reverse("patients:dashboard"))
    doctors = Doctor.objects.order_by("last_name", "first_name")
    return render(request, "patients/manage_doctors.html", {"doctors": doctors})


@login_required
def doctor_register(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied: staff only.")
        return redirect(reverse("patients:dashboard"))
    if request.method == "POST":
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(username=data["username"], password=data["password1"], first_name=data.get("first_name", ""), last_name=data.get("last_name", ""), email=data.get("email", ""))
            doctor = Doctor.objects.create(user=user, first_name=data.get("first_name", ""), last_name=data.get("last_name", ""), specialty=data.get("specialty", ""), email=data.get("email", ""), phone=data.get("phone", ""))
            messages.success(request, "Doctor registered successfully. You can now login.")
            return redirect(reverse("login"))
    else:
        form = DoctorRegistrationForm()
    return render(request, "patients/doctor_register.html", {"form": form})


@login_required
def manage_appointments(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied: staff only.")
        return redirect(reverse("patients:dashboard"))
    appointments = Appointment.objects.select_related("patient", "doctor").order_by("-scheduled_at")[:100]
    return render(request, "patients/manage_appointments.html", {"appointments": appointments})


@login_required
def new_patient(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied: staff only.")
        return redirect(reverse("patients:dashboard"))
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("patients:patient_list"))
    else:
        form = PatientForm()
    return render(request, "patients/form.html", {"form": form, "title": "Add New Patient"})


@login_required
def edit_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    # Allow staff or the patient themself to edit the record
    if not request.user.is_staff and (not hasattr(request.user, "patient_profile") or request.user.patient_profile.pk != patient.pk):
        messages.error(request, "Access denied: you may only edit your own profile.")
        return redirect(reverse("patients:dashboard"))
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect(reverse("patients:patient_detail", args=[patient.pk]))
    else:
        form = PatientForm(instance=patient)
    return render(request, "patients/form.html", {"form": form, "title": f"Configure {patient.first_name} {patient.last_name}"})


@login_required
def new_appointment(request):
    initial = {}
    if request.GET.get("patient"):
        initial["patient"] = request.GET.get("patient")
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("patients:appointment_list"))
    else:
        form = AppointmentForm(initial=initial)
    return render(request, "patients/form.html", {"form": form, "title": "Schedule Appointment"})


def register(request):
    if request.user.is_authenticated:
        messages.error(request, "You are already logged in. Registration is not allowed while signed in.")
        return redirect(reverse("patients:dashboard"))
    if request.method == "POST":
        user_form = UserCreationForm(request.POST)
        patient_form = PatientForm(request.POST)
        if user_form.is_valid() and patient_form.is_valid():
            user = user_form.save()
            patient = patient_form.save(commit=False)
            patient.user = user
            patient.save()
            # auto-login new user
            raw_password = request.POST.get("password1")
            user = authenticate(request, username=user.username, password=raw_password)
            if user:
                login(request, user)
            messages.success(request, "Registration successful. You are now logged in.")
            return redirect(reverse("patients:patient_portal"))
    else:
        user_form = UserCreationForm()
        patient_form = PatientForm()
    return render(request, "patients/register.html", {"user_form": user_form, "patient_form": patient_form})
