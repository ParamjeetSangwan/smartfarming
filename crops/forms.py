from django import forms
from .models import Crop

class CropFilterForm(forms.Form):
    country = forms.ChoiceField(required=False)
    soil_type = forms.ChoiceField(required=False)
    temperature = forms.FloatField(required=False)
    season = forms.ChoiceField(required=False)
    category = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['country'].choices = [('', 'Any')] + [(c, c) for c in Crop.objects.values_list('country', flat=True).distinct()]
        self.fields['soil_type'].choices = [('', 'Any')] + [(s, s) for s in Crop.objects.values_list('soil_type', flat=True).distinct()]
        self.fields['season'].choices = [('', 'Any')] + [(s, s) for s in Crop.objects.values_list('season', flat=True).distinct()]
        self.fields['category'].choices = [('', 'Any')] + [(c, c) for c in Crop.objects.values_list('category', flat=True).distinct()]
