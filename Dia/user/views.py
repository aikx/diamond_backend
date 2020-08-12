import json
import os
import random
import string
import smtplib

from email.mime.text import MIMEText
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from easydict import EasyDict
from django.views import View
from django.db.utils import IntegrityError, DataError
from django.db.models import Q
from email.header import Header
from user.models import User, EmailRecord, Message, Collection
from user.hypers import *
from utils.cast import encode, decode, get_time
from utils.response import JSR


def send_code(email, email_type):
    # 发信方的信息：发信邮箱，QQ 邮箱授权码
    from_addr = 'diadoc@163.com'
    password = 'UTXGEJFQTCJNDAHQ'

    # 收信方邮箱
    to_addr = email

    # 发信服务器
    smtp_server = 'smtp.163.com'

    # 生成随机验证码
    code_list = []
    for i in range(10):  # 0~9
        code_list.append(str(i))
    key_list = []
    for i in range(65, 91):  # A-Z
        key_list.append(chr(i))
    for i in range(97, 123):  # a-z
        key_list.append(chr(i))
    if email_type == 'register':
        code = random.sample(code_list, 6)  # 随机取6位数
        code_num = ''.join(code)
        # 数据库保存验证码！！！！！！！！！！！
        ver_code = EmailRecord()
        ver_code.code = code_num
        ver_code.email = email
        ver_code.send_time = datetime.now()
        ver_code.expire_time = datetime.now()+timedelta(minutes=5)
        ver_code.email_type = email_type

        # 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
        msg = MIMEText('验证码为' + code_num, 'plain', 'utf-8')
        msg['Subject'] = Header('金刚石文档注册验证码')
    else:
        code = random.sample(key_list, 10)
        code_num = ''.join(code)

        ver_code = EmailRecord()
        ver_code.code = '/forget/set?acc='+acc+'&key='+code_num
        ver_code.email = email
        ver_code.send_time = datetime.now()
        ver_code.expire_time = datetime.now() + timedelta(minutes=60)
        ver_code.email_type = email_type
        msg = MIMEText('找回密码的链接为:/forget/set?acc='+acc+'&key='+code_num + code_num, 'plain', 'utf-8')
        msg['Subject'] = Header('金刚石文档找回密码')

    # 邮件头信息
    msg['From'] = Header(from_addr)
    msg['To'] = Header(to_addr)

    # 开启发信服务，这里使用的是加密传输
    server = smtplib.SMTP_SSL(host='smtp.163.com')
    server.connect(smtp_server, 465)
    # 登录发信邮箱
    server.login(from_addr, password)
    # 发送邮件
    server.sendmail(from_addr, to_addr, msg.as_string())
    # 关闭服务器
    server.quit()


class SearchUser(View):
    @JSR('list', 'status')
    def post(self, request):
        if not request.session['is_login']:
            return [], 2
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'key'}:
            return [], 1
        us = User.objects.filter(name__icontains=kwargs['key'])
        ulist = []
        for u in us:
            ulist.append({
                'name': u.name,
                'portrait': u.profile_photo,
                'acc': u.email,
                'uid': encode(u.id)
            })
        return ulist, 0


class Register(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.acc, E.pwd, E.code, E.name, E.uni = 1, 2, 3, 4, 5, 6

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'acc', 'ver_code', 'pwd', 'name'}:
            return E.key,
        if not CHECK_ACC(kwargs['acc']):
            return E.acc,
        if not CHECK_PWD(kwargs['pwd']):
            return E.pwd,
        if not CHECK_NAME(kwargs['name']):
            return E.name,
        kwargs.update({'email': kwargs['acc']})
        kwargs.pop('acc')
        kwargs.update({'profile_photo': DEFAULT_PROFILE_ROOT + '\handsome.jpg'})
        kwargs.update({'point': 5})

        er = EmailRecord.objects.filter(code=kwargs['ver_code'], email=kwargs['acc']).exists()
        if not er:
            return E.code
        er = EmailRecord.objects.filter(code=kwargs['ver_code'], email=kwargs['acc']).get()
        if datetime.now() - er.expire_time > 0:
            try:
                u = User.objects.create(**kwargs)
            except IntegrityError:
                return E.uni,  # 字段unique未满足
            except DataError:
                return E.uk,  # 诸如某个CharField超过了max_len的错误
            except:
                return E.uk,
            request.session['is_login'] = True
            request.session['uid'] = encode(u.id)
            print(u.profile_photo.path)
            return 0

        return E.code


class Login(View):
    @JSR('count', 'status')
    def post(self, request):
        if request.session.get('is_login', None):
            u = User.objects.get(int(decode(request.session['uid'])))
            if u.login_date != date.today():
                u.login_date = date.today()
                u.wrong_count = 0
                try:
                    u.save()
                except:
                    return 0, -1
            return 0, 0

        E = EasyDict()
        E.uk = -1
        E.key, E.exist, E.pwd, E.many = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'acc', 'pwd'}:
            return 0, E.key

        u = User.objects.filter(email=kwargs['acc'])
        if not u.exists():
            return 0, E.exist
        u = u.get()

        if u.login_date != date.today():
            u.login_date = date.today()
            u.wrong_count = 0
            try:
                u.save()
            except:
                return u.wrong_count, E.uk

        if u.wrong_count == MAX_WRONG_PWD:
            return u.wrong_count, E.many

        if u.password != kwargs['pwd']:
            u.wrong_count += 1
            try:
                u.save()
            except:
                return 0, -1
            return u.wrong_count, E.pwd

        u.verify_vip()
        request.session['is_login'] = True
        request.session['uid'] = encode(u.id)
        request.session['name'] = u.name
        request.session['identity'] = u.identity
        request.session.save()
        u.session_key = request.session.session_key
        try:
            u.save()
        except:
            return u.wrong_count, E.uk
        return u.wrong_count, 0

    @JSR('status')
    def get(self, request):
        if request.session.get('is_login', None):
            request.session.flush()
            return 0
        else:
            return -1


class RegisterCode(View):
    @JSR('status')
    def get(self, request):
        if dict(request.GET).keys() != {'acc'}:
            return 1
        try:
            acc = str(request.GET.get('acc'))
        except:
            return -1

        send_code(acc, 'register')
        return 0


class FindPwd(View):
    @JSR('status')
    def get(self, request):
        if dict(request.GET).keys() != {'acc'}:
            return 1
        try:
            acc = str(request.GET.get('acc'))
        except:
            return -1
        send_code(acc, 'forget')
        return 0


class SetPwd(View):
    @JSR('status')
    def post(self,  request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'acc', 'pwd', 'key'}:
            return 1,
        u = User.objects.filter(email=kwargs['acc'])
        if not u.exists():
            return 2,
        u = u.get()
        if not CHECK_PWD(kwargs['pwd']):
            return 3,
        if not EmailRecord.objects.filter(code=kwargs['key']).exists():
            return 4,
        er = EmailRecord.objects.filter(Q(acc=kwargs['acc']) | Q(code=kwargs['key'])).get()
        u.password = kwargs['pwd']
        u.save()
        return 0,


class UnreadCount(View):
    @JSR('count', 'status')
    def get(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return 0, -1
        u = u.get()
        count = Message.objects.filter(Q(user_id=u.id) | Q(is_read=False)).count()
        return count, 0


class AskMessageList(View):
    @JSR('status', 'cur_dtdt', 'amount', 'list')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return 1, [], 0, ''
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return -1, [], 0, ''

        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1, [], 0, ''
        u = u.get()
        messages = Message.objects.filter(user_id=u.id).order_by('id')[(page - 1) * each: page * each]
        msg = []
        for message in messages:
            msg.append({
                'mid': encode(message.id),
                'dtdt': datetime.strptime(str(message.dt), "%Y-%m-%d %H:%M:%S"),
            })
        return 0, datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S"), len(msg), msg


class AskMessageInfo(View):
    @JSR('status', 'is_read', 'is_dnd', 'name', 'po', 'content', 'cur_dtdt', 'dt')
    def get(self, request):
        if dict(request.GET).keys() != {'mid'}:
            return 1, []*7
        try:
            mid = int(decode(request.GET.get('mid')))
        except ValueError:
            return -1, []*7

        u = User.objects.filter(id=int(decode(request.session['uid'])))

        if not u.exists():
            return -1, []*7
        u = u.get()
        msg = Message.objects.filter(id=mid)
        if not msg.exists():
            return -1, [] * 7
        msg = msg.get()
        return 0, msg.is_read, u.is_dnd, msg.title, msg.portrait_url, msg.content, get_time(), msg.dt


class SetMsgRead(View):
    @JSR('status')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'mid'}:
            return 1,
        msg = Message.objects.filter(id=int(decode(kwargs['mid'])))
        if not msg.exists():
            return -1,
        msg = msg.get()
        msg.is_read = True
        msg.save()
        return 0,


class SetAllMsgRead(View):
    @JSR('status')
    def post(self, request):
        msg = Message.objects.all()
        for m in msg:
            m.is_read = True
            m.save()
        return 0,


class SetDnd(View):
    @JSR('status')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'is_dnd'}:
            return 1,
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1,
        u = u.get()
        u.is_dnd = kwargs['is_dnd']
        u.save()
        return 0,


class AskDnd(View):
    @JSR('status', 'is_dnd')
    def post(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1, False
        u = u.get()
        return 0, u.is_dnd


class StarCondition(View):
    @JSR('is_starred', 'status')
    def get(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return False, -1
        u = u.get()
        if dict(request.GET).keys() != {'id', 'type'}:
            return False, 1
        try:
            did = int(decode(request.GET.get('id')))
        except:
            return False, -1
        is_starred = False
        if not Collection.objects.filter(Q(user_id=u.id) | Q(ent_id=did)).exists():
            is_starred = True
        return is_starred, 0


class Star(View):
    @JSR('status')
    def post(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1
        u = u.get()
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type', 'is_starred'}:
            return 1,
        if kwargs['is_starred']:
            try:
                Collection().objects.filter(id=int(decode(request.session['uid']))).delete()
            except:
                return -1,
        star = Collection()
        star.user = u
        star.ent = int(decode(kwargs['id']))
        star.type = kwargs['type']
        star.dt = get_time()
        star.save()
        return 0


class Member(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.exist = 1

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'time'}:
            return E.uk

        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return E.exist
        u = u.get()

        if u.vip_time < date.today():
            u.vip_time = date.today()
        u.vip_time = u.vip_time + relativedelta(months=int(kwargs['time']))
        u.identity = 'vip'
        try:
            u.save()
        except:
            return E.uk
        request.session['identity'] = 'vip'
        request.save()
        return 0

    @JSR('date', 'is_member')
    def get(self, request):
        if dict(request.GET).keys() != {'uid'}:
            return '', False
        try:
            uid = int(request.GET.get('uid'))
        except:
            return '', False
        u = User.objects.filter(id=int(decode(uid)))
        if not u.exists():
            return '', False
        u = u.get()
        is_vip = u.verify_vip()
        try:
            u.save()
        except:
            return '', False
        return u.vip_date.strftime("%Y-%m-%d") if is_vip else '', is_vip


class SimpleUserInfo(View):
    @JSR('name', 'portrait', 'acc', 'uid', 'status')
    def get(self, request):
        if not request.session['is_login']:
            return '', '', '', '', 2
        try:
            uid = int(decode(request.session.get('uid', None)))
        except:
            return '', '', '', '', -1
        u = User.objects.filter(id=uid)
        if not u.exists():
            return '', '', '', '', -1
        u = u.get()
        return u.name, u.profile_photo.path, u.email, encode(u.id), 0


class ChangePwd(View):
    @JSR('status')
    def post(self, request):
        if not request.session['is_login']:
            return 2
        E = EasyDict()
        E.uk = -1
        E.key, E.wr_pwd, E.ill_pwd = 1, 2, 3
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'old_pwd', 'new_pwd'}:
            return E.key

        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return E.uk
        u = u.get()

        if kwargs['old_pwd'] != u.password:
            return E.wr_pwd
        if not CHECK_PWD(kwargs['new_pwd']):
            return E.ill_pwd

        u.password = kwargs['new_pwd']
        try:
            u.save()
        except:
            return E.uk
        return 0


class UserInfo(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.name, E.school, E.company, E.job, E.intro = 1, 2, 3, 4, 5

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'name', 'sex', 'birthday', 'school', 'company', 'job', 'introduction', 'src'}:
            return E.uk,
        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return E.uk,
        u = u.get()

        if not CHECK_NAME(kwargs['name']):
            return E.name,
        if str(kwargs['sex']) not in GENDER_DICT.keys():
            return E.uk,
        if not CHECK_DESCS(kwargs['school']):
            return E.school,
        if not CHECK_DESCS(kwargs['company']):
            return E.company,
        if not CHECK_DESCS(kwargs['job']):
            return E.job,
        if not CHECK_DESCS(kwargs['introduction']):
            return E.intro,
        u.name = kwargs['name']
        u.gender = kwargs['sex']

        bir = kwargs['birthday']
        for ch in (_ for _ in bir if not _.isdigit() and _ != '-'):
            bir = bir.split(ch)[0]
        u.birthday = datetime.strptime(bir, '%Y-%m-%d').date()
        u.school = kwargs['school']
        u.company = kwargs['company']
        u.job = kwargs['job']
        u.intro = kwargs['introduction']

        try:
            u.save()
        except:
            return E.uk,
        return 0,

    @JSR('uid', 'name', 'sex', 'birthday', 'school', 'company', 'job', 'introduction')
    def get(self, request):
        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return '', '', 2, '', '', '', '', ''
        u = u.get()
        return u.id, u.name, int(u.gender), u.birthday.strftime('%Y-%m-%d'), u.school, u.company, u.job, u.intro


class StatisticsCard(View):
    @JSR('views', 'points', 'stars', 'likes')
    def get(self, request):
        uid = request.session.get('uid', None)
        if uid:
            u = User.objects.filter(id=uid).get()
            if u.login_date != date.today():
                u.get_data_day()
                u.get_data_count()
            return u.view_day, u.point, u.star_count, u.like_count
        else:
            return 0, 0, 0, 0


class ChangeProfile(View):
    @JSR('src', 'status', 'wrong_msg')
    def post(self, request):
        errc = EasyDict()
        errc.unknown = -1
        errc.toobig = 1

        file = request.FILES.get("profile", None)
        if not file:
            return '', errc.unknown, '获取图片失败'
        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return '', errc.unknown, '获取用户失败'
        u = u.get()

        if u.file_size + file.size > MAX_UPLOADED_FSIZE:
            return '', errc.toobig, '上传头像的大小超过了限制(1MB)'

        file_name = ''.join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)]) + '.' + \
                    str(file.name).split(".")[-1]
        file_path = os.path.join(DEFAULT_PROFILE_ROOT, file_name)
        with open(file_path, 'wb') as dest:
            [dest.write(chunk) for chunk in file.chunks()]
        u.profile_photo = file_path
        try:
            u.save()
        except:
            return '', errc.unknown, '头像保存失败'
        return file_path, 0, ''

# class GetMessage(View):
#     @JSR('amount', 'message', 'dict')
#     def get(self, request):
#         if dict(request.GET).keys() != {'page', 'each'}:
#             return 0, [], []
#         try:
#             uid = int(request.session['uid'])
#             page = int(request.GET.get('page'))
#             each = int(request.GET.get('each'))
#         except:
#             return 0, [], []
#         mes = Message.objects.filter(owner_id=uid).order_by('-time')
#         amount = mes.count()
#         mes = mes[(page - 1) * each: page * each]
#         a = []
#         li = []
#         for i in mes:
#             if i.article_comment:
#                 b = i.article_comment
#                 if b.fa_comment and b.fa_comment.author.id != uid:
#                     content = b.author.name + " 回复了您的评论 " + b.fa_comment.content + " ：" + b.content
#                 else:
#                     content = b.author.name + " 评论了您的文章 " + b.fa_article.title + " ：" + b.content
#                 a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'aid': b.id})
#                 li.append({'aid': b.fa_article_id})
#             elif i.resource_comment:
#                 b = i.resource_comment
#                 if b.fa_comment and b.fa_comment.author.id != uid:
#                     content = b.author.name + " 回复了您的评论 " + b.fa_comment.content + " ：" + b.content
#                 else:
#                     content = b.author.name + " 评论了您的资源 " + b.fa_resource.title + " ：" + b.content
#                 a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'rid': b.id})
#                 li.append({'rid': b.fa_resource_id})
#             else:
#                 b = i.complain
#                 content = "您的举报已被处理：" + b.content + " 处理结果：" + "通过" if b.result else "不通过"
#                 a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'mid': b.id})
#
#         return amount, a, li


# class GetComplainInfo(View):
#     @JSR('time', 'condition', 'id')
#     def get(self, request):
#
#
#
# class GetNews(View):
#     @JSR('amount', 'list')
#     def get(self, request):
#         if dict(request.GET).keys() != {'page', 'each'}:
#             return 0, []
#         try:
#             page = int(request.GET.get('page'))
#             each = int(request.GET.get('each'))
#         except:
#             return 0, []
#         u = Follow.objects.filter(follower_id=request.session['uid'])
#         a = []
#         for i in u:
#             e = i.followed
#             a = a + [q for q in e.article_author.filter(recycled=False, blocked=False)]
#             a = a + [q for q in e.resource_author.filter(recycled=False, blocked=False)]
#         a = sorted(a, key=lambda e: e.create_time, reverse=False)
#         b = [{'aid' if isinstance(q, Article) else 'rid': q.id} for q in a]
#         amount = len(b)
#         b = b[(page - 1) * each: page * each]
#         return amount, b
#
