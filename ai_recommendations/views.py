import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import AIQueryHistory
import httpx

# Load OpenRouter key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Compose message history
def get_conversation_history(user):
    history = AIQueryHistory.objects.filter(user=user).order_by('-timestamp')[:5]
    messages = []
    for entry in reversed(history):
        messages.append({"role": "user", "content": entry.prompt})
        messages.append({"role": "assistant", "content": entry.response})
    return messages

@login_required
def ai_recommendations_view(request):
    prompt = ""
    response_text = ""

    if request.method == "POST":
        # Handle delete
        if 'delete_id' in request.POST:
            AIQueryHistory.objects.filter(id=request.POST['delete_id'], user=request.user).delete()
            return redirect('ai_recommendations')

        # Handle query
        prompt = request.POST.get("prompt", "").strip()
        followup = request.POST.get("followup", "") == "true"

        if prompt:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",   # Change if deployed
                "X-Title": "Smart Farming Dashboard"
            }

            # Build conversation history
            messages = []
            if followup:
                messages.extend(get_conversation_history(request.user))
            messages.append({"role": "user", "content": prompt})

            try:
                response = httpx.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": "openai/gpt-4o-mini",   # safer choice than 3.5-turbo
                        "messages": messages,
                        "temperature": 0.7,
                    },
                    timeout=30
                )
                result = response.json()

                # Debugging log
                print("DEBUG OpenRouter Response:", result)

                if "choices" in result:
                    response_text = result['choices'][0]['message']['content']
                else:
                    response_text = f"API Error: {result}"

                # Save to DB
                AIQueryHistory.objects.create(
                    user=request.user,
                    prompt=prompt,
                    response=response_text,
                    timestamp=timezone.now()
                )

            except Exception as e:
                response_text = f"Error: {str(e)}"

    # History for UI display
    history = AIQueryHistory.objects.filter(user=request.user).order_by('-timestamp')[:5]

    return render(request, 'ai_recommendations.html', {
        'prompt': prompt,
        'response': response_text,
        'history': history,
    })
