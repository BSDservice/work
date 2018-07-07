from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from naryad.models import Record, Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place, Consignee,\
                          Employer, Consignor, Car, Task, AllocatedVolume
from django.views.decorators.csrf import ensure_csrf_cookie
import socket
import json
from django.views.decorators.csrf import csrf_exempt
import datetime


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
            d = delete_data(data['delete'])
            return HttpResponse('Синхронизация прошла успешно\nВнесено записей:{0}, удалено: {1}'.format(str(n), str(d)))
        elif request.META['HTTP_USER_AGENT'] == 'my-app/0.0.1' and request.META['HTTP_TYPE'] == 'post_records':
            records = json.loads(request.body.decode('utf-8'))
            n, d = records_sync(records)
            return HttpResponse(
                'Синхронизация прошла успешно\nВнесено записей:{0}, удалено: {1}'.format(str(n), str(d)))
        else:
            return HttpResponse('Синхронизация прервана(2)')
    else:
        return HttpResponse('Синхронизация прервана(3)')


def save_data(data):
    obj_dict = {'Record': Record,
                'Contractor': Contractor,
                'Carrier': Carrier,
                'Rubble': Rubble,
                'RubbleRoot': RubbleRoot,
                'RubbleQuality': RubbleQuality,
                'Destination': Destination,
                'Place': Place}
    for tab in data: data[tab].append([0,'неопределённый'])
    n = 0
    for tab, recs in data.items():
        for item in recs:
            if tab == 'Contractor':
                for tab_split in [Consignee, Employer, Consignor, Contractor]:
                    entry = tab_split(wesy_id=item[0], name=item[1])
                    entry.save()
            else:
                entry = obj_dict[tab](wesy_id=item[0], name=item[1])
                entry.save()
            n += 1
    return n


def delete_data(data):
    obj_dict = {'Record': Record,
                'Contractor': Contractor,
                'Carrier': Carrier,
                'Rubble': Rubble,
                'RubbleRoot': RubbleRoot,
                'RubbleQuality': RubbleQuality,
                'Destination': Destination,
                'Place': Place}
    n = 0
    for tab, recs in data.items():
        if tab == 'Contractor':
            for org in [Consignee, Employer, Consignor, Contractor]:
                org.objects.filter(wesy_id__in=recs).delete()
        else:
            obj_dict[tab].objects.filter(wesy_id__in=recs).delete()
        n += len(recs)
    return n


def records_sync(data):
    """
    Создает или обновляет записи о взвешивании, сопостовляя записи заданиям на отгрузку, если нет таковых создаёт их.
    Сверяет отгруженный объем по заданию и меняет статус задания если объём вывезен.
    Вносит изменения в выделенный объём перевозчику.
    """
    n = 0
    for wesy_id, rec in data['weights'].items():
        n += 1
        try:
            car = Car.objects.get(num=rec[0])
        except ObjectDoesNotExist:
            car = Car(num=rec[0], brand=[14])
            car.save()
        
        contractor = Contractor.objects.get(name=rec[19] if rec[19] is not None else "неопределённый")
        rubble = Rubble.objects.get(name=rec[2] if rec[2] is not None else "неопределённый")
        consignee = Consignee.objects.get(name=rec[6] if rec[6] is not None else "неопределённый")
        try:
            destination = Destination.objects.get(name=rec[7] if rec[7] is not None else "неопределённый")
        except ObjectDoesNotExist:
            print(rec)
        employer = Employer.objects.get(name=rec[9] if rec[9] is not None else "неопределённый")
        consignor = Consignor.objects.get(name=rec[10] if rec[10] is not None else "неопределённый")
        carrier = Carrier.objects.get(name=rec[4] if rec[4] is not None else "неопределённый")
        place = Place.objects.get(name=rec[5] if rec[5] is not None else "неопределённый")

        try:
            task = Task.objects.get(contractor=contractor, consignee=consignee, destination=destination,
                                    employer=employer, consignor=consignor, rubble=rubble, status=2)
        except ObjectDoesNotExist:
            task = Task(contractor=contractor, consignee=consignee, destination=destination, employer=employer,
                        consignor=consignor, rubble=rubble, status=2, date=datetime.datetime.now())

        if rec[13] is not None:
            date2 = datetime.datetime(year=rec[13][0], month=rec[13][1], day=rec[13][2], hour=rec[13][3],
                                      minute=rec[13][4], second=rec[13][5], microsecond=rec[13][6])
        else:
            date2 = rec[13]
        if rec[3] is str:
            weight = None
        else:
            weight = rec[3]

        try:
            obj = Record.objects.get(wesy_id=rec[15])
            obj.date1 = datetime.datetime(year=rec[12][0], month=rec[12][1], day=rec[12][2], hour=rec[12][3], minute=rec[12][4], second=rec[12][5], microsecond=rec[12][6])
            obj.date2 = date2
            obj.ttn = rec[11]
            obj.car = car
            obj.contractor = contractor
            obj.rubble = rubble
            obj.weight = float(rec[3])
            obj.consignee = consignee
            obj.destination = destination
            obj.employer = employer
            obj.consignor = consignor
            obj.carrier = carrier
            obj.place = place
            obj.wesy_id = rec[15]
            obj.status = rec[18]
            obj.task = task
        except ObjectDoesNotExist:

            obj = Record(date1=datetime.datetime(year=rec[12][0], month=rec[12][1], day=rec[12][2], hour=rec[12][3],
                                                 minute=rec[12][4], second=rec[12][5], microsecond=rec[12][6]),
                         ttn=rec[11], car=car, contractor=contractor, rubble=rubble, weight=weight,
                         consignee=consignee, destination=destination, employer=employer, consignor=consignor,
                         carrier=carrier, place=place, wesy_id=rec[15], status=rec[18], task=task, date2=date2)

        task.shipped += obj.weight
        if task.total_plan is not None and task.shipped > task.total_plan:
            task.status = 3
        task.save()
        obj.save()
        try:
            a_vol = AllocatedVolume.objects.get(task=task, carrier=carrier)
            a_vol.shipped += obj.weight
            a_vol.save()
        except ObjectDoesNotExist:
            pass

    for i in data['delete']:
        d = Record.objects.get(wesy_id=i)
        if d.task is not None:
            d.task.shipped -= d.weight
        try:
            a = AllocatedVolume.objects.get(task=d.task, carrier=d.carrier)
            a.shipped -= d.weight
            a.save()
        except ObjectDoesNotExist:
            pass
        d.save()
        d.delete()

    return n, len(data['delete'])
