from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from accounts.models import Flag, Staff
from django.contrib.auth.models import User
from Covigo.settings import PRODUCTION_MODE
import smtplib


# Returns the flag assigned to a patient_user by a staff_user
def get_flag(staff_user, patient_user):
    try:
        flag = staff_user.staffs_created_flags.get(patient=patient_user)
        return flag
    except Flag.DoesNotExist:
        return None


def get_user_from_uidb64(uidb64):
    try:
        # urlsafe_base64_decode() decodes to bytestring
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    return user


def get_superuser_staff_model():
    try:
        superuser = User.objects.filter(is_superuser=True).get()
        try:
            return superuser.staff
        except Staff.DoesNotExist:
            Staff.objects.create(user=superuser)
            return superuser.staff
    # TODO: specify which exception instead of the generic one
    except Exception:
        return None


def reset_password_email_generator(user, subject, template):
    if PRODUCTION_MODE:
        c = {
            'email': user.email,
            'domain': 'covigo.ddns.net',
            'site_name': 'Covigo',
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': default_token_generator.make_token(user),
            'protocol': 'https',
        }
    else:
        c = {
            'email': user.email,
            'domain': '127.0.0.1:8000',
            'site_name': 'Covigo',
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            'token': default_token_generator.make_token(user),
            'protocol': 'http',
        }
    email = render_to_string(template, c)
    send_email_to_user(user, subject, email)


def send_email_to_user(user, subject, message):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    email = 'shahdextra@gmail.com'
    pwd = 'roses12345!%'
    s.login(email,pwd)
    s.sendmail(email, user.email, f"Subject: {subject}\n{message}")
    s.quit()
