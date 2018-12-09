#!/usr/bin/env python
# -*- encoding: utf-8 -*-


from Deadline.DeadlineConnect import DeadlineCon as Connect
from config import *

__author__ = 'LeonWang'

'''
To use deadline standlone python api,you should
1. copy the "Deadline" folder containing the Standlone Python API from \\your\repository\api\python to the "site-packages" folder of your python installation;
2. set the web service listening SERVER_PORT in "Deadline Monitor-->Tools-->Configure Repository Options-->Web Service Settings-->Listening Port",by default it`s 8080;
3. in your Deadline client installation folder \\Thinkbox\Deadline\bin you will find deadlinewebservice.exe launch it and you are ready to use deadline api.
'''


def get_deadline_connect():
    try:
        return Connect(DEADLINE_SERVER_IP,DEADLINE_SERVER_PORT)
    except RuntimeError,e:
        print e.message
        return False


def get_pool_list():
    con = get_deadline_connect()
    pool_list = con.Pools.GetPoolNames()
    return pool_list


def get_slave_list():
    con = get_deadline_connect()
    slave_list = con.Slaves.GetSlaveNames()
    return slave_list


def add_pool(pool_name):
    con = get_deadline_connect()
    test = con.Pools.AddPool(pool_name)
    if test == True:
        return True
    else:
        print test
        return False


def add_nodes_to_pool(node_list,pool_name):
    con = get_deadline_connect()
    test = con.Slaves.AddPoolToSlave(node_list,pool_name)
    # print test
    return True


def get_status_with_name(slave_name):
    con = get_deadline_connect()
    try:
        slave_info = con.Slaves.GetSlaveInfo(slave_name)
        return slave_info
    except RuntimeError,e:
        print e.message

if __name__ == "__main__":
    # add_pool("test")
    print get_slave_list()

