from django import forms


class DownloadTaskForm(forms.Form):
    start_id = forms.IntegerField(
        min_value=0,
        label="Начальный ID",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Например, 1000"}),
    )
    end_id = forms.IntegerField(
        min_value=0,
        label="Конечный ID",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Например, 2000"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        start_id = cleaned_data.get("start_id")
        end_id = cleaned_data.get("end_id")

        if start_id is not None and end_id is not None:
            if start_id > end_id:
                raise forms.ValidationError("start_id не может быть больше end_id")
            if end_id - start_id + 1 > 1_000_000:
                raise forms.ValidationError("Диапазон слишком большой (максимум 1 000 000 записей)")

        return cleaned_data