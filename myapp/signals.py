# myapp/signals.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from .models import Job, Freelancer, Notification

@receiver(post_save, sender=Job)
def notify_all_freelancers_on_job_create(sender, instance: Job, created, **kwargs):
    if not created:
        return

    # Link to job detail (your template uses: {% url 'job_detail' job.id %})
    try:
        job_url = reverse("job_detail", args=[instance.id])
    except Exception:
        job_url = "/"

    # --- 1) In-app notifications for everyone ---
    freelancers = Freelancer.objects.select_related("profile").all()
    Notification.objects.bulk_create([
        Notification(
            freelancer=f,
            message=f"New job posted: {instance.title}",
            url=job_url,
        ) for f in freelancers
    ], batch_size=1000)

    # --- 2) Email blast to opted-in freelancers ---
    recipients = []
    for f in freelancers:
        prof = getattr(f, "profile", None)
        if prof is None or not getattr(prof, "email_notifications", True):
            continue
        # prefer Freelancer.email; fallback to profile.contact_email
        email = getattr(f, "email", "") or getattr(prof, "contact_email", "")
        if email:
            recipients.append(email)

    if not recipients:
        return

    subject = f"New job: {instance.title}"
    context = {
        "job": instance,
        "company": instance.recruiter.recruiter.company_name if instance.recruiter else "Recruiter",
        "job_url_full": (getattr(settings, "SITE_BASE_URL", "").rstrip("/") + job_url) if getattr(settings, "SITE_BASE_URL", "") else job_url,
    }
    html = render_to_string("emails/job_posted.html", context)
    text = strip_tags(html)

    def _send():
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[],                         # keep addresses private
            bcc=list(set(recipients)),     # BCC all opted-in freelancers
        )
        msg.attach_alternative(html, "text/html")
        msg.send()

    # send only after the Job save commits
    transaction.on_commit(_send)
