# ai_recommendations/views.py

import os
import base64
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import AIQueryHistory
import httpx
from django.conf import settings

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


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
    upload_error = ""

    # Pre-fill from scheme page — ?scheme=PM-KISAN...
    scheme_prefill = request.GET.get('scheme', '')
    initial_prompt = ""
    if scheme_prefill:
        initial_prompt = (
            f"Tell me everything about the {scheme_prefill} government scheme — "
            f"eligibility, benefits, how to apply, required documents, and any tips."
        )

    if request.method == "POST":
        # Handle clear all history
        if 'clear_all' in request.POST:
            AIQueryHistory.objects.filter(user=request.user).delete()
            return redirect('ai_recommendations')

        # Handle single delete
        if 'delete_id' in request.POST:
            AIQueryHistory.objects.filter(
                id=request.POST['delete_id'], user=request.user
            ).delete()
            return redirect('ai_recommendations')

        # Handle AI query
        prompt = request.POST.get("prompt", "").strip()
        followup = request.POST.get("followup", "") == "true"
        uploaded_file = request.FILES.get("upload_file")

        if prompt or uploaded_file:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Smart Farming Dashboard"
            }

            messages_list = []
            if followup:
                messages_list.extend(get_conversation_history(request.user))

            # Build content — text + optional image
            if uploaded_file:
                # Validate file
                if uploaded_file.content_type not in ALLOWED_IMAGE_TYPES:
                    upload_error = "Only JPG, PNG, GIF, WEBP images are supported."
                elif uploaded_file.size > MAX_IMAGE_SIZE:
                    upload_error = "Image too large. Max 5MB allowed."
                else:
                    image_data = base64.b64encode(uploaded_file.read()).decode('utf-8')
                    user_content = [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{uploaded_file.content_type};base64,{image_data}"
                            }
                        }
                    ]
                    if prompt:
                        user_content.append({"type": "text", "text": prompt})
                    else:
                        user_content.append({
                            "type": "text",
                            "text": (
                                "Please analyze this farming image. Identify any crops, pests, "
                                "diseases, or soil conditions visible, and provide recommendations."
                            )
                        })
                    messages_list.append({"role": "user", "content": user_content})
                    # For history label use prompt or filename
                    prompt = prompt or f"[Image: {uploaded_file.name}]"
            else:
                messages_list.append({"role": "user", "content": prompt})

            if not upload_error:
                try:
                    response = httpx.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json={
                            "model": "openai/gpt-4o-mini",
                            "messages": messages_list,
                            "temperature": 0.7,
                        },
                        timeout=60
                    )
                    result = response.json()

                    if "choices" in result:
                        response_text = result['choices'][0]['message']['content']
                    else:
                        response_text = f"API Error: {result}"

                    AIQueryHistory.objects.create(
                        user=request.user,
                        prompt=prompt,
                        response=response_text,
                        timestamp=timezone.now()
                    )

                except Exception as e:
                    response_text = f"Error: {str(e)}"

    history = AIQueryHistory.objects.filter(user=request.user).order_by('-timestamp')[:5]

    return render(request, 'ai_recommendations.html', {
        'prompt': prompt,
        'response': response_text,
        'history': history,
        'upload_error': upload_error,
        'initial_prompt': initial_prompt,
    })