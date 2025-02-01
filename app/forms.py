from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User

class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'c9yrh ctkuh c894v text-light rounded-full',
        'placeholder': 'Email',
        'id': 'id_username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'c9yrh ctkuh c894v text-light rounded-full',
        'placeholder': 'Password',
        'id': 'id_password',
    }))

class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Password',
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Confirm Password',
        })
    )

    age = forms.IntegerField(
        required=False,
        label="Age",
        widget=forms.NumberInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Age',
        })
    )
    phone_number = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Phone Number',
        })
    )
    country_of_origin = forms.CharField(
        required=False,
        label="Country of Origin",
        widget=forms.TextInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Country of Origin',
        })
    )
    university = forms.CharField(
        required=False,
        label="University",
        widget=forms.TextInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'University',
        })
    )
    course = forms.CharField(
        required=False,
        label="Course",
        widget=forms.TextInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Course',
        })
    )
    government_id = forms.FileField(
        required=False,
        label="Upload Government ID",
        widget=forms.ClearableFileInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
        })
    )
    profile_image = forms.ImageField(
        required=False,
        label="Upload Profile Image",
        widget=forms.ClearableFileInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'email', 'first_name', 'last_name', 'password1', 'password2',
            'age', 'phone_number', 'country_of_origin', 'university', 'course',
            'government_id', 'profile_image'
        )
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'c9yrh ctkuh c894v text-light rounded-full',
                'placeholder': 'Email',
                'id': 'id_email',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'c9yrh ctkuh c894v text-light rounded-full',
                'placeholder': 'First Name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'c9yrh ctkuh c894v text-light rounded-full',
                'placeholder': 'Last Name',
            }),
        }




class ContactForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Last Name',
        })
    )
    company = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Company',
        })
    )
    email = forms.EmailField(
        max_length=100,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Email Address',
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
            'placeholder': 'Phone Number',
        })
    )
    country = forms.ChoiceField(
        choices=[('US', 'US'), ('CA', 'CA'), ('EU', 'EU')],
        required=True,
        widget=forms.Select(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded-full',
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'c9yrh ctkuh c894v text-light rounded',
            'placeholder': 'Your Message',
            'rows': 4,
        }),
        required=True
    )

