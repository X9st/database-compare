"""设置服务"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import uuid

from sqlalchemy.orm import Session

from app.core.task.manager import TaskManager
from app.models.compare_task import CompareTask
from app.models.datasource import DataSource, DataSourceGroup
from app.models.settings import IgnoreRule, CompareTemplate, SystemSetting
from app.schemas.settings import (
    CreateIgnoreRuleRequest, UpdateIgnoreRuleRequest, IgnoreRuleResponse,
    CreateTemplateRequest, UpdateTemplateRequest, TemplateResponse, TemplateConfig,
    SystemSettings, UpdateSystemSettingsRequest, ExportConfigRequest
)
from app.utils.crypto import encrypt


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

    def create_task_from_template(self, template_id: str, override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """按模板创建 pending 任务（不自动启动）"""
        template = self.db.query(CompareTemplate).filter(
            CompareTemplate.id == template_id
        ).first()
        if not template:
            raise ValueError("模板不存在")

        template_config = template.config or {}
        merged_config = self._deep_merge(template_config, override or {})

        required_fields = ["source_id", "target_id", "table_selection", "options"]
        missing = [field for field in required_fields if not merged_config.get(field)]
        if missing:
            raise ValueError(f"模板配置不完整，缺少字段: {', '.join(missing)}")

        task = CompareTask(
            id=str(uuid.uuid4()),
            source_id=merged_config["source_id"],
            target_id=merged_config["target_id"],
            status="pending",
            config=merged_config
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        TaskManager().create_task(task_id=task.id)

        return {
            "task_id": task.id,
            "status": task.status,
            "created_at": task.created_at
        }

    # ==================== 系统设置 ====================

    def get_system_settings(self) -> SystemSettings:
        """获取系统设置"""
        settings = {}
        for setting in self.db.query(SystemSetting).all():
            try:
                settings[setting.key] = json.loads(setting.value)
            except Exception:
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

    # ==================== 配置导入导出 ====================

    def export_config(self, data: ExportConfigRequest) -> Dict[str, Any]:
        """导出配置文件"""
        export_data: Dict[str, Any] = {
            "config_version": "1.0.0",
            "exported_at": datetime.utcnow().isoformat(),
            "data": {}
        }

        if data.include_datasources:
            groups = self.db.query(DataSourceGroup).order_by(DataSourceGroup.sort_order).all()
            datasources = self.db.query(DataSource).order_by(DataSource.created_at.desc()).all()
            export_data["data"]["datasource_groups"] = [{
                "id": item.id,
                "name": item.name,
                "sort_order": item.sort_order
            } for item in groups]
            export_data["data"]["datasources"] = [{
                "id": item.id,
                "name": item.name,
                "group_id": item.group_id,
                "db_type": item.db_type,
                "host": item.host,
                "port": item.port,
                "database": item.database,
                "schema": item.schema,
                "username": item.username,
                "password_encrypted": item.password_encrypted,
                "charset": item.charset,
                "timeout": item.timeout,
                "extra_config": item.extra_config,
            } for item in datasources]

        if data.include_templates:
            templates = self.db.query(CompareTemplate).order_by(CompareTemplate.created_at.desc()).all()
            export_data["data"]["templates"] = [{
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "config": item.config,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
            } for item in templates]

        if data.include_rules:
            rules = self.db.query(IgnoreRule).order_by(IgnoreRule.created_at.desc()).all()
            export_data["data"]["ignore_rules"] = [{
                "id": item.id,
                "name": item.name,
                "rule_type": item.rule_type,
                "pattern": item.pattern,
                "tables": item.tables,
                "enabled": item.enabled,
                "created_at": item.created_at.isoformat() if item.created_at else None
            } for item in rules]

        if data.include_system_settings:
            setting_items = self.db.query(SystemSetting).all()
            export_data["data"]["system_settings"] = [{
                "key": item.key,
                "value": item.value
            } for item in setting_items]

        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"settings_export_{timestamp}.json"
        file_path = export_dir / file_name

        with file_path.open("w", encoding="utf-8") as fp:
            json.dump(export_data, fp, ensure_ascii=False, indent=2)

        return {
            "file_path": str(file_path),
            "file_name": file_name,
            "file_size": file_path.stat().st_size,
            "download_url": f"/api/v1/files/download/{file_name}"
        }

    def import_config(self, payload: Dict[str, Any]) -> Dict[str, int]:
        """导入配置文件"""
        if not isinstance(payload, dict):
            raise ValueError("配置内容必须是 JSON 对象")

        config_version = payload.get("config_version") or payload.get("version")
        if config_version and str(config_version).split(".")[0] != "1":
            raise ValueError(f"不支持的配置版本: {config_version}")

        data = payload.get("data", payload)
        if not isinstance(data, dict):
            raise ValueError("配置 data 字段格式错误")

        groups_imported = self._import_datasource_groups(data.get("datasource_groups", []))
        datasources_imported = self._import_datasources(data.get("datasources", []))
        templates_imported = self._import_templates(data.get("templates", []))
        rules_imported = self._import_rules(data.get("ignore_rules", []))
        system_settings_imported = self._import_system_settings(data.get("system_settings", []))

        self.db.commit()

        return {
            "datasource_groups_imported": groups_imported,
            "datasources_imported": datasources_imported,
            "templates_imported": templates_imported,
            "rules_imported": rules_imported,
            "system_settings_imported": system_settings_imported
        }

    def _import_datasource_groups(self, groups: List[Dict[str, Any]]) -> int:
        count = 0
        for item in groups or []:
            if not item.get("name"):
                continue
            group = None
            if item.get("id"):
                group = self.db.query(DataSourceGroup).filter(DataSourceGroup.id == item["id"]).first()
            if not group:
                group = self.db.query(DataSourceGroup).filter(DataSourceGroup.name == item["name"]).first()
            if not group:
                group = DataSourceGroup(id=item.get("id") or str(uuid.uuid4()))
                self.db.add(group)
            group.name = item["name"]
            group.sort_order = item.get("sort_order", group.sort_order or 0)
            count += 1
        return count

    def _import_datasources(self, datasources: List[Dict[str, Any]]) -> int:
        count = 0
        for item in datasources or []:
            db_type = str(item.get("db_type") or "").strip().lower()
            if not item.get("name") or not db_type:
                continue

            is_file_source = db_type in {"excel", "dbf"}
            if is_file_source:
                if not isinstance(item.get("extra_config"), dict):
                    continue
            else:
                required = ["host", "port", "database", "username"]
                if any(item.get(field) in (None, "") for field in required):
                    continue

            datasource = None
            if item.get("id"):
                datasource = self.db.query(DataSource).filter(DataSource.id == item["id"]).first()
            if not datasource:
                datasource = self.db.query(DataSource).filter(
                    DataSource.name == item["name"],
                    DataSource.db_type == db_type,
                    DataSource.host == item.get("host", "local-file" if is_file_source else ""),
                    DataSource.port == item.get("port", 0 if is_file_source else None),
                    DataSource.database == item.get("database", item["name"]),
                    DataSource.username == item.get("username", "file_user" if is_file_source else ""),
                ).first()
            if not datasource:
                datasource = DataSource(id=item.get("id") or str(uuid.uuid4()))
                self.db.add(datasource)

            datasource.name = item["name"]
            datasource.group_id = item.get("group_id")
            datasource.db_type = db_type
            datasource.host = item.get("host", "local-file" if is_file_source else datasource.host)
            datasource.port = item.get("port", 0 if is_file_source else datasource.port)
            datasource.database = item.get("database", item["name"])
            datasource.schema = item.get("schema")
            datasource.username = item.get("username", "file_user" if is_file_source else datasource.username)
            if item.get("password_encrypted"):
                datasource.password_encrypted = item["password_encrypted"]
            elif item.get("password"):
                datasource.password_encrypted = encrypt(item["password"])
            elif is_file_source and not datasource.password_encrypted:
                datasource.password_encrypted = encrypt("")
            datasource.charset = item.get("charset", datasource.charset or "UTF-8")
            datasource.timeout = item.get("timeout", datasource.timeout or 30)
            datasource.extra_config = item.get("extra_config")
            count += 1
        return count

    def _import_templates(self, templates: List[Dict[str, Any]]) -> int:
        count = 0
        for item in templates or []:
            if not item.get("name"):
                continue
            template = None
            if item.get("id"):
                template = self.db.query(CompareTemplate).filter(CompareTemplate.id == item["id"]).first()
            if not template:
                template = self.db.query(CompareTemplate).filter(CompareTemplate.name == item["name"]).first()
            if not template:
                template = CompareTemplate(id=item.get("id") or str(uuid.uuid4()))
                self.db.add(template)
            template.name = item["name"]
            template.description = item.get("description")
            template.config = item.get("config") or {}
            count += 1
        return count

    def _import_rules(self, rules: List[Dict[str, Any]]) -> int:
        count = 0
        for item in rules or []:
            if not item.get("name") or not item.get("rule_type") or not item.get("pattern"):
                continue
            rule = None
            if item.get("id"):
                rule = self.db.query(IgnoreRule).filter(IgnoreRule.id == item["id"]).first()
            if not rule:
                rule = self.db.query(IgnoreRule).filter(
                    IgnoreRule.name == item["name"],
                    IgnoreRule.rule_type == item["rule_type"],
                    IgnoreRule.pattern == item["pattern"]
                ).first()
            if not rule:
                rule = IgnoreRule(id=item.get("id") or str(uuid.uuid4()))
                self.db.add(rule)
            rule.name = item["name"]
            rule.rule_type = item["rule_type"]
            rule.pattern = item["pattern"]
            rule.tables = item.get("tables")
            rule.enabled = item.get("enabled", True)
            count += 1
        return count

    def _import_system_settings(self, settings: List[Dict[str, Any]]) -> int:
        count = 0
        for item in settings or []:
            key = item.get("key")
            if not key:
                continue
            setting = self.db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if not setting:
                setting = SystemSetting(key=key, value="")
                self.db.add(setting)

            value = item.get("value")
            if isinstance(value, str):
                setting.value = value
            else:
                setting.value = json.dumps(value, ensure_ascii=False)
            count += 1
        return count

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
