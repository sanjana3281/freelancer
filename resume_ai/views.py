from django.shortcuts import render

# Create your views here.
import os, uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .services.suggester import extract_text_from_file, suggest_changes
from django.contrib.auth.decorators import login_required

# @login_required(login_url="/login/")  # optional: require login
def resume_suggest_view(request):
    if request.method == "POST":
        f = request.FILES.get("resume")
        if not f:
            messages.error(request, "Please upload a PDF or DOCX.")
            return redirect("resume_ai:suggest")

        ext = os.path.splitext(f.name)[1].lower()
        if ext not in [".pdf", ".docx"]:
            messages.error(request, "Allowed types: PDF, DOCX.")
            return redirect("resume_ai:suggest")

        # size guard
        if f.size > 5 * 1024 * 1024:
            messages.error(request, "File too large (max 5MB).")
            return redirect("resume_ai:suggest")

        # save
        dest = settings.MEDIA_ROOT / "resumes"
        os.makedirs(dest, exist_ok=True)
        path = dest / f"{uuid.uuid4().hex}{ext}"
        with open(path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)

        # extract + analyze
        text = extract_text_from_file(str(path))
        result = suggest_changes(text)
        return render(request, "resume_ai/suggestions.html", {"result": result})

    return render(request, "resume_ai/upload.html")   # <-- must return on GET
