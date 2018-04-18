import fdb
import datetime


def db_con(start, end):

    con = fdb.connect(host='localhost',
                      database='C:\\Documents and Settings\\All Users\\Application Data\\NAIS\\WeightRoom43s\\Database\\WEIGHTROOM_2018.FDB',
                      user='SYSDBA',
                      password='masterkey', sql_dialect=3, charset='WIN1251')
    exc = (u'Донской камень', u'Договор 1', u'Машпром', u'Обуховский щебзавод')
    cur = con.cursor()
    cur.execute("""SELECT TRANSPORT_NUMBER, VCPAYER, P_NAME, DOC_NETTO, K_NAME, ST_NAME, VCRECIVER, VCUPLOADINGPOINT, 
    TO_NAME, VCTRANSPPAYER, VCSENDER, INVOICE, FIRST_WEIGHT_DATE, FIRST_WEIGHT_TIME, SECOND_WEIGHT_DATE, SECOND_WEIGHT_TIME,
    TR_TYPE, STATUS
     FROM weights_sel (0, ?, ?) w
          LEFT JOIN ttndata t ON t.idweights = w.id
          LEFT JOIN subcontractors s ON s.id = t.ireciverid
          LEFT JOIN dictval dv2 ON dv2.idictid = t.iuploadingpointsid AND  dv2.istpdictvalid = 50 /* Цена доставки */ AND  dv2.istpdictid = 16 /* Пункт разгрузки */
     WHERE w.deleted = 'F' /* AND w.status = 1 */AND to_name IN (?, ?, ?, ?)
    """, (start, end, exc[0], exc[1], exc[2], exc[3]))
    return cur.fetchall()
    # print(cur.fetchone())
    # print(cur.fetchonemap())


if __name__ == '__main__':
    start = datetime.datetime.now() - datetime.timedelta(days=1)
    end = datetime.datetime.now()
    print(db_con(start,end))