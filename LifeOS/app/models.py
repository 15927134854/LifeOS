from app import db
from pydantic import BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String

# 数据库模型定义
class ValueGoalCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    root = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('value_goal_category.id'))
    children = db.relationship('ValueGoalCategory', backref=db.backref('parent', remote_side=[id]))
    value_goals = db.relationship('ValueGoal', secondary='value_goal_category_mapping', back_populates='categories')


class ValueGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    characteristic = db.Column(db.String(255), nullable=False)
    categories = db.relationship('ValueGoalCategory', secondary='value_goal_category_mapping', back_populates='value_goals')
    meta_action_mappings = db.relationship('MetaActionValueGoalMapping', back_populates='value_goal')
    meta_actions = db.relationship('MetaAction', secondary='meta_action_value_goal_mapping', back_populates='value_goals')


class ValueGoalCategoryMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value_goal_id = db.Column(db.Integer, db.ForeignKey('value_goal.id'))
    value_goal_category_id = db.Column(db.Integer, db.ForeignKey('value_goal_category.id'))


class ValueSystemPriority(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    period = db.Column(db.String(255), nullable=False)  # e.g., 'D' for daily, 'W' for weekly, 'M' for monthly
    start_time = db.Column(db.DateTime, nullable=False)  # Period start
    end_time = db.Column(db.DateTime, nullable=False)  # Period end
    category_id = db.Column(db.Integer, db.ForeignKey('value_goal_category.id'))
    category = db.relationship('ValueGoalCategory')
    values = db.relationship('ValueGoal', secondary='value_system_priority_value_goal_mapping', backref='value_system_priorities')
    weights = db.Column(db.Text, nullable=False)  # Store JSON as Text for SQLite compatibility

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validate_category_root()
        self.normalize_weights()

    def validate_category_root(self):
        """Validate that the category has a root"""
        if not self.category:
            raise ValueError("Category is required")
        current = self.category
        while current.parent:
            current = current.parent
        if not current.root:
            raise ValueError("Category must have a root category")

    def normalize_weights(self):
        """Normalize weights for all value goals and category levels"""
        if not self.weights:
            return

        # Convert string to dict if needed
        if isinstance(self.weights, str):
            import json
            self.weights = json.loads(self.weights)

        # Normalize value goal weights
        if 'value_goals' in self.weights:
            total = sum(self.weights['value_goals'].values())
            if total > 0:
                self.weights['value_goals'] = {
                    k: v/total for k, v in self.weights['value_goals'].items()
                }

        # Normalize category weights
        if 'categories' in self.weights:
            self._normalize_category_weights(self.category)

        # Convert back to string for storage
        self.weights = json.dumps(self.weights)

    def _normalize_category_weights(self, category):
        """Recursively normalize weights for category hierarchy"""
        if not category or 'categories' not in self.weights:
            return

        # Convert string to dict if needed
        if isinstance(self.weights, str):
            import json
            self.weights = json.loads(self.weights)

        # Normalize current level
        if str(category.id) in self.weights['categories']:
            siblings = [c for c in category.parent.children if str(c.id) in self.weights['categories']] if category.parent else [category]
            total = sum(self.weights['categories'][str(c.id)] for c in siblings)
            if total > 0:
                self.weights['categories'][str(category.id)] /= total

        # Normalize children
        for child in category.children:
            self._normalize_category_weights(child)

        # Convert back to string for storage
        self.weights = json.dumps(self.weights)

    def get_period_slice(self, start, end):
        """Get priorities within a time range"""
        return ValueSystemPriority.query.filter(
            ValueSystemPriority.start_time >= start,
            ValueSystemPriority.end_time <= end
        ).all()

    def get_current_period(self):
        """Get current period's priorities"""
        from datetime import datetime
        now = datetime.now()
        return ValueSystemPriority.query.filter(
            ValueSystemPriority.start_time <= now,
            ValueSystemPriority.end_time >= now
        ).all()

    def get_period_by_type(self, period_type):
        """Get priorities for specific period type"""
        return ValueSystemPriority.query.filter_by(period=period_type).all()

    def __repr__(self):
        return f'<ValueSystemPriority {self.id}: {self.name} ({self.start_time} - {self.end_time})>'


class ValueSystemPriorityValueGoalMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value_system_priority_id = db.Column(db.Integer, db.ForeignKey('value_system_priority.id'))
    value_goal_id = db.Column(db.Integer, db.ForeignKey('value_goal.id'))


class MetaActionCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    root = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('meta_action_category.id'))
    children = db.relationship('MetaActionCategory', backref=db.backref('parent', remote_side=[id]))
    meta_actions = db.relationship('MetaAction', secondary='meta_action_category_mapping', back_populates='categories')


class MetaActionCategoryMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meta_action_id = db.Column(db.Integer, db.ForeignKey('meta_action.id'))
    meta_action_category_id = db.Column(db.Integer, db.ForeignKey('meta_action_category.id'))



class InteractionStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    meta_action_id = db.Column(db.Integer, db.ForeignKey('meta_action.id'))
    meta_action = db.relationship('MetaAction', back_populates='interaction_statuses')
    interacting_action_id = db.Column(db.Integer, db.ForeignKey('meta_action.id'))
    interacting_action = db.relationship('MetaAction', foreign_keys=[interacting_action_id])

    # Add unique constraint to prevent duplicate relationships
    __table_args__ = (
        db.UniqueConstraint('meta_action_id', 'interacting_action_id', name='uq_interaction_status'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validate_unique_relationship()

    def validate_unique_relationship(self):
        """Validate that the relationship doesn't already exist in either direction"""
        if self.meta_action_id and self.interacting_action_id:
            # Check for existing relationship in either direction
            existing = InteractionStatus.query.filter(
                db.or_(
                    db.and_(
                        InteractionStatus.meta_action_id == self.meta_action_id,
                        InteractionStatus.interacting_action_id == self.interacting_action_id
                    ),
                    db.and_(
                        InteractionStatus.meta_action_id == self.interacting_action_id,
                        InteractionStatus.interacting_action_id == self.meta_action_id
                    )
                )
            ).first()
            if existing:
                raise ValueError("This relationship already exists")

    @classmethod
    def get_related_actions(cls, action_id):
        """Get all related actions for a given action_id, regardless of direction"""
        return cls.query.filter(
            db.or_(
                cls.meta_action_id == action_id,
                cls.interacting_action_id == action_id
            )
        ).all()


class MetaAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    effectiveness = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Boolean, default=True)
    recommendation = db.Column(db.Boolean, default=True)
    categories = db.relationship('MetaActionCategory', secondary='meta_action_category_mapping', back_populates='meta_actions')
    value_goal_mappings = db.relationship('MetaActionValueGoalMapping', back_populates='meta_action')
    value_goals = db.relationship('ValueGoal', secondary='meta_action_value_goal_mapping', back_populates='meta_actions')
    interaction_statuses = db.relationship('InteractionStatus', back_populates='meta_action')
    interacting_actions = db.relationship('InteractionStatus', foreign_keys=[InteractionStatus.interacting_action_id])

    def get_all_related_actions(self):
        """Get all actions that interact with this action, regardless of direction"""
        return InteractionStatus.get_related_actions(self.id)


class MetaActionValueGoalMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meta_action_id = db.Column(db.Integer, db.ForeignKey('meta_action.id'))
    value_goal_id = db.Column(db.Integer, db.ForeignKey('value_goal.id'))
    weight = db.Column(db.Float, nullable=False, default=1.0)  # Strength of causation
    confidence = db.Column(db.Float, nullable=False, default=0.5)  # Confidence in causation
    time_lag = db.Column(db.Float, nullable=False, default=0.0)  # Time delay in causation
    evidence_count = db.Column(db.Integer, nullable=False, default=0)  # Number of supporting evidence
    last_updated = db.Column(db.DateTime, nullable=False)  # Last time this relationship was updated
    
    meta_action = db.relationship('MetaAction', back_populates='value_goal_mappings')
    value_goal = db.relationship('ValueGoal', back_populates='meta_action_mappings')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import datetime
        if not self.last_updated:
            self.last_updated = datetime.now()


class ActionStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    planned_start_at = db.Column(db.DateTime, nullable=False)
    planned_end_at = db.Column(db.DateTime, nullable=False)
    actual_start_at = db.Column(db.DateTime)
    actual_end_at = db.Column(db.DateTime)
    status = db.Column(db.String(255), nullable=False)
    achievement_rate = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    action_plan_id = db.Column(db.Integer, db.ForeignKey('action_plan.id'))
    action_plan = db.relationship('ActionPlan', back_populates='action_statuses')
    meta_action_id = db.Column(db.Integer, db.ForeignKey('meta_action.id'))
    meta_action = db.relationship('MetaAction')

    def update_action_plan_times(self):
        """Update the parent ActionPlan's start_time and end_time"""
        if self.action_plan:
            self.action_plan.update_times()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.created_at:
            self.created_at = db.func.now()
        self.update_action_plan_times()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name in ['actual_start_at', 'actual_end_at'] and self.action_plan:
            self.update_action_plan_times()


class ActionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    meta_actions = db.relationship('MetaAction', secondary='action_plan_meta_action_mapping', backref='action_plans')
    action_statuses = db.relationship('ActionStatus', back_populates='action_plan')

    def update_times(self):
        """Update start_time and end_time based on action_statuses"""
        if not self.action_statuses:
            return

        # Get all actual start and end times that are not None
        start_times = [status.actual_start_at for status in self.action_statuses if status.actual_start_at]
        end_times = [status.actual_end_at for status in self.action_statuses if status.actual_end_at]

        if start_times:
            self.start_time = min(start_times)
        if end_times:
            self.end_time = max(end_times)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.created_at:
            self.created_at = db.func.now()


class ActionPlanMetaActionMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action_plan_id = db.Column(db.Integer, db.ForeignKey('action_plan.id'))
    meta_action_id = db.Column(db.Integer, db.ForeignKey('meta_action.id'))
