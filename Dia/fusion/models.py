from ckeditor.fields import RichTextField
from django.db import models

from entity.hypers import BASIC_DATA_MAX_LEN, COMMENT_MAX_LEN
from meta_config import TIME_FMT, KB


class Collection(models.Model):
    user = models.ForeignKey('user.User', related_name='related_collection', on_delete=models.CASCADE)
    ent = models.ForeignKey('entity.Entity', related_name='ent', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True, verbose_name='文件收藏时间')

    class Meta:
        ordering = ["-dt"]

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class Links(models.Model):
    user = models.ForeignKey(null=False, to='user.User', related_name='links', on_delete=models.CASCADE)
    ent = models.ForeignKey(null=False, to='entity.Entity', related_name='links', on_delete=models.CASCADE)


class Template(models.Model):
    creator = models.ForeignKey(to='user.User', null=True, on_delete=models.SET_NULL)
    name = models.CharField(unique=False, default='未命名', max_length=65)
    content = RichTextField(default='', max_length=32 * KB)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)
    only_vip = models.BooleanField(default=False)

    class Meta:
        ordering = ['-create_dt']


class Comment(models.Model):

    did = models.ForeignKey('entity.Entity', on_delete=models.CASCADE)
    uid = models.ForeignKey('user.User', on_delete=models.CASCADE)
    threadId = models.CharField(unique=False, max_length=BASIC_DATA_MAX_LEN)
    commentId = models.CharField(unique=False, max_length=BASIC_DATA_MAX_LEN)
    content = models.CharField(unique=False, max_length=COMMENT_MAX_LEN)
    createdAt = models.BigIntegerField(default=0)
