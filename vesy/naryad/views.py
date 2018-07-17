from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from .models import Record, Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place, Consignee,\
                          Employer, Consignor, Car, Task, AllocatedVolume
import json
from django.views.decorators.csrf import csrf_exempt
import datetime
from .tools import records_sync, save_data
from django.contrib.auth.decorators import login_required
#from .forms import TaskForm
from django.db.models import Sum


@csrf_exempt
def data_sync(request):
    """
    Синхронизация данных для таблиц: Record, Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality,
                                     Destination, Place, Consignee, Employer, Consignor
    GET - отправляет ID имеющихся записей
    POST - принимает словарь новых записей и записей удалённых, вносит изменения в базу согласно полученного словаря
    """

    if request.method == 'GET':
        if request.GET.get('type') == 'get_data':
            ans = {}
            lst = [Record, Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place]
            for cls in lst:
                tmp = cls.objects.all()
                ans[cls.__name__] = [i.wesy_id for i in tmp]
            return JsonResponse(ans)
        elif request.GET.get('type') == 'get_weights':
            records = Record.objects.all()
            ans = {'weights': {i.wesy_id: int(i.status) for i in records}}
            return JsonResponse(ans)
        else:
            return HttpResponse('Синхронизация прервана(1)')

    elif request.method == 'POST':
        if request.META['HTTP_USER_AGENT'] == 'my-app/0.0.1' and request.META['HTTP_TYPE'] == 'post_data':
            data = json.loads(request.body.decode('utf-8'))
            n = save_data(data['data'])
            return HttpResponse('Синхронизация прошла успешно')
        elif request.META['HTTP_USER_AGENT'] == 'my-app/0.0.1' and request.META['HTTP_TYPE'] == 'post_records':
            records = json.loads(request.body.decode('utf-8'))
            n = records_sync(records)
            print(Record.objects.filter(status=1).count())
            return HttpResponse(
                'Синхронизация прошла успешно')
        else:
            return HttpResponse('Синхронизация прервана(2)')
    else:
        return HttpResponse('Синхронизация прервана(3)')


@login_required
def naryad(request):
    tasks = Task.objects.all()
    for task in tasks:
        records = Record.objects.filter(task=task, date2__gt=task.date)
        shipped = records.aggregate(Sum('weight'))['weight__sum']
        if shipped is None:
            task.shipped = 0
        else:
            task.shipped = shipped
        try:
            task.save()
        except Exception:
            print(task)
    dostavka = tasks.filter(employer=Employer.objects.get(name='ООО Машпром'))
    samovyvoz = tasks.exclude(employer=Employer.objects.get(name='ООО Машпром'))
    return render(request, 'naryad/index.html', {'dostavka': dostavka, 'samovyvoz': samovyvoz})


@login_required
def add_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = Task(request.cleaned_data)
            task.save()
            tasks = Task.objects.all()
            return render(request, 'naryad/index.html', {'tasks': tasks})
    else:
        pass
        #form = NameForm()
    return render(request, 'naryd/add_task.html')


@login_required
def update_task(request, task_id):
    print(request.POST.items)
    task = Task.objects.get(id=task_id)
    tasks = Task.objects.all()
    for task in tasks:
        if task.status == 2:
            records = Record.objects.filter(task=task, date__gt=task.date)
            task.shipped = records.aggregate(Sum('weight'))
    
    return render(request, 'naryad/index.html', {'tasks': tasks})
    
