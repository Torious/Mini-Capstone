from django.contrib import messages

from Covigo.messages import Messages
from appointments.models import Appointment
from accounts.utils import send_system_message_to_user
from messaging.utils import send_notification


def book_appointment(request, appointment_id, user, send_message=True):
    """
    books an appointment in the corresponding appointment availability by setting the patient column to the user
    @params: appointment_id: the  appointment's id
    @params: user: the current patient user object
    @return: void
    """

    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        if send_message:
            messages.error(request, "Could not book appointment: The selected appointment could not be found; it may have been deleted.")
        return False

    appointment.patient = user
    doctor = user.patient.get_assigned_staff_user()
    template = Messages.APPOINTMENT_BOOKED.value
    appointment.save()

    if send_message:
        messages.success(request, 'The selected appointment was booked successfully.')

    c_doctor = {
        "other_person": user,
        "is_doctor": True,
        "date": str(appointment.start_date.date()),
        "time": str(appointment.start_date.time())
    }
    c_patient = {
        "other_person": doctor,
        "is_doctor": False,
        "date": str(appointment.start_date.date()),
        "time": str(appointment.start_date.time())
    }
    send_system_message_to_user(user, template=template, c=c_patient)
    send_system_message_to_user(doctor, template=template, c=c_doctor)

    # SEND NOTIFICATION TO DOCTOR
    app_name = 'appointments'
    send_notification(user.id, doctor.id,
                      user.first_name + " " + user.last_name + " has booked an appointment with you on " + appointment.start_date.strftime(
                          "%B %d, %Y, at %I:%M %p"),
                      app_name=app_name)
    send_notification(doctor.id, user.id,
                      f"You have successfully booked an appointment with Dr. {doctor.last_name} on " + appointment.start_date.strftime(
                          "%B %d, %Y, at %I:%M %p"),
                      app_name=app_name)

    return True


def cancel_appointment(request, appointment_id, send_message=True):
    """
    cancels the booked appointment with the corresponding appointment id:
    this is done by setting the patient_id column of the specific booked appointment to "None"
    @params: appointment_id: the appointment's id
    @return: void
    """

    try:
        booked = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        if send_message:
            messages.error(request, "Could not cancel appointment: The selected appointment could not be found; it may have been deleted.")
        return False

    patient_user = booked.patient

    if patient_user is None:
        if send_message:
            messages.warning(request, "Could not cancel appointment: The selected appointment is unbooked; it may have already been cancelled.")
        return None

    doctor_user = booked.staff
    template = Messages.APPOINTMENT_CANCELLED.value
    booked.patient = None
    booked.save()

    if send_message:
        messages.success(request, 'The appointment was canceled successfully.')

    c_doctor = {
        "other_person": patient_user,
        "is_doctor": True,
        "date": str(booked.start_date.date()),
        "time": str(booked.start_date.time())
    }
    c_patient = {
        "other_person": doctor_user,
        "is_doctor": False,
        "date": str(booked.start_date.date()),
        "time": str(booked.start_date.time())
    }
    send_system_message_to_user(patient_user, template=template, c=c_patient)
    send_system_message_to_user(doctor_user, template=template, c=c_doctor)

    # SEND NOTIFICATION TO DOCTOR AND PATIENT
    app_name = 'appointments'
    send_notification(patient_user.id, doctor_user.id,
                      f"The appointment on {booked.start_date.strftime('%B %d, %Y, at %I:%M %p')} with {patient_user.first_name} {patient_user.last_name} has been cancelled",
                      app_name=app_name)
    send_notification(doctor_user.id, patient_user.id,
                      f"The appointment on {booked.start_date.strftime('%B %d, %Y, at %I:%M %p')} with Dr. {doctor_user.last_name} has been cancelled",
                      app_name=app_name)

    return True


def delete_availability(request, appointment_id, send_message=True):
    """
    deletes the entire appointment object row from the database in order to "delete" the availability
    :param appointment_id: the specific appointment's appointment id
    :return: None
    """

    try:
        unbooked = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        if send_message:
            messages.error(request, "Could not delete availability: The selected availability could not be found; it may have already been deleted.")
        return False

    if unbooked.patient:
        cancel_appointment(request, appointment_id, False)

    unbooked.delete()

    if send_message:
        messages.success(request, 'The availability was deleted successfully.')

    return True


def rebook_appointment_with_new_doctor(new_doctor_id, old_doctor_id, patient):
    """
    this function is called when a patient has a doctor reassignment:
    rebooks the appointments a patient had with an old, previously assigned, doctor to the new doctor if they have an availability at
    the same time as the appointment time with their original doctor (if there is no corresponding availability, the appointment is cancelled)
    @params: new_doctor_id: the newly assigned doctor's id
    @params: old_doctor_id: the old, previously assigned, doctor's id
    @params: patient: the specific patient user object
    @return: void
    """

    # if the newly assigned doctor is the same, do nothing
    try:
        if int(new_doctor_id) == int(old_doctor_id):
            return
    except TypeError:
        return

    patient_id = patient.id
    try:
        booked_appointments = Appointment.objects.filter(staff_id=old_doctor_id, patient_id=patient_id).all()

    # if the patient has no booked appointments with the old, previously assigned, doctor, do nothing
    except Appointment.DoesNotExist:
        return

    new_doctor_availabilities = Appointment.objects.filter(patient=None, staff_id=new_doctor_id).all()

    # if the newly assigned doctor does not have any availabilities, cancel all the patient's current appointments
    if len(new_doctor_availabilities) == 0:
        for appointment in booked_appointments:
            appointment.patient_id = None
            appointment.save()

    # if the newly assigned doctor has availabilities
    else:
        # check each booked appointment for a corresponding availability at the same day and time with the newly assigned doctor
        for appointment in booked_appointments:
            found_corresponding_availability = False
            for availability in new_doctor_availabilities:
                # if a corresponding availability is found, cancel the corresponding booked appointment with the old, previously assigned, doctor and book a new
                #  appointment at the same day and time with the newly assigned doctor
                if is_appointment_and_availability_same_datetime(appointment, availability):
                    appointment.patient_id = None
                    availability.patient = patient
                    appointment.save()
                    availability.save()
                    found_corresponding_availability = True

                    break
            # if a corresponding availability is not found, just cancel the booked appointment with the old, previously assigned, doctor
            if not found_corresponding_availability:
                appointment.patient_id = None
                appointment.save()


def is_appointment_and_availability_same_datetime(appointment, availability):
    """
    returns a boolean if the appointment and availability start and end dates are the same, up to the minute
    @params : appointment: an appointment object of a booked appointment with the old, previously assigned, doctor
    @params : availability: an appointment object of an availability with the newly assigned doctor
    @return : True if both arguments have the same start and end dates, else False
    """

    appointment.start_date = appointment.start_date.replace(microsecond=0, second=0)
    appointment.end_date = appointment.end_date.replace(microsecond=0, second=0)
    availability.start_date = availability.start_date.replace(microsecond=0, second=0)
    availability.end_date = availability.end_date.replace(microsecond=0, second=0)

    return appointment.start_date == availability.start_date and appointment.end_date == availability.end_date


def format_appointments_start_end_times(appointments):
    start_end_times = list(appointments.values_list("start_date", "start_date__time", "end_date__time"))

    times = list(map(lambda x: {
        "day": x[0].strftime('%A'),
        "date": x[0].strftime("%Y-%m-%d"),
        "start": x[1].strftime("%H:%M"),
        "end": x[2].strftime("%H:%M")
    }, start_end_times))

    return times
