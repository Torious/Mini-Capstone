import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

from symptoms.forms import CreateSymptomForm
from symptoms.models import Symptom, PatientSymptom
from symptoms.utils import (
    assign_symptom_to_user,
    get_assigned_symptoms_from_patient,
    get_earliest_reporting_due_date,
    get_latest_reporting_due_date,
    is_symptom_editing_allowed,
)

from datetime import datetime, timedelta, time


@login_required
@never_cache
def index(request):
    if not request.user.has_perm("accounts.manage_symptoms"):
        raise PermissionDenied

    return redirect('symptoms:list_symptoms')


# this function simply renders the "Symptoms" list page with all
# the symptoms present in the database along with their respective details
@login_required
@never_cache
def list_symptoms(request):
    if not request.user.has_perm("accounts.manage_symptoms"):
        raise PermissionDenied

    return render(request, 'symptoms/list_symptoms.html')


@login_required
@never_cache
def list_symptoms_table(request):
    if not request.user.has_perm("accounts.manage_symptoms"):
        raise PermissionDenied

    symptoms_table = []
    for symptom in Symptom.objects.all():
        symptoms_table.append({
            "id": symptom.id,
            "name": symptom.name,
            "description": symptom.description,
            "enabled": symptom.is_active,
        })

    serialized_symptoms = json.dumps({'data': symptoms_table}, indent=4)

    return HttpResponse(serialized_symptoms, content_type='application/json')


# this function allows form data from the "Create Symptom" page to be submitted and handled properly
# in such a manner as to dynamically change the view depending on what request method is detected and used
@login_required
@never_cache
def create_symptom(request):
    if not request.user.has_perm("accounts.manage_symptoms"):
        raise PermissionDenied

    if request.method == 'POST':
        create_symptom_form = CreateSymptomForm(request.POST)

        if create_symptom_form.is_valid():
            if not Symptom.objects.filter(name=create_symptom_form.data.get('name')).exists():
                symptom = create_symptom_form.save()

                symptom.is_active = True
                symptom.save()

                if request.POST.get('Create and Return'):
                    messages.success(request, 'The symptom was created successfully.')
                    return redirect('symptoms:list_symptoms')

                else:
                    messages.success(request, 'The symptom was created successfully.')
                    return render(request, 'symptoms/create_symptom.html', {
                        'form': create_symptom_form
                    })

            else:
                messages.error(request,
                               'The symptom was not created successfully: This symptom name already exists for a given symptom. Please change the symptom name.')

    else:
        create_symptom_form = CreateSymptomForm()

    return render(request, 'symptoms/create_symptom.html', {
        'form': create_symptom_form
    })


# this function allows form data from the "Edit Symptom" page to be submitted and handled properly
# in such a manner as to dynamically change the database symptom contents, depending on what request
# method is detected and used, by making edits to it
@login_required
@never_cache
def edit_symptom(request, symptom_id):
    if not request.user.has_perm("accounts.manage_symptoms"):
        raise PermissionDenied

    symptom = Symptom.objects.get(id=symptom_id)

    if request.method == 'POST':
        edit_symptom_form = CreateSymptomForm(request.POST, instance=symptom)

        if not edit_symptom_form.has_changed():
            messages.error(request,
                           f"The symptom was not edited successfully: No edits made on this symptom. If you wish to make no changes, please click the \"Cancel\" button to go back to the list of symptoms.")
            return render(request, 'symptoms/edit_symptom.html', {
                'form': edit_symptom_form
            })

        if edit_symptom_form.is_valid():
            if not Symptom.objects.exclude(id=symptom_id).filter(name=edit_symptom_form.data.get('name')).exists():
                edit_symptom_form.save()

                if request.POST.get('Edit and Return'):
                    messages.success(request, 'The symptom was edited successfully.')
                    return redirect('symptoms:list_symptoms')

            else:
                messages.error(request,
                               'The symptom was not edited successfully: This symptom name already exists for a given symptom. Please change the symptom name.')

    else:
        edit_symptom_form = CreateSymptomForm(instance=symptom)

    return render(request, 'symptoms/edit_symptom.html', {
        'form': edit_symptom_form
    })


@login_required
@never_cache
def assign_symptom(request, user_id):
    patient = User.objects.get(pk=user_id)

    can_assign_symptom = (not patient.is_staff and (request.user.has_perm("accounts.assign_symptom_patient") or request.user.has_perm("accounts.assign_symptom_assigned") and patient in request.user.staff.get_assigned_patient_users()))

    if not can_assign_symptom:
        raise PermissionDenied

    if patient.first_name == "" and patient.last_name == "":
        patient_name = patient
    else:
        patient_name = f"{patient.first_name} {patient.last_name}"

    assigned_symptoms = get_assigned_symptoms_from_patient(patient)
    patient_information = patient.patient

    # Check if Assign Symptom can be treated as Editing instead
    allow_editing = is_symptom_editing_allowed(user_id)

    # Ensure this is a post request
    if request.method == 'POST':

        # Get the action of the button
        action = str(request.POST.get('button-action'))

        # Ensure this was the action of assigning symptoms or updating
        if action == 'assign' or action == 'update':
            symptom_list = request.POST.getlist('symptom')

            # Assigns symptoms selected for patient
            if action == 'assign':
                starting_date = datetime.combine(datetime.strptime(request.POST['starting_date'], '%Y-%m-%d'), time.max)
                interval = int(request.POST.get('interval'))

                if len(symptom_list) > 1:
                    messages.success(request, 'The symptoms were assigned to this patient successfully.')

                elif len(symptom_list) == 1:
                    messages.success(request, 'The symptom was assigned to this patient successfully.')

                else:
                    messages.error(request,
                                   'No symptoms were selected to be assigned to this patient. If you wish to not assign any symptoms to this patient at this point in time, please click the \"Cancel\" button to go back to this patient\'s profile. Otherwise, please select at least one symptom to assign.')
                    return render(request, 'symptoms/assign_symptom.html', {
                        'symptoms': Symptom.objects.all(),
                        'patient': patient,
                        'patient_name': patient_name
                    })

            else:  # Update
                # Get the number of extended days the report was extended for
                report_extended_days = int(request.POST.get('extended_days'))

                if report_extended_days <= 0:
                    report_extended_days = 0

                # get earliest and latest due date for current assigned symptoms
                earliest_due_date = get_earliest_reporting_due_date(user_id)
                latest_due_date = get_latest_reporting_due_date(user_id)

                # starting date is the earliest due date
                starting_date = earliest_due_date

                # Calculate the original interval of how many days the symptom should be reported for
                date_difference = latest_due_date - earliest_due_date
                original_interval = date_difference.days + 1

                # How many days the symptoms should be reported for including extended days
                interval = original_interval + report_extended_days

            # For everyday a symptom should be reported, loop and assign it to the user
            while interval != 0:
                for symptom_id in symptom_list:
                    assign_symptom_to_user(symptom_id, user_id, starting_date)
                interval = interval - 1
                starting_date = starting_date + timedelta(days=1)

            if action == 'update':
                # delete old symptoms with data=null that are no longer assigned
                query = PatientSymptom.objects.filter(
                    Q(user_id=user_id) & Q(data=None) & ~Q(symptom_id__in=symptom_list))
                query.delete()

                messages.success(request, 'The assigned symptoms to this patient were updated successfully.')

            if action == 'assign':
                # Assigns quarantine status for patient
                quarantine_status_changed = request.POST.get('should_quarantine') is not None
                if patient_information.is_quarantining is not quarantine_status_changed:
                    patient_information.is_quarantining = quarantine_status_changed
                    patient_information.save()

        return redirect('accounts:profile', user_id=user_id)

    return render(request, 'symptoms/assign_symptom.html', {
        'symptoms': Symptom.objects.all(),
        'assigned_symptoms': assigned_symptoms,
        'patient': patient,
        'patient_name': patient_name,
        'patient_is_quarantining': patient_information.is_quarantining,
        'allow_editing': allow_editing,
    })


@login_required
@never_cache
def toggle_symptom(request, symptom_id):
    if not request.user.has_perm("accounts.manage_symptoms"):
        raise PermissionDenied

    symptom = Symptom.objects.get(id=symptom_id)
    symptom.is_active = not symptom.is_active
    symptom.save()

    return redirect('symptoms:list_symptoms')
