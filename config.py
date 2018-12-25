#!/usr/bin/env python
# -*- encoding: utf-8 -*-

__author__ = 'LeonWang'

RELEASE_WITH = 1  # 0 refers DEADLINE, 1 refers CPU&RAM

# COMMON BCS ARGS
ACCESS_KEY_ID = "###########"
ACCESS_KEY_SECRET = "##############"
REGION = "cn-beijing"
MAX_RETRY_COUNT = 10
MAX_RETRY_TIME = 60*1000 #60s
WAIT_RANDOM_MIN = 1*1000
WAIT_RANDOM_MAX = 5*1000
LOG_FILE = r"C:\release_log.txt"


# ARGS FOR CREATE CLUSTER
DEADLINE_POOL_NAME = "bcs_test" # 可保持空白，不做链接到deadline pool操作，只创建bcs cluster
IMAGE_ID = "m-###############"
INSTANCE_TYPE = "ecs.sn2.3xlarge"
VPC_CIDR_BLOCK = "192.168.0.0/16"
VPC_ID = "vpc-############"
DESIRED_VM_COUNT = 2
CLUSTER_NAME = "test_deadline2"
CLUSTER_DESCRIPTION = "Leon test"
GROUP_NAME = "group1"

# ARGS FOR BCS CPU&RAM RELEASE CONDITION, SET FOR EACH CLUSTER BELONG TO CUSTOMER
CPU_RAM_RELEASE_CONDITION = dict(
                                default={"RELEASE_TIME_MINUTE": 5, "CPU_PERCENT": 50, "RAM_PERCENT": 50},
                                test5={"RELEASE_TIME_MINUTE": 10, "CPU_PERCENT": 1, "RAM_PERCENT": 1},
                                test_deadline2={"RELEASE_TIME_MINUTE": 5, "CPU_PERCENT": 2, "RAM_PERCENT": 2},
                                 )

# AN ADMINISTRATOR ACCOUNT THAT IMAGE HAS
WIN_USER = "render"
WIN_USER_PASSWORD = "######"

# ARGS FOR DEADLINE
DEADLINE_SERVER_IP = '192.168.#.###'  # SERVER_IP for the web service
DEADLINE_SERVER_PORT = 8082  # the web service listening SERVER_PORT

