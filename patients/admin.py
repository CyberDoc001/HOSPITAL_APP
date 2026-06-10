from django.contrib import admin
from .models import Doctor, Patient, Appointment, MedicalRecord, Admission, Notification


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    fields = ("scheduled_at", "doctor", "status", "reason")
    readonly_fields = ("scheduled_at", "doctor", "status", "reason")
    can_delete = False

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialty", "email", "phone")
    search_fields = ("first_name", "last_name", "specialty", "email")

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "primary_physician", "active")
    list_filter = ("active", "gender")
    search_fields = ("first_name", "last_name", "email", "phone")
    inlines = [AppointmentInline]
    readonly_fields = ("next_appointment",)
    fieldsets = (
        (None, {
            "fields": ("user", "first_name", "last_name", "dob", "gender", "email", "phone", "address", "emergency_contact", "primary_physician", "active")
        }),
        ("Appointment Summary", {
            "fields": ("next_appointment",),
        }),
    )

    def next_appointment(self, obj):
        appointment = obj.appointments.filter(status="scheduled").order_by("scheduled_at").first()
        return appointment.scheduled_at if appointment else "None"
    next_appointment.short_description = "Next Appointment"

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "scheduled_at", "status")
    list_filter = ("status", "scheduled_at")
    search_fields = ("patient__first_name", "patient__last_name", "doctor__first_name", "doctor__last_name")

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("patient", "record_type", "created_at")
    list_filter = ("record_type",)
    search_fields = ("patient__first_name", "patient__last_name", "description")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("patient", "message", "sent_at", "read")
    list_filter = ("read",)
    search_fields = ("patient__first_name", "patient__last_name", "message")

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ("patient", "ward", "admission_date", "discharge_date", "status")
    list_filter = ("ward", "status")
    search_fields = ("patient__first_name", "patient__last_name", "ward")
