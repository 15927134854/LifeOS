# lifeos_script.py
import sys
import os
import django
import datetime
import random
import json
import logging
from django.db import transaction  # 导入 transaction 模块

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录到 PYTHONPATH
sys.path.append(PROJECT_ROOT)
# 设置 DJANGO_SETTINGS_MODULE 环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LifeOS.settings")
django.setup()


if not os.path.exists('values.json'):
    logger.error("当前工作目录: %s", os.getcwd())
    logger.error("查找的文件路径: %s", os.path.abspath('goal/values.json'))
    raise FileNotFoundError("values.json 未找到，请确认文件是否存在以及路径是否正确。")

try:
    with open('values.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except IOError as e:
    logger.error("读取 values.json 文件时发生错误: %s", e)
    raise
except json.JSONDecodeError as e:
    logger.error("解析 values.json 文件时发生错误: %s", e)
    raise


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
    # 初始化随机数生成器
    random.seed(datetime.datetime.now().timestamp())

    weights = [random.random() for _ in value_goals]
    decay_factors = [random.random() for _ in value_goals]

    # 计算人的生命周期（0-80岁）
    lifespan_years = 80
    current_year = timezone.now().year
    birth_year = current_year - random.randint(0, 80)  # 随机出生年份

    # 将生命周期划分为多个阶段
    life_stages = [
        (0, 5, "婴幼儿期"),
        (6, 12, "童年期"),
        (13, 19, "青少年期"),
        (20, 35, "青年期"),
        (36, 50, "中年期"),
        (51, 65, "壮年期"),
        (66, 80, "老年期")
    ]

    system = ValueSystemPriority.objects.create(
        name="Value System Priority",
        description="Default value system priority description",
        effective_at=timezone.now(),
        status="生效",
        period=f"{current_year}-{current_year + 10}",  # 假设系统有效期为10年
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
        logger.error("保存 ValueSystemPriority 时发生错误: %s", e)
        return None

    # 刷新system实例以确保values关系被正确保存
    try:
        system.refresh_from_db()
    except Exception as e:
        logger.error("刷新 ValueSystemPriority 数据时发生错误: %s", e)
        return None

    return system, value_goals  # 返回 system 和 value_goals 两个值


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
        if len(meta_actions) < 5:
            print("错误: 元行动数量不足，无法构建行动计划。")
            break

        selected_meta_actions = random.sample(meta_actions, random.randint(8, 12))  # 增加动作数量
        actions = []

        for meta_action in selected_meta_actions:
            created_at = timezone.now()
            plan_start_at = timezone.now()
            plan_end_at = timezone.now()
            actual_start_at = None
            actual_end_at = None
            status = random.choice(['未开始', '进行中', '已完成'])
            if meta_action.pv is not None:
                ac = random.uniform(0.5, float(meta_action.pv) * 1.2)  # 更广泛的评分范围
            else:
                logger.warning("meta_action.pv 为 None，使用默认值 5.0")
                ac = random.uniform(0.5, 6.0)
            ev = random.uniform(0.3, ac)
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

    # 预加载所有 ValueGoal 以减少数据库查询
    value_goals = list(ValueGoal.objects.all())
    value_goal_ids = {vg.id: vg for vg in value_goals}
    value_goal_names = {vg.name: vg for vg in value_goals}

    # 构建元行动
    meta_actions = build_meta_actions(values_data, value_goals)

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
        # 初始化 goal_name 变量
        goal_name = ""
        for value_goal in value_system_priority.values.all():
            goal_contributions[value_goal.name] = 0.0001  # 使用极小非零值初始化

        # 计算每个ValueGoal的贡献
        for action in action_plan.actions.all():
            if action.meta_action and action.meta_action.causations.exists():
                for causation in action.meta_action.causations.all():
                    # 使用预加载的 ValueGoal 映射
                    value_goal_id = causation.causation_pair['value_goal_id']
                    value_goal = value_goal_ids.get(value_goal_id)
                    if not value_goal:
                        logger.warning("未找到 ID 为 %s 的 ValueGoal", value_goal_id)
                        continue

                    strength_association = causation.weight * causation.confidence
                    goal = action.ev * action.achievement_rate
                    
                    # 获取对应的权重值
                    try:
                        value_index = list(value_system_priority.values.all()).index(value_goal)
                        if value_index < len(value_system_priority.get_weights()):
                            value = value_system_priority.get_weights()[value_index]
                        else:
                            logger.warning("未找到 %s 的权重值，使用默认值 0.5", value_goal.name)
                            value = 0.5  # 默认权重值
                    except Exception as e:
                        logger.error("获取权重值时发生错误: %s", e)
                        value = 0.5  # 默认权重值

                    contribution = value * strength_association * goal
                    goal_name = value_goal.name  # 设置 goal_name 变量
                    goal_contributions[goal_name] += contribution or random.uniform(0.1, 1)  # 替换可能的 0 值

        # 累计每个ValueGoal的贡献
        # 初始化累计字典（无论是否为空）
        if not cumulative_life_meaning_by_goal:
            cumulative_goal_contributions = {k: v if v != 0 else random.uniform(0.1, 1) 
                                      for k, v in goal_contributions.items()}
        else:
            # 后续周期，添加上一周期的累计值并应用衰减因子
            cumulative_goal_contributions = {}
            previous_contributions = cumulative_life_meaning_by_goal[-1]

            for goal_name, contribution in goal_contributions.items():
                # 找到对应ValueGoal的索引以获取正确的衰减因子
                try:
                    goal = value_goal_names[goal_name]
                    goal_index = list(value_system_priority.values.all()).index(goal)
                except KeyError:
                    logger.warning("未找到名为 %s 的 ValueGoal", goal_name)
                    decay_factor = 0.5  # 默认衰减因子
                else:
                    # 添加索引边界检查
                    if goal_index < len(value_system_priority.decay_factors):
                        decay_factor = value_system_priority.decay_factors[goal_index]
                    else:
                        decay_factor = 0.5  # 默认衰减因子

                    # 计算累计贡献：上一周期累计值 * 衰减因子 + 当前周期贡献
                    cumulative_value = previous_contributions.get(goal_name, 0) * decay_factor + contribution
                    cumulative_goal_contributions[goal_name] = cumulative_value if cumulative_value != 0 else random.uniform(0.1, 1)

        # 不论是否为空，始终更新列表
        previous_lifemeanings.append(lifemeaning)
        life_meaning_data.append(lifemeaning.life_meaning)
        cumulative_life_meaning_data.append(cumulative_lifemeaning.cumulative_life_meaning)
        # 确保每次循环都更新贡献数据
        life_meaning_by_goal.append(goal_contributions)
        cumulative_life_meaning_by_goal.append(cumulative_goal_contributions)

    return life_meaning_data, cumulative_life_meaning_data, life_meaning_by_goal, cumulative_life_meaning_by_goal, len(action_plans)


# 新增推荐函数

def recommend_actions_by_age(age, value_goals):
    """
    根据年龄推荐价值目标的优先级和具体行动建议。
    
    参数:
        age (int): 当前年龄
        value_goals (list of str): 所有价值目标名称列表
    返回:
        dict: {value_goal_name: weight} 和行动建议
    """
    # 预设年龄段配置
    if age <= 12:
        weights = {'家庭': 0.4, '健康': 0.3, '学习': 0.2, '社交': 0.1}
        actions = [
            "多陪伴家人，建立安全感",
            "培养良好的作息和饮食习惯",
            "鼓励探索感兴趣的事物，激发好奇心"
        ]
    elif 13 <= age <= 18:
        weights = {'学习': 0.4, '健康': 0.3, '社交': 0.2, '自我表达': 0.1}
        actions = [
            "设定阶段性学习目标并坚持执行",
            "每天保持适量运动，保持身体健康",
            "积极参与学校活动，拓展社交圈"
        ]
    elif 19 <= age <= 30:
        weights = {'成长': 0.4, '职业': 0.3, '社交': 0.2, '财务': 0.1}
        actions = [
            "制定清晰的职业发展规划",
            "主动学习新技能，提升核心竞争力",
            "建立稳定的人际关系网络"
        ]
    elif 31 <= age <= 45:
        weights = {'职业': 0.3, '家庭': 0.3, '成长': 0.2, '社会责任': 0.2}
        actions = [
            "平衡工作与家庭，避免过度消耗",
            "为家庭提供稳定保障（如保险、储蓄）",
            "参与公益或社区事务，回馈社会"
        ]
    elif 46 <= age <= 60:
        weights = {'家庭': 0.3, '健康': 0.3, '社会责任': 0.2, '精神追求': 0.2}
        actions = [
            "重视子女教育或支持其独立",
            "定期体检，保持规律作息",
            "分享人生经验，参与指导他人"
        ]
    else:
        weights = {'健康': 0.4, '家庭': 0.3, '精神追求': 0.2, '社会连接': 0.1}
        actions = [
            "保持身体活力，适度锻炼",
            "与家人共度美好时光，传递家风",
            "撰写回忆录或参与志愿活动，延续价值"
        ]

    # 过滤掉未定义的价值目标
    weights = {k: v for k, v in weights.items() if k in value_goals}

    return {
        'weights': weights,
        'actions': actions
    }


def visualize_life_meaning(data, cumulative_data, data_by_goal):
    """可视化人生意义数据."""
    # 示例实现：打印数据
    print("Visualizing life meaning data:")
    print(f"Data: {data}")
    print(f"Cumulative Data: {cumulative_data}")
    print(f"Data by Goal: {data_by_goal}")

# 示例调用
value_goals = ['家庭', '健康', '学习', '社交', '成长', '职业', '社会责任', '精神追求']
current_age = 28
recommendation = recommend_actions_by_age(current_age, value_goals)
print(f"\\n--- {current_age} 岁 行动建议 ---")
print("推荐价值目标权重:")
for goal, weight in recommendation['weights'].items():
    print(f"- {goal}: {weight * 100:.0f}%")
print("\n具体行动建议:")
for action in recommendation['actions']:
    print(f"- {action}")

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
        # 可选：清理其他相关模型数据
        Lifemeaning.objects.all().delete()
        CumulativeLifemeaning.objects.all().delete()
        ValueSystemPriority.objects.all().delete()
        ValueGoalWeight.objects.all().delete()
        MetaActionCausationValueGoal.objects.all().delete()
        Action.objects.all().delete()
    except Exception as e:
        logger.error("清理现有数据时发生错误: %s", e)
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
    system, value_goals = build_value_system_priority(values_data)  # 修改为接收两个返回值
    if not system:
        print("构建价值目标体系失败")
        exit(1)

    # 确保 system.lifespan_stages 被正确初始化
    if not system.lifespan_stages:
        # 如果 lifespan_stages 为空，使用默认生命周期阶段
        system.lifespan_stages = [
            (0, 5, "婴幼儿期"),
            (6, 12, "童年期"),
            (13, 19, "青少年期"),
            (20, 35, "青年期"),
            (36, 50, "中年期"),
            (51, 65, "壮年期"),
            (66, 80, "老年期")
        ]
        system.save()  # 保存更新后的 system 实例

    # 将 system 赋值给 value_system_priority 变量
    value_system_priority = system

    # 构建元行动
    meta_actions = build_meta_actions(values_data, value_goals)
    if not meta_actions:
        print("构建元行动失败")
        exit(1)

    # 构建行动计划
    try:
        with transaction.atomic():
            num_cycles = random.randint(20, 25)  # 固定范围以提高可预测性
            action_plans = build_action_plans(meta_actions, num_cycles)
    except Exception as e:
        logger.error("构建行动计划时发生错误: %s", e)
        exit(1)

    # 运行仿真
    try:
        with transaction.atomic():
            life_meaning_data, cumulative_life_meaning_data, life_meaning_by_goal, \
                cumulative_life_meaning_by_goal, num_cycles = simulate(
                value_system_priority, action_plans)
    except Exception as e:
        logger.error("运行仿真时发生错误: %s", e)
        exit(1)

    print("人生意义数据:", life_meaning_data)
    print("累计人生意义数据:", cumulative_life_meaning_data)
    print("每个价值目标的人生意义贡献:", life_meaning_by_goal)
    print("每个价值目标的累计人生意义贡献:", cumulative_life_meaning_by_goal)

    # 调用可视化函数
    visualize_life_meaning(life_meaning_data, cumulative_life_meaning_data, life_meaning_by_goal)

    # 生成用于D3.js可视化的数据结构
    output_data = {
        "life_meaning": life_meaning_data,
        "cumulative_life_meaning": cumulative_life_meaning_data,
        "life_meaning_by_goal": [
            {**{k: float(v) for k, v in item.items()}} for item in life_meaning_by_goal
        ],
        "cumulative_life_meaning_by_goal": [
            {**{k: float(v) for k, v in item.items()}} for item in cumulative_life_meaning_by_goal
        ],
        "lifespan_stages": [
            {
                "stage": stage[2],
                "age_range": f"{stage[0]}-{stage[1]}岁",
                "duration": f"{stage[1] - stage[0] + 1}年"
            } for stage in system.lifespan_stages  # 使用构建的价值体系中的生命周期阶段数据
        ]  # 添加结构化的人生阶段信息
    }

    # 写入simulation_output.json文件
    with open('simulation_output.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print("数据已导出到 simulation_output.json")
    print("lifespan_stages 数据:", [stage[2] for stage in system.lifespan_stages])  # 更清晰地输出生命周期阶段名称

    # 确保 simulation_output 包含必要的字段
    simulation_output = {
        'life_meaning_by_goal': [{
            '家庭': 0.8,
            '健康': 0.7,
            '学习': 0.6,
            '社交': 0.5
        }]
    }

    value_goals = []
    if 'life_meaning_by_goal' in simulation_output:
        value_goals = list(simulation_output['life_meaning_by_goal'][0].keys())
    else:
        value_goals = []  # 或者根据需求进行默认赋值

    # 获取当前年龄（示例）
    current_age = 28  # 可从用户输入或数据源读取

    # 获取推荐
    recommendation = recommend_actions_by_age(current_age, value_goals)
    print(f"\\n--- {current_age} 岁 行动建议 ---")
    print("推荐价值目标权重:")
    for goal, weight in recommendation['weights'].items():
        print(f"- {goal}: {weight * 100:.0f}%")
    print("\n具体行动建议:")
    for action in recommendation['actions']:
        print(f"- {action}")
