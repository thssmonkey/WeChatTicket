from django.test import TestCase, LiveServerTestCase
from django.core.urlresolvers import resolve
from unittest.mock import Mock, patch, MagicMock
from django.http import HttpRequest
from selenium import webdriver
from codex.baseerror import *
from wechat.models import *
from unittest.mock import *
from wechat.views import *
from wechat.handlers import *
import userpage.urls
import datetime
import time
import json

class ModelsTest(TestCase):

    def test_get_by_openid_wrong(self):
        user = User()
        with self.assertRaises(LogicError):
            user.get_by_openid(0)

class HandlerTest(TestCase):

    mock_time = datetime.datetime.now()

    mock_user = {
        "open_id": "12",
        "student_id": "12345",
    }

    mock_activity = {
        "id": "1",
        "name": "2",
        "key": "3",
        "description": "4",
        "end_time": mock_time,
        "start_time": mock_time,
        "book_end": mock_time,
        "book_start": mock_time,
        "total_tickets": "5",
        "pic_url": "6",
        "status": 1,
        "place": "7",
        "remain_tickets": 5
    }

    mock_ticket = {
        "student_id": "12345",
        "unique_id": "wobuzhidaoanicai",
        "activity": Activity(**mock_activity),
        "status": 1,
    }

#绑定
    def test_bind_account_handler_check(self):
        handler = BindAccountHandler(view = CustomWeChatView, msg = {}, user = {})
        handler.input = {
            "MsgType": "text",
            "Content": "绑定"
        }
        self.assertTrue(handler.check())

        handler.input = {
            "MsgType": "event",
            "Event": "CLICK",
            "EventKey": 'SERVICE_BIND',
        }
        self.assertTrue(handler.check())

    def test_bind_account_handler_handle(self):
        handler = BindAccountHandler(view = CustomWeChatView, msg = {}, user = {})
        handler.input = {
            "ToUserName": "?",
            "FromUserName": "?"
        }

#抢啥
    def test_book_what_handler_check(self):
        handler = BookWhatHandler(view = CustomWeChatView, msg = {}, user = {})
        handler.input = {
            "MsgType": "text",
            "Content": "抢啥"
        }
        self.assertTrue(handler.check())

        handler.input = {
            "MsgType": "event",
            "Event": "CLICK",
            "EventKey": 'SERVICE_BOOK_WHAT',
        }
        self.assertTrue(handler.check())

    def test_book_what_handler_handle(self):
        handler = BookWhatHandler(view = CustomWeChatView, msg = {}, user = {})
        handler.input = {
            "ToUserName": "?",
            "FromUserName": "?"
        }
        activities = []
        with patch.object(Activity.objects, 'filter', return_data = activities) as mock_act:
            with patch.object(Activity.objects, 'order_by', return_data = mock_act):
                self.assertTrue(handler.handle())

        for i in range(10):
            activities.append(Mock(book_start=datetime.datetime.now(), book_end=Mock(return_value=999999999)))

        with patch.object(Activity.objects, 'filter', return_data = activities) as mock_act:
            with patch.object(Activity.objects, 'order_by', return_data = mock_act):
                self.assertTrue(handler.handle())

#抢票
    def test_book_ticket_handler_check(self):
        handler = BookTicketHandler(view = CustomWeChatView, msg = {}, user = {})
        handler.input = {
            "MsgType": "text",
            "Content": "抢票 key"
        }
        self.assertTrue(handler.check())

        handler.input = {
            "MsgType": "event",
            "Event": "CLICK",
            "EventKey": 'BOOKING_ACTIVITY_0',
        }
        self.assertTrue(handler.check())

    def test_book_ticket_handler_handle(self):
        handler = BookTicketHandler(view = CustomWeChatView, msg = {}, user = {})
        handler.input = {
            "ToUserName": "?",
            "FromUserName": "?",
            "MsgType": "event",
            "Event": "CLICK",
            "EventKey": 'BOOKING_ACTIVITY_1',
        }
        handler.user = User(**self.mock_user)
        with patch.object(WeChatHandler, 'is_event_book_click', return_value=True):
            with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
                with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                    self.assertTrue(handler.handle())

        handler.input = {
            "ToUserName": "?",
            "FromUserName": "?",
            "MsgType": "text",
            "Content": "抢票 3"
        }

        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())

        handler.user.student_id = ""
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())
        handler.user.student_id = "12345"

        self.mock_activity["status"] = Activity.STATUS_DELETED
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())
        self.mock_activity["status"] = 1

        self.mock_activity["status"] = Activity.STATUS_SAVED
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())
        self.mock_activity["status"] = 1

        self.mock_ticket["status"] = Ticket.STATUS_USED
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())
        self.mock_ticket["status"] = 1

        self.mock_activity["book_end"] = 0
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[]):
                self.assertTrue(handler.handle())
        self.mock_activity["book_end"] = self.mock_time

        handler.flag = 1
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[]):
                self.assertTrue(handler.handle())

        handler.flag = 2
        self.mock_activity["remain_tickets"] = 0
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[]):
                self.assertTrue(handler.handle())
        self.mock_activity["remain_tickets"] = 5

        self.mock_ticket["status"] = Ticket.STATUS_CANCELLED
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                with patch.object(Ticket, 'save', return_value=1):
                    with patch.object(Activity, 'save', return_value=1):
                        self.assertTrue(handler.handle())
        self.mock_ticket["status"] = 1

        self.mock_ticket["status"] = 4
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                with patch.object(Ticket, 'save', return_value=1):
                    with patch.object(Activity, 'save', return_value=1):
                        self.assertTrue(handler.handle())
        self.mock_ticket["status"] = 1
        handler.flag = 0

#退票
    def test_refund_ticket_handler_check(self):
        handler = RefundTicketHandler(view = CustomWeChatView, msg = {}, user = {})
        handler.input = {
            "MsgType": "text",
            "Content": "退票 key"
        }
        self.assertTrue(handler.check())

    def test_refund_ticket_handler_check(self):
        handler = RefundTicketHandler(view = CustomWeChatView, msg = {}, user = {})
        handler.input = {
            "ToUserName": "?",
            "FromUserName": "?",
            "MsgType": "text",
            "Content": "退票 3"
        }
        handler.user = User(**self.mock_user)
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())

        handler.user.student_id = ""
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())
        handler.user.student_id = "12345"

        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[]):
                self.assertTrue(handler.handle())

        self.mock_ticket["status"] = Ticket.STATUS_CANCELLED
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                        self.assertTrue(handler.handle())
        self.mock_ticket["status"] = 1

        handler.flag = 1
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())

        handler.flag = 2
        self.mock_ticket["status"] = Ticket.STATUS_USED
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                self.assertTrue(handler.handle())
        self.mock_ticket["status"] = 1

        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            with patch.object(Ticket.objects, 'filter', return_value=[Ticket(**self.mock_ticket)]):
                    with patch.object(Activity, 'save', return_value=1):
                        with patch.object(Ticket, 'save', return_value=1):
                            self.assertTrue(handler.handle())
        self.mock_ticket["status"] = 1
        handler.flag = 0





