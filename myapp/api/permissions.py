from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsRecruiter(BasePermission):
    """
    Allow only logged-in users whose session role is 'recruiter'
    (or adapt to your auth if you use Django auth groups).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated or bool(request.session.get("role") == "recruiter")

class IsOwnerRecruiterProfile(BasePermission):
    """
    Object-level: only the profile owner can access/modify.
    """
    def has_object_permission(self, request, view, obj):
        recruiter_id_in_session = request.session.get("recruiter_id")
        return bool(recruiter_id_in_session and obj.recruiter_id == recruiter_id_in_session)
