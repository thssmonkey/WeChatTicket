from django.shortcuts import render
from codex.baseview import APIView
from django.contrib import auth
from codex.baseerror import *
from wechat.models import *
from WeChatTicket.settings import *
from wechat.views import *
from wechat.wrapper import *
import requests
import time
import datetime

#管理员用户登录
class UserLogin(APIView):

    def get(self):

        res = self.request.user.is_authenticated()
        if res:
            return 0
        else:
            raise ValidateError("用户验证失败")

    def post(self):

        user = auth.authenticate(username=self.input['username'], password=self.input['password'])
        if user:
            if user.is_active:
                auth.login(self.request, user)
            return 0
        else:
            raise ValidateError("用户登录失败")

#管理员用户登出
class UserLogout(APIView):

    def post(self):

        try:
            if self.request.user.is_authenticated():
                auth.logout(self.request)
                return 0
            else:
                raise ValidateError("用户已经登出")
        except:
            raise ValidateError("用户登出失败")

#获取活动列表
class ActivityList(APIView):

    def get(self):

        if not self.request.user.is_authenticated():
            raise ValidateError("用户未登录")
        activityList = []
        try:
            activities = Activity.objects.filter(status__gte = Activity.STATUS_SAVED)
            for activity in activities:
                activityList.append( {
                    "id": activity.id,
                    "name": activity.name,
                    "description": activity.description,
                    "startTime": int(time.mktime(activity.start_time.timetuple())),
                    "endTime": int(time.mktime(activity.end_time.timetuple())),
                    "place": activity.place,
                    "bookStart": int(time.mktime(activity.book_start.timetuple())),
                    "bookEnd": int(time.mktime(activity.book_end.timetuple())),
                    "currentTime": int(time.mktime(datetime.datetime.now().timetuple())),
                    "status": activity.status,
                } )
        except:
            raise LogicError("获取活动列表失败")
        return activityList

#删除活动
class ActivityDelete(APIView):

    def post(self):

        self.check_input("id")
        try:
            activity = Activity.objects.filter(id = self.input['id'])[0]
            activity.status = Activity.STATUS_DELETED
            activity.save()
        except:
            raise LogicError("活动删除失败")
        return 0

#创建活动
class ActivityCreate(APIView):

    def post(self):

        self.check_input("name", "key", "place", "description", "picUrl", "startTime", "endTime", "bookStart", "bookEnd", "totalTickets", "status")
        if not self.request.user.is_authenticated():
            raise ValidateError("用户未登录")
        try:
            Activity.objects.create(
                name = self.input['name'],
                key = self.input['key'],
                place = self.input['place'],
                description = self.input['description'],
                pic_url = self.input['picUrl'],
                start_time = self.input['startTime'],
                end_time = self.input['endTime'],
                book_start = self.input['bookStart'],
                book_end = self.input['bookEnd'],
                total_tickets = self.input['totalTickets'],
                status = self.input['status'],
                remain_tickets = self.input['totalTickets']
            )
        except:
            raise LogicError("活动创建失败")
        return 0

#上传图片并保存到服务器
class ImageUpload(APIView):

    def post(self):

        if not self.request.user.is_authenticated():
            raise ValidateError("用户未登录")
        self.check_input("image")
        try:
            image = self.input['image'][0]
            imageFile = open(IMAGE_ROOT + image.name, "w+b")
            imageFile.write(image.read())
            imageFile.close()
        except:
            raise LogicError("图片上传失败")

        return SITE_DOMAIN + "/static/images/" + image.name

#获取活动详情
class ActivityDetail(APIView):

    def get(self):

        self.check_input("id")
        if not self.request.user.is_authenticated():
            raise ValidateError("用户未登录")
        try:
            activity = Activity.objects.filter(id = self.input['id'])[0]
            uesdTickets = 0
            for ticket in Ticket.objects.filter(activity = activity):
                if ticket.status == Ticket.STATUS_USED:
                    uesdTickets += 1
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
                "bookedTickets": activity.total_tickets - activity.remain_tickets,
                "uesdTickets": uesdTickets,
                "currentTime": int(time.mktime(datetime.datetime.now().timetuple())),
                "status": activity.status,
            }
        except:
            raise LogicError("获取活动详情失败")
        return activityDetail

    def post(self):

        self.check_input("id", "name", "place", "description", "picUrl", "startTime", "endTime", "bookStart", "bookEnd", "totalTickets", "status")
        if not self.request.user.is_authenticated():
            raise ValidateError("用户未登录")
        try:
            activity = Activity.objects.filter(id = self.input['id'])[0]
            activity.name = self.input['name']
            activity.key = self.input['key']
            activity.place = self.input['place']
            activity.description = self.input['description']
            activity.pic_url = self.input['picUrl']
            activity.start_time = self.input['startTime']
            activity.end_time = self.input['endTime']
            activity.book_start = self.input['bookStart']
            activity.book_end = self.input['bookEnd']
            activity.total_tickets = self.input['totalTickets']
            activity.status = self.input['status']
            activity.save()
        except:
            raise LogicError("修改活动详情失败")
        return 0

#微信抢票菜单调整
class ActivityMenu(APIView):

    def get(self):

        if not self.request.user.is_authenticated():
            raise ValidateError("用户未登录")
        currentInMenuList = []
        currentCanJoinMenuList = []
        try:
            for menu in CustomWeChatView.lib.get_wechat_menu():
                if menu["name"] == "抢票":
                    currentInMenuList += menu.get("sub_button", [])
            keyStr = ''
            for menu in currentInMenuList:
                keyStr += menu["key"]
            activities = Activity.objects.filter(status__gte = Activity.STATUS_SAVED)
            for activity in activities:
                pos = 0
                flag = False
                if str(activity.id) in keyStr:
                    for menu in currentInMenuList:
                        pos += 1
                        if str(activity.id) == menu["key"].split('_')[-1]:
                            flag = True
                            break
                if not flag:
                    pos = 0
                currentCanJoinMenuList.append( {
                    "id": activity.id,
                    "name": activity.name,
                    "menuIndex": pos,
                } )
        except:
            raise LogicError("获取当前微信抢票菜单失败")
        return currentCanJoinMenuList

    def post(self):

        activitiyIdList = self.input
        for id in activitiyIdList:
            self.check_input(id)
        if not self.request.user.is_authenticated():
            raise ValidateError("用户未登录")
        menuList = []
        try:
            for id in activitiyIdList:
                menuList.append(Activity.objects.get(id = id))
            CustomWeChatView.update_menu(menuList)
        except:
            raise LogicError("修改微信抢票失败")
        return 0

#检票
class ActivityCheckin(APIView):

    def post(self):
        if "ticket" in self.input:
            self.check_input("actId", "ticket")
        elif "studentId" in self.input:
            self.check_input("actId", "studentId")
        if not self.request.user.is_authenticated():
            raise ValidateError("用户未登录")
        try:
            activity = Activity.objects.filter(id = self.input['actId'])
            if "ticket" in self.input:
                ticket = Ticket.objects.filter(unique_id = self.input['ticket'], activity = activity)
            elif "studentId" in self.input:
                ticket = Ticket.objects.filter(student_id = self.input['studentId'], activity = activity)
        except:
            raise ValidateError("检票失败")
        if ticket and ticket[0].status == Ticket.STATUS_VALID:
            ticket[0].status = Ticket.STATUS_USED
            ticket[0].save()
            ticketDetail = {
                "ticket": ticket[0].unique_id,
                "studentId": ticket[0].student_id,
            }
            return ticketDetail
        elif ticket and ticket[0].status == Ticket.STATUS_USED:
            raise ValidateError("该票已被检过")
        else:
            raise ValidateError("检票失败")











