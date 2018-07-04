from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from naryad.models import Record, Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place, Consignee,\
                          Employer, Consignor, Car, Task
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
            ans = {'weights': [{i.wesy_id: i.status} for i in records]}
            return JsonResponse(ans)
        else:
            return HttpResponse('Синхронизация прервана(1)')

    elif request.method == 'POST':
        if request.META['HTTP_USER_AGENT'] == 'my-app/0.0.1' and request.META['HTTP_TYPE'] == 'post_data':
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception as error:
                return HttpResponse('Синхронизация прервана при форматировании данных\nОШИБКА:{0}'.format(
                    error.with_traceback(error.__traceback__)))
            try:
                n = save_data(data['data'])
            except Exception as error:
                return HttpResponse('Синхронизация прервана при записи в базу\nОШИБКА:{0}'.format(
                    error.with_traceback(error.__traceback__)))
            try:
                d = delete_data(data['delete'])
            except Exception as error:
                return HttpResponse('Синхронизация прервана при записи в базу\nОШИБКА:{0}'.format(
                    error.with_traceback(error.__traceback__)))
            return HttpResponse('Синхронизация прошла успешно\nВнесено записей:{0}, удалено: {1}'.format(str(n), str(d)))

        elif request.META['HTTP_USER_AGENT'] == 'my-app/0.0.1' and request.META['HTTP_TYPE'] == 'post_records':
            try:
                records = json.loads(request.body.decode('utf-8'))
                # records_sync(records)
            except Exception as error:
                return HttpResponse('Синхронизация прервана при форматировании данных\nОШИБКА:{0}'.format(
                    error.with_traceback(error.__traceback__)))
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
    date1, date2, ttn, car, contractor, rubble, weight, consignee, destination,
    employer, consignor, carrier, place, wesy_id, status, task
    """
    for vesy_id, rec in data['weights'].items():

        try:
            car = Car.objects.get(num=rec[0])
        except Exception:
            try:
                car = Car(num=rec[0], brand=[14])
            except Exception as error:
                return 'Синхронизация прервана при форматировании данных\nОШИБКА:{0}'.format(
                        error.with_traceback(error.__traceback__))

        contractor = Contractor.objects.get(name=rec[19])
        rubble = Rubble.objects.get(name=rec[2])
        consignee = Consignee.objects.get()
        destination = Destination.objects.get()
        employer = Employer.objects.get()
        consignor = Consignor.objects.get()
        carrier = Carrier.objects.get()
        place = Place.objects.get()

        try:
            task = Task.objects.get()
        except Exception:
            try:
                task = Task()
            except Exception as error:
                return 'Синхронизация прервана при форматировании данных\nОШИБКА:{0}'.format(
                        error.with_traceback(error.__traceback__))

        try:
            obj = Record.objects.get(vesy_id=rec[15])
            obj.date1 = datetime.datetime(rec[12])
            obj.date2 = datetime.datetime(rec[13])
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
            obj.vesy_id = rec[15]
            obj.status = rec[18]
            obj.task = task
            obj.driver = driver
            obj.save()
        except Exception:
            try:
                obj = Record(date1=datetime.datetime(rec[12]), date2=datetime.datetime(rec[13]), ttn=rec[11], car=car,
                             contractor=contractor, rubble=rubble, weight=float(rec[3]), consignee=consignee,
                             destination=destination,
                             employer=employer, consignor=consignor, carrier=carrier, place=place, vesy_id=rec[15],
                             status=rec[18], task=task)
                obj.save()
            except Exception as error:
                return 'Синхронизация прервана при форматировании данных\nОШИБКА:{0}'.format(
                        error.with_traceback(error.__traceback__))
