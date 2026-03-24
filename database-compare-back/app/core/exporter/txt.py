"""TXT报告导出器"""
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path


class TXTExporter:
    """TXT纯文本报告导出器"""
    
    def export(self, result_data: Dict[str, Any], output_path: str) -> str:
        """导出TXT报告"""
        content = self._generate_content(result_data)
        
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def _generate_content(self, result_data: Dict[str, Any]) -> str:
        """生成TXT内容"""
        lines = []
        
        summary = result_data.get('summary', {})
        structure_diffs = result_data.get('structure_diffs', [])
        data_diffs = result_data.get('data_diffs', [])
        source_info = result_data.get('source_info', {})
        target_info = result_data.get('target_info', {})
        
        # 标题
        lines.append("=" * 80)
        lines.append("                    数据库自动化比对报告")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 数据源信息
        lines.append("-" * 80)
        lines.append("【数据源信息】")
        lines.append("-" * 80)
        lines.append("")
        lines.append("源数据库:")
        lines.append(f"  类型: {source_info.get('db_type', '-')}")
        lines.append(f"  地址: {source_info.get('host', '-')}")
        lines.append(f"  端口: {source_info.get('port', '-')}")
        lines.append(f"  数据库: {source_info.get('database', '-')}")
        lines.append("")
        lines.append("目标数据库:")
        lines.append(f"  类型: {target_info.get('db_type', '-')}")
        lines.append(f"  地址: {target_info.get('host', '-')}")
        lines.append(f"  端口: {target_info.get('port', '-')}")
        lines.append(f"  数据库: {target_info.get('database', '-')}")
        lines.append("")
        
        # 比对汇总
        lines.append("-" * 80)
        lines.append("【比对汇总】")
        lines.append("-" * 80)
        lines.append("")
        lines.append(f"  比对表总数: {summary.get('total_tables', 0)}")
        lines.append(f"  结构一致表: {summary.get('structure_same_count', 0)}")
        lines.append(f"  结构差异表: {summary.get('structure_diff_count', 0)}")
        lines.append(f"  数据一致表: {summary.get('data_same_count', 0)}")
        lines.append(f"  数据差异表: {summary.get('data_diff_count', 0)}")
        lines.append(f"  比对耗时: {summary.get('elapsed_time', '-')}")
        lines.append("")
        
        # 结构差异明细
        lines.append("-" * 80)
        lines.append(f"【结构差异明细】 共 {len(structure_diffs)} 条")
        lines.append("-" * 80)
        lines.append("")
        
        if not structure_diffs:
            lines.append("  无结构差异")
        else:
            for i, diff in enumerate(structure_diffs[:200], 1):
                lines.append(f"  [{i}] 表名: {diff.get('table_name', '-')}")
                lines.append(f"      差异类型: {diff.get('diff_type', '-')}")
                if diff.get('field_name'):
                    lines.append(f"      字段名: {diff.get('field_name')}")
                if diff.get('source_value'):
                    lines.append(f"      源库值: {diff.get('source_value')}")
                if diff.get('target_value'):
                    lines.append(f"      目标库值: {diff.get('target_value')}")
                lines.append(f"      差异说明: {diff.get('diff_detail', '-')}")
                lines.append("")
            
            if len(structure_diffs) > 200:
                lines.append(f"  ... 还有 {len(structure_diffs) - 200} 条差异未显示")
                lines.append("")
        
        # 数据差异明细
        lines.append("-" * 80)
        lines.append(f"【数据差异明细】 共 {len(data_diffs)} 条")
        lines.append("-" * 80)
        lines.append("")
        
        if not data_diffs:
            lines.append("  无数据差异")
        else:
            for i, diff in enumerate(data_diffs[:200], 1):
                lines.append(f"  [{i}] 表名: {diff.get('table_name', '-')}")
                lines.append(f"      差异类型: {diff.get('diff_type', '-')}")
                lines.append(f"      主键值: {diff.get('primary_key', {})}")
                if diff.get('diff_columns'):
                    lines.append(f"      差异字段: {', '.join(diff.get('diff_columns', []))}")
                if diff.get('source_values'):
                    source_str = str(diff.get('source_values', {}))[:100]
                    lines.append(f"      源库值: {source_str}")
                if diff.get('target_values'):
                    target_str = str(diff.get('target_values', {}))[:100]
                    lines.append(f"      目标库值: {target_str}")
                lines.append("")
            
            if len(data_diffs) > 200:
                lines.append(f"  ... 还有 {len(data_diffs) - 200} 条差异未显示")
                lines.append("")
        
        # 结论
        lines.append("-" * 80)
        lines.append("【比对结论】")
        lines.append("-" * 80)
        lines.append("")
        
        if len(structure_diffs) == 0 and len(data_diffs) == 0:
            lines.append("  ✓ 所有比对表结构一致，数据一致，比对通过！")
        else:
            if len(structure_diffs) > 0:
                lines.append(f"  ✗ 发现 {len(structure_diffs)} 条结构差异")
            if len(data_diffs) > 0:
                lines.append(f"  ✗ 发现 {len(data_diffs)} 条数据差异")
            lines.append("")
            lines.append("  请检查差异明细，确认是否需要处理。")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("                        报告结束")
        lines.append("=" * 80)
        
        return '\n'.join(lines)
