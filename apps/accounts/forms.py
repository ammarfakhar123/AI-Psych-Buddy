from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from .models import Profile

User = get_user_model()


def _style(form):
    """Add Bootstrap classes to every widget."""
    for field in form.fields.values():
        css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
        field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css}".strip()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name", "support_focus")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)
