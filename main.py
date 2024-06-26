#!/usr/bin/python3
import os
import re
import json
import time
import logging
import asyncio
import datetime
import functools
import traceback
import threading

from uuid import uuid4

import mailparser

import tornado.web
import tornado.ioloop

from tornado.web import HTTPError
from tornado.options import define, options

from peewee import *
from playhouse.shortcuts import model_to_dict

import aiosmtpd.smtp
from aiosmtpd.controller import Controller


database = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = database
    def to_dict(self, **kwargs):
        ret = model_to_dict(self, **kwargs)
        return ret


class User(BaseModel):
    def dict(self):
        fmt = "%Y-%m-%d %H:%M:%S"
        item = self.to_dict(exclude=[User.mail, User.create_time])
        return item
    uuid                = CharField(max_length=32, unique=True)
    create_time         = DateTimeField(default=datetime.datetime.now)
    last_active         = BigIntegerField(default=time.time)


class Mail(BaseModel):
    def dict(self, exclude=[]):
        fmt = "%Y-%m-%d %H:%M:%S"
        item = self.to_dict(exclude=[Mail.user, *exclude])
        item["create_time"] = self.create_time.strftime(fmt)
        item["send_time"] = self.send_time.strftime(fmt)
        return item
    user                = ForeignKeyField(User, backref="mail")

    subject             = CharField(max_length=512)
    content             = CharField(max_length=65535)
    html_content        = CharField(max_length=65535)
    sender              = CharField(max_length=256)

    create_time         = DateTimeField(default=datetime.datetime.now)
    send_time           = DateTimeField()


class SmtpdHandler(object):
    domains = []
    async def handle_DATA(self, server, session, envelope):
        mail = mailparser.parse_from_bytes(envelope.content)
        mm = dict(subject=mail.subject)
        mm["content"]      = "".join(mail.text_plain)
        mm["html_content"] = "".join(mail.text_html)
        mm["sender"]    = envelope.mail_from
        mm["send_time"] = mail.date

        Mail.create(**mm, user=envelope.rcpt_tos[0])
        return "250 Message accepted for delivery"

    async def handle_RCPT(self, server, session, envelope,
                          address, rcpt_options):
        addr = re.search("^(?P<uuid>[a-z0-9]{4,12})@(?P<domain>[a-z0-9_\.-]+)$",
                                    address)
        if addr is None:
            return "501 Malformed Address"
        if addr["domain"] not in self.domains:
            return "501 Domain Not Handled"
        user = User.get_or_none(uuid=addr["uuid"])
        if user is None:
            # return "510 Addresss Does Not Exist"
            user, _ = User.get_or_create(uuid=addr["uuid"])
        envelope.rcpt_tos.append(user)
        return "250 OK"


class BaseHTTPService(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def is_valid_uuid(self, uuid):
        # 检查UUID是否在黑名单中
        if uuid.lower() in options.black_list.split(','):
            return False  # 如果UUID在黑名单中，则返回False
        valid = re.search("^([a-z0-9]{4,12})$", uuid)
        return valid is not None

    def write_error(self, *args, **kwargs):
        _, err, _ = kwargs["exc_info"]
        status = getattr(err, "status_code", 500)
        self.set_status(status)
        self.write({"code": status})
        self.finish()


class SmtpMailBoxHandler(BaseHTTPService):
    def delete(self, uuid):
        user = User.get_or_none(uuid=uuid)
        if user is None:
            raise HTTPError(404)
        Mail.delete().where(Mail.user==user).execute()

    def get(self, uuid):
        user = User.get_or_none(uuid=uuid)
        if user is None:
            raise HTTPError(404)
        mail = user.mail.select().order_by(Mail.send_time.desc()
                                ).limit(32)
        ret = [item.dict(exclude=[Mail.content, \
                Mail.html_content]) for item in mail]
        self.finish(json.dumps(ret))


class SmtpMailBoxDetailHandler(BaseHTTPService):
    def get(self, uuid, mail_id):
        user = User.get_or_none(uuid=uuid)
        if user is None:
            raise HTTPError(404)
        mail = Mail.get_or_none(user=user,
                                id=mail_id)
        mail = mail.dict() if mail else {}
        self.finish(mail)


class SmtpMailBoxIframeLoadHandler(BaseHTTPService):
    def set_default_headers(self):
        self.set_header("Content-Type", "text/html; charset=UTF-8")

    def get(self, uuid, mail_id):
        user = User.get_or_none(uuid=uuid)
        if user is None:
            raise HTTPError(404)
        mail = Mail.get_or_none(user=user,
                                id=mail_id)
        mail = mail.dict() if mail else {}
        html = mail.get("html_content", "") \
                            or mail.get("content")
        html = html.strip()
        self.write('<base target="_blank">')
        self.write('<meta name="referrer" content="none">')
        if not html.startswith("<"):
            html = '<pre>%s</pre>' % html
        self.finish(html)


class SmtpMailBoxIframeNewtabHandler(BaseHTTPService):
    def set_default_headers(self):
        self.set_header("Content-Type", "text/html; charset=UTF-8")

    def get(self, uuid, mail_id):
        src = "/mail/{}/{}/iframe".format(uuid, mail_id)
        self.render("iframe.html", src=src)


class SmtpMailBoxRssHandler(BaseHTTPService):
    def set_default_headers(self):
        self.set_header("Content-Type", "text/xml; charset=UTF-8")

    def initialize(self, domain):
        self.domain = domain

    def get(self, uuid):
        if uuid == 'dbdbdbdb': # 当uuid是该值，展示所有用户和对应的邮件
            user_all = User.select().limit(1000)
            tz = time.strftime("%z")
            self.render("rss_all.xml", tz=tz, domain=self.domain,
                        user_all=user_all, server=self.request.headers["Host"])
            return

        user = User.get_or_none(uuid=uuid)
        if user is None:
            raise HTTPError(404)
        user.last_active = time.time()
        user.save() # prevent schd auto remove
        tz = time.strftime("%z")
        self.render("rss.xml", tz=tz, domain=self.domain,
                user=user, server=self.request.headers["Host"])


class SmtpUserHandler(BaseHTTPService):
    def delete(self, uuid):
        user = User.get_or_none(uuid=uuid)
        if user is None:
            raise HTTPError(404)
        user.delete_instance(True)
        self.clear_cookie("uuid")

    def post(self, uuid):
        uuid = uuid or self.get_cookie("uuid", "")
        user = {"uuid": uuid or uuid4().hex[::4]}
        if not self.is_valid_uuid(user["uuid"]):
            # raise HTTPError(400)
            user["uuid"] = uuid4().hex[::4]  # 如果传过来的是不符合规则的uuid，重新生成一个
        user, _ = User.get_or_create(uuid=user["uuid"],
                                     defaults=user)
        user.last_active = time.time()
        user.save()
        self.set_cookie("uuid", user.uuid,
                            expires_days=2**16)
        self.finish(user.dict())


class SmtpIndexHandler(BaseHTTPService):
    def set_default_headers(self):
        self.set_header("Content-Type", "text/html")

    def initialize(self, domain):
        self.domain = domain

    def get(self):
        self.render("index.html",
                    domain=self.domain)


class SmtpIntroHandler(BaseHTTPService):
    def set_default_headers(self):
        self.set_header("Content-Type", "text/html")

    def get(self):
        self.render("intro.html")


def schd_cleaner(seconds, interval):
    logger = logging.getLogger("cleaner")
    while True:
        time.sleep(interval)
        logger.info("user clean task is running")
        for user in User.select().where(User.last_active < (time.time() - seconds)):
            logger.warning("clean user data: %s" % user.uuid)
            user.delete_instance(True)


if __name__ == "__main__":
    define("domain", multiple=True, type=str)
    define("database", type=str, default="mail.db")
    define("listen", type=str, default="0.0.0.0")
    define("port", type=int, default=8888)
    define("clean_seconds", type=int, default=7*86400)
    define("black_list", type=str, default="admin,postmaster,system,webmaster,administrator,hostmaster,service,server,root") # 黑名单，用于过滤发件人，逗号分隔

    options.parse_command_line()

    tornado.ioloop.IOLoop.configure("tornado.platform.asyncio.AsyncIOLoop")
    database.init(options.database, pragmas={"locking_mode": "NORMAL",
                                             "journal_mod": "wal",
                                             "synchronous": "OFF"})
    templates = os.path.join(os.path.dirname(__file__), "templates")
    statics = os.path.join(os.path.dirname(__file__), "static")
    server = tornado.web.Application(
    [
        ("/intro", SmtpIntroHandler),
        ("/favicon.ico", tornado.web.StaticFileHandler, dict(url="/static/favicon.ico",
                                            permanent=False)),
        ("/", SmtpIndexHandler, dict(domain=options.domain[0])),
        ("/mail/([a-z0-9]{4,12})/(\d+)/iframe", SmtpMailBoxIframeLoadHandler),
        ("/mail/([a-z0-9]{4,12})/(\d+)/show", SmtpMailBoxIframeNewtabHandler),
        ("/mail/([a-z0-9]{4,12})/(\d+)", SmtpMailBoxDetailHandler),
        ("/mail/([a-z0-9]{4,12})/rss", SmtpMailBoxRssHandler,
                            dict(domain=options.domain[0])),
        ("/mail/([a-z0-9]{4,12})", SmtpMailBoxHandler),
        ("/user/([a-z0-9]{4,12})?", SmtpUserHandler),
    ],
    template_path=templates,
    static_path=statics)

    server.listen(options.port, address=options.listen, xheaders=True)

    #SmtpdHandler.domains.append(options.domain)
    SmtpdHandler.domains.extend(options.domain)
    if '\\' in os.environ.get('PATH'):
        # 在 Windows 操作系统上，使用 Controller 和 SmtpdHandler 并指定 hostname="0.0.0.0" 和 port=25 会导致错误。
        # 这是因为在 Windows 上，非特权用户（非管理员）通常无法绑定到低于 1024 的端口（例如端口 25）。
        smtp = Controller(SmtpdHandler(), hostname="127.0.0.1", port=25)
    else:
        smtp = Controller(SmtpdHandler(), hostname="0.0.0.0",port=25)
    smtp.start()

    User.create_table()
    Mail.create_table()

    # cleaner = threading.Thread(target=schd_cleaner, args=(7*86400, 600))
    cleaner = threading.Thread(target=schd_cleaner, args=(options.clean_seconds, 60))
    cleaner.start()

    loop = asyncio.get_event_loop()
    loop.run_forever()
