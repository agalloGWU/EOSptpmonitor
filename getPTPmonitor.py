#!/usr/bin/env python3

"""
Script to retrieve Precision Timing Protocol (PTP) monitor data from an Arista EOS switch;
Insert into a SQLite3 database
"""

import jsonrpclib
import sqlite3
import time


def create_ptp_table():
    conn = sqlite3.connect('./zFork.sqlite3')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ptpmondata (
        lastSyncSeqId INT,
        realLastSyncTime INT primary key,
        meanPathDelay INT,
        intf VARCHAR(25),
        offsetFromMaster INT,
        skew float)
    ''')

def create_temp_table():
    conn = sqlite3.connect('./zFork.sqlite3')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS temperature_data (
        queryTime INT,
        name VARCHARR(25),
        currentTemperature float,
        description VARCHAR(50))
        ''')


def create_CPU_table():
    conn = sqlite3.connect('./zFork.sqlite3')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS cpu_data (
        queryTime INT,
        currentCPUocc float)
        ''')

def new_connection(infile):
    try:
        sqliteConnection = sqlite3.connect(infile)
        # print("Successfully Connected to SQLite")
    except sqlite3.Error as error:
        print("Failed to connect to the database", error)

    return sqliteConnection


def insert_ptp_data(connection, ptp_values):
    try:
        cursor = connection.cursor()
        sqlite_insert_query = """INSERT or IGNORE INTO ptpmondata
                          (lastSyncSeqId, realLastSyncTime, meanPathDelay, intf, offsetFromMaster, skew)
                           VALUES 
                          (?,?,?,?,?,?)"""
        count = cursor.executemany(sqlite_insert_query, ptp_values)
        connection.commit()
        # print("Record inserted successfully into ptpmondata table ", cursor.rowcount)
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to insert data into sqlite ptpmondata table", error)
    finally:
        if connection:
            connection.close()
            # print("The SQLite connection is closed")

def insert_temp_data(connection, temp_values):
    try:
        cursor = connection.cursor()
        sqlite_insert_query = """INSERT or IGNORE INTO temperature_data
                          (queryTime, name, currentTemperature, description)
                           VALUES 
                          (?,?,?,?)"""
        count = cursor.executemany(sqlite_insert_query, temp_values)
        connection.commit()
        # print("Record inserted successfully into temp_values table ", cursor.rowcount)
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to insert data into sqlite temp_values table", error)
    finally:
        if connection:
            connection.close()
            # print("The SQLite connection is closed")


def insert_cpu_data(connection, epoch, cpu_values):
    try:
        cursor = connection.cursor()
        sqlite_insert_query = """INSERT or IGNORE INTO cpu_data
                          (queryTime, currentCPUocc)
                           VALUES 
                          (?,?)"""
        count = cursor.execute(sqlite_insert_query, [epoch, cpu_values])
        connection.commit()
        # print("Record inserted successfully into cpu data table ", cursor.rowcount)
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to insert data into sqlite cpu data table", error)
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

    ptp_response = eapi_conn.runCmds(1, ['show ptp monitor'])
    temp_response = eapi_conn.runCmds(1, ['show system environment temperature'])
    cpu_response = eapi_conn.runCmds(1, ['show processes top once'])

    ptp_data = ptp_response[0]['ptpMonitorData']
    temp_data = temp_response[0]['tempSensors']
    # we're looking for the percent the CPU is busy, so well subtract idle time from 100, to two decimal places
    cpu_load = round(100 -  cpu_response[0]['cpuInfo']['%Cpu(s)']['idle'], 2)

    return ptp_data, temp_data, cpu_load


def create_tuple(in_ptpdata, in_tempdata, epoch):
    """EOS returns json, resulting in a list of dicts
    SQL insert assumes a stable order of values;
    this function creates a list of tuples in the correct order
    so we can safely use INSERT and use executemany
    Order is:
        lastSyncSeqId, meanPathDelay, intf, offsetFromMaster, realLastSyncTime, skew"""
    t_tuple = ()    # temp holder in loop
    ordered_ptp_data = []
    stable_tuple = ()
    for item in in_ptpdata:
        stable_tuple = (
            item['lastSyncSeqId'],
            item['realLastSyncTime'],
            item['meanPathDelay'],
            item['intf'],
            item['offsetFromMaster'],
            item['skew']
        )
        ordered_ptp_data.append(stable_tuple)

    ordered_temp_data = []
    stable_tuple = ()
    epoch_time = epoch
    for item in in_tempdata:
        stable_tuple = (
            epoch_time,
            item['name'],
            item['currentTemperature'],
            item['description']
        )
        ordered_temp_data.append(stable_tuple)

    return ordered_ptp_data, ordered_temp_data


def main():
    create_ptp_table()
    create_temp_table()
    create_CPU_table()
    epoch_time = int(time.time())
    ptpdata, tempdata, cpuoccupancy = get_data()
    ptp_tuple, temp_tuple = create_tuple(ptpdata, tempdata, epoch_time)
    database = new_connection('./zFork.sqlite3')
    insert_ptp_data(database, ptp_tuple)
    database = new_connection('./zFork.sqlite3')
    insert_temp_data(database, temp_tuple)
    database = new_connection('./zFork.sqlite3')
    insert_cpu_data(database, epoch_time, cpuoccupancy)


if __name__ == "__main__":
    main()
