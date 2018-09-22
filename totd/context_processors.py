from django.db.models import Q
from .models import Tip

import datetime

def tips(request):
    """
    Adds a list of tips for the current request
    """
    if not request.user.is_authenticated:
        return {}

    #import pdb; pdb.set_trace()

    tips = Tip.objects.filter(run_start__lte=datetime.datetime.now())
    tips = tips.filter(Q(run_end__isnull=True) | Q(run_end__gte=datetime.datetime.now()))
    tips = tips.filter(Q(view='') | Q(view=request.resolver_match.url_name)).exclude(seen_by=request.user)
    if len(tips) > 0:
        tips[0].seen_by.add(request.user)

        return {
            'tip': tips[0],
        }

    return {}