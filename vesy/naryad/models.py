from django.db import models


class Record(models.Model):
    """Представление записи из базы весовой"""
    date1 = models.DateTimeField(verbose_name='въезд на территорию')
    date2 = models.DateTimeField(verbose_name='выезд с территории', null=True, blank=True)
    ttn = models.CharField(max_length=7, verbose_name='номер ТТН', null=True, blank=True)
    car = models.ForeignKey('Car', on_delete=models.SET_NULL, null=True, verbose_name='автомобиль')
    contractor = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, verbose_name='контрагент')
    stone = models.ForeignKey('Stone', on_delete=models.SET_NULL, null=True, verbose_name='фракция')
    weight = models.DecimalField(verbose_name='вес, тн.')
    consignee = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, verbose_name='грузополучатель')
    destination = models.ForeignKey('Destination', on_delete=models.SET_NULL, null=True, verbose_name='пункт назначения')
    employer = models.ForeignKey('Organization', on_delete=models.SET_NULL, verbose_name='заказчик')
    consignor = models.ForeignKey('Organization', on_delete=models.SET_NULL, verbose_name='грузоотправитель')
    CAR_STATUS = (
        (1, 'в заводе'),
        (2, 'убыл'),
    )

    status = models.CharField(max_length=1, choices=CAR_STATUS, blank=True, default=1, help_text='нахождение в заводе')


class Car(models.Model):
    pass


class Organization(models.Model):
    pass


class Stone(models.Model):
    pass


class Destination(models.Model):
    pass
