from django import template

register = template.Library()


@register.filter
def millions(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value  # If invalid number, just return it

    # If number is one million or more → convert to millions
    if value >= 1_000_000:
        return f"{round(value / 1_000_000, 2)}M"

    # Otherwise → format with commas (e.g. 530,000)
    return f"{int(value):,}"
