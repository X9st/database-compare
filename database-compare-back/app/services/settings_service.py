"""设置服务"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
import json

from app.models.settings import IgnoreRule, CompareTemplate, SystemSetting
from app.schemas.settings import (
    CreateIgnoreRuleRequest, UpdateIgnoreRuleRequest, IgnoreRuleResponse,
    CreateTemplateRequest, UpdateTemplateRequest, TemplateResponse, TemplateConfig,
    SystemSettings, UpdateSystemSettingsRequest
)


class SettingsService:
    """设置服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 忽略规则 ====================
    
    def get_ignore_rules(self) -> List[IgnoreRuleResponse]:
        """获取忽略规则列表"""
        rules = self.db.query(IgnoreRule).order_by(IgnoreRule.created_at.desc()).all()
        return [IgnoreRuleResponse(
            id=r.id,
            name=r.name,
            rule_type=r.rule_type,
            pattern=r.pattern,
            tables=r.tables,
            enabled=r.enabled,
            created_at=r.created_at
        ) for r in rules]
    
    def create_ignore_rule(self, data: CreateIgnoreRuleRequest) -> IgnoreRuleResponse:
        """创建忽略规则"""
        rule = IgnoreRule(
            id=str(uuid.uuid4()),
            name=data.name,
            rule_type=data.rule_type,
            pattern=data.pattern,
            tables=data.tables,
            enabled=data.enabled
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        return IgnoreRuleResponse(
            id=rule.id,
            name=rule.name,
            rule_type=rule.rule_type,
            pattern=rule.pattern,
            tables=rule.tables,
            enabled=rule.enabled,
            created_at=rule.created_at
        )
    
    def update_ignore_rule(self, rule_id: str, data: UpdateIgnoreRuleRequest) -> Optional[IgnoreRuleResponse]:
        """更新忽略规则"""
        rule = self.db.query(IgnoreRule).filter(IgnoreRule.id == rule_id).first()
        if not rule:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        self.db.commit()
        self.db.refresh(rule)
        
        return IgnoreRuleResponse(
            id=rule.id,
            name=rule.name,
            rule_type=rule.rule_type,
            pattern=rule.pattern,
            tables=rule.tables,
            enabled=rule.enabled,
            created_at=rule.created_at
        )
    
    def delete_ignore_rule(self, rule_id: str) -> bool:
        """删除忽略规则"""
        rule = self.db.query(IgnoreRule).filter(IgnoreRule.id == rule_id).first()
        if not rule:
            return False
        
        self.db.delete(rule)
        self.db.commit()
        return True
    
    def toggle_ignore_rule(self, rule_id: str, enabled: bool) -> bool:
        """启用/禁用忽略规则"""
        rule = self.db.query(IgnoreRule).filter(IgnoreRule.id == rule_id).first()
        if not rule:
            return False
        
        rule.enabled = enabled
        self.db.commit()
        return True
    
    # ==================== 比对模板 ====================
    
    def get_templates(self) -> List[TemplateResponse]:
        """获取模板列表"""
        templates = self.db.query(CompareTemplate).order_by(
            CompareTemplate.created_at.desc()
        ).all()
        
        return [TemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            config=TemplateConfig(**(t.config or {})),
            created_at=t.created_at,
            updated_at=t.updated_at
        ) for t in templates]
    
    def get_template(self, template_id: str) -> Optional[TemplateResponse]:
        """获取单个模板"""
        t = self.db.query(CompareTemplate).filter(
            CompareTemplate.id == template_id
        ).first()
        
        if not t:
            return None
        
        return TemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            config=TemplateConfig(**(t.config or {})),
            created_at=t.created_at,
            updated_at=t.updated_at
        )
    
    def create_template(self, data: CreateTemplateRequest) -> TemplateResponse:
        """创建模板"""
        template = CompareTemplate(
            id=str(uuid.uuid4()),
            name=data.name,
            description=data.description,
            config=data.config.model_dump()
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return TemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            config=TemplateConfig(**(template.config or {})),
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    
    def update_template(self, template_id: str, data: UpdateTemplateRequest) -> Optional[TemplateResponse]:
        """更新模板"""
        template = self.db.query(CompareTemplate).filter(
            CompareTemplate.id == template_id
        ).first()
        
        if not template:
            return None
        
        if data.name is not None:
            template.name = data.name
        if data.description is not None:
            template.description = data.description
        if data.config is not None:
            template.config = data.config.model_dump()
        
        self.db.commit()
        self.db.refresh(template)
        
        return TemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            config=TemplateConfig(**(template.config or {})),
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        template = self.db.query(CompareTemplate).filter(
            CompareTemplate.id == template_id
        ).first()
        
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True
    
    # ==================== 系统设置 ====================
    
    def get_system_settings(self) -> SystemSettings:
        """获取系统设置"""
        settings = {}
        for setting in self.db.query(SystemSetting).all():
            try:
                settings[setting.key] = json.loads(setting.value)
            except:
                settings[setting.key] = setting.value
        
        return SystemSettings(**settings)
    
    def update_system_settings(self, data: UpdateSystemSettingsRequest) -> SystemSettings:
        """更新系统设置"""
        update_data = data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setting = self.db.query(SystemSetting).filter(
                SystemSetting.key == key
            ).first()
            
            if setting:
                setting.value = json.dumps(value)
            else:
                setting = SystemSetting(key=key, value=json.dumps(value))
                self.db.add(setting)
        
        self.db.commit()
        
        return self.get_system_settings()
