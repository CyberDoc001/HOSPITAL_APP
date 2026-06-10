from django.db import models
from django.conf import settings


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctor_profile",
    )
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    specialty = models.CharField(max_length=128)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name}"

    @property
    def name(self):
        return str(self)


class Patient(models.Model):
    GENDER_CHOICES = [
        ("female", "Female"),
        ("male", "Male"),
        ("other", "Other"),
    ]

    # link to Django auth user (optional)
    from django.conf import settings
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_profile",
    )

    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    dob = models.DateField(verbose_name="Date of Birth")
    gender = models.CharField(max_length=16, choices=GENDER_CHOICES)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=256, blank=True)
    primary_physician = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def name(self):
        return str(self)


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("checked_in", "Checked In"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="scheduled")
    reason = models.CharField(max_length=256, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"Appointment for {self.patient} on {self.scheduled_at:%Y-%m-%d %H:%M}"


class MedicalRecord(models.Model):
    RECORD_TYPES = [
        ("consultation", "Consultation"),
        ("lab_report", "Lab Report"),
        ("prescription", "Prescription"),
        ("discharge_summary", "Discharge Summary"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_records")
    record_type = models.CharField(max_length=64, choices=RECORD_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.record_type} - {self.patient}"


class Admission(models.Model):
    STATUS_CHOICES = [
        ("admitted", "Admitted"),
        ("discharged", "Discharged"),
        ("in_treatment", "In Treatment"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="admissions")
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    ward = models.CharField(max_length=128)
    bed_number = models.CharField(max_length=16)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="admitted")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-admission_date"]

    def __str__(self):
        return f"Admission for {self.patient} in {self.ward}"


class Notification(models.Model):
    """Simple notification record for patients."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Notification to {self.patient}: {self.message[:50]}"


class Billing(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="bills")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=256, blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Bill {self.amount} for {self.patient} - {'Paid' if self.paid else 'Unpaid'}"
