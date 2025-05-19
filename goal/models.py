from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone


class ValueGoalCategory(models.Model):
    """
    价值目标分类
    """
    objects = None
    name = models.CharField(max_length=255, verbose_name="人生价值目标分类名称")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    root = models.BooleanField(default=False, verbose_name="是否为 root 分类根")

    def __str__(self):
        return self.name


class ValueGoal(models.Model):
    """
    价值目标
    """
    name = models.CharField(max_length=255, verbose_name="人生价值目标名称")
    definition = models.TextField(verbose_name="人生价值目标的定义")
    characteristic = models.JSONField(default=list, verbose_name="定义特征", help_text="例如 ['批判性', '开放性']")
    categories = models.ManyToManyField(ValueGoalCategory, related_name='value_goals',
                                        verbose_name="归类到的价值目标分类")

    def __str__(self):
        return self.name


class ValueSystemPriority(models.Model):
    """
    价值目标体系
    """

    class Status(models.TextChoices):
        ACTIVE = '生效', '生效'
        INACTIVE = '失效', '失效'
        UNKNOWN = '未知', '未知'

    name = models.CharField(max_length=255, verbose_name="价值目标体系名称")
    description = models.TextField(verbose_name="描述")
    effective_at = models.DateTimeField(verbose_name="生效时间")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNKNOWN, verbose_name="状态")
    period = models.CharField(max_length=50, verbose_name="时间切面")
    category = models.ForeignKey(ValueGoalCategory, on_delete=models.CASCADE,
                                 limit_choices_to={'root': True}, verbose_name="对应分类方案")
    values = models.ManyToManyField(ValueGoal, through='ValueGoalWeight', related_name='systems',
                                    verbose_name="包含的价值目标")
    decay_factors = models.JSONField(default=list, verbose_name="衰减因子")

    def get_weights(self):
        return list(self.valuegoalweight_set.values_list('weight', flat=True))

    def __str__(self):
        return self.name


class ValueGoalWeight(models.Model):
    """
    价值目标体系中价值目标权重
    """
    system = models.ForeignKey(ValueSystemPriority, on_delete=models.CASCADE)
    value_goal = models.ForeignKey(ValueGoal, on_delete=models.CASCADE)
    weight = models.FloatField(
        verbose_name="权重",
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    category = models.ForeignKey(ValueGoalCategory, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('system', 'value_goal', 'category')
        indexes = [
            models.Index(fields=['system', 'category']),
        ]
        db_table = 'goal_value_goal_categories'


class MetaActionCategory(models.Model):
    """
    元行动分类
    """
    name = models.CharField(max_length=255, verbose_name="行动分类名称")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    root = models.BooleanField(default=False, verbose_name="是否为 root 分类根")

    def __str__(self):
        return self.name


class MetaActionCategoryMapping(models.Model):
    """
    元行动与分类的映射关系
    """
    meta_action = models.ForeignKey('MetaAction', on_delete=models.CASCADE)
    category = models.ForeignKey(MetaActionCategory, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('meta_action', 'category')


class MetaActionCausationValueGoal(models.Model):
    """
    元行动与价值目标的因果关系
    """
    meta_action = models.ForeignKey('MetaAction', on_delete=models.CASCADE, related_name='causation_relations')
    causation_pair = models.JSONField(default=dict, verbose_name="因果关系对")
    weight = models.FloatField(
        verbose_name="因果强度权重",
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    confidence = models.FloatField(
        verbose_name="因果关系置信度",
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    class Meta:
        indexes = [
            models.Index(fields=['meta_action']),
        ]

    def clean(self):
        if not isinstance(self.causation_pair, dict):
            raise ValidationError("causation_pair 必须是字典类型")
        if 'value_goal_id' not in self.causation_pair:
            raise ValidationError("causation_pair 必须包含 value_goal_id")


class MetaActionInteractionMetaAction(models.Model):
    """
    元行动间的协同/拮抗关系
    """
    from_meta_action = models.ForeignKey('MetaAction', on_delete=models.CASCADE, related_name='from_interactions')
    to_meta_action = models.ForeignKey('MetaAction', on_delete=models.CASCADE, related_name='to_interactions')
    interaction_type = models.CharField(max_length=50, choices=(('synergy', '协同'), ('antagonism', '拮抗')))

    class Meta:
        unique_together = ('from_meta_action', 'to_meta_action')
        indexes = [
            models.Index(fields=['from_meta_action', 'to_meta_action']),
        ]


class MetaAction(models.Model):
    """
    元行动
    """
    objects = None
    name = models.CharField(max_length=255, verbose_name="行动名称")
    content = models.TextField(verbose_name="行动的具体内容描述，需要符合 SMART 原则")
    pv = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="行动工作价值量。生命有限，由时间来度量价值应该是个可行的方案，假设 80 年为标准寿命是满分价值"
    )
    effectiveness = models.BooleanField(default=True, verbose_name="有效性")
    priority = models.BooleanField(default=True, verbose_name="优先级")
    recommendation = models.BooleanField(default=True, verbose_name="推荐度")

    # 分类关系：MetaAction -(cat)→ MetaActionCategory
    categories = models.ManyToManyField(
        'MetaActionCategory',
        through='MetaActionCategoryMapping',
        related_name='meta_actions',
        verbose_name="Categorization 归属于... `MetaAction`-(cat)→`MetaActionCategory`实例归属于分类节点"
    )

    # 因果关系：MetaAction -(cau)→ MetaActionCausationValueGoal
    causations = models.ManyToManyField(
        'MetaActionCausationValueGoal',
        related_name='meta_actions',
        verbose_name="Causation 因果导致关系... `MetaAction`-(Causation)→`ValueGoal`"
    )

    # 行动间协同/拮抗关系：MetaAction ←(interaction)→ MetaAction
    interactions = models.ManyToManyField(
        'self',
        through='MetaActionInteractionMetaAction',
        symmetrical=False,
        related_name='interacted_with',
        verbose_name="行动间协同/拮抗效应关系 `MetaAction`←(Interaction)→`MetaAction`",
        blank=True
    )

    def __str__(self):
        return self.name


class Action(models.Model):
    """
    行动
    """
    meta_action = models.ForeignKey('MetaAction', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='actions',
                                    verbose_name="派生自的 MetaAction")
    description = models.TextField(verbose_name="行动描述")
    plan_start_at = models.DateTimeField(verbose_name="计划开始时间")
    plan_end_at = models.DateTimeField(verbose_name="计划结束时间")
    pv = models.FloatField(verbose_name="目标行动价值量")
    actual_start_at = models.DateTimeField(null=True, blank=True, verbose_name="实际开始时间")
    actual_end_at = models.DateTimeField(null=True, blank=True, verbose_name="实际结束时间")
    status = models.CharField(max_length=50, verbose_name="完成状态")
    ac = models.FloatField(verbose_name="实际投入价值量")
    ev = models.FloatField(verbose_name="挣得价值量")
    achievement_rate = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
                                         verbose_name="达成率")
    note = models.TextField(blank=True, null=True, verbose_name="过程记录")

    def clean(self):
        if not self.plan_start_at or not self.plan_end_at:
            raise ValidationError("计划开始时间和计划结束时间都必须填写")

        if self.plan_start_at > self.plan_end_at:
            raise ValidationError("计划开始时间不能晚于计划结束时间")

        if self.actual_start_at:
            if self.actual_start_at < self.plan_start_at or self.actual_start_at > self.plan_end_at:
                raise ValidationError("实际开始时间应在计划时间范围内")
            if self.actual_end_at and self.actual_start_at > self.actual_end_at:
                raise ValidationError("实际开始时间不能晚于实际结束时间")

        if self.actual_end_at:
            if self.actual_end_at < self.plan_start_at or self.actual_end_at > self.plan_end_at:
                raise ValidationError("实际结束时间应在计划时间范围内")

        if self.ev < 0:
            raise ValidationError("挣得价值量不能为负数")

        if self.ac < 0:
            raise ValidationError("实际投入价值量不能为负数")

    def __str__(self):
        return self.description


class ActionPlan(models.Model):
    """
    行动计划
    """
    name = models.CharField(max_length=255, verbose_name="行动计划名称")
    actions = models.ManyToManyField(to='Action', blank=True, related_name='related_actions')
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    note = models.TextField(blank=True, null=True, verbose_name="过程记录")

    def clean(self):
        if (self.start_time and self.end_time) and (self.start_time > self.end_time):
            raise ValidationError("开始时间不能晚于结束时间")

    def __str__(self):
        return self.name


class Lifemeaning(models.Model):
    """
    人生意义
    """
    created_at = models.DateTimeField(default=timezone.now, verbose_name="记录时间")
    action_plan = models.ForeignKey(ActionPlan, on_delete=models.CASCADE, verbose_name="行动计划")
    value_system_priority = models.ForeignKey(ValueSystemPriority, on_delete=models.CASCADE,
                                              verbose_name="价值体系")
    life_meaning = models.FloatField(null=True, blank=True, verbose_name="人生意义数值")

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.life_meaning:
            self.calculate_life_meaning()
        super().save(*args, **kwargs)

    def calculate_life_meaning(self):
        try:
            meta_action = MetaAction.objects.get(name=self.action_plan)
        except MetaAction.DoesNotExist:
            # 处理找不到MetaAction的情况，例如设置默认值或抛出自定义异常
            meta_action = None  # 或者采取其他适当措施
            
        if meta_action is not None:
            # 如果成功获取了meta_action，则继续执行相关逻辑
            total = 0.0

            # 获取所有相关的元动作及其因果关系和权重
            causation_relations = (
                MetaActionCausationValueGoal.objects
                .select_related('meta_action')
                .filter(meta_action__action__plans=meta_action)
                .annotate(meta_action_id=F('meta_action__id'))
                .values(
                    'meta_action_id',
                    'weight',
                    'confidence',
                    'causation_pair'
                )
            )

            # 构建按元动作ID组织的因果关系字典
            causation_dict = {}
            for rel in causation_relations:
                causation_dict.setdefault(rel['meta_action_id'], []).append(rel)

            # 获取所有相关价值目标权重
            weights_dict = {
                vg.value_goal_id: vg.weight
                for vg in ValueGoalWeight.objects.filter(system=self.value_system_priority)
            }

            # 获取所有相关动作
            actions = (
                Action.objects
                .filter(plans=self.action_plan)
                .annotate(meta_action_id=F('meta_action__id'))
                .values('meta_action_id', 'ev', 'achievement_rate')
            )

            # 计算总和
            for action in actions:
                if action['meta_action_id']:
                    for causation_relation in causation_dict.get(action['meta_action_id'], []):
                        try:
                            # 确保causation有必要的属性
                            causation_weight = causation_relation.get('weight', 0) or 0
                            causation_confidence = causation_relation.get('confidence', 0) or 0
                            causation_data = causation_relation.get('causation_pair') or {}

                            value_goal_id = causation_data.get("value_goal_id")
                            if not value_goal_id:
                                continue

                            strength_association = causation_weight * causation_confidence
                            goal = action['ev'] * action['achievement_rate']
                            total += (weights_dict.get(value_goal_id, 0.0)) * strength_association * goal
                        except Exception as e:
                            print(f"警告: 因果关系解析失败: {e}")

            self.life_meaning = total
        else:
            # 如果meta_action为None，则跳过需要它的逻辑或抛出异常
            # ... 处理没有找到meta_action的状况 ...
            pass


class CumulativeLifemeaning(models.Model):
    """
    累计人生意义
    """
    created_at = models.DateTimeField(default=timezone.now, verbose_name="记录时间")
    action_plan = models.ForeignKey('ActionPlan', on_delete=models.CASCADE, null=True, blank=True)
    value_system_priority = models.ForeignKey(
        'ValueSystemPriority',  # 假设目标模型名
        on_delete=models.CASCADE,  # 或者 SET_NULL 等
        related_name='cumulative_lifemeanings'
    )
    cumulative_life_meaning = models.FloatField(null=True, blank=True, verbose_name="累计人生意义数值")
    previous_lifemeanings = models.ManyToManyField(Lifemeaning, related_name='cumulative_records',
                                                   verbose_name="之前的人生意义记录")
    accumulated_meaning = models.FloatField(null=True, blank=True, verbose_name="累积的意义")
    last_updated = models.DateTimeField(null=True, blank=True, verbose_name="最后更新时间")
    total_meaning = models.FloatField(null=True, blank=True, verbose_name="总意义值")
    value_system_priority = models.FloatField(default=0.0)  # 新增字段用于计算优先级
    life_meaning_history = models.JSONField(default=list, verbose_name="人生意义历史记录")  # 新增字段

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        # 如果是新对象，则不指定ID，让数据库自动生成
        if not self.pk:
            # 临时保存当前ID
            temp_id = self.id
            self.id = None  # 清除ID以确保数据库生成新的自增ID
            
            # 确保action_plan在保存前被正确设置
            if not self.action_plan:
                # 如果没有设置action_plan，尝试从value_system_priority获取
                if self.value_system_priority and hasattr(self.value_system_priority, 'action_plan'):
                    self.action_plan = self.value_system_priority.action_plan
                else:
                    raise ValueError("CumulativeLifemeaning requires an action_plan to be set")
            
            super().save(*args, **kwargs)
            self.id = temp_id  # 恢复原始ID（如果有需要）
        else:
            # 如果已经存在，则直接继续
            pass

        # 现在可以安全地使用 previous_lifemeanings 多对多关系
        self.calculate_cumulative_life_meaning()

        # 最后再调用父类的 save() 以确保更新的数据被保存（如果需要）
        if self.pk:
            super().save(*args, **kwargs)

    def calculate_cumulative_life_meaning(self):
        # 假设 value_system_priority 是另一个模型实例，其拥有 decay_factors 字段
        # 修改前: self.value_system_priority.decay_factors
        if not hasattr(self, 'life_meaning_history'):
            self.life_meaning_history = []
            
        n = len(self.life_meaning_history)
        
        # 示例修正：如果 decay_factors 存在于当前模型自身上
        decay_factors = list(self.decay_factors[:n]) if hasattr(self, 'decay_factors') else []
