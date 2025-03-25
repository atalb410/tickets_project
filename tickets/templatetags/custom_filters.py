from django import template

register = template.Library()

@register.filter
def some_existing_filter(value):
    # Existing filter logic
    return value

@register.filter
def has_accepted_quote(quotes_with_labels):
    return any(quote.status == "Accepted" for quote, _ in quotes_with_labels)

@register.filter
def replace_underscore(value):
    if isinstance(value, str):  # Ensure the value is a string
        return value.replace("_", " ")
    return value  # Return unchanged if not a string