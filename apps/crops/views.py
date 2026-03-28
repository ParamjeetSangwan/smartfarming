from django.shortcuts import render
from .models import Crop
from .forms import CropFilterForm

def crop_suggestion(request):
    form = CropFilterForm(request.GET or None)
    crops = Crop.objects.all()

    if form.is_valid():
        country = form.cleaned_data.get('country')
        soil_type = form.cleaned_data.get('soil_type')
        temperature = form.cleaned_data.get('temperature')
        season = form.cleaned_data.get('season')
        category = form.cleaned_data.get('category')

        if country:
            crops = crops.filter(country=country)
        if soil_type:
            crops = crops.filter(soil_type=soil_type)
        if temperature is not None:
            crops = crops.filter(temperature=temperature)
        if season:
            crops = crops.filter(season=season)
        if category:
            crops = crops.filter(category=category)
    else:
        crops = Crop.objects.none()  # or crops = Crop.objects.all() if you want all shown when no filter

    return render(request, 'crop_suggestion.html', {'form': form, 'crops': crops})
