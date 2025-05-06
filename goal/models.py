# Create your models here.
from django.db import models

from LifeOS.common.utils import BaseModel


class GoalTemplate(BaseModel):
    """目标表"""
    name = models.CharField(max_length=100, verbose_name="目标名称")  # 已有字段

    class Meta:
        verbose_name = u'目标表'
        verbose_name_plural = verbose_name
        app_label = 'goal'
        db_table = 'goal_template'