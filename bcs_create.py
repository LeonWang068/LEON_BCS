#!/usr/bin/env python
# -*- encoding: utf-8 -*-


'''
创建：
1、创建新的cluster，确认创建成功后把实例加到deadline pool或者group中；
2、为已存在的cluster补充或修改实例数，确认创建成功后把实例加到deadline pool中。
'''
import time
import datetime
import os
from batchcompute import *
from config import *
from batchcompute.resources import (
    JobDescription, TaskDescription, DAG,
    GroupDescription, ClusterDescription,
    Configs, Networks, VPC, Classic, Mounts, Notification, Topic
)
from bcs_release import get_bcs_client,nodes_in_cluster_group
from deadline_func import *


def create_cluster():
    try:
        client = get_bcs_client()
        # Cluster description.
        cluster_desc = ClusterDescription()
        cluster_desc.Name = CLUSTER_NAME
        cluster_desc.Description = CLUSTER_DESCRIPTION
        # cluster_desc.ImageType = ''  # 'System'
        cluster_desc.ImageId = IMAGE_ID
        cluster_desc.InstanceType = INSTANCE_TYPE
        # Group description
        group_desc1 = GroupDescription()
        group_desc1.DesiredVMCount = DESIRED_VM_COUNT
        # group_desc1.InstanceType = ""  #user group special instance type
        group_desc1.ResourceType = 'OnDemand'
        cluster_desc.add_group(GROUP_NAME, group_desc1)
        configs = Configs()
        # Configs.Disks
        configs.add_system_disk(50, 'cloud_efficiency')
        # Configs.Networks
        # networks  = Networks()
        # vpc = VPC()
        # vpc.CidrBlock = VPC_CIDR_BLOCK
        # vpc.setVpcId = VPC_ID
        # networks.VPC = vpc
        # configs.Networks = networks
        cluster_desc.Configs = configs
        cluster_desc.Configs.Networks.VPC.CidrBlock = VPC_CIDR_BLOCK
        cluster_desc.Configs.Networks.VPC.VpcId = VPC_ID
        # print cluster_desc
        rsp = client.create_cluster(cluster_desc)
        # rsp = client.create_cluster(cluster_desc)
        while 1:
            client = get_bcs_client()
            cluster_info = client.get_cluster(rsp.Id)
            print "%s starting cluster ..." % time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
            print cluster_info.Metrics.RunningCount, cluster_info.Groups[cluster_info.Groups.keys()[0]]["DesiredVMCount"]
            if cluster_info.Metrics.RunningCount == cluster_info.Groups[cluster_info.Groups.keys()[0]]["DesiredVMCount"]:
                break
            time.sleep(5)
        return rsp.Id
    except ClientError, e:
        print (e.get_status_code(), e.get_code(), e.get_requestid(), e.get_msg())
        return False


if __name__ == "__main__":
    start_time = datetime.datetime.now()
    logging_file = os.path.join(os.path.split(LOG_FILE)[0], "%s.txt" % start_time.strftime('%Y-%m-%d-%H-%M-%S'))
    logging_file_object = open(logging_file, "a+")
    logging_file_object.write('\n %s start creating bcs cluster' % start_time.strftime('%Y-%m-%d %H:%M'))
    logging_file_object.close()
    cluster_id = create_cluster()
    print "%s cluster success started" % time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
    logging_file_object = open(logging_file, "a+")
    logging_file_object.write('\n %s cluster success started' % time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()))
    # logging_file_object.close()
    client = get_bcs_client()
    cluster_info = client.get_cluster(cluster_id)
    nodes_dict = nodes_in_cluster_group(cluster_id,cluster_info.Groups.keys()[0])
    # print nodes_dict
    try:
        if DEADLINE_POOL_NAME != "":
            if DEADLINE_POOL_NAME not in get_pool_list():
                add_pool(DEADLINE_POOL_NAME)
                print "%s deadline pool %s success created" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),DEADLINE_POOL_NAME)
                logging_file_object.write("\n %s deadline pool %s success created" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),DEADLINE_POOL_NAME))
            while 1:
                if set(nodes_dict.keys()).issubset(set(get_slave_list())):
                    add_nodes_to_pool(nodes_dict.keys(), DEADLINE_POOL_NAME)
                    print "%s %s node has been add to deadline pool %s" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),nodes_dict.keys(),DEADLINE_POOL_NAME)
                    logging_file_object.write("\n %s %s node has been add to deadline pool %s" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),nodes_dict.keys(),DEADLINE_POOL_NAME))
                    break
                print "%s slaves starting..." % time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
                time.sleep(5)
        else:
            print "%s can not find user defined DEADLINE_POOL_NAME" % time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
            logging_file_object.write("\n %s can not find user defined DEADLINE_POOL_NAME" % time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()))
    except RuntimeError,e:
        print "%s %s" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),e.message)
        logging_file_object.write("\n %s %s" % (time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),e.message))
    logging_file_object.close()

