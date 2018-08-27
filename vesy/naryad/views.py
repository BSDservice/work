from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import Record, Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place, Consignee,\
                          Employer, Consignor, Car, Task, AllocatedVolume
import json
from django.views.decorators.csrf import csrf_exempt
import datetime
from .tools import records_sync, save_data
from django.contrib.auth.decorators import login_required
from .forms import TaskFormUpdate, TaskForm
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
            lst = [Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place]
            for cls in lst:
                tmp = cls.objects.all()
                ans[cls.__name__] = [i.name for i in tmp]
            return JsonResponse(ans)
        elif request.GET.get('type') == 'get_weights':
            records = Record.objects.filter(date1__gt=datetime.datetime.now()-datetime.timedelta(hours=12))
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
            if n == 'update_data':
                return HttpResponse('update_data')
            else:
                return HttpResponse('Синхронизация прошла успешно')
        else:
            return HttpResponse('Синхронизация прервана(2)')
    else:
        return HttpResponse('Синхронизация прервана(3)')


@login_required
def naryad(request):
    """
    Отображает задания
    """
    tasks = Task.objects.filter(status='2').order_by('status', 'contractor')
    for task in tasks:
        task.cars_on_loading = 0
        records = Record.objects.filter(task=task, date2__gt=task.date, status__in=['1', '2'])
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
            if rec.status == '1':
                task.cars_on_loading += 1

        task.shipped = shipped if shipped else 0
        task.daily_shipped = daily if daily else 0
        task.finish()
        task.check_status()
        try:
            task.save()
        except Exception:
            print(task)
    dostavka = tasks.filter(employer=Employer.objects.get(name='ООО Машпром'))
    samovyvoz = tasks.exclude(employer=Employer.objects.get(name='ООО Машпром'))
    cargo_type = {str(i["id"]): i["name"] for i in RubbleRoot.objects.values() if i["name"] is not None}
    cargo_quality = {str(i["id"]): i["name"] for i in RubbleQuality.objects.values() if i["name"] is not None}
    return render(request, 'naryad/index.html', {'dostavka': dostavka, 'samovyvoz': samovyvoz, 'cargo_type': cargo_type, 'cargo_quality': cargo_quality})


@login_required
def show_hide_tasks(request):
    if request.method == 'GET':
        tasks = Task.objects.filter(status__in=['1', '3']).order_by('status', 'contractor')
        dostavka = tasks.filter(employer=Employer.objects.get(name='ООО Машпром'))
        samovyvoz = tasks.exclude(employer=Employer.objects.get(name='ООО Машпром'))
        return render(request, 'naryad/list_hide_tasks.html', {'dostavka': dostavka, 'samovyvoz': samovyvoz})


@login_required
def add_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            try:
                task = Task.objects.get(contractor=form.cleaned_data['contractor'], consignee=form.cleaned_data['consignee'],
                                        employer=form.cleaned_data['employer'], consignor=form.cleaned_data['consignor'],
                                        destination=form.cleaned_data['destination'], rubble=form.cleaned_data['rubble'])
                task.date = form.cleaned_data['date']
                task.comments = form.cleaned_data['comments']
                task.daily_plan = form.cleaned_data['daily_plan']
                task.total_plan = form.cleaned_data['total_plan']
                task.status = form.cleaned_data['status']
                task.hours = form.cleaned_data['hours']
                task.cargo_type = form.cleaned_data['cargo_type']
                task.cargo_quality = form.cleaned_data['cargo_quality']
                task.place = form.cleaned_data['place']
                task.save()
            except Task.DoesNotExist:
                task = Task()
                task.contractor = form.cleaned_data['contractor']
                task.consignee = form.cleaned_data['consignee']
                task.employer = form.cleaned_data['employer']
                task.consignor = form.cleaned_data['consignor']
                task.destination = form.cleaned_data['destination']
                task.rubble = form.cleaned_data['rubble']
                task.date = form.cleaned_data['date']
                task.comments = form.cleaned_data['comments']
                task.daily_plan = form.cleaned_data['daily_plan']
                task.total_plan = form.cleaned_data['total_plan']
                task.status = form.cleaned_data['status']
                task.hours = form.cleaned_data['hours']
                task.cargo_type = form.cleaned_data['cargo_type']
                task.cargo_quality = form.cleaned_data['cargo_quality']
                task.place = form.cleaned_data['place']
                task.save()
            return redirect('naryad')
    else:
        form = TaskForm(initial={'date': datetime.datetime.now()}).as_p()
        return render(request, 'naryad/add_task.html', {'form': form})


@login_required
def update_task(request, task_id):
    """
    if request.method == 'GET' and task_id == 0:
        task_id = request.GET.get('task_id')
    task = Task.objects.get(id=task_id)
    """
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        task = Task.objects.get(id=task_id)
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
            task.save()
            return redirect('naryad')
        else:
            print(form.errors)
            print(request.POST)
            return redirect('naryad')
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