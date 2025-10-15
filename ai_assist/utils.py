# ai_assist/utils.py
def profile_to_json(profile):
    f = profile.freelancer

    roles = [
        {
            "title": getattr(r.role, "name", None) or getattr(r, "title", None),
            "years": getattr(r, "years", None),
        }
        for r in profile.freelancerrole_set.all()
    ]

    skills = [
        {
            "name": getattr(s.skill, "name", None) or getattr(s, "name", None),
            "level": getattr(s, "level", None),
            "years": getattr(s, "years", None),
        }
        for s in profile.freelancerskill_set.all()
    ]

    langs = [
        {
            "name": getattr(l.language, "name", None) or getattr(l, "name", None),
            "proficiency": getattr(l, "proficiency", None),
        }
        for l in profile.freelancerlanguage_set.all()
    ]

    projects = [
        {
            "title": p.title,
            "role": getattr(p, "role_title", None)
                    or (getattr(p, "role", None) and getattr(p.role, "name", None)),
            "summary": getattr(p, "description", None),
            "start": getattr(p, "start_date", None) and p.start_date.isoformat(),
            "end": getattr(p, "end_date", None) and p.end_date.isoformat(),
            "links": {
                "demo": getattr(p, "demo_url", None) or getattr(p, "live_demo", None),
                "repo": getattr(p, "github_url", None)
                        or getattr(p, "repo_url", None)
                        or getattr(p, "repository", None),
            },
            "results": getattr(p, "results", None),
        }
        for p in profile.freelancerproject_set.all()
    ]

    achievements = [
        {
            "title": a.title,
            "when": getattr(a, "date", None) and a.date.isoformat(),
            "notes": getattr(a, "description", None),
        }
        for a in profile.achievement_set.all()
    ]

    publications = [
        {
            "title": p.title,
            "venue": getattr(p, "venue", None),
            "year": getattr(p, "year", None),
            "link": getattr(p, "url", None),
        }
        for p in profile.publication_set.all()
    ]

    return {
        "freelancer": {"name": f.name, "headline": getattr(profile, "headline", None)},
        "roles": roles,
        "skills": skills,
        "languages": langs,
        "projects": projects,
        "achievements": achievements,
        "publications": publications,
        "portfolio": getattr(profile, "portfolio_url", None),
        "location": {"city": getattr(profile, "city", None), "country": getattr(profile, "country", None)},
    }
