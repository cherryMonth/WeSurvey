# coding=utf-8


import xmlrpclib

<<<<<<< HEAD
s = xmlrpclib.Server("http://localhost:5007")

data = {"user_id": 1, 'url': "www.baidu.com", "num": 10, "dispersion": 5, "type": True, "func": ""}

print s.kill_task("1")
=======
s = xmlrpclib.Server("http://localhost:5001")

temp = s.get_online_protocol()
print s.get_online_sock()
print temp
>>>>>>> 9d5b2532604be72831385144fc45a0fcbf2d3cf4
