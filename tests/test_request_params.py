# coding: utf-8
class Request(object):
    def __init__(self):
        self.params = {}
        self.params["filter"] = 'user_id > "3"'
        self.params["heart_rate"] = 70
        self.params["blood_o2"] = "95"
        self.params["temperature"] = 98.2
        # self.params["username"] = "user_01"
        # self.params["password"] = "user_01"


request = Request()
