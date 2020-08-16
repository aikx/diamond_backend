import json
import time

from django.db.models import Q
from django.views import View
from easydict import EasyDict as ED

from entity.models import Entity
from fusion.models import Collection, Comment
from meta_config import HOST_IP
from user.models import User
from utils.cast import decode
from utils.meta_wrapper import JSR


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


class FSStar(View):
    @JSR('status')
    def post(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1
        u = u.get()
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type', 'is_starred'}:
            return 1,
        
        ent = Entity.get_via_encoded_id(kwargs['id'])
        if ent is None:
            return 3
        
        if kwargs['is_starred']:
            Collection.objects.get_or_create(user=u, ent=ent)
        else:
            Collection.objects.filter(ent=ent, user_id=int(decode(request.session['uid']))).delete()
        return 0


class TempAll(View):
    @JSR('status', 'my_list', 'official_list')
    def get(self, request):
        pass


class CommentAdd(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = json.loads(request.body)
        if kwargs.keys() != {'did', 'uid', 'threadId', 'commentId', 'content'}:
            return E.k
        
        did = kwargs.get('did')
        
        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent
        try:
            new_comment = Comment(did=Entity.objects.get(id=did),
                                  uid=User.objects.get(id=kwargs.get('uid')),
                                  threadId=kwargs.get('threadId'),
                                  commentId=kwargs.get('commentId'),
                                  content=kwargs.get('content'),
                                  createdAt=int(time.time() * 1000))
            new_comment.save()
        except:
            return E.u
        return 0


class CommentGet(View):
    @JSR('status', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au, None
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au, None
        kwargs = eval(list(request.GET.keys())[0])
        if kwargs.keys() != {'did', 'threadId'}:
            return E.k, None
        
        try:
            items = list(Comment.objects.filter(did=Entity.objects.get(id=kwargs.get('did')),
                                                threadId=kwargs.get('threadId')).values())
        except:
            return E.u, None
        if items is None:
            return E.no_ent, None
        res = []
        for it in items:
            dic = {'commentId': it.get('commentId'),
                   'authorId': str(it.get('uid_id')),
                   'content': it.get('content'),
                   'createdAt': it.get('createdAt')}
            res.append(dic)
        return 0, res


class CommentUpdate(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = json.loads(request.body)
        if kwargs.keys() != {'did', 'uid', 'threadId', 'commentId', 'content'}:
            return E.k
        
        try:
            upd_comment = Comment.objects.get(did=Entity.objects.get(id=kwargs.get('did')),
                                              uid=User.objects.get(id=kwargs.get('uid')),
                                              threadId=kwargs.get('threadId'),
                                              commentId=kwargs.get('commentId'))
            if upd_comment is None:
                return E.no_ent
            upd_comment.content = kwargs.get('content')
            upd_comment.save()
        except:
            return E.u
        return 0


class CommentRemove(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = json.loads(request.body)
        if kwargs.keys() != {'did', 'uid', 'threadId', 'commentId'}:
            return E.k
        try:
            rmv_comment = Comment.objects.get(did=Entity.objects.get(id=kwargs.get('did')),
                                              uid=User.objects.get(id=kwargs.get('uid')),
                                              threadId=kwargs.get('threadId'),
                                              commentId=kwargs.get('commentId'))
            if rmv_comment is None:
                return E.no_ent
            rmv_comment.delete()
        except:
            return E.u
        return 0


class CommentUsers(View):
    @JSR('status', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au, None
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au, None
        kwargs = eval(list(request.GET.keys())[0])
        if kwargs.keys() != {'did'}:
            return E.k, None
        
        did = kwargs.get('did')
        
        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent, None
        try:
            comments = Comment.objects.filter(did=did)
            users = []
            user = User.get_via_encoded_id(request.session['uid'])
            dic = {'id': str(user.id),
                   'name': user.name,
                   'avatar': f'http://{HOST_IP}:8000/' + user.portrait}
            users.append(dic)
            for comment in comments:
                user = User.get_via_encoded_id(comment.uid.id)
                dic = {'id': str(user.id),
                       'name': user.name,
                       'avatar': f'http://{HOST_IP}:8000/' + user.portrait}
                if dic not in users:
                    users.append(dic)
        except:
            
            return E.u, None
        return 0, users
