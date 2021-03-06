from django.contrib.auth.forms import UserCreationForm

from .models import MyUser


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        for fieldname in ["username", "password1", "password2"]:
            self.fields[fieldname].help_text = None

    class Meta:
        model = MyUser
        fields = ("username", "email", "password1", "password2")
