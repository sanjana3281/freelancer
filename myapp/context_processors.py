from .models import Freelancer, Notification

def freelancer_nav_context(request):
    # Only show for logged-in freelancers (you use session-based auth)
    fid = request.session.get("freelancer_id")
    role = request.session.get("role")

    if not fid or role != "freelancer":
        return {"nav_is_freelancer": False, "nav_unread_count": 0}

    try:
        fr = Freelancer.objects.only("id").get(id=fid)
    except Freelancer.DoesNotExist:
        return {"nav_is_freelancer": False, "nav_unread_count": 0}

    unread = Notification.objects.filter(freelancer=fr, is_read=False).count()
    return {"nav_is_freelancer": True, "nav_unread_count": unread}
