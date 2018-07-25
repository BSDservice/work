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
from .forms import TaskFormUpdate
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
            return HttpResponse(
                'Синхронизация прошла успешно')
        else:
            return HttpResponse('Синхронизация прервана(2)')
    else:
        return HttpResponse('Синхронизация прервана(3)')


@login_required
def naryad(request):
    """
    Отображает задания
    """
    tasks = Task.objects.all().order_by('status', 'contractor')
    for task in tasks:
        records = Record.objects.filter(task=task, date2__gt=task.date)
        shipped = records.aggregate(Sum('weight'))['weight__sum']
        daily = 0
        x = datetime.datetime.now().time() < task.date.time()
        for rec in records:
            if x:
                if rec.date2 > datetime.datetime.now().replace(hour=task.date.time().hour,
                                                               minute=task.date.time().minute,
                                                               second=task.date.time().second)+datetime.timedelta(days=-1):
                    daily += rec.weight
            else:
                if rec.date2 > datetime.datetime.now().replace(hour=task.date.time().hour,
                                                               minute=task.date.time().minute,
                                                               second=task.date.time().second):
                    daily += rec.weight

        task.shipped = shipped if shipped else 0
        task.daily_shipped = daily if daily else 0
        task.finish()
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
    if request.method == 'GET' and task_id == 0:
        task_id = request.GET.get('task_id')
    task = Task.objects.get(id=task_id)
    if request.method == 'POST':
        form = TaskFormUpdate(request.POST)
        if form.is_valid():
            task.date = form.cleaned_data['date']
            task.comments = form.cleaned_data['comments']
            task.daily_plan = form.cleaned_data['daily_plan']
            task.total_plan = form.cleaned_data['total_plan']
            task.status = form.cleaned_data['status']
            task.hours = form.cleaned_data['hours']
            task.cargo_type = form.cleaned_data['cargo_type']
            task.cargo_quality = form.cleaned_data['cargo_quality']
            task.place = form.cleaned_data['place']
            task.check_status()
            task.save()
            return naryad(request)
        else:
            print(form.errors)
            return naryad(request)
    else:
        form = TaskFormUpdate(initial={'date': task.date, 'contractor': task.contractor, 'comments': task.comments,
                                       'consignee': task.consignee, 'employer': task.employer, 'consignor': task.consignor,
                                       'destination': task.destination, 'place': task.place, 'total_plan': task.total_plan,
                                       'daily_plan': task.daily_plan, 'status': task.status, 'rubble': task.rubble,
                                       'hours': task.hours, 'cargo_type': task.cargo_type,
                                       'cargo_quality': task.cargo_quality}).as_p()
        return render(request, 'naryad/edit.html', {'form': form, 'task': task})


"""
consignee, employer, consignor, destination, place, total_plan, daily_plan, status, rubble, hours
"""