import fdb
import datetime
import requests
import json
import pickle
import time
from sys import exit
import functools


def except_error_connection(func):
    @functools.wraps(func)
    def decor(self, cur, log):
        try:
            func(self, cur, log)
        except requests.exceptions.ConnectionError as err:
            print('Ошибка соединения с web-сервером: {}'.format(err))
            delay = [1, 2, 3]
            for i in delay:
                print('повторная попытка соединения через {} секунд...'.format(i * 60))
                time.sleep(i * 60)
                try:
                    func(self, cur, log)
                    return decor
                except requests.exceptions.ConnectionError:
                    continue
            print('web-сервер не отвечает, проверьте соединение с Интернет '
                  'и работоспособность web-сервера, перезапустите драйвер.')
            print('программа будет закрыта через 30 сек...')
            print(err, file=log)
            time.sleep(30)
            exit(1)
    return decor


class SyncDB:
    """
    Хранит дату последней синхронизации
    """
    def __init__(self):
        self.start_date = datetime.datetime.now() - datetime.timedelta(days=1, hours=5, minutes=20)
        self.end_date = datetime.datetime.now().replace(year=2045)
        self.last_delete_sync_id = 0

    @except_error_connection
    def sync_data(self, cursor, file):
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
        r = requests.get('http://127.0.0.1:8000/data_sync/get', params={'type': 'get_data'})
        response = json.loads(r.text)  # список ID записей на WEB сервере
        for tab in table_for_sync.items():
            cursor.execute("SELECT DISTINCT NAME FROM " + tab[0] + " WHERE DELETED = 'F'")
            tmp = cursor.fetchall()
            tmp.append(('неопределённый',))
            data_for_web[tab[1]] = [i[0] for i in tmp if i[0] not in response[tab[1]]]

        r = requests.post('http://127.0.0.1:8000/data_sync/post', headers={'user-agent': 'my-app/0.0.1', 'type': 'post_data'}, data=json.dumps(
            {'data': data_for_web}))
        if r.text == 'Синхронизация прошла успешно':
            pass
        else:
            print(r.text, file=file)

    @except_error_connection
    def sync_weights(self, cursor, file):
        """
        Синхронизирует записи взвешиваний
        """
        cursor.execute("""SELECT TRANSPORT_NUMBER, VCPAYER, P_NAME, DOC_NETTO, K_NAME, ST_NAME, VCRECIVER, VCUPLOADINGPOINT, 
                                TO_NAME, VCTRANSPPAYER, VCSENDER, INVOICE, FIRST_WEIGHT_DATE, FIRST_WEIGHT_TIME, SECOND_WEIGHT_DATE, SECOND_WEIGHT_TIME,
                                TR_TYPE, W.ID, VCCARGOMARK, TP_NAME, W.STATUS, S_NAME
                        FROM weights_sel (0, ?, ?) w             
                        LEFT JOIN ttndata t ON t.idweights = w.id 
                        LEFT JOIN subcontractors s ON s.id = t.ireciverid
                        LEFT JOIN dictval dv2 ON dv2.idictid = t.iuploadingpointsid AND  dv2.istpdictvalid = 50 AND  dv2.istpdictid = 16
                        WHERE w.deleted = 'F' AND to_name IN ('Донской камень', 'Машпром', 'Обуховский щебзавод')""",
                       (self.start_date, self.end_date))
        data = cursor.fetchall()
        data = list(map(list, data))

        SyncDB.cast_types_for_json(data)
        r = requests.get('http://127.0.0.1:8000/data_sync/get', params={'type': 'get_weights'})
        response = json.loads(r.text)  # словарь {'weights':{ID записи: статус, ...} на WEB сервере
        records = dict()
        records['weights'] = {i[15]: i for i in data if str(i[15]) not in response['weights'].keys() or response['weights'][str(i[15])] != i[18]}  # записи ID которых нет на WEB или статус которых изменился

        # проверка наличие информации об удалённых записях
        if self.last_delete_sync_id == 0:
            cursor.execute("""SELECT * FROM EVENT_LAST_IDS WHERE ID > 107718""")
            self.last_delete_sync_id = cursor.fetchall()[-1][0]
            print(self.last_delete_sync_id)
        else:
            cursor.execute(
                """SELECT * FROM EVENT_LAST_IDS eli WHERE eli.ID > ? AND eli.EVENT_NAME = 'WR_DELETE_WEIGHT'""",
                (self.last_delete_sync_id,))
            tmp = cursor.fetchall()
            if tmp:
                self.last_delete_sync_id = tmp[-1][0]
                id_for_del_list = [i[2] for i in tmp]
                records['delete'] = id_for_del_list

        r = requests.post('http://127.0.0.1:8000/data_sync/post', headers={'user-agent': 'my-app/0.0.1', 'type': 'post_records'},
                          data=json.dumps(records))
        if r.text == 'update_data':
            self.sync_data(cursor, file)
            r = requests.post('http://127.0.0.1:8000/data_sync/post',
                              headers={'user-agent': 'my-app/0.0.1', 'type': 'post_records'},
                              data=json.dumps(records))
            if r.text == 'update_data':
                print('Ошибка синхронизации при записи в удаленную базу', file=file)
        for rec in data:
            if rec[18] == 1:
                self.start_date = datetime.datetime(year=rec[12][0], month=rec[12][1], day=rec[12][2], hour=rec[12][3],
                                                    minute=rec[12][4], second=rec[12][5], microsecond=rec[12][6]) - \
                                  datetime.timedelta(hours=1)
                break


    @staticmethod
    def cast_types_for_json(lst):
        """приведение списка из локальной базы к формату передачи JSON"""
        for rec in lst:
            if rec[3] is not None:
                rec[3] = str(rec[3])
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
        con = fdb.connect(host='192.168.1.111',
                          database='C:\\ProgramData\\NAIS\\WeightRoom43s\\Database\\WEIGHTROOM_2018.FDB',
                          user='SYSDBA',
                          password='masterkey', sql_dialect=3, charset='WIN1251')
        cur = con.cursor()
        
        try:
            with open('syncdbfile', 'rb') as file:
                data = pickle.load(file)
        except FileNotFoundError:
            data = SyncDB()
        print(8*' '+'синхронизируемся с '+str(data.start_date))
        print(data.sync_data.__doc__)
        data.sync_data(cur, log)
        print(8*' '+'ОПЕРАЦИЯ ЗАВЕРШЕНА',  end=' ')
        print(data.sync_weights.__doc__)
        data.sync_weights(cur, log)
        print(8*' '+'ОПЕРАЦИЯ ЗАВЕРШЕНА')
        with open('syncdbfile', 'wb') as file:
            pickle.dump(data, file)
        print(8*' '+'Синхронизация работает в реальном времени...')
        while True:
            """
            try:
                events = con.event_conduit(['WR_SECOND_WEIGHT', 'WR_FIRST_WEIGHT', 'WR_DELETE_WEIGHT'])
                events.begin()
                e = events.wait()
            except Exception as err:
                print('{} Ошибка: {}'.format(datetime.datetime.now(), err), file=log)
                continue
            finally:
                events.close()
            """
            time.sleep(60)
            data.sync_weights(cur, log)
            with open('syncdbfile', 'wb') as file:
                pickle.dump(data, file)
