from django import forms

from django.contrib.auth.models import User


class LoginForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ('username','password')
		widgets = {
			'password': forms.PasswordInput()
		}

class RegisterForm(forms.ModelForm):
	password2 = forms.CharField(label="Confirm Password", 
		widget = forms.PasswordInput(
			attrs={
				'id': 'password2', 
				'data-toggle': "popover", 
				'data-trigger': 'manual',
				"data-placement": "bottom" 
			}
		)
	)
	class Meta:
		model = User
		fields = ('username', 'email', 'password')
		widgets = {
			'password': forms.PasswordInput(attrs={'id': 'password'})
		}

	def clean(self):
		cleaned_data = super(RegisterForm, self).clean()
		password = cleaned_data.get('password')
		password2 = cleaned_data.get('password2')

		if password2 != password:
			raise form.ValidationError(
				"Confirm password doesn't match!"
				)

class ProfileForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name')

class PasswordResetForm(forms.Form):
	old_password = forms.CharField(label="Old Password",
			widget = forms.PasswordInput(
				attrs={
					'id': 'old_password'
				}
			)
		)
	password = forms.CharField(label="New Password", 
		widget = forms.PasswordInput(
			attrs={
				'id': 'password', 
				'data-toggle': "popover", 
				'data-trigger': 'manual',
				"data-placement": "bottom" 
			}
		)
	)
	password2 = forms.CharField(label="Confirm Password", 
		widget = forms.PasswordInput(
			attrs={
				'id': 'password2', 
				'data-toggle': "popover", 
				'data-trigger': 'manual',
				"data-placement": "bottom" 
			}
		)
	)

	def clean(self):
		cleaned_data = super(PasswordResetForm, self).clean()
		password = cleaned_data.get('password')
		password2 = cleaned_data.get('password2')

		if password2 != password:
			raise form.ValidationError(
				"Confirm password doesn't match!"
				)
