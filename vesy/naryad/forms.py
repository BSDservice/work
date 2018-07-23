from django import forms
from .models import Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place, Consignee,\
                    Employer, Consignor, Task
import datetime

"""
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['date', 'contractor']



class TaskForm(forms.Form):
    date = forms.DateTimeField(widget=forms.DateTimeInput)

    CONTRACTOR_SELECT = Contractor.objects.all()
    contractor = forms.Select(choices=CONTRACTOR_SELECT)

    CONSIGNEE_SELECT = Consignee.objects.all()
    consignee = forms.Select(choices=CONSIGNEE_SELECT)

    EMPLOYER_SELECT = Employer.objects.all()
    employer = forms.Select(choices=EMPLOYER_SELECT)

    CONSIGNOR_SELECT = Consignor.objects.all()
    consignor = forms.Select(choices=CONSIGNOR_SELECT)

    DESTINATION_SELECT = Destination.objects.all()
    destination = forms.Select(choices=DESTINATION_SELECT)

    PLACE_SELECT = Place.objects.all()
    place = forms.CharField(label='место погрузки')

    total_plan = forms.IntegerField(label='общий объем')
    daily_plan = forms.IntegerField(label='суточный объем')
    price = forms.IntegerField(label='цена')
    TASK_STATUS = (
        (1, 'черновик'),
        (2, 'к выполнению'),
        (3, 'выполнено'),
    )
    status = forms.Select(choices=TASK_STATUS)   
    RUBBLE_SELECT = Rubble.objects.all()
    rubble = forms.Select(choices=RUBBLE_SELECT)
    hours = forms.CharField(label='Часы приема')
    comments = forms.CharField(label='Комментарий')
"""


class TaskFormUpdate(forms.Form):
    date = forms.DateTimeField(widget=forms.DateTimeInput, label="Дата формирования")
    contractor = forms.CharField(disabled=True, label="Контрагент", required=False)
    consignee = forms.CharField(disabled=True, label="Грузополучатель", required=False)
    employer = forms.CharField(disabled=True, label="Заказчик", required=False)
    consignor = forms.CharField(disabled=True, label="Грузоотправитель", required=False)
    destination = forms.CharField(disabled=True, label="Пункт разгрузки", required=False)
    rubble = forms.CharField(disabled=True, label="Груз в документах", required=False)
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
