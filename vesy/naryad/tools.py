from .models import Record, Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place, Consignee,\
                          Employer, Consignor, Car, Task, AllocatedVolume, LastChanges
from django.core.exceptions import ObjectDoesNotExist
import datetime
import decimal


def save_data(data):
    obj_dict = {'Contractor': Contractor,
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
                    entry = tab_split(name=item)
                    entry.save()
            else:
                entry = obj_dict[tab](name=item)
                entry.save()
            n += 1
    return n


def records_sync(data):
    """
    Создает или обновляет записи о взвешивании, сопостовляя записи заданиям на отгрузку, если нет таковых создаёт их.
    """
    if 'delete' in data.keys():
        fetch_del = Record.objects.filter(wesy_id__in=data['delete'])
        for rec in fetch_del:
            if rec.status == 1:
                rec.task.cars_on_loading -= 1
                rec.task.save()
            rec.status = 'D'
            rec.save()

    n = 0
    for wesy_id, rec in data['weights'].items():
        n += 1
        try:
            car = Car.objects.get(num=rec[0])
        except Car.DoesNotExist:
            car = Car(num=rec[0], brand=[14])
            car.save()
        try:
            contractor = Contractor.objects.get(name=rec[19] if rec[19] is not None else "не определён")
            rubble = Rubble.objects.get(name=rec[2] if rec[2] is not None else "не определён")
            consignee = Consignee.objects.get(name=rec[6] if rec[6] is not None else "не определён")
            destination = Destination.objects.get(name=rec[7] if rec[7] is not None else "не определён")
            employer = Employer.objects.get(name=rec[9] if rec[9] is not None else "не определён")
            consignor = Consignor.objects.get(name=rec[10] if rec[10] is not None else "не определён")
            carrier = Carrier.objects.get(name=rec[4] if rec[4] is not None else "не определён")
            place = Place.objects.get(name=rec[5] if rec[5] is not None else "не определён")
        except ObjectDoesNotExist as err:
            return 'update_data'

        try:
            task = Task.objects.get(contractor=contractor, consignee=consignee, destination=destination,
                                    employer=employer, consignor=consignor, rubble=rubble)
            if task.status == '3':
                task.date = datetime.datetime(year=rec[12][0], month=rec[12][1], day=rec[12][2], hour=rec[12][3],
                                              minute=rec[12][4])
                task.status = '2'

        except Task.DoesNotExist:

            task = Task(contractor=contractor, consignee=consignee, destination=destination, employer=employer,
                        consignor=consignor, rubble=rubble, status=2,
                        date=datetime.datetime(year=rec[12][0], month=rec[12][1], day=rec[12][2], hour=rec[12][3],
                                               minute=rec[12][4]),
                        cargo_type=RubbleRoot.objects.get(name="не определён"),
                        cargo_quality=RubbleQuality.objects.get(name="не определён"))
            task.save()

        except Task.MultipleObjectsReturned as err:
            tasks_list_duplicate = Task.objects.filter(contractor=contractor, consignee=consignee, destination=destination,
                                                       employer=employer, consignor=consignor, rubble=rubble)
            for task_dup in tasks_list_duplicate:
                if task_dup is tasks_list_duplicate[0]:
                    continue
                else:
                    records_to_detach = Record.objects.filter(task=task_dup)
                    for record in records_to_detach:
                        record.task = tasks_list_duplicate[0]
                        record.save()
                    task_dup.delete()

        if rec[13] is not None:
            date2 = datetime.datetime(year=rec[13][0], month=rec[13][1], day=rec[13][2], hour=rec[13][3], minute=rec[13][4], second=rec[13][5], microsecond=rec[13][6])
        else:
            date2 = rec[13]
        
        weight = decimal.Decimal(rec[3])

        try:
            obj = Record.objects.get(wesy_id=rec[15])
            obj.date1 = datetime.datetime(year=rec[12][0], month=rec[12][1], day=rec[12][2], hour=rec[12][3], minute=rec[12][4], second=rec[12][5], microsecond=rec[12][6])
            obj.date2 = date2
            obj.ttn = rec[11]
            obj.car = car
            obj.contractor = contractor
            obj.rubble = rubble
            obj.weight = decimal.Decimal(rec[3])
            obj.consignee = consignee
            obj.destination = destination
            obj.employer = employer
            obj.consignor = consignor
            obj.carrier = carrier
            obj.place = place
            obj.wesy_id = rec[15]
            obj.status = rec[18]
            obj.task = task
            if rec[18] == 2:
                task.cars_on_loading -= 1
        except Record.DoesNotExist:
            obj = Record(date1=datetime.datetime(year=rec[12][0], month=rec[12][1], day=rec[12][2], hour=rec[12][3],
                                                 minute=rec[12][4], second=rec[12][5], microsecond=rec[12][6]),
                         ttn=rec[11], car=car, contractor=contractor, rubble=rubble, weight=weight,
                         consignee=consignee, destination=destination, employer=employer, consignor=consignor,
                         carrier=carrier, place=place, wesy_id=rec[15], status=rec[18], task=task, date2=date2)
            if rec[18] == 1:
                task.cars_on_loading += 1

        task_to_log = LastChanges(task=task, date=datetime.datetime.now())
        if task.cars_on_loading < 0: task.cars_on_loading = 0
        task.save()
        obj.save()
        task_to_log.save()
        try:
            a_vol = AllocatedVolume.objects.get(task=task, carrier=carrier)
            a_vol.shipped = a_vol.shipped + obj.weight
            a_vol.save()
        except ObjectDoesNotExist:
            pass

    return n