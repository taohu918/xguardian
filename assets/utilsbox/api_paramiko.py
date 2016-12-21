# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

import paramiko
import time
import os
from xguardian import settings
from functools import reduce

path_split_list = settings.STATICFILES_DIRS[0].split('\\')


class APIParamiko(object):
    # 添加新主机会自动通过前端传来的账号密码，来把秘钥传过去。
    # 执行命令通过秘钥执行，首先去数据库判断是否有主机权限。
    def __init__(self):
        self.key_path = '/root/.ssh/id_rsa'
        self.static_file_path = reduce(lambda x, y: os.path.join(x, y), path_split_list) + '/upload'
        # print(self.static_file_path)

    @staticmethod
    def pass_rsa(ip, port, username, password):
        # 这个方法默认传输秘钥使用。
        ssh = paramiko.Transport((ip, port))
        ssh.connect(username=username, password=password)
        ssh_transfor = paramiko.SFTPClient.from_transport(ssh)
        ssh_transfor.put('/root/.ssh/id_rsa.pub', '/root/.ssh/authorized_keys')
        ssh_transfor.put('/root/collect_items.py', '/root/collect_items.py')  # 刚刚开始，把秘钥和搜集模块都传到节点上。
        ssh_transfor.close()

    def ssh_exec_cmd(self, ip, username, port, command, q_obj):
        # 通过秘钥执行命令
        stime = int(time.time())
        time_array = time.localtime(stime)
        xstyle_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)

        command_info = {}
        key = paramiko.RSAKey.from_private_key_file(self.key_path)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, key)
        stdin, stdout, stderr = ssh.exec_command(command)
        answer = stdout.read()
        ssh.close()

        time_cost = '%.2f' % (int(time.time()) - stime)

        if answer:
            command_info[ip] = [xstyle_time, time_cost + ' sec', command, answer]
        else:
            command_info[ip] = [xstyle_time, time_cost + ' sec', command, stderr.read()]

        q_obj.put(command_info)

    def execute_collect(self, ip, port, username):
        key = paramiko.RSAKey.from_private_key_file(self.key_path)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, key)
        stdin, stdout, stderr = ssh.exec_command('python /root/collect_items.py')
        answer = stdout.read()
        ssh.close()
        return answer

    def obj_upload(self, ip, username, port, source_file, target_path, q_obj):
        # 通过秘钥传输文件
        stime = int(time.time())
        time_array = time.localtime(stime)
        xstyle_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)

        upload_info = {}

        key = paramiko.RSAKey.from_private_key_file(self.key_path)
        t = paramiko.Transport((ip, port))
        t.connect(username=username, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(t)

        obj = os.path.join(self.static_file_path, source_file)
        target_obj = os.path.join(target_path, source_file)

        print('begin transfer: %s to %s' % (obj, target_obj))
        sftp.put(obj, target_obj)
        time_cost = '%.2f' % (int(time.time()) - stime)

        t.close()
        upload_info[ip] = [xstyle_time, time_cost + ' sec', source_file, 'the file is transfer successful!']
        q_obj.put(upload_info)
        print(upload_info[ip])
