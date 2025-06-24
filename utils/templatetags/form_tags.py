from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


@register.simple_tag
def form_field(field):
    """
    Renders a single Django form field with:
    - Bootstrap 5 label
    - Help text if available
    - Inline validation errors
    """
    label_html = field.label_tag(attrs={"class": "form-label"})
    field_html = str(field)
    help_html = (
        f'<small class="form-text text-muted">{field.help_text}</small>'
        if field.help_text
        else ""
    )
    errors_html = "".join(
        f'<div class="invalid-feedback d-block">{e}</div>' for e in field.errors
    )

    return mark_safe(
        f"""
    <div class="mb-3">
        {label_html}
        {field_html}
        {help_html}
        {errors_html}
    </div>
    """
    )
