from django.shortcuts import redirect, resolve_url


class ResumeFailure(Exception):
    pass


def set_resume(request):
    try:
        resume_points = request._resume_points
    except AttributeError:
        if not hasattr(request, "META"):
            raise TypeError(
                "add_resume_point() argument must be an HttpRequest object, not "
                "'%s'." % request.__class__.__name__
            )
        raise ResumeFailure(
            "You cannot add resume points without installing "
            "resume.middleware.ResumeMiddleware"
        )
    else:
        return resume_points.add(request.get_full_path())


def resume_or_redirect(request, to, permanent=False, *args, **kwargs):
    if len(request._resume_points) > 0:
        resume_from = request._resume_points.pop()
        return redirect(resume_from)
    else:
        return redirect(to, permanent=permanent, *args, **kwargs)
