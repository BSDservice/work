from django import forms
from .models import Contractor, Rubble, RubbleRoot, RubbleQuality, Destination, Place, Consignee, Employer, Consignor


class TaskForm(forms.Form):
    date = forms.DateTimeField(widget=forms.DateTimeInput, label="Дата формирования")
    contractor = forms.ModelChoiceField(widget=forms.Select, queryset=Contractor.objects.all(), label="Контрагент")
    consignee = forms.ModelChoiceField(widget=forms.Select, queryset=Consignee.objects.all(), label="Грузополучатель")
    employer = forms.ModelChoiceField(widget=forms.Select, queryset=Employer.objects.all(), label="Заказчик-плательщик")
    consignor = forms.ModelChoiceField(widget=forms.Select, queryset=Consignor.objects.all(), label="Грузоотправитель")
    destination = forms.ModelChoiceField(widget=forms.Select, queryset=Destination.objects.all(), label="Пункт разгрузки")
    rubble = forms.ModelChoiceField(widget=forms.Select, queryset=Rubble.objects.all(), label="Груз в документах")
    cargo_type = forms.ModelChoiceField(widget=forms.Select, queryset=RubbleRoot.objects.all(), label='Фактический груз')
    cargo_quality = forms.ModelChoiceField(widget=forms.Select, queryset=RubbleQuality.objects.all(), label='Качество груза', required=False)
    place = forms.ModelChoiceField(widget=forms.Select, queryset=Place.objects.all(), label='Место погрузки', required=False)
    total_plan = forms.IntegerField(label='Общий объем')
    daily_plan = forms.IntegerField(label='Суточный объем')
    TASK_STATUS = (
        (1, 'ЧЕРНОВИК'),
        (2, 'К ВЫПОЛНЕНИЮ'),
        (3, 'ВЫПОЛНЕНО'),
    )
    status = forms.ChoiceField(widget=forms.Select, choices=TASK_STATUS, label="Статус заявки")

    hours = forms.CharField(label='Часы приема')
    comments = forms.CharField(label='Комментарий', required=False)


class TaskFormUpdate(forms.Form):
    date = forms.DateTimeField(widget=forms.DateTimeInput, label="Дата формирования", input_formats=['%Y-%m-%dT%H:%M', ])
    # contractor = forms.CharField(disabled=True, label="Контрагент", required=False)
    # consignee = forms.CharField(disabled=True, label="Грузополучатель", required=False)
    # employer = forms.CharField(disabled=True, label="Заказчик", required=False)
    # consignor = forms.CharField(disabled=True, label="Грузоотправитель", required=False)
    # destination = forms.CharField(disabled=True, label="Пункт разгрузки", required=False)
    # rubble = forms.CharField(disabled=True, label="Груз в документах", required=False)
    cargo_type = forms.ModelChoiceField(widget=forms.Select, queryset=RubbleRoot.objects.all(), label='Фактический груз')
    cargo_quality = forms.ModelChoiceField(widget=forms.Select, queryset=RubbleQuality.objects.all(), label='Качество груза', required=False)
    # place = forms.ModelChoiceField(widget=forms.Select, queryset=Place.objects.all(), label='Место погрузки', required=False)
    total_plan = forms.IntegerField(label='Общий объем')
    daily_plan = forms.IntegerField(label='Суточный объем')
    """
    TASK_STATUS = (
        (1, 'ЧЕРНОВИК'),
        (2, 'К ВЫПОЛНЕНИЮ'),
        (3, 'ВЫПОЛНЕНО'),
    )
    status = forms.ChoiceField(widget=forms.Select, choices=TASK_STATUS, label="Статус заявки")
    """

    hours = forms.CharField(label='Часы приема', required=False)
    comments = forms.CharField(label='Комментарий', required=False)
