from django.test import TestCase, LiveServerTestCase
from django.core.urlresolvers import resolve
from unittest.mock import Mock, patch, MagicMock
from django.http import HttpRequest
from selenium import webdriver
from codex.baseerror import *
from wechat.models import *
from unittest.mock import *
from userpage.views import *
import userpage.urls
import datetime
import time
import json


class URLTest(TestCase):

    def test_u_bind(self):
        response = self.client.get('/u/bind/')
        self.assertContains(response, 'inputUsername')

class UserBindTest(TestCase):

#测试validate_user
    def test_validate_user_raise_error_without_input(self):
        user_bind_view = UserBind()
        with self.assertRaises(ValidateError):
            user_bind_view.validate_user()

    def test_validate_user_error_with_empty_input(self):
        user_bind_view = UserBind()
        user_bind_view.input = {'student_id': '', 'password': ''}
        with self.assertRaises(ValidateError):
            user_bind_view.validate_user()

    @patch('userpage.views.request.urlopen')
    def test_validate_user_with_wrong_username_password(self, mock_open: MagicMock):
        user_bind_view = UserBind()
        user_bind_view.input = {'student_id': 1, 'password': 'x'}
        mock_response = MagicMock()
        mock_response.read = MagicMock(return_value=b'{"ticket":"ticket"}')
        mock_open.return_value = MagicMock()
        mock_open.return_value._enter_ = MagicMock(return_value=mock_response)
        with self.assertRaises(ValidateError):
            user_bind_view.validate_user()

#测试get
    def test_get_without_openid(self):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    def test_get_with_openid(self):
        found = resolve('/user/bind/',urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid":"1"}')
        with patch.object(User,'get_by_openid',return_value=Mock(student_id=1)) as MockUser:
            response = json.loads(found.func(request).content.decode())
            self.assertEqual(response['code'],0)

#测试post
    def test_post_with_openid_username_password(self):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid": "1","student_id":"1","password":"x"}')
        with patch.object(User, 'get_by_openid', return_value=Mock(student_id=1)):
            with patch.object(UserBind, 'validate_user', return_value=0):
                response = json.loads(found.func(request).content.decode())
                self.assertEqual(response['code'], 0)

    def test_post_without_openid_username_password(self):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertNotEqual(response['code'], 0)

    def test_post_without_openid(self):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"student_id":"1","password":"x"}')
        response = json.loads(found.func(request).content.decode())
        self.assertNotEqual(response['code'], 0)

    def test_post_without_student_id(self):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid": "1","password":"x"}')
        response = json.loads(found.func(request).content.decode())
        self.assertNotEqual(response['code'], 0)

    def test_post_without_password(self):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid": "1","student_id":"1"}')
        response = json.loads(found.func(request).content.decode())
        self.assertNotEqual(response['code'], 0)

class ActivityDetailTest(TestCase):

    mock_time = datetime.datetime.now()

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

    def test_get_without_id(self):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    def test_get_with_wrong_id(self):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id": "33"}')
        response = json.loads(found.func(request).content.decode())
        self.assertNotEqual(response['code'], 0)

    def test_get_with_wrong_status(self):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id":"1"}')
        self.mock_activity['status'] = 0
        activity = Activity(**self.mock_activity)
        with patch.object(Activity.objects, 'get', return_value=activity):
            response = json.loads(found.func(request).content.decode())
            self.assertNotEqual(response['code'], 0)
        self.mock_activity['status'] = 1

    def test_get_with_correct_value(self):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id":"1"}')
        with patch.object(Activity.objects, 'get', return_value=Activity(**self.mock_activity)):
            response = json.loads(found.func(request).content.decode())
            self.assertEqual(response['code'], 0)

class TicketDetailTest(TestCase):

    mock_user = {
        "open_id": "12",
        "student_id": "12345",
    }

    mock_ticket = {
        "student_id": "12345",
        "unique_id": "wobuzhidaoanicai",
        "activity": Activity(**ActivityDetailTest.mock_activity),
        "status": 0,
    }

    def test_get_without_openid_ticket(self):
        found = resolve('/ticket/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertNotEqual(response['code'], 0)

    def test_get_without_ticket(self):
        found = resolve('/ticket/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid":"12"}')
        response = json.loads(found.func(request).content.decode())
        self.assertNotEqual(response['code'], 0)

    def test_get_without_openid(self):
        found = resolve('/ticket/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"ticket":"wobuzhidaoanicai"}')
        response = json.loads(found.func(request).content.decode())
        self.assertNotEqual(response['code'], 0)

    def test_get_with_openid_ticket(self):
        found = resolve('/ticket/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid":"12","ticket":"wobuzhidaoanicai"}')
        with  patch.object(User.objects, 'get', return_value=User(**self.mock_user)):
            with patch.object(Ticket.objects, 'get', return_value=Ticket(**self.mock_ticket)):
                response = json.loads(found.func(request).content.decode())
                self.assertEqual(response['code'], 0)
