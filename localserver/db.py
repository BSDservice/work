import fdb
import datetime
import requests
import json
import pickle
import time


class SyncDB:
    """"""
    def __init__(self):
        self.start_date = datetime.datetime.now() - datetime.timedelta(days=1)
        self.end_date = datetime.datetime.now().replace(year=2045)
        
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
            cursor.execute("SELECT ID, NAME FROM " + tab[0] + " WHERE DELETED = 'F'")
            tmp = cursor.fetchall()
            tmp.append((0, 'неопределённый'))
            data_for_web[tab[1]] = [i for i in tmp if i[0] not in response[tab[1]]]

        r = requests.post('http://127.0.0.1:8000/data_sync/post', headers={'user-agent': 'my-app/0.0.1', 'type': 'post_data'}, data=json.dumps(
            {'data': data_for_web}))
        if r.text == 'Синхронизация прошла успешно':
            pass
        else:
            print(r.text, file=file)

    def sync_weights(self, cursor, file):
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
        SyncDB.cast_types_for_json(self, data)
        r = requests.get('http://127.0.0.1:8000/data_sync/get', params={'type': 'get_weights'})
        response = json.loads(r.text)  # словарь {'weights':{ID записи: статус, ...} на WEB сервере
        records = dict()
        records['weights'] = {i[15]: i for i in data if str(i[15]) not in response['weights'].keys() or response['weights'][str(i[15])] != i[18]}  # записи ID которых нет на WEB или статус которых изменился
        r = requests.post('http://127.0.0.1:8000/data_sync/post', headers={'user-agent': 'my-app/0.0.1', 'type': 'post_records'},
                        data=json.dumps(records))
        for rec in data:
            if rec[18] == 1:
                self.start_date = datetime.datetime(year=rec[12][0], month=rec[12][1], day=rec[12][2], hour=rec[12][3], minute=rec[12][4]-1, second=rec[12][5], microsecond=rec[12][6])
                break
        if r.text == 'Синхронизация прошла успешно':
            pass
        else:
            print(r.text, file=file)

    def cast_types_for_json(self, lst):
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
        
        try:
            with open('syncdbfile', 'rb') as file:
                data = pickle.load(file)
        except FileNotFoundError:
            data = SyncDB()

        data.sync_data(cur, log)
        data.sync_weights(cur, log)

        with open('syncdbfile', 'wb') as file:
            pickle.dump(data, file)
        
        while True:
            try:
                events = con.event_conduit(['WR_SECOND_WEIGHT', 'WR_FIRST_WEIGHT'])
                events.begin()
                e = events.wait()
            except Exception as err:
                print('{} Ошибка: {}'.format(datetime.datetime.now(), err), file=log)
                continue
            finally:
                events.close()
            time.sleep(2)
            data.sync_weights(cur, log)
            with open('syncdbfile', 'wb') as file:
                pickle.dump(data, file)
