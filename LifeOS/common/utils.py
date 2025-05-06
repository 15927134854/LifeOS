from django.db import models
from rest_framework_jwt.utils import jwt_decode_handler

class BaseModel(models.Model):
    """为模型类补充字段"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        # 说明是抽象模型类, 用于继承使用，数据库迁移时不会创建BaseModel的表
        abstract = True


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功后返回数据
    """
    return{
        'token': token,
        'user_id': user.id,
        'username': user.username,
        'name': user.name
    }


# 获取用户信息
def GetTokenUser(request):
    try:
        token = request.META.get("HTTP_AUTHORIZATION")
        if not token:
            return
        jwt_token = token.split(" ")[1]
        token_user = jwt_decode_handler(jwt_token)
    except Exception as e:
        return e
    return token_user