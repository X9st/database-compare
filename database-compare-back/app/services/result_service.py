"""结果服务"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from collections import Counter, defaultdict
import math
import json
from pathlib import Path
from datetime import datetime

from app.models.datasource import DataSource
from app.models.compare_task import CompareTask, CompareResult, StructureDiff, DataDiff
from app.core.exporter import ExcelExporter, HTMLExporter, TXTExporter
from app.schemas.result import (
    CompareResultResponse, DataSourceSummary, ResultSummary,
    StructureDiffItem, DataDiffItem, TableCompareDetail,
    ResultCompareResponse, ResultCompareSummary, DiffCompareGroup
)
from app.schemas.common import PageInfo


class ResultService:
    """结果服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_result(self, result_id: str) -> Optional[CompareResultResponse]:
        """获取比对结果"""
        result = self.db.query(CompareResult).filter(
            CompareResult.id == result_id
        ).first()
        
        if not result:
            return None
        
        # 获取任务信息
        task = self.db.query(CompareTask).filter(
            CompareTask.id == result.task_id
        ).first()
        
        if not task:
            return None
        
        # 获取数据源信息
        source_ds = self.db.query(DataSource).filter(
            DataSource.id == task.source_id
        ).first()
        target_ds = self.db.query(DataSource).filter(
            DataSource.id == task.target_id
        ).first()
        
        # 计算耗时
        duration = None
        if task.started_at and task.completed_at:
            duration = int((task.completed_at - task.started_at).total_seconds())
        
        summary = result.summary or {}
        
        return CompareResultResponse(
            result_id=result.id,
            task_id=task.id,
            status=task.status,
            source_db=DataSourceSummary(
                id=source_ds.id,
                name=source_ds.name,
                db_type=source_ds.db_type
            ) if source_ds else None,
            target_db=DataSourceSummary(
                id=target_ds.id,
                name=target_ds.name,
                db_type=target_ds.db_type
            ) if target_ds else None,
            start_time=task.started_at,
            end_time=task.completed_at,
            duration_seconds=duration,
            summary=ResultSummary(
                total_tables=summary.get('total_tables', 0),
                structure_match_tables=summary.get('structure_match_tables', 0),
                structure_diff_tables=summary.get('structure_diff_tables', 0),
                data_match_tables=summary.get('data_match_tables', 0),
                data_diff_tables=summary.get('data_diff_tables', 0),
                no_diff_tables=summary.get('no_diff_tables', 0),
                total_structure_diffs=summary.get('total_structure_diffs', 0),
                total_data_diffs=summary.get('total_data_diffs', 0),
                structure_diff_type_counts=summary.get('structure_diff_type_counts', {}) or {},
                data_diff_type_counts=summary.get('data_diff_type_counts', {}) or {},
            )
        )
    
    def get_structure_diffs(self, result_id: str, table_name: str = None,
                            diff_type: str = None, page: int = 1, 
                            page_size: int = 20) -> tuple[List[StructureDiffItem], PageInfo]:
        """获取结构差异列表"""
        query = self.db.query(StructureDiff).filter(
            StructureDiff.result_id == result_id
        )
        
        if table_name:
            query = query.filter(StructureDiff.table_name == table_name)
        if diff_type:
            query = query.filter(StructureDiff.diff_type == diff_type)
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        diffs = query.offset(offset).limit(page_size).all()
        
        items = [StructureDiffItem(
            id=d.id,
            table_name=d.table_name,
            diff_type=d.diff_type,
            field_name=d.field_name,
            source_value=d.source_value,
            target_value=d.target_value,
            diff_detail=d.diff_detail
        ) for d in diffs]
        
        page_info = PageInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0
        )
        
        return items, page_info
    
    def get_data_diffs(self, result_id: str, table_name: str = None,
                       diff_type: str = None, page: int = 1,
                       page_size: int = 20) -> tuple[List[DataDiffItem], PageInfo]:
        """获取数据差异列表"""
        query = self.db.query(DataDiff).filter(
            DataDiff.result_id == result_id
        )
        
        if table_name:
            query = query.filter(DataDiff.table_name == table_name)
        if diff_type:
            query = query.filter(DataDiff.diff_type == diff_type)
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        diffs = query.offset(offset).limit(page_size).all()
        
        items = [DataDiffItem(
            id=d.id,
            table_name=d.table_name,
            primary_key=d.primary_key,
            diff_type=d.diff_type,
            diff_columns=d.diff_columns or [],
            source_values=d.source_values,
            target_values=d.target_values
        ) for d in diffs]
        
        page_info = PageInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0
        )
        
        return items, page_info
    
    def get_table_detail(self, result_id: str, table_name: str) -> Optional[TableCompareDetail]:
        """获取单表比对详情"""
        result = self.db.query(CompareResult).filter(
            CompareResult.id == result_id
        ).first()
        
        if not result:
            return None

        task = self.db.query(CompareTask).filter(
            CompareTask.id == result.task_id
        ).first()
        progress = (task.progress if task else {}) or {}
        table_stats = progress.get("table_stats", {}) if isinstance(progress, dict) else {}
        stat = table_stats.get(table_name, {}) if isinstance(table_stats, dict) else {}
        source_row_count = int(stat.get("source_row_count", 0) or 0)
        target_row_count = int(stat.get("target_row_count", 0) or 0)
        compare_time_ms = int(stat.get("compare_time_ms", 0) or 0)

        # 兼容历史结果：若无表级快照，尝试从 row_count_diff 回填
        if source_row_count == 0 and target_row_count == 0:
            row_count_diff = (
                self.db.query(DataDiff)
                .filter(
                    DataDiff.result_id == result_id,
                    DataDiff.table_name == table_name,
                    DataDiff.diff_type == "row_count_diff",
                )
                .first()
            )
            if row_count_diff:
                source_row_count = int(((row_count_diff.source_values or {}).get("row_count", 0)) or 0)
                target_row_count = int(((row_count_diff.target_values or {}).get("row_count", 0)) or 0)
        
        # 统计结构差异数
        structure_count = self.db.query(StructureDiff).filter(
            StructureDiff.result_id == result_id,
            StructureDiff.table_name == table_name
        ).count()
        
        # 统计数据差异数
        data_count = self.db.query(DataDiff).filter(
            DataDiff.result_id == result_id,
            DataDiff.table_name == table_name
        ).count()
        
        return TableCompareDetail(
            table_name=table_name,
            structure_match=structure_count == 0,
            data_match=data_count == 0,
            source_row_count=source_row_count,
            target_row_count=target_row_count,
            structure_diffs_count=structure_count,
            data_diffs_count=data_count,
            compare_time_ms=compare_time_ms
        )

    def compare_results(self, baseline_result_id: str, current_result_id: str) -> ResultCompareResponse:
        """对比两次结果，输出新增/消除/不变差异"""
        baseline = self.db.query(CompareResult).filter(CompareResult.id == baseline_result_id).first()
        current = self.db.query(CompareResult).filter(CompareResult.id == current_result_id).first()
        if not baseline:
            raise ValueError(f"基线结果不存在: {baseline_result_id}")
        if not current:
            raise ValueError(f"当前结果不存在: {current_result_id}")

        baseline_structure = self.db.query(StructureDiff).filter(StructureDiff.result_id == baseline_result_id).all()
        current_structure = self.db.query(StructureDiff).filter(StructureDiff.result_id == current_result_id).all()
        baseline_data = self.db.query(DataDiff).filter(DataDiff.result_id == baseline_result_id).all()
        current_data = self.db.query(DataDiff).filter(DataDiff.result_id == current_result_id).all()

        (
            added_structure,
            resolved_structure,
            unchanged_structure,
        ) = self._diff_records(
            baseline_records=baseline_structure,
            current_records=current_structure,
            signature_fn=self._structure_signature,
            item_fn=self._to_structure_item,
        )
        (
            added_data,
            resolved_data,
            unchanged_data,
        ) = self._diff_records(
            baseline_records=baseline_data,
            current_records=current_data,
            signature_fn=self._data_signature,
            item_fn=self._to_data_item,
        )

        summary = ResultCompareSummary(
            added=len(added_structure) + len(added_data),
            resolved=len(resolved_structure) + len(resolved_data),
            unchanged=len(unchanged_structure) + len(unchanged_data),
            added_structure=len(added_structure),
            added_data=len(added_data),
            resolved_structure=len(resolved_structure),
            resolved_data=len(resolved_data),
            unchanged_structure=len(unchanged_structure),
            unchanged_data=len(unchanged_data),
        )

        return ResultCompareResponse(
            baseline_result_id=baseline_result_id,
            current_result_id=current_result_id,
            summary=summary,
            added=DiffCompareGroup(structure=added_structure, data=added_data),
            resolved=DiffCompareGroup(structure=resolved_structure, data=resolved_data),
            unchanged=DiffCompareGroup(structure=unchanged_structure, data=unchanged_data),
        )

    def export_compare_report(self, baseline_result_id: str, current_result_id: str, export_format: str = "txt") -> Dict[str, Any]:
        """导出结果对比结论"""
        export_format = (export_format or "txt").lower().strip()
        if export_format not in {"txt", "html", "excel"}:
            raise ValueError("不支持的导出格式，仅支持 txt/html/excel")

        compare_payload = self.compare_results(
            baseline_result_id=baseline_result_id,
            current_result_id=current_result_id,
        )
        report_payload, excel_payload = self._build_compare_export_payload(compare_payload)

        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ext = {"txt": "txt", "html": "html", "excel": "xlsx"}[export_format]
        filename = f"compare_delta_{baseline_result_id[:8]}_{current_result_id[:8]}_{timestamp}.{ext}"
        output_path = export_dir / filename

        if export_format == "txt":
            TXTExporter().export(report_payload, str(output_path))
        elif export_format == "html":
            HTMLExporter().export(report_payload, str(output_path))
        else:
            ExcelExporter().export_compare_result(
                result=excel_payload["result"],
                structure_diffs=excel_payload["structure_diffs"],
                data_diffs=excel_payload["data_diffs"],
                output_path=str(output_path),
            )

        file_size = output_path.stat().st_size
        return {
            "file_path": str(output_path),
            "file_name": filename,
            "file_size": file_size,
            "download_url": f"/api/v1/files/download/{filename}",
        }

    def export_result(self, result_id: str, export_format: str,
                      options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """导出比对结果"""
        export_format = export_format.lower().strip()
        if export_format not in {"excel", "html", "txt"}:
            raise ValueError("不支持的导出格式，仅支持 excel/html/txt")

        context = self._build_export_context(result_id, options or {})

        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        ext = {"excel": "xlsx", "html": "html", "txt": "txt"}[export_format]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"compare_result_{result_id}_{timestamp}.{ext}"
        output_path = export_dir / filename

        if export_format == "excel":
            ExcelExporter().export_compare_result(
                result=context["result"],
                structure_diffs=context["structure_diffs"],
                data_diffs=context["data_diffs"],
                output_path=str(output_path)
            )
        elif export_format == "html":
            HTMLExporter().export(context["report_payload"], str(output_path))
        else:
            TXTExporter().export(context["report_payload"], str(output_path))

        file_size = output_path.stat().st_size
        return {
            "file_path": str(output_path),
            "file_name": filename,
            "file_size": file_size,
            "download_url": f"/api/v1/files/download/{filename}"
        }

    def _build_export_context(self, result_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        result = self.db.query(CompareResult).filter(
            CompareResult.id == result_id
        ).first()
        if not result:
            raise ValueError("结果不存在")

        task = self.db.query(CompareTask).filter(
            CompareTask.id == result.task_id
        ).first()
        if not task:
            raise ValueError("关联任务不存在")

        source_ds = self.db.query(DataSource).filter(
            DataSource.id == task.source_id
        ).first()
        target_ds = self.db.query(DataSource).filter(
            DataSource.id == task.target_id
        ).first()

        include_structure_diffs = options.get("include_structure_diffs", True)
        include_data_diffs = options.get("include_data_diffs", True)
        max_data_diffs = options.get("max_data_diffs", 1000)
        tables = options.get("tables") or []

        structure_query = self.db.query(StructureDiff).filter(
            StructureDiff.result_id == result_id
        )
        data_query = self.db.query(DataDiff).filter(
            DataDiff.result_id == result_id
        )
        if tables:
            structure_query = structure_query.filter(StructureDiff.table_name.in_(tables))
            data_query = data_query.filter(DataDiff.table_name.in_(tables))

        structure_records = structure_query.all() if include_structure_diffs else []
        data_records = data_query.limit(max_data_diffs).all() if include_data_diffs else []

        structure_diffs = [{
            "id": item.id,
            "table_name": item.table_name,
            "diff_type": item.diff_type,
            "field_name": item.field_name,
            "source_value": item.source_value,
            "target_value": item.target_value,
            "diff_detail": item.diff_detail
        } for item in structure_records]
        data_diffs = [{
            "id": item.id,
            "table_name": item.table_name,
            "primary_key": item.primary_key or {},
            "diff_type": item.diff_type,
            "diff_columns": item.diff_columns or [],
            "source_values": item.source_values or {},
            "target_values": item.target_values or {}
        } for item in data_records]

        summary = result.summary or {}
        duration_seconds = None
        if task.started_at and task.completed_at:
            duration_seconds = int((task.completed_at - task.started_at).total_seconds())

        result_payload = {
            "result_id": result.id,
            "task_id": task.id,
            "source_db": {
                "id": source_ds.id if source_ds else "",
                "name": source_ds.name if source_ds else "",
                "db_type": source_ds.db_type if source_ds else ""
            },
            "target_db": {
                "id": target_ds.id if target_ds else "",
                "name": target_ds.name if target_ds else "",
                "db_type": target_ds.db_type if target_ds else ""
            },
            "duration_seconds": duration_seconds or 0,
            "summary": {
                "total_tables": summary.get("total_tables", 0),
                "structure_match_tables": summary.get("structure_match_tables", 0),
                "structure_diff_tables": summary.get("structure_diff_tables", 0),
                "data_match_tables": summary.get("data_match_tables", 0),
                "data_diff_tables": summary.get("data_diff_tables", 0),
                "total_structure_diffs": summary.get("total_structure_diffs", 0),
                "total_data_diffs": summary.get("total_data_diffs", 0),
            }
        }

        report_payload = {
            "summary": {
                "total_tables": summary.get("total_tables", 0),
                "structure_same_count": summary.get("structure_match_tables", 0),
                "structure_diff_count": summary.get("structure_diff_tables", 0),
                "data_same_count": summary.get("data_match_tables", 0),
                "data_diff_count": summary.get("data_diff_tables", 0),
                "elapsed_time": f"{duration_seconds or 0}s"
            },
            "structure_diffs": structure_diffs,
            "data_diffs": data_diffs,
            "source_info": {
                "name": source_ds.name if source_ds else "",
                "db_type": source_ds.db_type if source_ds else "",
                "host": source_ds.host if source_ds else "",
                "port": source_ds.port if source_ds else "",
                "database": source_ds.database if source_ds else ""
            },
            "target_info": {
                "name": target_ds.name if target_ds else "",
                "db_type": target_ds.db_type if target_ds else "",
                "host": target_ds.host if target_ds else "",
                "port": target_ds.port if target_ds else "",
                "database": target_ds.database if target_ds else ""
            }
        }

        return {
            "result": result_payload,
            "structure_diffs": structure_diffs,
            "data_diffs": data_diffs,
            "report_payload": report_payload
        }

    def _diff_records(self, baseline_records, current_records, signature_fn, item_fn):
        baseline_group = defaultdict(list)
        current_group = defaultdict(list)

        for record in baseline_records:
            baseline_group[signature_fn(record)].append(record)
        for record in current_records:
            current_group[signature_fn(record)].append(record)

        baseline_counter = Counter({k: len(v) for k, v in baseline_group.items()})
        current_counter = Counter({k: len(v) for k, v in current_group.items()})

        added_items = []
        resolved_items = []
        unchanged_items = []

        all_keys = set(baseline_counter.keys()) | set(current_counter.keys())
        for key in all_keys:
            base_count = baseline_counter.get(key, 0)
            curr_count = current_counter.get(key, 0)
            min_count = min(base_count, curr_count)
            if min_count > 0:
                unchanged_items.extend(item_fn(record) for record in current_group.get(key, [])[:min_count])
            if curr_count > base_count:
                extra = curr_count - base_count
                added_items.extend(item_fn(record) for record in current_group.get(key, [])[min_count:min_count + extra])
            if base_count > curr_count:
                extra = base_count - curr_count
                resolved_items.extend(item_fn(record) for record in baseline_group.get(key, [])[min_count:min_count + extra])

        return added_items, resolved_items, unchanged_items

    def _to_structure_item(self, record: StructureDiff) -> StructureDiffItem:
        return StructureDiffItem(
            id=record.id,
            table_name=record.table_name,
            diff_type=record.diff_type,
            field_name=record.field_name,
            source_value=record.source_value,
            target_value=record.target_value,
            diff_detail=record.diff_detail,
        )

    def _to_data_item(self, record: DataDiff) -> DataDiffItem:
        return DataDiffItem(
            id=record.id,
            table_name=record.table_name,
            primary_key=record.primary_key or {},
            diff_type=record.diff_type,
            diff_columns=record.diff_columns or [],
            source_values=record.source_values or {},
            target_values=record.target_values or {},
        )

    def _structure_signature(self, record: StructureDiff) -> str:
        field = record.field_name or ""
        source_value = record.source_value or ""
        target_value = record.target_value or ""
        detail = record.diff_detail or ""
        return "||".join([record.table_name, record.diff_type, field, source_value, target_value, detail])

    def _data_signature(self, record: DataDiff) -> str:
        primary_key = record.primary_key or {}
        diff_columns = record.diff_columns or []
        source_values = record.source_values or {}
        target_values = record.target_values or {}
        normalized = {
            "table_name": record.table_name,
            "diff_type": record.diff_type,
            "primary_key": primary_key,
            "diff_columns": sorted(diff_columns),
            "source_values": source_values,
            "target_values": target_values,
        }
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True, default=str)

    def _build_compare_export_payload(self, compare_payload: ResultCompareResponse) -> tuple[Dict[str, Any], Dict[str, Any]]:
        def to_structure_dict(item: StructureDiffItem, status: str) -> Dict[str, Any]:
            return {
                "id": item.id,
                "table_name": item.table_name,
                "diff_type": item.diff_type,
                "field_name": item.field_name,
                "source_value": item.source_value,
                "target_value": item.target_value,
                "diff_detail": f"[{status}] {item.diff_detail or ''}".strip(),
                "status": status,
            }

        def to_data_dict(item: DataDiffItem, status: str) -> Dict[str, Any]:
            return {
                "id": item.id,
                "table_name": item.table_name,
                "primary_key": item.primary_key,
                "diff_type": item.diff_type,
                "diff_columns": item.diff_columns or [],
                "source_values": item.source_values or {},
                "target_values": item.target_values or {},
                "status": status,
            }

        structure_diffs = (
            [to_structure_dict(item, "added") for item in compare_payload.added.structure]
            + [to_structure_dict(item, "resolved") for item in compare_payload.resolved.structure]
            + [to_structure_dict(item, "unchanged") for item in compare_payload.unchanged.structure]
        )
        data_diffs = (
            [to_data_dict(item, "added") for item in compare_payload.added.data]
            + [to_data_dict(item, "resolved") for item in compare_payload.resolved.data]
            + [to_data_dict(item, "unchanged") for item in compare_payload.unchanged.data]
        )

        summary = compare_payload.summary.model_dump()
        report_payload = {
            "summary": {
                "total_tables": 0,
                "structure_same_count": summary.get("unchanged_structure", 0),
                "structure_diff_count": summary.get("added_structure", 0) + summary.get("resolved_structure", 0),
                "data_same_count": summary.get("unchanged_data", 0),
                "data_diff_count": summary.get("added_data", 0) + summary.get("resolved_data", 0),
                "elapsed_time": "-",
            },
            "structure_diffs": structure_diffs,
            "data_diffs": data_diffs,
            "source_info": {
                "name": f"baseline:{compare_payload.baseline_result_id}",
                "db_type": "compare-result",
                "host": "-",
                "port": "-",
                "database": "-",
            },
            "target_info": {
                "name": f"current:{compare_payload.current_result_id}",
                "db_type": "compare-result",
                "host": "-",
                "port": "-",
                "database": "-",
            },
        }

        excel_payload = {
            "result": {
                "source_db": {"name": f"baseline:{compare_payload.baseline_result_id}"},
                "target_db": {"name": f"current:{compare_payload.current_result_id}"},
                "duration_seconds": 0,
                "summary": {
                    "total_tables": 0,
                    "structure_match_tables": summary.get("unchanged_structure", 0),
                    "structure_diff_tables": summary.get("added_structure", 0) + summary.get("resolved_structure", 0),
                    "data_match_tables": summary.get("unchanged_data", 0),
                    "data_diff_tables": summary.get("added_data", 0) + summary.get("resolved_data", 0),
                    "total_structure_diffs": len(structure_diffs),
                    "total_data_diffs": len(data_diffs),
                },
            },
            "structure_diffs": structure_diffs,
            "data_diffs": data_diffs,
        }

        return report_payload, excel_payload
