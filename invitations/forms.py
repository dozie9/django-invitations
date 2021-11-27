from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from .adapters import get_invitations_adapter
from .exceptions import AlreadyAccepted, AlreadyInvited, UserRegisteredEmail, UserRegisteredPhone
from .utils import get_invitation_model

Invitation = get_invitation_model()


class CleanEmailMixin(object):

    def validate_invitation(self, email):
        if Invitation.objects.all_valid().filter(
                email__iexact=email, accepted=False):
            raise AlreadyInvited
        elif Invitation.objects.filter(
                email__iexact=email, accepted=True):
            raise AlreadyAccepted
        elif get_user_model().objects.filter(email__iexact=email):
            raise UserRegisteredEmail
        else:
            return True

    def clean_email(self):
        email = self.cleaned_data["email"]
        email = get_invitations_adapter().clean_email(email)

        errors = {
            "already_invited": _("This e-mail address has already been"
                                 " invited."),
            "already_accepted": _("This e-mail address has already"
                                  " accepted an invite."),
            "email_in_use": _("An active user is using this e-mail address"),
        }
        try:
            self.validate_invitation(email)
        except(AlreadyInvited):
            raise forms.ValidationError(errors["already_invited"])
        except(AlreadyAccepted):
            raise forms.ValidationError(errors["already_accepted"])
        except(UserRegisteredEmail):
            raise forms.ValidationError(errors["email_in_use"])
        return email


class CleanPhoneNumberMixin(object):

    def validate_invitation(self, phone_number):
        if Invitation.objects.all_valid().filter(
                phone_number=phone_number, accepted=False):
            raise AlreadyInvited
        elif Invitation.objects.filter(
                phone_number=phone_number, accepted=True):
            raise AlreadyAccepted
        elif get_user_model().objects.filter(phone_number=phone_number):
            raise UserRegisteredPhone
        else:
            return True

    def clean_phone(self):
        phone_number = self.cleaned_data["phone_number"]
        phone_number = get_invitations_adapter().clean_phone_number(phone_number)

        errors = {
            "already_invited": _("This e-mail address has already been"
                                 " invited."),
            "already_accepted": _("This e-mail address has already"
                                  " accepted an invite."),
            "email_in_use": _("An active user is using this e-mail address"),
            "phone_in_use": _("An active user is using this phone no."),
        }
        try:
            self.validate_invitation(phone_number)
        except(AlreadyInvited):
            raise forms.ValidationError(errors["already_invited"])
        except(AlreadyAccepted):
            raise forms.ValidationError(errors["already_accepted"])
        except(UserRegisteredPhone):
            raise forms.ValidationError(errors["phone_in_use"])
        return phone_number


class InviteForm(forms.Form, CleanEmailMixin, CleanPhoneNumberMixin):

    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(
            attrs={"type": "email", "size": "30"}), initial="")

    def save(self, email):
        return Invitation.create(email=email)


class InvitationAdminAddForm(forms.ModelForm, CleanEmailMixin):
    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"}))

    def save(self, *args, **kwargs):
        cleaned_data = super(InvitationAdminAddForm, self).clean()
        email = cleaned_data.get("email")
        params = {'email': email}
        if cleaned_data.get("inviter"):
            params['inviter'] = cleaned_data.get("inviter")
        instance = Invitation.create(**params)
        instance.send_invitation(self.request)
        super(InvitationAdminAddForm, self).save(*args, **kwargs)
        return instance

    class Meta:
        model = Invitation
        fields = ("email", "inviter")


class InvitationAdminChangeForm(forms.ModelForm):

    class Meta:
        model = Invitation
        fields = '__all__'
