# myapp/signals.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.db.models import Avg, Count

from .models import Job, Freelancer, Notification,FreelancerReview


@receiver(post_save, sender=Job)
def notify_all_freelancers_on_job_create(sender, instance: Job, created, **kwargs):
    if not created:
        return

    # URLs
    try:
        job_url = reverse("job_detail", args=[instance.id])
    except Exception:
        job_url = "/"

    # ---------- Recruiter info (from your models) ----------
    # job.recruiter -> RecruiterProfile
    rp = getattr(instance, "recruiter", None)                # RecruiterProfile
    acct = getattr(rp, "recruiter", None)                    # Recruiter

    company_name = getattr(acct, "company_name", "Recruiter")
    contact_person = getattr(acct, "contact_person", company_name)

    # sender/reply-to email
    recruiter_email = (
        getattr(acct, "email", None)                         # Recruiter.email (required on your model)
        or getattr(rp, "contact_email_alt", None)            # fallback
        or getattr(settings, "DEFAULT_FROM_EMAIL", None)     # final fallback
    )

    # ---------- In-app notifications ----------
    freelancers = Freelancer.objects.select_related("profile").all()
    Notification.objects.bulk_create([
        Notification(
            freelancer=f,
            message=f"New job posted: {instance.title}",
            url=job_url,
        ) for f in freelancers
    ], batch_size=1000)

    # ---------- Email recipients (only opted-in / with email) ----------
    recipients = []
    for f in freelancers:
        prof = getattr(f, "profile", None)
        if prof is None or not getattr(prof, "email_notifications", True):
            continue
        email = getattr(f, "email", "") or getattr(prof, "contact_email", "")
        if email:
            recipients.append(email)

    if not recipients:
        return

    # ---------- Email content ----------
    subject = f"New Job Posted: {instance.title}"
    context = {
        "job": instance,
        "company": company_name,
        "recruiter_name": contact_person,
        "job_url_full": (getattr(settings, "SITE_BASE_URL", "").rstrip("/") + job_url)
                        if getattr(settings, "SITE_BASE_URL", "") else job_url,
    }
    html = render_to_string("emails/job_posted.html", context)
    text = strip_tags(html)

    # ---------- Send AFTER commit; never 500 the request ----------
    def _send():
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email=recruiter_email,                 # sender shown in inbox
                to=[],                                      # keep addresses private
                bcc=list(set(recipients)),                  # all freelancers
                reply_to=[recruiter_email] if recruiter_email else None,
            )
            msg.attach_alternative(html, "text/html")
            msg.send(fail_silently=False)                   # show real SMTP errors in console
            print(f"✅ Job email sent from {recruiter_email} to {len(recipients)} freelancers.")
        except Exception as e:
            # Don’t crash the request if email fails
            print(f"❌ Email sending failed: {e}")

    transaction.on_commit(_send)




#for review and contact


def _recalc(f):
    s = f.reviews_received.aggregate(avg=Avg("rating"), cnt=Count("id"))
    f.rating_avg = s["avg"] or None
    f.rating_count = s["cnt"] or 0
    f.save(update_fields=["rating_avg", "rating_count"])

@receiver(post_save, sender=FreelancerReview)
def _on_save(sender, instance, **kw): _recalc(instance.freelancer)

@receiver(post_delete, sender=FreelancerReview)
def _on_del(sender, instance, **kw): _recalc(instance.freelancer)
