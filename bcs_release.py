#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import time
import datetime
import os
import json
import wmi
import warnings
from retrying import retry
from batchcompute import Client, ClientError, JsonError
from config import *
from deadline_func import *

__author__ = 'LeonWang'


def get_bcs_client():
    ENDPOINT = "batchcompute.%s.aliyuncs.com" % REGION
    Client.register_region(REGION, ENDPOINT)
    return Client(ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY_SECRET)


def list_clusters():
    # {u'test': {'running_count': 2, 'group': u'group1', 'id': u'cls-qo35hl7kflntkvfot0o007'}}
    client = get_bcs_client()
    cluster_dict = {}
    try:
        marker = ""
        max_item = 100
        cluster_cnt = 0
        while 1:
            response = client.list_clusters(marker, max_item)
            marker = response.NextMarker
            cluster_cnt += len(response.Items)
            for cluster in response.Items:
                # print cluster.Id
                # print cluster.Name
                # print cluster.State
                # print cluster.ImageId
                # print cluster.Metrics.RunningCount
                group_list = []
                for group in cluster.Groups:
                    group_list.append(group)
                    # print group,cluster.Groups[group]["ActualVMCount"],cluster.Groups[group]["InstanceType"]
                cluster_dict[cluster.Name] = dict(
                                                id=cluster.Id,
                                                running_count=cluster.Metrics.RunningCount,
                                                group=group_list[0],
                                                )
            if marker.strip() == '':
                break
        if cluster_dict == {}:
            return False
        else:
            return cluster_dict
    except ClientError, e:
        print (e.get_status_code(), e.get_code(), e.get_requestid(), e.get_msg())


def is_retry_error(exception):
    if isinstance(exception, ClientError) and exception.get_status_code()/100 == 5:
        return True
    elif isinstance(exception, JsonError):
        return True
    else:
        return False


def nodes_in_cluster_group(cluster_id, group_name):
    client = get_bcs_client()

    # @retry(stop_max_attempt_number=MAX_RETRY_COUNT,
    #     stop_max_delay=MAX_RETRY_TIME,
    #     retry_on_exception=is_retry_error,
    #     wait_random_min=WAIT_RANDOM_MIN,
    #     wait_random_max=WAIT_RANDOM_MAX)
    def list_wrapper(cluster_id, group_name, next_marker, max_item_count):
        return client.list_cluster_instances(cluster_id, group_name, next_marker, max_item_count)

        # round = 1
    max_item_count = 100
    next_marker = ""
    instance_dict = {}
    while 1:
        # round += 1
        response = list_wrapper(cluster_id, group_name, next_marker, max_item_count)
        next_marker = response.NextMarker
        # print len(response.Items)
        for cluster_instance in response.Items:
            instance_dict[cluster_instance.HostName] = {'id' : cluster_instance.Id,
                                                        'ip' : cluster_instance.IpAddress}
        if next_marker.strip() == '':
            break
    return instance_dict


def delete_node_by_id(cluster_id, group_name, node_id):
    client = get_bcs_client()
    @retry(stop_max_attempt_number=MAX_RETRY_COUNT,
           stop_max_delay=MAX_RETRY_TIME,
           retry_on_exception=is_retry_error,
           wait_random_min=WAIT_RANDOM_MIN,
           wait_random_max=WAIT_RANDOM_MAX)
    def delete_wrapper(cluster_id, group_name, node_id):
        try:
            return client.delete_cluster_instance(cluster_id, group_name, node_id)
        except ClientError, e:
            if e.get_status_code() == 409:
                warnings.warn(
                    "id %s in group(%s) of cluster(%s) have been already deleted" % (node_id, group_name, cluster_id),
                    RuntimeWarning)
                return
            else:
                raise e

    delete_wrapper(cluster_id, group_name, node_id)


def get_cpu_gpu_percent(ip, user, password):
    result = {}
    conn = wmi.WMI(computer=ip, user=user, password=password)
    cp = conn.Win32_Processor()
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M')
    cs = conn.Win32_ComputerSystem()
    os = conn.Win32_OperatingSystem()
    memTotal = int(int(cs[0].TotalPhysicalMemory) / 1024 / 1024)
    memFree = int(int(os[0].FreePhysicalMemory) / 1024)
    memPercent = 100 - memFree * 100 / memTotal
    result['time'] = timestamp
    result['cp'] = cp[0].LoadPercentage
    result['mp'] = memPercent
    return result

def delete_cluster(cluster_id):
    client = get_bcs_client()
    try:
        rsp = client.delete_cluster(cluster_id)
        return True
    except ClientError, e:
        print (e.get_status_code(), e.get_code(), e.get_requestid(), e.get_msg())


if __name__ == '__main__':
    start_time = datetime.datetime.now()
    logging_file = os.path.join(os.path.split(LOG_FILE)[0],"%s.txt"%start_time.strftime('%Y-%m-%d-%H-%M-%S'))
    logging_file_object = open(logging_file,"a+")
    logging_file_object.write('\n %s start monitoring' % start_time.strftime('%Y-%m-%d %H:%M'))
    logging_file_object.close()
    while 1:
        this_now = datetime.datetime.now()
        delta = this_now - start_time
        if delta.seconds % 60 == 0:
            try:
                file_object = open(LOG_FILE,'r')
            except:
                file_object = None
            try:
                log_dict = json.loads(file_object.read())
                file_object.close()
            except:
                log_dict = {}
            try:
                cluster_dict = list_clusters()
                release_dict = {}
                this_time_dict = {}
                for cluster in cluster_dict.keys():
                    # print cluster,cluster_dict[cluster]
                    # {u'test': {'running_count': 2, 'instances': {u'hq-bcs3': {'ip': u'192.168.192.174', 'id': u'ins-qo316d6q6lo1hbl02d4000'}, u'hq-bcs2': {'ip': u'192.168.192.173', 'id': u'ins-qo316d110lo1gatk2d4000'}}, 'group': u'group1', 'id': u'cls-qo35hl7kflntkvfot0o007'}}
                    if cluster_dict[cluster]['running_count'] == 0:
                        delete_cluster(cluster_dict[cluster]['id'])
                        logging_file_object = open(logging_file, 'a+')
                        logging_file_object.write("\n %s %s has been released with no instances" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()), cluster))
                        print "%s %s has been released with no instances" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()), cluster)
                    else:
                        cluster_dict[cluster]['instances'] = nodes_in_cluster_group(cluster_dict[cluster]['id'],cluster_dict[cluster]['group'])
                        if cluster in CPU_RAM_RELEASE_CONDITION.keys():
                            cluster_condition = CPU_RAM_RELEASE_CONDITION[cluster]
                        else:
                            cluster_condition = CPU_RAM_RELEASE_CONDITION['default']
                        for instance in cluster_dict[cluster]['instances'].keys():
                            if RELEASE_WITH == 0:
                                try:
                                    temp_stat = get_status_with_name("iZ2zea2sf1mn2vZ")['Stat']
                                except:
                                    temp_stat = 0
                                # 0 = Unknown, 1 = Rendering, 2 = Idle, 3 = Offline, 4 = Stalled, 8 = StartingJob
                                judge_condition = temp_stat != 1 or temp_stat != 8
                            else:
                                arg_dict = get_cpu_gpu_percent(ip=cluster_dict[cluster]['instances'][instance]['ip'], user=WIN_USER, password=WIN_USER_PASSWORD)
                                judge_condition = arg_dict['cp'] < cluster_condition['CPU_PERCENT'] and arg_dict['mp'] < cluster_condition['RAM_PERCENT']
                            if judge_condition:
                                release_conf = 1
                                i = 1
                                while i < cluster_condition['RELEASE_TIME_MINUTE']:
                                    temp = this_now - datetime.timedelta(minutes=i)
                                    print temp.strftime('%Y-%m-%d %H:%M')
                                    print log_dict.keys()
                                    if temp.strftime('%Y-%m-%d %H:%M') in log_dict.keys():
                                        print 'yes'
                                        if log_dict[temp.strftime('%Y-%m-%d %H:%M')][instance]['release'] == 0:
                                            break
                                    else:
                                        break
                                    i += 1
                                # print i
                                if i == cluster_condition['RELEASE_TIME_MINUTE']:
                                    release_dict[instance] = {
                                        'instance_id': cluster_dict[cluster]['instances'][instance]['id'],
                                        'instance_ip': cluster_dict[cluster]['instances'][instance]['ip'],
                                        'cluster_id': cluster_dict[cluster]['id'],
                                        'group_name': cluster_dict[cluster]['group']
                                    }
                            else:
                                release_conf = 0
                            instance_dict = dict(
                                instance_id=cluster_dict[cluster]['instances'][instance]['id'],
                                instance_ip=cluster_dict[cluster]['instances'][instance]['ip'],
                                cluster_id=cluster_dict[cluster]['id'],
                                group_name=cluster_dict[cluster]['group'],
                                release=release_conf
                            )
                            this_time_dict[instance] = instance_dict
                            # now = datetime.datetime.now()
                    this_time = this_now.strftime('%Y-%m-%d %H:%M')
                    log_dict[this_time] = this_time_dict
                    file_object = open(LOG_FILE, 'w')
                    file_object.write(json.dumps(log_dict))
                    file_object.close()
                    logging_file_object = open(logging_file, 'a+')
                    logging_file_object.write("\n %s Writing logs to %s" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()), LOG_FILE))
                    print "%s Writing logs to %s" % (time.strftime('%a, %d %b %Y %H:%M', time.localtime()), LOG_FILE)
                    logging_file_object.write("\n %s releasing nodes ：%s" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()), release_dict.keys()))
                    logging_file_object.close()
                    print "%s releasing nodes ：%s" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()), release_dict)
                    if release_dict != {}:
                        for node in release_dict.keys():
                            delete_node_by_id(release_dict[node]['cluster_id'],release_dict[node]['group_name'],release_dict[node]['instance_id'])
                            logging_file_object = open(logging_file, 'a+')
                            logging_file_object.write("\n %s %s id:%s ip:%s has been released" % (time.strftime('%a, %d %b %Y %H:%M', time.localtime()), node, release_dict[node]['instance_id'],release_dict[node]['instance_ip']))
                            logging_file_object.close()
                            print "%s %s id:%s ip:%s has been released" % (time.strftime('%a, %d %b %Y %H:%M', time.localtime()), node, release_dict[node]['instance_id'],release_dict[node]['instance_ip'])
            except:
                print "there has no clusters"
                break
        time.sleep(1)


'''
程序每分钟循环记录，cluster list，cluster内存在的实例数，实例列表，各实例cpu ram状态：
1、循环检测用户指定region下cluster内实例cpu&ram状态，
2、根据用户配置的cluster释放条件进行判断
先根据cluster获得用户设定的条件，再拿跑出的数据直接跟条件里面的cp和mp比较，符合条件的话在去logdict里面找几分钟之前的数据，如果也符合添加到删除list里面，不符合就记一条
3、符合用户自定义界限，释放掉该实例，不符合界限，存log（log以时间为主键，实例名为二键，各项参数为三键）
4、如果cluster内实例数量为0，删除该cluster
还是设定各个cluster超过多长时间就释放掉，然后循环cluster 里面node，根据ip用
deadline获取slave状态，idle或者获取不到都算作失败。
cluster
'''