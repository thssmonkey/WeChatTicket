# -*- coding: utf-8 -*-
#
import re
from wechat.wrapper import WeChatHandler
from wechat.models import *
import time
import datetime
import hashlib

__author__ = "Epsirom"


class ErrorHandler(WeChatHandler):

    def check(self):
        return True

    def handle(self):
        return self.reply_text('对不起，服务器现在有点忙，暂时不能给您答复 T T')


class DefaultHandler(WeChatHandler):

    def check(self):
        return True

    def handle(self):
        return self.reply_text('对不起，没有找到您需要的信息:(')


class HelpOrSubscribeHandler(WeChatHandler):

    def check(self):
        return self.is_text('帮助', 'help') or self.is_event('scan', 'subscribe') or \
               self.is_event_click(self.view.event_keys['help'])

    def handle(self):
        return self.reply_single_news({
            'Title': self.get_message('help_title'),
            'Description': self.get_message('help_description'),
            'Url': self.url_help(),
        })


class UnbindOrUnsubscribeHandler(WeChatHandler):

    def check(self):
        return self.is_text('解绑') or self.is_event('unsubscribe')

    def handle(self):
        self.user.student_id = ''
        self.user.save()
 #       return self.reply_text(self.get_message('unbind_account'))
        return self.reply_single_news({
            'Title': "重新绑定",
            'Description': "学号绑定已经解除，重新绑定请点击～",
            'Url': self.url_bind(),
        })


class BindAccountHandler(WeChatHandler):

    def check(self):
        return self.is_text('绑定') or self.is_event_click(self.view.event_keys['account_bind'])

    def handle(self):
        if self.user.student_id:
            return self.reply_text(self.get_message('bind_account'))
        else:
            return self.reply_single_news({
                'Title': "绑定学号",
                'Description': "抢票等功能必须绑定学号后才能使用，绑定请点击～",
                'Url': self.url_bind(),
            })


class BookEmptyHandler(WeChatHandler):

    def check(self):
        return self.is_event_click(self.view.event_keys['book_empty'])

    def handle(self):
        return self.reply_text(self.get_message('book_empty'))


class ComputeExpHandler(WeChatHandler):

    def check(self):
        return re.match(r'^[\+\-\*\/\(\)\d]+$', self.input['Content'])

    def handle(self):
        try:
            for ch in self.input['Content']:
                if not ch in "0123456789+-*/":
                    return self.reply_text("数学表达式错误，请重新输入")
            res = eval(self.input['Content'])
        except:
            return self.reply_text("数学表达式错误，请重新输入")
        else:
            return self.reply_text(str(res))


class CheckTicketHandler(WeChatHandler):

    def check(self):
        return self.is_text('查票') or self.is_event_click(self.view.event_keys['get_ticket'])

    def handle(self):
        tickets = Ticket.objects.filter(student_id = self.user.student_id, status__gte = Ticket.STATUS_VALID)
        if self.user.student_id == '' or not self.user:
            return self.reply_single_news({
                'Title': "绑定学号",
                'Description': "查票等功能必须绑定学号后才能使用，绑定请点击～",
                'Url': self.url_bind(),
            })
        elif not tickets:
            return self.reply_text(self.get_message('get_ticket', tickets=tickets))
        else:
            articles = []
            for ticket in tickets:
                activity = ticket.activity
                articles.append({
                    'Title': activity.name + "\n活动时间：\n" + str(activity.start_time).split('+')[0]
                    + " -- " + str(activity.end_time).split('+')[0],
                    'Description': activity.description,
                    'Url': self.url_get_ticket() + str(ticket.unique_id),
                    'PicUrl': activity.pic_url,
                })
            return self.reply_news(articles)


class BookWhatHandler(WeChatHandler):

    def check(self):
        return self.is_text('抢啥') or self.is_event_click(self.view.event_keys['book_what'])

    def handle(self):
        activities = Activity.objects.filter(status = Activity.STATUS_PUBLISHED).order_by("book_start")
        if not activities:
            return self.reply_text(self.get_message('book_what', activities = activities))
        articles = []
        for activity in activities:
            articles.append( {
                'Title': activity.name + "\n余票：" + str(activity.remain_tickets) + "\n抢票时间：\n"
                + str(activity.book_start).split('+')[0] + " -- " + str(activity.book_end).split('+')[0],
                'Description': activity.description,
                'Url': self.url_book_what() + str(activity.id),
                'PicUrl': activity.pic_url,
            } )
        return self.reply_news(articles)


class BookTicketHandler(WeChatHandler):

    user = ""
    flag = 0

    def check(self):
        return self.is_event_book_click(self.view.event_keys['book_header']) or self.is_text_command("抢票")

    def handle(self):
        if self.is_event_book_click(self.view.event_keys['book_header']):
            activityId = self.input['EventKey'].split('_')[-1]
            activity = Activity.objects.get(id = int(activityId))
        elif self.is_text_command("抢票"):
            commands = self.input['Content'].split()[-1]
            activity = Activity.objects.get(key=commands)
        if self.flag == 0:
            currentTime = str(datetime.datetime.now())
        else:
            currentTime = str(0)
        existTicket = Ticket.objects.filter(student_id = self.user.student_id, activity = activity)
        if self.user.student_id == '' or not self.user:
            print(1)
            return self.reply_single_news({
                'Title': "绑定学号",
                'Description': "抢票等功能必须绑定学号后才能使用，绑定请点击～",
                'Url': self.url_bind(),
            })
            #return self.reply_text(self.get_message('bind_account'))
        elif activity.status == Activity.STATUS_DELETED:
            print(2)
            return self.reply_text("该活动已被取消")
        elif activity.status == Activity.STATUS_SAVED:
            print(3)
            return self.reply_text("该活动还未发布")
        elif existTicket and existTicket[0].status == Ticket.STATUS_VALID:
            print(4)
            return self.reply_text("您已经订有该票")
        elif existTicket and existTicket[0].status == Ticket.STATUS_USED:
            print(5)
            return self.reply_text("您已经订有该票并且在使用中")
        elif currentTime >= str(activity.book_end) and self.flag == 0:
            print(6)
            return self.reply_text("抢票时间已经结束")
        elif currentTime < str(activity.book_start) and self.flag != 2:
            print(7)
            return self.reply_text("抢票还未开始")
        elif activity.remain_tickets <= 0:
            print(8)
            return self.reply_text("票已经抢完")
        elif existTicket and existTicket[0].status == Ticket.STATUS_CANCELLED:
            print(9)
            existTicket[0].status = Ticket.STATUS_VALID
            existTicket[0].save()
            activity.remain_tickets -= 1
            activity.save()
            #return self.reply_text(self.get_message('book_succeed', ticket = existTicket[0]))
            return self.reply_single_news({
                'Title': activity.name + " 抢票成功！！！",
                'Description': activity.description,
                'Url': self.url_get_ticket() + existTicket[0].unique_id,
                'PicUrl': activity.pic_url,
            })
        else:
            print(10)
            ticket = Ticket(
                student_id=self.user.student_id,
                unique_id=hashlib.md5(str(time.clock()).encode('utf-8')).hexdigest(),
                activity = activity,
                status=Ticket.STATUS_VALID
            )
            ticket.save()
            activity.remain_tickets -= 1
            activity.save()
            #return self.reply_text(self.get_message('book_succeed', ticket = ticket))
            return self.reply_single_news({
                'Title': activity.name + " 抢票成功！！！",
                'Description': activity.description,
                'Url': self.url_get_ticket() + ticket.unique_id,
                'PicUrl': activity.pic_url,
            })


class RefundTicketHandler(WeChatHandler):

    user = ""
    flag = 0

    def check(self):
        return self.is_text_command("退票")

    def handle(self):
        if self.user.student_id == '' or not self.user:
            print(1)
            return self.reply_single_news({
                'Title': "绑定学号",
                'Description': "退票等功能必须绑定学号后才能使用，绑定请点击～",
                'Url': self.url_bind(),
            })
            #return self.reply_text(self.get_message('bind_account'))
        commands = self.input['Content'].split()[-1]
        activity = Activity.objects.get(key = commands)
        ticket = Ticket.objects.filter(student_id = self.user.student_id, activity = activity)
        if not ticket:
            print(2)
            return self.reply_text("您未订该票")
        if ticket[0].status == Ticket.STATUS_CANCELLED:
            print(3)
            return self.reply_text("您已退订该票")
        if self.flag == 0:
            currentTime = str(datetime.datetime.now())
        else:
            currentTime = str(0)

        if currentTime >= str(activity.start_time) and self.flag == 0:
            print(4)
            if currentTime < str(activity.end_time):
                return self.reply_text("活动已经开始，退票无效")
            else:
                return self.reply_text("活动已经结束，退票无效")
        if currentTime < str(activity.book_start) and self.flag != 2:
            print(5)
            return self.reply_text("还未开始发售")
        if ticket[0].status == Ticket.STATUS_USED:
            print(6)
            return self.reply_text("该票正在使用中，退票无效")
        print(7)
        activity.remain_tickets += 1
        activity.save()
        ticket[0].status = Ticket.STATUS_CANCELLED
        ticket[0].save()
        return self.reply_text("退票成功")




















