from django.db import models


class Task(models.Model):
    date = models.DateTimeField(verbose_name='дата формирования задания')
    contractor = models.ForeignKey('Contractor', on_delete=models.CASCADE, verbose_name='контрагент')
    consignee = models.ForeignKey('Consignee', on_delete=models.CASCADE, verbose_name='грузополучатель')
    employer = models.ForeignKey('Employer', on_delete=models.CASCADE, verbose_name='заказчик')
    consignor = models.ForeignKey('Consignor', on_delete=models.CASCADE, verbose_name='грузоотправитель')
    destination = models.ForeignKey('Destination', on_delete=models.CASCADE, verbose_name='пункт назначения')
    place = models.ForeignKey('Place', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='место погрузки')
    total_plan = models.SmallIntegerField(verbose_name='общий объем', null=True)
    daily_plan = models.SmallIntegerField(verbose_name='суточный объем', null=True)
    TASK_STATUS = (
        (1, 'черновик'),
        (2, 'к выполнению'),
        (3, 'выполнено'),
    )
    shipped = models.FloatField(verbose_name='отгружено по заданию', default=0)
    price = models.SmallIntegerField(verbose_name='цена', null=True)
    status = models.CharField(max_length=1, choices=TASK_STATUS, default=1, help_text='статус задания')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
    rubble = models.ForeignKey('Rubble', on_delete=models.CASCADE, verbose_name='выписываемый материал')
    hours = models.CharField(max_length=20, verbose_name='Часы приема', null=True)
    comments = models.CharField(max_length=200, verbose_name='Комментарий', null=True, blank=True)
    
    def __str__(self):
        return 'контрагент: {}; груз: {}; отгружено {}; пункт разгрузки{}'.format(self.contractor, self.rubble, str(self.shipped), self.destination)


class Record(models.Model):
    """Представление записи из базы весовой"""
    date1 = models.DateTimeField(verbose_name='въезд на территорию')
    date2 = models.DateTimeField(verbose_name='выезд с территории', null=True, blank=True)
    ttn = models.CharField(max_length=7, verbose_name='номер ТТН', null=True, blank=True)
    car = models.ForeignKey('Car', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='автомобиль')
    contractor = models.ForeignKey('Contractor', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='контрагент')
    rubble = models.ForeignKey('Rubble', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='фракция')
    weight = models.FloatField(verbose_name='вес, тн.', null=True, blank=True)
    consignee = models.ForeignKey('Consignee', on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name='грузополучатель')
    destination = models.ForeignKey('Destination', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='пункт назначения')
    employer = models.ForeignKey('Employer', on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name='заказчик')
    consignor = models.ForeignKey('Consignor', on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name='грузоотправитель')
    carrier = models.ForeignKey('Carrier', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='перевозчик')
    place = models.ForeignKey('Place', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='место погрузки')
    wesy_id = models.SmallIntegerField(unique=True)
    CAR_STATUS = (
        ('1', 'в заводе'),
        ('2', 'убыл'),
    )
    status = models.CharField(max_length=1, choices=CAR_STATUS, default=1, help_text='нахождение в заводе')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True)
    def __str__(self):
        return 'контрагент: {}; груз: {}; пункт разгрузки{}'.format(self.contractor, self.rubble, self.destination)


class Car(models.Model):
    brand = models.CharField(max_length=20, verbose_name='марка', null=True, blank=True)
    num = models.CharField(max_length=20, verbose_name='гос.номер', unique=True, null=True)
    carrier = models.ForeignKey('Carrier', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.num)


class Organization(models.Model):
    name = models.CharField(max_length=100, verbose_name='название', null=True, blank=True)
    wesy_id = models.SmallIntegerField()

    def __str__(self):
        return str(self.name)

    class Meta:
        abstract = True
    

class Contractor(Organization):
    """Контрагент, SUBCONTRACTOR"""
    pass


class Consignee(Organization):
    """Грузополучатель, SUBCONTRACTOR"""
    pass


class Employer(Organization):
    """Заказчик, SUBCONTRACTOR"""
    pass


class Consignor(Organization):
    """Грузоотправитель, , SUBCONTRACTOR"""
    pass


class Carrier(Organization):
    """Перевозчик, DRIVERS"""
    pass


class Rubble(models.Model):
    """PRODUCTS"""
    name = models.CharField(max_length=100, verbose_name='наименование груза', null=True, blank=True)
    wesy_id = models.SmallIntegerField()
    visible = models.CharField(max_length=1, verbose_name='наименование груза', default=1)

    def __str__(self):
        return str(self.name)


class RubbleRoot(models.Model):
    """TYPES_OF_PRODUCTS"""
    name = models.CharField(max_length=100, verbose_name='род груза', null=True, blank=True)
    wesy_id = models.SmallIntegerField()


class RubbleQuality(models.Model):
    """CARGOMARK"""
    name = models.CharField(max_length=100, verbose_name='качество груза', null=True, blank=True)
    wesy_id = models.SmallIntegerField()


class Destination(models.Model):
    """UPLOADINGPOINTS"""
    name = models.CharField(max_length=200, verbose_name='пункт разгрузки', null=True, blank=True, unique=True)
    wesy_id = models.SmallIntegerField()

    def __str__(self):
        return str(self.name)


class Place(models.Model):
    """STORAGES"""
    name = models.CharField(max_length=20, verbose_name='название', null=True, blank=True)
    wesy_id = models.SmallIntegerField()

    def __str__(self):
        return str(self.name)


class AllocatedVolume(models.Model):
    """Выделенный объём на перевозчика"""
    task = models.ForeignKey(Task, verbose_name='задание', on_delete=models.CASCADE)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE, verbose_name='перевозчик')
    weight = models.SmallIntegerField(verbose_name='объем')
    shipped = models.FloatField(verbose_name='отгружено', null=True)


