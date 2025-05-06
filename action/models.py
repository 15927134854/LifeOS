from django.db import models

from LifeOS.common.utils import BaseModel


# Create your models here.

class ActionTemplate(BaseModel):
    """目标表"""
    name = models.CharField(max_length=100, verbose_name="行动名称")  # 已有字段

    class Meta:
        verbose_name = u'目标表'
        verbose_name_plural = verbose_name
        app_label = 'action'
        db_table = 'action_template'