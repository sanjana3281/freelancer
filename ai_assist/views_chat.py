from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .services_gemini import analyze_chat_with_gemini


# try:
#     from openai import OpenAI
#     _openai_available = True
# except Exception:
#     _openai_available = False

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# @login_required
def resume_chat_page(request):
    """Renders the chat UI page."""
    return render(request, "ai/resume_chat.html")

# @require_http_methods(["POST"])
# @login_required
# @login_required
# @require_http_methods(["POST"])
def resume_chat_reply(request):
    msg = (request.POST.get("message") or "").strip()
    resume = (request.POST.get("resume") or "").strip()
    if not msg:
        return JsonResponse({"reply": "Please type a question about your resume."})
    reply = analyze_chat_with_gemini(resume, msg)
    return JsonResponse({"reply": reply})


@csrf_exempt
# @login_required
def resume_analysis(request):
    if request.method == "POST":
        # Here you can later call the OpenAI API or analyze resume text
        return JsonResponse({"ok": True, "message": "AI will analyze the resume here."})
    return JsonResponse({"error": "POST only"}, status=405)


# ai_assist/views_chat.py
# from django.shortcuts import render
# from django.views.decorators.http import require_POST
# from django.http import JsonResponse

# def resume_chat_page(request):
#     # simple page; use whatever template you already made for chat
#     return render(request, "ai/resume_chat.html", {})

# @require_POST
# def resume_chat_reply(request):
#     # you already have this one; keeping here for completeness
#     text = request.POST.get("q", "").strip()
#     if not text:
#         return JsonResponse({"ok": False, "error": "No question."}, status=400)
#     # … generate reply …
#     return JsonResponse({"ok": True, "reply": "stub"})
