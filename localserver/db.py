import fdb
import datetime
import requests
import json


class SyncDB:
    """"""
    def __init__(self):
        self.last_call = None
        self.last_event_id = 0
        self.data = None

    def __str__(self):
        return 'записей в объекте: {0}\nпоследняя синхрозизаця: {1}\nlast_id: {2}'.format(len(self.data), self.last_call, self.last_event_id)

    def sync_db(self, cursor, status, start_date=None, end_date=datetime.datetime.now()):

        last_call = None
        if status == 2:
            cursor.execute("SELECT * FROM event_last_ids WHERE id > ? AND EVENT_NAME = 'WR_SECOND_WEIGHT'", (self.last_event_id,))
            last_events_ids = cur.fetchallmap()
            self.last_event_id = last_events_ids[-1]['id']
            id_for_fetch = tuple(i['LAST_ID'] for i in last_events_ids)
            id_for_fetch = " AND IDWEIGHTS IN " + str(id_for_fetch) + " "
        else:
            id_for_fetch = ''

        if self.last_call:
            start_date = self.last_call - datetime.timedelta(minutes=1)
        elif start_date is None:
            start_date = datetime.datetime.now() - datetime.timedelta(days=1)

        cur.execute(""" SELECT TRANSPORT_NUMBER, VCPAYER, P_NAME, DOC_NETTO, K_NAME, ST_NAME, VCRECIVER, VCUPLOADINGPOINT, 
                          TO_NAME, VCTRANSPPAYER, VCSENDER, INVOICE, FIRST_WEIGHT_DATE, FIRST_WEIGHT_TIME, SECOND_WEIGHT_DATE, SECOND_WEIGHT_TIME,
                          TR_TYPE, IDWEIGHTS 
                        FROM weights_sel (0, ?, ?) w             
                          LEFT JOIN ttndata t ON t.idweights = w.id 
                          LEFT JOIN subcontractors s ON s.id = t.ireciverid
                          LEFT JOIN dictval dv2 ON dv2.idictid = t.iuploadingpointsid AND  dv2.istpdictvalid = 50 /* Цена доставки */ AND  dv2.istpdictid = 16 /* Пункт разгрузки */
                        WHERE w.deleted = 'F' AND w.status = ? AND to_name IN ('Донской камень', 'Договор 1', 'Машпром', 'Обуховский щебзавод')""" + id_for_fetch, (start_date, end_date, status))
        self.data = cur.fetchall()
        if status == 1:
            self.last_call = datetime.datetime.combine(self.data[0][12], self.data[0][13])


def start(cursor):
    """
    первый запуск, запуск после сбоя.
    Получает ID записей на WEB сервере и сравнивает их с записями на локальном сервере.
    Отправляет записи отсутствующие на WEB сервере и список ID подлежащих удалению
    """

    #  Record, Contractor, Carrier, Rubble, RubbleRoot, RubbleQuality, Destination, Place

    start_date = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=10)
    end_date = datetime.datetime.now() + datetime.timedelta(hours=1)






    cursor.execute(""" SELECT TRANSPORT_NUMBER, VCPAYER, P_NAME, DOC_NETTO, K_NAME, ST_NAME, VCRECIVER, VCUPLOADINGPOINT, 
                              TO_NAME, VCTRANSPPAYER, VCSENDER, INVOICE, FIRST_WEIGHT_DATE, FIRST_WEIGHT_TIME, SECOND_WEIGHT_DATE, SECOND_WEIGHT_TIME,
                              TR_TYPE, IDWEIGHTS, W.ID, VCCARGOMARK, TP_NAME 
                            FROM weights_sel (0, ?, ?) w             
                              LEFT JOIN ttndata t ON t.idweights = w.id 
                              LEFT JOIN subcontractors s ON s.id = t.ireciverid
                              LEFT JOIN dictval dv2 ON dv2.idictid = t.iuploadingpointsid AND  dv2.istpdictvalid = 50 /* Цена доставки */ AND  dv2.istpdictid = 16 /* Пункт разгрузки */
                            WHERE w.deleted = 'F' AND to_name IN ('Донской камень', 'Договор 1', 'Машпром', 'Обуховский щебзавод')""",(start_date, end_date))
    data = cursor.fetchall()  # выгрузка из локальной базы
    records_to_web = [rec for rec in data if rec[-1] not in response]  # записи отсутствующие на WEB сервере
    records_del = [j for j in response if j not in [i[-1] for i in data]]  # id отсутствующие в локальной базе(удаленные)

    # записи отсутствующие на WEB сервере

    # id отсутствующие в локальной базе(удаленные)
    # data_to_web = [rec for rec in data if rec[-1] not in response]  # записи отсутствующие на WEB сервере
    # wasdel = [j for j in response if j not in [i[-1] for i in data]]  # id отсутствующие в локальной базе(удаленные)

    """ ... """


def sync_data(cursor, file):
    """
    Синхронизирует таблицы: 'CARGOMARK'          :  'RubbleQuality',
                            'SUBCONTRACTORS'     :  'Contractor',
                            'DRIVERS'            :  'Carrier',
                            'PRODUCTS'           :  'Rubble',
                            'STORAGES'           :  'Place',
                            'UPLOADINGPOINTS'    :  'Destination',
                            'TYPES_OF_PRODUCTS'  :  'RubbleRoot'
    """

    table_for_sync = {'CARGOMARK': 'RubbleQuality',
                      'SUBCONTRACTORS': 'Contractor',
                      'DRIVERS': 'Carrier',
                      'PRODUCTS': 'Rubble',
                      'STORAGES': 'Place',
                      'UPLOADINGPOINTS': 'Destination',
                      'TYPES_OF_PRODUCTS': 'RubbleRoot'}

    data_for_web = {}
    wasdel = {}
    r = requests.get('http://127.0.0.1:8000/data_sync/get', params={'type': 'get_data'})
    response = json.loads(r.text)  # список ID записей на WEB сервере
    for tab in table_for_sync.items():
        cursor.execute("SELECT ID, NAME FROM " + tab[0] + " WHERE DELETED = 'F'")
        tmp = cursor.fetchall()
        data_for_web[tab[1]] = [i for i in tmp if i[0] not in response[tab[1]]]
        wasdel[tab[1]] = [i for i in response[tab[1]] if i not in [j[0] for j in tmp]]

    r = requests.post('http://127.0.0.1:8000/data_sync/post', headers={'user-agent': 'my-app/0.0.1', 'type': 'post_data'}, data=json.dumps(
        {'delete': wasdel, 'data': data_for_web}))
    print(r.text, file=file)


def sync_weights(cursor, file,
                 start_date=datetime.datetime.now() - datetime.timedelta(days=1),
                 end_date=datetime.datetime.now() + datetime.timedelta(hours=1)):
    cursor.execute("""SELECT TRANSPORT_NUMBER, VCPAYER, P_NAME, DOC_NETTO, K_NAME, ST_NAME, VCRECIVER, VCUPLOADINGPOINT, 
                             TO_NAME, VCTRANSPPAYER, VCSENDER, INVOICE, FIRST_WEIGHT_DATE, FIRST_WEIGHT_TIME, SECOND_WEIGHT_DATE, SECOND_WEIGHT_TIME,
                             TR_TYPE, W.ID, VCCARGOMARK, TP_NAME, W.STATUS, S_NAME
                      FROM weights_sel (0, ?, ?) w             
                       LEFT JOIN ttndata t ON t.idweights = w.id 
                       LEFT JOIN subcontractors s ON s.id = t.ireciverid
                       LEFT JOIN dictval dv2 ON dv2.idictid = t.iuploadingpointsid AND  dv2.istpdictvalid = 50 AND  dv2.istpdictid = 16
                       WHERE w.deleted = 'F' AND to_name IN ('Донской камень', 'Машпром', 'Обуховский щебзавод')""",
                   (start_date, end_date))
    data = cursor.fetchall()
    data = list(map(list, data))
    cast_types_for_json(data)
    r = requests.get('http://127.0.0.1:8000/data_sync/get', params={'type': 'get_weights'})
    response = json.loads(r.text)  # словарь {'weights':{ID записи: статус, ...} на WEB сервере
    print(response)
    records = dict()
    records['weights'] = {i[15]: i for i in data if str(i[15]) not in response['weights'].keys() or response['weights'][str(i[15])] != i[18]}  # записи ID которых нет на WEB или статус которых изменился
    records['delete'] = [i for i in response['weights'].keys() if int(i) not in [j[15] for j in data]]
    # print(records)

    """
    for i in response['weights']:
        if int(list(i.keys())[0]) not in [j[15] for j in data]:
            print('нет такого в списке')
    """
    r = requests.post('http://127.0.0.1:8000/data_sync/post', headers={'user-agent': 'my-app/0.0.1', 'type': 'post_records'},
                      data=json.dumps(records))
    print(r.text)
    print(r.text, file=file)


def cast_types_for_json(lst):
    """приведение списка из локальной базы к формату передачи JSON"""
    for rec in lst:
        if rec[3] is not None:
            rec[3] = float(rec[3])
        else:
            rec[3] = 0
        rec[12] = (rec[12].year, rec[12].month, rec[12].day, rec[13].hour, rec[13].minute, rec[13].second, rec[13].microsecond)
        if rec[14] is None:
            rec[13] = None
        else:
            rec[13] = (rec[14].year, rec[14].month, rec[14].day, rec[15].hour, rec[15].minute, rec[15].second, rec[15].microsecond)
        del rec[14], rec[14]


if __name__ == '__main__':
    with open('data.log', 'a') as log:
        print('START : {}'.format(str(datetime.datetime.now())), file=log)
        con = fdb.connect(host='192.168.1.200',
                          database='C:\\Documents and Settings\\All Users\\Application Data\\NAIS\\WeightRoom43s\\Database\\WEIGHTROOM_2018.FDB',
                          user='SYSDBA',
                          password='masterkey', sql_dialect=3, charset='WIN1251')
        cur = con.cursor()
        sync_data(cur, log)
        sync_weights(cur, log)



"""
    while True:
        events = con.event_conduit(['WR_SECOND_WEIGHT', 'WR_FIRST_WEIGHT'])
        events.begin()
        e = events.wait()
        events.close()
        print(e)
        status = 1
        if e['WR_SECOND_WEIGHT'] == 1:
            status = 2
        elif e['WR_FIRST_WEIGHT'] == 1:
            status = 1
        try:
            with open('.\\db\\pickle_db', 'rb') as file:
                data = pickle.load(file)
                data.sync_db(cur, status)
                if status == 1:
                    print('в заводе {0} машин'.format(len(data.data)))
                elif status == 2:
                    print('с {0} было отгружено {1} машин'.format(data.last_call, len(data.data)))
                    print(data.data)
            with open('.\\db\\pickle_db', 'wb') as file:
                pickle.dump(data, file)

        except FileNotFoundError:
            f = SyncDB()
            f.sync_db(cur, 1)
            print(f)
            with open('.\\db\\pickle_db', 'wb') as file:
                pickle.dump(f, file)
"""
