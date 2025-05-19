# lifeos_script.py
import sys
import os
import django
import datetime
import random
import json

# 添加项目根目录到 PYTHONPATH
sys.path.append("D:\\运维仿真\\LifeOS")
# 设置 DJANGO_SETTINGS_MODULE 环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LifeOS.settings")
django.setup()


if not os.path.exists('values.json'):
    print(f"当前工作目录: {os.getcwd()}")
    print(f"查找的文件路径: {os.path.abspath('goal/values.json')}")
    raise FileNotFoundError("values.json 未找到，请确认文件是否存在以及路径是否正确。")

with open('values.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

from django.utils import timezone
from goal.models import (
    ValueGoalCategory, ValueGoal, ValueSystemPriority, ValueGoalWeight,
    MetaAction,
    MetaActionCausationValueGoal,
    Action, ActionPlan, Lifemeaning, CumulativeLifemeaning
)


def create_category_tree(data):
    root_category = ValueGoalCategory.objects.create(name="Root Category", root=True)
    value_goals = []

    for big_category in data:
        for small_category in big_category['小类']:
            small_cat_obj = ValueGoalCategory.objects.create(name=small_category['小类'])
            small_cat_obj.parent = root_category
            small_cat_obj.save()

            for category in small_category['类目']:
                goal = ValueGoal.objects.create(
                    name=category['类目'],
                    definition=category['定义'],
                    characteristic=category['特性']
                )
                goal.categories.add(small_cat_obj)
                value_goals.append(goal)

    return root_category, value_goals


def build_value_system_priority(values_data):
    if 'ValueSystemData' not in values_data:
        print("错误: JSON 数据中缺少 'ValueSystemData' 字段。")
        return None

    root_category, value_goals = create_category_tree(values_data['ValueSystemData'])
    weights = [random.random() for _ in value_goals]
    decay_factors = [random.random() for _ in value_goals]

    system = ValueSystemPriority.objects.create(
        name="Value System Priority",
        description="Default value system priority description",
        effective_at=timezone.now(),
        status="生效",
        period="2025",
        category=root_category
    )

    for goal, weight in zip(value_goals, weights):
        ValueGoalWeight.objects.create(
            system=system,
            value_goal=goal,
            weight=weight,
            category=root_category
        )

    system.values.set(value_goals)
    try:
        system.save()
    except Exception as e:
        print(f"保存 ValueSystemPriority 时发生错误: {e}")
        return None

    # 刷新system实例以确保values关系被正确保存
    try:
        system.refresh_from_db()
    except Exception as e:
        print(f"刷新 ValueSystemPriority 数据时发生错误: {e}")
        return None

    return system


def build_meta_actions(values_data, value_goals):
    meta_actions = []
    if 'ValueSystemData' not in values_data:
        print("错误: JSON 数据中缺少 'ValueSystemData' 字段。")
        return meta_actions

    for big_category in values_data['ValueSystemData']:
        for small_category in big_category['小类']:
            for category in small_category['类目']:
                action_examples = category['行动示例'].split('，')

                for action_example in action_examples:
                    pv = random.uniform(1, 10)
                    meta_action = MetaAction.objects.create(
                        name=action_example.strip(),
                        content=action_example.strip(),
                        pv=pv
                    )
                    value_goal = next((vg for vg in value_goals if vg.name == category['类目']), None)
                    if value_goal:
                        causation = MetaActionCausationValueGoal.objects.create(
                            meta_action=meta_action,
                            causation_pair={"value_goal_id": value_goal.id},
                            weight=1.0,
                            confidence=random.random()
                        )
                        meta_action.causations.add(causation)

                    meta_actions.append(meta_action)

    return meta_actions


def build_action_plans(meta_actions, num_cycles):
    action_plans = []
    for cycle in range(num_cycles):
        if len(meta_actions) < 3:
            print("错误: 元行动数量不足，无法构建行动计划。")
            break

        selected_meta_actions = random.sample(meta_actions, random.randint(3, 5))
        actions = []

        for meta_action in selected_meta_actions:
            created_at = timezone.now()
            plan_start_at = timezone.now()
            plan_end_at = timezone.now()
            actual_start_at = None
            actual_end_at = None
            status = random.choice(['未开始', '进行中', '已完成'])
            ac = random.uniform(1, meta_action.pv)
            ev = random.uniform(1, ac)
            achievement_rate = ev / float(meta_action.pv)
            notes = None

            action = Action.objects.create(
                meta_action=meta_action,
                description=meta_action.name,
                plan_start_at=plan_start_at,
                plan_end_at=plan_end_at,
                pv=float(meta_action.pv),
                actual_start_at=actual_start_at,
                actual_end_at=actual_end_at,
                status=status,
                ac=ac,
                ev=ev,
                achievement_rate=achievement_rate,
                note=notes
            )
            actions.append(action)

        action_plan = ActionPlan.objects.create(
            name=f"Action Plan Cycle {cycle + 1}",
            start_time=plan_start_at,
            end_time=plan_end_at
        )
        action_plan.actions.set(actions)
        action_plans.append(action_plan)

    return action_plans


def simulate(value_system_priority, action_plans):
    previous_lifemeanings = []
    life_meaning_data = []
    cumulative_life_meaning_data = []

    # 保存每个ValueGoal的详细贡献数据
    life_meaning_by_goal = []
    cumulative_life_meaning_by_goal = []

    for action_plan in action_plans:
        # 创建 Lifemeaning 实例
        lifemeaning = Lifemeaning.objects.create(
            action_plan=action_plan,
            value_system_priority=value_system_priority,
            life_meaning=random.uniform(1, 100)  # 确保该字段有具体数值
        )
        # 创建 CumulativeLifemeaning 实例
        total_meaning = random.uniform(1, 100)
        accumulated_meaning = random.uniform(1, 100)
        cumulative_lifemeaning, created = CumulativeLifemeaning.objects.get_or_create(
            id=4,
            defaults={
                'total_meaning': total_meaning,
                'accumulated_meaning': accumulated_meaning,
                'last_updated': timezone.now(),
                'action_plan': action_plan
            }
        )
        print(type(cumulative_lifemeaning))  # 确认其类型是否为期望的类实例
        if not hasattr(cumulative_lifemeaning, 'previous_lifemeanings'):
            raise ValueError("cumulative_lifemeaning 不是期望的类实例")
        cumulative_lifemeaning.previous_lifemeanings.set(previous_lifemeanings)
        cumulative_lifemeaning.save()

        # 确保不添加 None 或 0 值到 life_meaning_data 和 cumulative_life_meaning_data
        life_meaning_data.append(lifemeaning.life_meaning if lifemeaning.life_meaning is not None else random.uniform(1, 100))
        cumulative_life_meaning_data.append(cumulative_lifemeaning.cumulative_life_meaning if cumulative_lifemeaning.cumulative_life_meaning is not None else random.uniform(1, 100))

        # 计算每个ValueGoal的贡献
        goal_contributions = {}
        for value_goal in value_system_priority.values.all():
            goal_contributions[value_goal.name] = 0.0001  # 使用极小非零值初始化

        # 计算每个ValueGoal的贡献
        for action in action_plan.actions.all():
            if action.meta_action and action.meta_action.causations.exists():
                for causation in action.meta_action.causations.all():
                    value_goal = ValueGoal.objects.get(id=causation.causation_pair['value_goal_id'])
                    value_index = list(value_system_priority.values.all()).index(value_goal)
                    value = value_system_priority.get_weights()[value_index]

                    strength_association = causation.weight * causation.confidence
                    goal = action.ev * action.achievement_rate
                    contribution = value * strength_association * goal
                    goal_contributions[value_goal.name] += contribution or random.uniform(0.1, 1)  # 替换可能的 0 值

        # 累计每个ValueGoal的贡献
        if not cumulative_life_meaning_by_goal:
            # 首个周期，初始化累计字典
            cumulative_goal_contributions = {k: v if v != 0 else random.uniform(0.1, 1) for k, v in goal_contributions.items()}
        else:
            # 后续周期，添加上一周期的累计值并应用衰减因子
            cumulative_goal_contributions = {}
            previous_contributions = cumulative_life_meaning_by_goal[-1]

            for goal_name, contribution in goal_contributions.items():
                # 找到对应ValueGoal的索引以获取正确的衰减因子
                goal = ValueGoal.objects.get(name=goal_name)
                goal_index = list(value_system_priority.values.all()).index(goal)
                # 添加索引边界检查
                if goal_index < len(value_system_priority.decay_factors):
                    decay_factor = value_system_priority.decay_factors[goal_index]
                else:
                    # 可选：记录日志或设置默认值
                    decay_factor = 0.5  # 默认衰减因子

                # 计算累计贡献：上一周期累计值 * 衰减因子 + 当前周期贡献
                cumulative_value = previous_contributions.get(goal_name, 0) * decay_factor + contribution
                cumulative_goal_contributions[goal_name] = cumulative_value if cumulative_value != 0 else random.uniform(0.1, 1)  # 替换可能的 0 值

        previous_lifemeanings.append(lifemeaning)
        life_meaning_data.append(lifemeaning.life_meaning)
        cumulative_life_meaning_data.append(cumulative_lifemeaning.cumulative_life_meaning)

        # 保存每个ValueGoal的贡献数据
        life_meaning_by_goal.append(goal_contributions)
        cumulative_life_meaning_by_goal.append(cumulative_goal_contributions)

    return life_meaning_data, cumulative_life_meaning_data, life_meaning_by_goal, cumulative_life_meaning_by_goal, len(action_plans)


if __name__ == "__main__":
    import os
    import sys
    import django

    # 设置正确的 Django 配置模块路径
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LifeOS.settings")
    # 将项目根目录添加到 Python 路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        django.setup()
    except Exception as e:
        print(f"Django setup 发生错误: {e}")
        exit(1)

    # 清理现有数据
    try:
        ValueGoalCategory.objects.all().delete()
        ValueGoal.objects.all().delete()
        MetaAction.objects.all().delete()
        ActionPlan.objects.all().delete()
    except Exception as e:
        print(f"清理现有数据时发生错误: {e}")
        # 继续执行后续操作，因为某些表可能为空

    # 加载 JSON 数据
    try:
        with open('values.json', 'r', encoding='utf-8') as f:
            values_data = json.load(f)
    except FileNotFoundError:
        print("错误: 找不到 values.json 文件")
        exit(1)
    except json.JSONDecodeError:
        print("错误: values.json 文件格式不正确")
        exit(1)

    # 构建价值目标体系
    value_system_priority = build_value_system_priority(values_data)

    # 构建元行动
    value_goals = ValueGoal.objects.all()
    meta_actions = build_meta_actions(values_data, value_goals)

    # 构建行动计划
    num_cycles = 5
    action_plans = build_action_plans(meta_actions, num_cycles)

    # 进行仿真
    life_meaning_data, cumulative_life_meaning_data, life_meaning_by_goal, cumulative_life_meaning_by_goal, num_cycles = simulate(
        value_system_priority, action_plans)

    print("人生意义数据:", life_meaning_data)
    print("累计人生意义数据:", cumulative_life_meaning_data)
    print("每个价值目标的人生意义贡献:", life_meaning_by_goal)
    print("每个价值目标的累计人生意义贡献:", cumulative_life_meaning_by_goal)

    # 数据可视化部分
    import matplotlib.pyplot as plt

    # Specify the path to a font that supports CJK characters, e.g., 'SimHei'
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    import numpy as np
    import seaborn as sns
    sns.set(style="whitegrid")

    # 极坐标图函数
    def plot_radar_chart(labels, values, title):
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values += values[:1]  # 闭合图形
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.fill(angles, values, color='red', alpha=0.25)
        ax.plot(angles, values, color='red', linewidth=2)
        ax.set_xticks(angles[:-1], labels)
        ax.set_title(title)
        ax.grid(True)
        plt.tight_layout()
        plt.show()

    # 1. 人生意义趋势雷达图
    if life_meaning_data:
        labels = [f'Cycle {i+1}' for i in range(len(life_meaning_data))]
        values = life_meaning_data
        plot_radar_chart(labels, values, 'Life Meaning Trend (Radar Chart)')

    # 2. 累计人生意义趋势雷达图
    if cumulative_life_meaning_data:
        labels = [f'Cycle {i+1}' for i in range(len(cumulative_life_meaning_data))]
        values = cumulative_life_meaning_data
        plot_radar_chart(labels, values, 'Cumulative Life Meaning Trend (Radar Chart)')

    # 3. 每个价值目标的贡献雷达图
    if life_meaning_by_goal:
        goal_names = list(life_meaning_by_goal[0].keys())
        goal_values = [sum(d[goal] for d in life_meaning_by_goal if goal in d) for goal in goal_names]
        plot_radar_chart(goal_names, goal_values, 'Contribution by Value Goal (Radar Chart)')

    # 4. 累计价值目标贡献雷达图
    if cumulative_life_meaning_by_goal:
        cumulative_goal_values = [sum(d[goal] for d in cumulative_life_meaning_by_goal if goal in d) for goal in goal_names]
        plot_radar_chart(goal_names, cumulative_goal_values, 'Cumulative Contribution by Value Goal (Radar Chart)')
