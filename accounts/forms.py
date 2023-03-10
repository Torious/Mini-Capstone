from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, TextInput, CheckboxSelectMultiple, Select, CharField, Form, MultipleChoiceField, \
    ChoiceField
from django.db import connection
from django.contrib.auth.models import User

from Covigo.form_field_classes import *
from accounts.models import Profile

from re import match, sub

from accounts.utils import hour_options_generator, get_staff_permission_codenames, get_patient_permission_codenames

STAFF_PATIENT_CHOICES = (
    ("Patient", 'Patient User'),
    ("Doctor", 'Doctor User'),
    ("Staff", 'Staff User'),
)

IS_CONFIRMED_CHOICES = (
    (True, 'Confirmed Case'),
    (False, 'Unconfirmed Case')
)

IS_NEGATIVE_CHOICES = (
    (True, 'Tested Negative'),
    (False, 'Untested or Tested Positive')
)

IS_QUARANTINING_CHOICES = (
    (True, 'Required to Quarantine'),
    (False, 'Not Required to Quarantine ')
)

SYSTEM_MESSAGE_CHOICES = (
    ("use_email", "Receive system messages by email"),
    ("use_sms", "Receive system messages by sms"),
)

REMINDER_INTERVAL_CHOICES = hour_options_generator(6)


class CreateUserForm(ModelForm):
    user_type = ChoiceField(
        choices=STAFF_PATIENT_CHOICES,
        widget=Select(
            attrs={
                "class": SELECTION_CLASS
            }
        )
    )

    class Meta:
        model = User
        fields = [
            "email",
            "groups",
        ]
        widgets = {
            "email": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            ),
            "groups": CheckboxSelectMultiple(
                attrs={
                    "class": CHECKBOX_CLASS
                }
            )
        }

    def clean_email(self):
        cleaned_email = self.cleaned_data.get("email")
        if cleaned_email != "" and User.objects.filter(email=cleaned_email).exists():
            raise ValidationError(
                "Email already in use by another user."
            )
        return cleaned_email

    def clean_groups(self):
        cleaned_groups = self.cleaned_data.get("groups")
        user_type = self.data.get("user_type")
        if len(cleaned_groups) > 1:
            raise ValidationError(
                "Cannot select more than one group."
            )
        if user_type == "Patient" and any(item in cleaned_groups.values_list("permissions__codename", flat=True) for item in get_staff_permission_codenames()):
            raise ValidationError(
                "Cannot assign a Staff group to a Patient user."
            )
        elif user_type != "Patient" and any(item in cleaned_groups.values_list("permissions__codename", flat=True) for item in get_patient_permission_codenames()):
            raise ValidationError(
                "Cannot assign a Patient group to a Staff/Doctor user."
            )
        return cleaned_groups


class CreateProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            "phone_number"
        ]
        widgets = {
            "phone_number": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            )
        }

    def clean_phone_number(self):
        # TODO: Better phone number sanitization including country codes and similar
        cleaned_phone_number = self.cleaned_data.get("phone_number")
        subbed_phone_number = sub("[+() -]", "", cleaned_phone_number)

        if not match(r'^[0-9]{0,14}$', subbed_phone_number):
            raise forms.ValidationError(
                "Please enter a valid phone number."
            )
        return subbed_phone_number


class RegisterUserForm(ModelForm):
    username = CharField(
        # Set required to false here to override django's builtin popup.
        # The "required-ness" will be checked in clean_username()
        required=False,
        widget=TextInput(
            attrs={
                "placeholder": "Username",
                "class": GUEST_CHARFIELD_CLASS_STANDALONE
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id')
        super(RegisterUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name"
        ]
        widgets = {
            "email": TextInput(
                attrs={
                    "placeholder": "Email Address",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),

            "first_name": TextInput(
                attrs={
                    "placeholder": "First Name",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),
            "last_name": TextInput(
                attrs={
                    "placeholder": "Last Name",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),
        }

    def clean_username(self):
        cleaned_username = self.cleaned_data.get("username")
        if cleaned_username == "":
            raise ValidationError(
                "Please provide a username."
            )
        if cleaned_username != "" and User.objects.filter(email=cleaned_username).exclude(id=self.user_id).exists():
            raise ValidationError(
                "Username already in use by another user."
            )
        if not match(r'^[A-Za-z0-9@._-]+$', cleaned_username):
            raise forms.ValidationError(
                "Username can only contain letters, numbers, periods '.', underscores '_', hyphens '-', or the at symbol '@'."
            )
        return cleaned_username

    def clean_email(self):
        cleaned_email = self.cleaned_data.get("email")
        if cleaned_email == "":
            raise ValidationError(
                "Please provide an email."
            )

        if cleaned_email != "" and User.objects.filter(email=cleaned_email).exclude(id=self.user_id).exists():
            raise ValidationError(
                "Email already in use by another user."
            )
        return cleaned_email

    def clean_first_name(self):
        cleaned_first_name = self.cleaned_data.get("first_name")
        if cleaned_first_name == "":
            raise ValidationError(
                "Please provide your first name."
            )
        return cleaned_first_name

    def clean_last_name(self):
        cleaned_last_name = self.cleaned_data.get("last_name")
        if cleaned_last_name == "":
            raise ValidationError(
                "Please provide your last name."
            )
        return cleaned_last_name


class RegisterProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id')
        super(RegisterProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Profile
        fields = [
            "phone_number",
            "address",
            "postal_code",
        ]
        widgets = {
            "phone_number": TextInput(
                attrs={
                    "placeholder": "Phone Number",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),
            "address": TextInput(
                attrs={
                    "placeholder": "Address",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            ),
            "postal_code": TextInput(
                attrs={
                    "placeholder": "Postal Code",
                    "class": GUEST_CHARFIELD_CLASS_STANDALONE
                }
            )
        }

    def clean_phone_number(self):
        # TODO: Better phone number sanitization including country codes and similar
        cleaned_phone_number = self.cleaned_data.get("phone_number")
        subbed_phone_number = sub("[+() -]", "", cleaned_phone_number)

        if not match(r'^[0-9]{0,14}$', subbed_phone_number):
            raise forms.ValidationError(
                "Please enter a valid phone number."
            )
        return subbed_phone_number

    def clean_address(self):
        cleaned_address = self.cleaned_data.get("address")
        if cleaned_address == "":
            raise ValidationError(
                "Please provide your address."
            )
        return cleaned_address

    def clean_postal_code(self):
        cleaned_postal_code = self.cleaned_data.get("postal_code")
        subbed_postal_code = sub("[._-]", "", cleaned_postal_code).upper()
        if cleaned_postal_code == "":
            raise ValidationError(
                "Please provide your postal code."
            )
        if not match(r'(?!.*[DFIOQU])[A-VXY][0-9][A-Z][\s][0-9][A-Z][0-9]$', subbed_postal_code):
            raise forms.ValidationError(
                "Please enter a valid postal code."
            )
        c = connection.cursor()
        r = c.execute('SELECT id from postal_codes where POSTAL_CODE = %s', [subbed_postal_code])
        if r != 1:
            raise forms.ValidationError(
                "The postal code entered may not exist; check spelling and try again"
            )
        return subbed_postal_code


class EditUserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = User.objects.get(id=kwargs.pop('user_id'))
        super(EditUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "groups"
        ]
        widgets = {
            "username": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            ),
            "email": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            ),

            "first_name": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            ),
            "last_name": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            ),
            "groups": CheckboxSelectMultiple(
                attrs={
                    "class": CHECKBOX_CLASS
                }
            ),
        }

    def clean_username(self):
        cleaned_username = self.cleaned_data.get("username")
        old_username = self.user.username
        if cleaned_username == "":
            raise ValidationError(
                "Please provide a username."
            )
        if cleaned_username != "" and User.objects.filter(email=cleaned_username).exclude(id=self.user.id).exists():
            raise ValidationError(
                "Username already in use by another user."
            )
        if not cleaned_username == old_username and not match(r'^[A-Za-z0-9@._-]+$', cleaned_username):
            raise forms.ValidationError(
                "Username can only contain letters, numbers, periods '.', underscores '_', hyphens '-', or the at symbol '@'."
            )
        return cleaned_username

    def clean_email(self):
        cleaned_email = self.cleaned_data.get("email")
        if cleaned_email != "" and User.objects.filter(email=cleaned_email).exclude(id=self.user.id).exists():
            raise ValidationError(
                "Email already in use by another user."
            )
        return cleaned_email

    def clean_groups(self):
        cleaned_groups = self.cleaned_data.get("groups")
        permissions = cleaned_groups.values_list("permissions__codename", flat=True)

        if len(cleaned_groups) > 1:
            raise ValidationError(
                "Cannot select more than one group."
            )

        if not self.user.is_staff and any(item in permissions for item in get_staff_permission_codenames()):
            raise ValidationError(
                "Cannot assign a Staff group to a Patient user."
            )

        elif self.user.is_staff and any(item in permissions for item in get_patient_permission_codenames()):
            raise ValidationError(
                "Cannot assign a Patient group to a Staff/Doctor user."
            )

        return cleaned_groups


class EditProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id')
        super(EditProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Profile
        fields = [
            "phone_number",
            "address",
            "postal_code",
        ]
        widgets = {
            "phone_number": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            ),
            "address": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            ),
            "postal_code": TextInput(
                attrs={
                    "class": TEXTINPUT_CLASS
                }
            )
        }

    def clean_phone_number(self):
        # TODO: Better phone number sanitization including country codes and similar
        cleaned_phone_number = self.cleaned_data.get("phone_number")
        subbed_phone_number = sub("[+() -]", "", cleaned_phone_number)

        if not match(r'^[0-9]{0,14}$', subbed_phone_number):
            raise forms.ValidationError(
                "Please enter a valid phone number."
            )
        return subbed_phone_number

    def clean_postal_code(self):
        cleaned_postal_code = self.cleaned_data.get("postal_code")
        subbed_postal_code = sub("[._-]", "", cleaned_postal_code).upper()
        if cleaned_postal_code == "":
            raise ValidationError(
                "Please provide your postal code."
            )
        if not match(r'(?!.*[DFIOQU])[A-VXY][0-9][A-Z][\s][0-9][A-Z][0-9]$', subbed_postal_code):
            raise forms.ValidationError(
                "Please enter a valid postal code."
            )
        c = connection.cursor()
        r = c.execute('SELECT id from Covigo.postal_codes where POSTAL_CODE = %s', [subbed_postal_code])
        if r != 1:
            raise forms.ValidationError(
                "The postal code entered may not exist; check its spelling and try again."
            )
        return subbed_postal_code


class EditPreferencesForm(Form):
    system_msg_methods = MultipleChoiceField(
        choices=SYSTEM_MESSAGE_CHOICES,
        widget=CheckboxSelectMultiple(
            attrs={
                "class": CHECKBOX_CLASS
            }
        ),
        required=True
    )

    status_reminder_interval = ChoiceField(
        choices=REMINDER_INTERVAL_CHOICES,
        widget=Select(
            attrs={
                "class": SELECTION_CLASS
            }
        ),
        required=True
    )


class ResetPasswordForm(SetPasswordForm):
    error_messages = {
        "password_mismatch": "The two password fields didn't match."
    }
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'new-password',
                'placeholder': 'New Password',
                'class': GUEST_CHARFIELD_CLASS_TOP
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'new-password',
                'placeholder': 'Confirm Password',
                'class': GUEST_CHARFIELD_CLASS_BOTTOM
            }
        ),
    )


class ChangePasswordForm(PasswordChangeForm):
    error_messages = {
        "password_incorrect": "Your old password was entered incorrectly. Please enter it again.",
        "password_mismatch": "The two password fields didn't match."
    }

    old_password = forms.CharField(
        label="Old Password",
        widget=forms.PasswordInput(
            attrs={
                # TODO: Figure out what goes in the autocomplete here
                "autocomplete": "password",
                "placeholder": "Old Password",
                "class": GUEST_CHARFIELD_CLASS_TOP
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )

    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "New Password",
                "class": GUEST_CHARFIELD_CLASS_MIDDLE
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )

    new_password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Confirm Password",
                "class": GUEST_CHARFIELD_CLASS_BOTTOM
            }
        ),
    )


class EditCaseForm(Form):
    is_confirmed = ChoiceField(
        choices=IS_CONFIRMED_CHOICES,
        widget=Select(
            attrs={
                "class": SELECTION_CLASS
            }
        ),
    )
    is_negative = ChoiceField(
        choices=IS_NEGATIVE_CHOICES,
        widget=Select(
            attrs={
                "class": SELECTION_CLASS
            }
        ),
    )
    is_quarantining = ChoiceField(
        choices=IS_QUARANTINING_CHOICES,
        widget=Select(
            attrs={
                "class": SELECTION_CLASS
            }
        ),
    )
