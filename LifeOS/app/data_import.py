import json
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db
from app.models import (
    MetaAction, ValueGoal, ValueGoalCategory,
    MetaActionValueGoalMapping, ValueGoalCategoryMapping
)
from config import Config


def import_data():
    """Import initial data from values.json into the database.
    
    The import process follows this structure:
    1. Create ValueGoalCategory tree (ValueSystemData -> 大类 -> 小类)
    2. Create ValueGoal records (类目)
    3. Create MetaAction records (行动示例)
    4. Create mappings between MetaAction and ValueGoal
    """
    with open(Config.INITIAL_VALUES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # First, create the root category for the whole value system
    root_category = ValueGoalCategory(
        name="ValueSystemData",
        root=True
    )
    db.session.add(root_category)
    
    # Dictionary to store created categories for reference
    categories = {"ValueSystemData": root_category}
    
    for category_data in data['ValueSystemData']:
        # Create main category (大类) as child of root
        main_category = ValueGoalCategory(
            name=category_data['大类'],
            root=False,
            parent=root_category
        )
        db.session.add(main_category)
        categories[category_data['大类']] = main_category
        
        for sub_category_data in category_data['小类']:
            # Create sub-category
            sub_category = ValueGoalCategory(
                name=sub_category_data['小类'],
                root=False,
                parent=main_category
            )
            db.session.add(sub_category)
            categories[sub_category_data['小类']] = sub_category
            
            for item in sub_category_data['类目']:
                # Create ValueGoal
                value_goal = ValueGoal(
                    name=item['类目'],
                    definition=item['定义'],
                    characteristic=item['特性']
                )
                db.session.add(value_goal)
                
                # Create category mapping
                category_mapping = ValueGoalCategoryMapping(
                    value_goal=value_goal,
                    value_goal_category=sub_category
                )
                db.session.add(category_mapping)
                
                # Create MetaActions and mappings
                action_examples = [a.strip() for a in item['行动示例'].split(',')]
                for action_content in action_examples:
                    # Create MetaAction
                    meta_action = MetaAction(
                        name=action_content[:50],  # Truncate to 50 chars for name
                        content=action_content,
                        effectiveness=True,
                        priority=True,
                        recommendation=True
                    )
                    db.session.add(meta_action)
                    
                    # Create value goal mapping
                    value_goal_mapping = MetaActionValueGoalMapping(
                        meta_action=meta_action,
                        value_goal=value_goal,
                        weight=1.0,
                        confidence=0.5,
                        time_lag=0.0,
                        evidence_count=0,
                        last_updated=datetime.now()
                    )
                    db.session.add(value_goal_mapping)

    try:
        db.session.commit()
        print("Data import completed successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error during data import: {str(e)}")
        raise


if __name__ == "__main__":
    print(f"Importing data from {Config.INITIAL_VALUES_FILE}")
    import_data()
