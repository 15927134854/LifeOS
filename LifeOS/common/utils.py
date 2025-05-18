from django.db import models


class BaseModel(models.Model):
    """为模型类补充字段"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        # 说明是抽象模型类, 用于继承使用，数据库迁移时不会创建BaseModel的表
        abstract = True


def get_token_user(request):
    # 示例实现逻辑
    token = request.META.get('HTTP_AUTHORIZATION', '').split(' ').pop() if request.META.get('HTTP_AUTHORIZATION', '') else None
    # 此处添加解析 token 并返回用户对象的逻辑
    return None  # 默认返回 None 或者模拟用户
