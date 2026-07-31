from django import forms

class FlowerImageForm(forms.Form):
    image = forms.ImageField(
        label="Image de fleur",
        required=True,
        widget=forms.FileInput(attrs={
            "accept": "image/*",
            "class": "form-control-file"
        })
    )
