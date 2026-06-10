from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("accounts/register/", views.register, name="register"),
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/new/", views.new_patient, name="new_patient"),
    path("patients/<int:pk>/", views.patient_detail, name="patient_detail"),
    path("patients/<int:pk>/edit/", views.edit_patient, name="edit_patient"),
    path("doctor/", views.doctor_appointment_list, name="doctor_dashboard"),
    path("patient/portal/", views.patient_portal, name="patient_portal"),
    path("patient/appointments/", views.patient_appointments, name="patient_appointments"),
    path("patient/appointments/new/", views.patient_book_appointment, name="patient_book_appointment"),
    path("patient/notifications/", views.patient_notifications, name="patient_notifications"),
    path("doctor/portal/", views.doctor_portal, name="doctor_portal"),
    path("doctor/register/", views.doctor_register, name="doctor_register"),
    path("doctor/login/", views.doctor_login, name="doctor_login"),
    path("doctor/patients/", views.doctor_patient_list, name="doctor_patient_list"),
    path("doctor/patients/<int:pk>/", views.doctor_patient_detail, name="doctor_patient_detail"),
    path("doctor/appointments/<int:pk>/approve/", views.approve_appointment, name="approve_appointment"),
    path("admin/patients/", views.manage_patients, name="manage_patients"),
    path("admin/doctors/", views.manage_doctors, name="manage_doctors"),
    path("admin/appointments/", views.manage_appointments, name="manage_appointments"),
    path("admin/portal/", views.admin_portal, name="admin_portal"),
    path("doctor/appointments/", views.doctor_appointment_list, name="doctor_appointment_list"),
    path("appointments/<int:pk>/consultation/", views.consultation, name="consultation"),
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/new/", views.new_appointment, name="new_appointment"),
    path("records/", views.medical_record_list, name="record_list"),
]
