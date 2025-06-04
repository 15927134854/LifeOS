from django.contrib import admin

from goal.models import ValueGoalCategory, ValueGoal, ValueSystemPriority, ValueGoalWeight, MetaActionCategory, \
    MetaActionCategoryMapping, MetaActionCausationValueGoal, MetaActionInteractionMetaAction, MetaAction, Action, \
    ActionPlan, Lifemeaning, CumulativeLifemeaning

# Register your models here.


admin.site.register(ValueGoalCategory)
admin.site.register(ValueGoal)
admin.site.register(ValueSystemPriority)
admin.site.register(ValueGoalWeight)
admin.site.register(MetaActionCategory)
admin.site.register(MetaActionCategoryMapping)
admin.site.register(MetaActionCausationValueGoal)
admin.site.register(MetaActionInteractionMetaAction)
admin.site.register(MetaAction)
admin.site.register(Action)
admin.site.register(ActionPlan)
admin.site.register(Lifemeaning)
admin.site.register(CumulativeLifemeaning)

admin.site.site_header = '人生意义管理系统'

