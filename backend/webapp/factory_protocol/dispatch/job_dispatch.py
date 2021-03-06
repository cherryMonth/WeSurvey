# coding=utf-8

"""
实现任务的分发
"""

from backend.webapp.onlineProtocol import online
import xmlrpclib
import json
from twisted.internet import reactor
import datetime
import time


class NodeDisPatch:

    def __init__(self):
        self.task_id = 0
        self.work = dict()

    @staticmethod
    def get_next_index(node_list):  # 先找到权重最大的结点分配给其任务 然后降低其权重

        total = 0
        _index = -1
        for _i in range(len(node_list)):
            node_list[_i].cur_weight += node_list[_i].weight
            total += node_list[_i].weight
            if _index == -1 or node_list[_index].cur_weight < node_list[_i].cur_weight:
                _index = _i

        node_list[_index].cur_weight -= total
        return node_list[_index]

    def put_data(self, data, user_id):
        node_list = online.get_online_protocols("node")
        node = self.get_next_index(node_list) if node_list else None
        if node:
            try:
                server = xmlrpclib.Server("http://" + node.rpc_address)
                data['task_id'] = str(self.task_id)
                self.task_id += 1
                data['user_id'] = user_id
                data['node_id'] = node.id
                node.work_number += 1
                data['cur_weight'] = node.cur_weight
                data['status'] = 'work'
                data['schedule'] = 0.0
                data['ack'] = 0
                data['entry_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.work[data['task_id']] = data
                if not online.observe.get('user' + str(data['user_id'])):
                    online.observe['user' + str(data['user_id'])] = list()
                server.add_job(data)
                return {'status': 200}
            except Exception as e:
                return {'status': 500, 'info': str(e)}
        else:
            return {'status': 500, 'info': 'no slave can work!'}

    def get_work_info(self, user_id):
        work = list()
        for key in self.work.keys():
            if self.work[key]['user_id'] == user_id:
                work.append(self.work[key])
        return work

    def check_task_info(self):
        for key in self.work.keys():
            _time = self.work[key]['entry_time']
            time_list = time.strptime(_time, '%Y-%m-%d %H:%M:%S')
            total = time.mktime(time_list)
            cur = int(time.time())
            node_list = online.get_online_protocols("node")
            if cur - total > 5 and self.work[key]['status'] != "failed":
                try:
                    self.work[key]['status'] = "failed"
                    self.work[key]['ack'] += 1
                    self.work[key]['entry_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print cur - total
                    name = online.id_name_map[self.work[key]["node_id"]]
                    if node_list:
                        self.work[key]['result'] = "<a>任务超时</a>"
                        server = xmlrpclib.Server("http://" + online.online_protocol[name].rpc_address)
                        server.kill_task(key)
                    else:
                        self.work[key]['result'] = "<a>no slave</a>"
                    self.dispatch_info("user" + str(self.work[key]['user_id']), self.work[key])
                except Exception as e:
                    print e
            elif self.work[key]['status'] == "failed":
                if self.work[key]['ack'] < 3:
                    node = self.get_next_index(node_list) if node_list else None
                    if node:
                        try:
                            self.work[key]['node_id'] = node.id
                            self.work[key]['cur_weight'] = node.cur_weight
                            server = xmlrpclib.Server("http://" + node.rpc_address)
                            server.add_job(self.work[key])
                        except Exception as e:
                            print e
                    else:
                        self.work[key]['result'] = "<a>no slave</a>"
                elif self.work[key]['ack'] >= 3:
                    self.work[key]["result"] = "<a>超过最大重试次数</a>"
                self.dispatch_info("user" + str(self.work[key]['user_id']), self.work[key])
        reactor.callLater(1, self.check_task_info)

    def dispatch_info(self, user, info):
        task_list = online.get_online_protocols("task")
        for task in task_list:
            if task.div_name == user:
                task.transport.write(json.dumps(info))


NodeDisPatch = NodeDisPatch()
reactor.callLater(1, NodeDisPatch.check_task_info)
