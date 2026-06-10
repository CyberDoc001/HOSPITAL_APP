from django import forms
from .models import Appointment, Patient, Doctor
from django.contrib.auth.forms import UserCreationForm
from django import forms as djforms
from django.contrib.auth.models import User


class DoctorRegistrationForm(djforms.Form):
    username = djforms.CharField(max_length=150)
    password1 = djforms.CharField(widget=djforms.PasswordInput)
    password2 = djforms.CharField(widget=djforms.PasswordInput)
    first_name = djforms.CharField(max_length=128)
    last_name = djforms.CharField(max_length=128)
    specialty = djforms.CharField(max_length=128, required=False)
    email = djforms.EmailField(required=False)
    phone = djforms.CharField(max_length=32, required=False)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise djforms.ValidationError("Passwords do not match")
        if User.objects.filter(username=cleaned.get("username")).exists():
            raise djforms.ValidationError("Username already exists")
        return cleaned


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "dob",
            "gender",
            "email",
            "phone",
            "address",
            "emergency_contact",
            "primary_physician",
            "active",
        ]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "emergency_contact": forms.Textarea(attrs={"rows": 2}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "scheduled_at", "status", "reason", "notes"]
        widgets = {
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ConsultationForm(forms.Form):
    diagnosis = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False)
    prescriptions = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False, help_text="One per line: Medicine name and dose")
    lab_requests = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False, help_text="Describe required lab tests")
    consultation_notes = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False, help_text="Add consultation notes for the patient")
    next_appointment = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type":"datetime-local"}))
    next_doctor = forms.ModelChoiceField(queryset=Doctor.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set queryset at runtime to avoid import-time DB access issues
        self.fields["next_doctor"].queryset = Doctor.objects.all()


class DoctorLoginForm(djforms.Form):
    surname = djforms.CharField(max_length=128, label="Surname")
    email = djforms.EmailField(label="Email")
