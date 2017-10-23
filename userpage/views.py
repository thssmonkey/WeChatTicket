from codex.baseerror import *
from codex.baseview import APIView
from wechat.models import *
import requests
import time
import datetime
from urllib import request, parse
import json

#用户绑定
class UserBind(APIView):

    def validate_user(self):
        """
        input: self.input['student_id'] and self.input['password']
        raise: ValidateError when validating failed
        """

        try:
            url = "https://learn.tsinghua.edu.cn/MultiLanguage/lesson/teacher/loginteacher.jsp"
            username = self.input['student_id']
            password = self.input['password']
            if username and password:
                params = {
                    'username': username,
                    'password': password
                }
                params = parse.urlencode(params).encode('utf-8')
                response = request.urlopen(url, params)
                retr = str(response.read())
                if retr.find("loginteacher_action.jsp") >= 0:
                    return 0
                else:
                    raise ValidateError('账户密码输入错误')
            else:
                raise ValidateError('账户密码验证错误')
        except Exception:
            raise ValidateError('账户密码验证错误')

        # with urlopen(self.url, urllib.urlencode(params).encode('ascii')) as response:
        #     result = json.loads(response.read().decode())
        #     if result['status'] != 'RESTLOGIN_OK':
        #         raise ValidateError(msg='')
        # return

        # try:
        #     url = 'https://id.tsinghua.edu.cn/security_check'
        #     data = {'username': self.input['student_id'], 'password': self.input['password']}
        #     res = requests.post(url, data)
        #     if self.input['student_id'] and self.input['password']:
        #         urlopen()
        #     elif self.input['student_id'] in res.text:
        #         return 0
        #     else:
        #         raise ValidateError("用户绑定验证失败")
        # except:
        #     raise ValidateError("用户绑定验证失败")
        '''
        return 0
        '''
        #raise NotImplementedError('You should implement UserBind.validate_user method')

    def get(self):
        self.check_input('openid')
        return User.get_by_openid(self.input['openid']).student_id

    def post(self):
        self.check_input('openid', 'student_id', 'password')
        user = User.get_by_openid(self.input['openid'])
        self.validate_user()
        user.student_id = self.input['student_id']
        user.save()

#获取活动详情
class ActivityDetail(APIView):

    def get(self):

        self.check_input("id")
        try:
            activity = Activity.objects.get(id = self.input['id'], status = 1)
            activityDetail = {
                "name": activity.name,
                "key": activity.key,
                "description": activity.description,
                "startTime": int(time.mktime(activity.start_time.timetuple())),
                "endTime": int(time.mktime(activity.end_time.timetuple())),
                "place": activity.place,
                "bookStart": int(time.mktime(activity.book_start.timetuple())),
                "bookEnd": int(time.mktime(activity.book_end.timetuple())),
                "totalTickets": activity.total_tickets,
                "picUrl": activity.pic_url,
                "remainTickets": activity.remain_tickets,
                "currentTime": int(time.mktime(datetime.datetime.now().timetuple())),
            }
        except:
            raise LogicError("获取活动详情失败")
        return activityDetail

#获取电子票的详情
class TicketDetail(APIView):

    def get(self):

        self.check_input("openid", "ticket")
        try:
            user = User.objects.get(open_id = self.input['openid'])
            ticket = Ticket.objects.get(student_id = user.student_id, unique_id = self.input['ticket'])
            activity = ticket.activity
            ticketDetail = {
                "activityName": activity.name,
                "place": activity.place,
                "activityKey": activity.key,
                "uniqueId": ticket.unique_id,
                "startTime": int(time.mktime(activity.start_time.timetuple())),
                "endTime": int(time.mktime(activity.end_time.timetuple())),
                "currentTime": int(time.mktime(datetime.datetime.now().timetuple())),
                "status": ticket.status,
            }
        except:
            raise LogicError("获取电子票详情失败")
        return ticketDetail


































