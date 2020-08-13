from django.urls import path, re_path
from django.views.generic import TemplateView

from user.views import *
from entity.views import *
from record.views import *
from fusion.views import *
from misc.views import *
from teamwork.views import *

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html"), name='index'),

    # 用户通用
    path('user_info', UserInfo.as_view(), name='user_info'),  # 用户信息
    path('search_user', SearchUser.as_view(), name='search_user'),  # 关键词搜索用户
    path('user/edit_info', EditInfo.as_view(), name='edit_info'),  # 修改个人信息

    # 用户登录注册找回密码
    path('user/login/submit', Login.as_view(), name='login_submit'),  # 登录
    path('user/register/submit', Register.as_view(), name='register_submit'),  # 注册和请求注册验证码
    path('user/logout/submit', Login.as_view(), name='logout_submit'),  # 注销登录
    path('user/forget/send_email', FindPwd.as_view(), name='forget_send_email'),  # 找回密码
    path('user/forget/set_pwd', SetPwd.as_view(), name='forget_set_pwd'),  # 找回密码设置新密码
    path('user/change_password', ChangePwd.as_view(), name='user_change_password'),  # 修改密码
    path('user/change_profile', ChangeProfile.as_view(), name='user_change_profile'),

    # 消息
    path('msg/unread_count', UnreadCount.as_view(), name='msg_unread_count'),
    path('msg/list/', AskMessageList.as_view(), name='msg_list'),
    path('msg/info/', AskMessageInfo.as_view(), name='msg_info'),
    path('msg/ar', SetMsgRead.as_view(), name='msg_ar'),
    path('msg/ar_all', SetAllMsgRead.as_view(), name='msg_ar_all'),
    path('msg/dnd', SetDnd.as_view(), name='msg_dnd'),  # 设置及查询消息免打扰

    # 文件系统
    # path('fs/new', FSNew.as_view(), name='fs_new'), # 请求新建文件or夹
    # path('fs/fold/elem', .as_view(), name='fs_fold_elem'), # 请求文件夹下的所有条目
    # path('fs/recycle/elem', .as_view(), name='fs_recycle_elem'), # 请求回收站下的所有条目
    # path('fs/father', .as_view(), name='fs_father'), # 请求文件or夹的上级文件夹
    # path('fs/doc/info', .as_view(), name='fs_doc_info'), # 请求文档预览信息（弹窗）
    # path('fs/fold/info', .as_view(), name='fs_fold_info'), # 请求文件夹预览信息（弹窗）
    # path('fs/rename', .as_view(), name='fs_rename') # 修改文件, / 文件夹名称（重命名）
    # path('fs/link/new', .as_view(), name='fs_link_new'), # 请求新建快捷方式到桌面
    # path('fs/move', .as_view(), name='fs_move'), # 移动文档或文件夹
    # path('fs/copy', .as_view(), name='fs_copy'), # 复制文档
    # path('fs/delete', .as_view(), name='fs_delete'), # 删除文档or文件夹
    # path('fs/delete_link', .as_view(), name='fs_delete_link'), # 从桌面移除快捷方式
    # path('fs/star', .as_view(), name='fs_star'), # 收藏文件or夹
    # path('fs/user/root', .as_view(), name='fs_user_root'), # 请求个人根文件夹fid
    # path('fs/team/root', .as_view(), name='fs_team_root'), # 请求团队根文件夹fid
    # path('fs/recycle/recover', .as_view(), name='fs_recycle_recover'), # 恢复回收站的内容
    # path('fs/recycle/delete', .as_view(), name='fs_recycle_delete'), # 彻底删除回收站的内容
    # path('fs/recycle/clear', .as_view(), name='fs_recycle_clear'), # 彻底删回收站库

    # 团队相关
    path('team/new_from_fold', NewFromFold.as_view(), name='team_new_from_fold'),
    path('team/invitation', Invitation.as_view(), name='team_invitation'),
    path('team/auth', Auth.as_view(), name='team_auth'),
    path('team/remove', Remove.as_view(), name='team_remove'),
    path('team/info', Info.as_view(), name='team_info'),
    path('team/delete', Delete.as_view(), name='team_delete'),
    path('team/new', New.as_view(), name='team_new'),
    path('team/edit_info', EditInfo.as_view(), name='team_edit_info'),
    path('team/all', All.as_view(), name='team_all'),
    path('team/identity', Identity.as_view(), name='team_identity'),
    path('team/quit', Quit.as_view(), name='team_quit'),

    re_path(r'.*', TemplateView.as_view(template_name='index.html')),
]

