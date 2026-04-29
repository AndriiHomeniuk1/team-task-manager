from django import forms
from django.forms.widgets import ClearableFileInput
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe

from .models import Worker


class CustomClearableFileInput(ClearableFileInput):
    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {"name": name})
        input_html = f'<input type="file"{flatatt(final_attrs)}>'

        preview_html = ""
        if value and hasattr(value, "url"):
            preview_html = (
                f'<img src="{value.url}"'
                f'alt="avatar"'
                f'class="avatar avatar-lg shadow-sm rounded-circle mb-2">'
            )

        clear_html = ""
        if value:
            clear_html = f"""
                <div class="form-check mb-2">
                  <input type="checkbox"
                         name="{self.clear_checkbox_name(name)}"
                         id="{self.clear_checkbox_id(name)}"
                         class="form-check-input">
                  <label for="{self.clear_checkbox_id(name)}"
                         class="form-check-label text-dark">
                    Remove avatar
                  </label>
                </div>
            """

        return mark_safe(input_html + preview_html + clear_html)


class WorkerUpdateForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = [
            "username",
            "first_name",
            "last_name",
            "position",
            "phone_number",
            "email",
            "location",
            "github_url",
            "avatar",
        ]

        widgets = {
            "avatar": CustomClearableFileInput(
                attrs={
                    "class": (
                        "form-control border px-3 py-2"
                        "rounded-pill shadow-sm"
                    )
                }
            ),
        }
