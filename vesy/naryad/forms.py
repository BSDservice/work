from django import forms
from .models import Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place, Consignee,\
                    Employer, Consignor

"""
class TaskForm(forms.Form):
    date = forms.DateTimeField(label='дата формирования задания')

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
