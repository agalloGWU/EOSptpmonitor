#!/usr/bin/env python3

"""
Script to retrieve Precision Timing Protocol (PTP) monitor data from an Arista EOS switch;
Insert into a SQLite3 database
"""

import jsonrpclib
from pprint import pprint
import sqlite3


def create_table():
    conn = sqlite3.connect('./EOSptpmondata.sqlite3')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ptpmondata (
    lastSyncSeqId INT primary key,
    meanPathDelay INT,
    intf VARCHAR(25),
    offsetFromMaster INT,
    realLastSyncTime INT,
    skew float)
    ''')


def new_connection(infile):
    try:
        sqliteConnection = sqlite3.connect(infile)
        # print("Successfully Connected to SQLite")
    except sqlite3.Error as error:
        print("Failed to connect to the database", error)

    return sqliteConnection


def insert_data(connection, values):
    try:
        cursor = connection.cursor()
        sqlite_insert_query = """INSERT or IGNORE INTO ptpmondata
                          (lastSyncSeqId, meanPathDelay, intf, offsetFromMaster, realLastSyncTime, skew)
                           VALUES 
                          (?,?,?,?,?,?)"""
        count = cursor.executemany(sqlite_insert_query, values)
        connection.commit()
        # print("Record inserted successfully into ptpmondata table ", cursor.rowcount)
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to insert data into sqlite table", error)
    finally:
        if connection:
            connection.close()
            # print("The SQLite connection is closed")


def get_data():
    from creds import target, username, password
    ip = target
    port = 80
    username = username
    target_password = password

    eapi_url = 'http://{}:{}@{}:{}/command-api'.format(username, target_password, ip, port)
    eapi_conn = jsonrpclib.Server(eapi_url)
    response = eapi_conn.runCmds(1, ['show ptp monitor'])

    return response[0]['ptpMonitorData']

def create_tuple(indata):
    """switch returns a json, resulting in a list of dicts
    SQL insert assumes a stable order of values
    this function creates a list of tuples in the correct order
    so we can safely use INSERT and executemany
    Order is:
        lastSyncSeqId, meanPathDelay, intf, offsetFromMaster, realLastSyncTime, skew"""
    t_tuple = ()    # temp holder in loop
    ordered_ptp_data = []
    for item in indata:
        stable_tuple = (
            item['lastSyncSeqId'],
            item['meanPathDelay'],
            item['intf'],
            item['offsetFromMaster'],
            item['realLastSyncTime'],
            item['skew']
        )
        ordered_ptp_data.append(stable_tuple)
    return ordered_ptp_data


def main():
    create_table()
    ptpdata = get_data()
    ptp_tuple = create_tuple(ptpdata)
    database = new_connection('./EOSptpmondata.sqlite3')
    insert_data(database, ptp_tuple)


if __name__ == "__main__":
    main()
