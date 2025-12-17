from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps


def anonymous_required(path_url="main_topics"):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                try:
                    return redirect(reverse(path_url))
                except:
                    return redirect(path_url)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

