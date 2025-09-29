from django.shortcuts import render
import requests
from users.models import UserProfile  # ✅ Add this line

def weather_view(request):
    profile = UserProfile.objects.get(user=request.user)
    city = request.GET.get('city') or profile.location or 'Delhi'

    try:
        api_key = '96abd0e67bb4f6b8bef607889abde06f'
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
        response = requests.get(url)
        weather_data = response.json()
        if weather_data.get("cod") != 200:
            raise ValueError("City not found")
    except Exception as e:
        return render(request, 'weather.html', {'error': str(e)})

    return render(request, 'weather.html', {'weather_data': weather_data})
