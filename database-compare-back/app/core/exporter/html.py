"""HTML报告导出器"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import html


class HTMLExporter:
    """HTML报告导出器"""
    
    def __init__(self):
        self.template = self._get_template()
    
    def export(self, result_data: Dict[str, Any], output_path: str) -> str:
        """导出HTML报告"""
        html_content = self._generate_html(result_data)
        
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_html(self, result_data: Dict[str, Any]) -> str:
        """生成HTML内容"""
        summary = result_data.get('summary', {})
        structure_diffs = result_data.get('structure_diffs', [])
        data_diffs = result_data.get('data_diffs', [])
        source_info = result_data.get('source_info', {})
        target_info = result_data.get('target_info', {})
        
        # 生成结构差异表格
        structure_rows = self._generate_structure_rows(structure_diffs)
        
        # 生成数据差异表格
        data_rows = self._generate_data_rows(data_diffs)
        
        # 填充模板
        html_content = self.template.format(
            title="数据库比对报告",
            generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source_db_type=source_info.get('db_type', '-'),
            source_host=source_info.get('host', '-'),
            source_database=source_info.get('database', '-'),
            target_db_type=target_info.get('db_type', '-'),
            target_host=target_info.get('host', '-'),
            target_database=target_info.get('database', '-'),
            total_tables=summary.get('total_tables', 0),
            structure_same=summary.get('structure_same_count', 0),
            structure_diff=summary.get('structure_diff_count', 0),
            data_same=summary.get('data_same_count', 0),
            data_diff=summary.get('data_diff_count', 0),
            structure_rows=structure_rows,
            data_rows=data_rows,
            structure_diff_count=len(structure_diffs),
            data_diff_count=len(data_diffs)
        )
        
        return html_content
    
    def _generate_structure_rows(self, structure_diffs: List[Dict]) -> str:
        """生成结构差异行"""
        if not structure_diffs:
            return '<tr><td colspan="6" class="no-data">无结构差异</td></tr>'
        
        rows = []
        for diff in structure_diffs[:500]:  # 限制最多500条
            rows.append(f'''
                <tr>
                    <td>{html.escape(str(diff.get('table_name', '')))}</td>
                    <td>{html.escape(str(diff.get('diff_type', '')))}</td>
                    <td>{html.escape(str(diff.get('field_name', '-')))}</td>
                    <td>{html.escape(str(diff.get('source_value', '-')))}</td>
                    <td>{html.escape(str(diff.get('target_value', '-')))}</td>
                    <td>{html.escape(str(diff.get('diff_detail', '')))}</td>
                </tr>
            ''')
        
        if len(structure_diffs) > 500:
            rows.append(f'<tr><td colspan="6" class="more-info">... 还有 {len(structure_diffs) - 500} 条差异未显示</td></tr>')
        
        return '\n'.join(rows)
    
    def _generate_data_rows(self, data_diffs: List[Dict]) -> str:
        """生成数据差异行"""
        if not data_diffs:
            return '<tr><td colspan="6" class="no-data">无数据差异</td></tr>'
        
        rows = []
        for diff in data_diffs[:500]:  # 限制最多500条
            pk_str = str(diff.get('primary_key', {}))
            diff_cols = ', '.join(diff.get('diff_columns', [])) or '-'
            source_vals = str(diff.get('source_values', {}))[:100]
            target_vals = str(diff.get('target_values', {}))[:100]
            
            rows.append(f'''
                <tr>
                    <td>{html.escape(str(diff.get('table_name', '')))}</td>
                    <td>{html.escape(str(diff.get('diff_type', '')))}</td>
                    <td>{html.escape(pk_str[:50])}</td>
                    <td>{html.escape(diff_cols)}</td>
                    <td>{html.escape(source_vals)}</td>
                    <td>{html.escape(target_vals)}</td>
                </tr>
            ''')
        
        if len(data_diffs) > 500:
            rows.append(f'<tr><td colspan="6" class="more-info">... 还有 {len(data_diffs) - 500} 条差异未显示</td></tr>')
        
        return '\n'.join(rows)
    
    def _get_template(self) -> str:
        """获取HTML模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #1890ff;
        }}
        .header h1 {{
            color: #1890ff;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .time {{
            color: #666;
            font-size: 14px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 18px;
            color: #333;
            padding: 10px 15px;
            background: #f0f5ff;
            border-left: 4px solid #1890ff;
            margin-bottom: 15px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        .info-card {{
            background: #fafafa;
            border-radius: 4px;
            padding: 15px;
        }}
        .info-card h3 {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }}
        .info-card .value {{
            font-size: 16px;
            color: #333;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 15px;
        }}
        .summary-card {{
            text-align: center;
            padding: 20px;
            border-radius: 4px;
            background: #f0f5ff;
        }}
        .summary-card.success {{
            background: #f6ffed;
            border: 1px solid #b7eb8f;
        }}
        .summary-card.error {{
            background: #fff2f0;
            border: 1px solid #ffccc7;
        }}
        .summary-card .number {{
            font-size: 32px;
            font-weight: bold;
            color: #1890ff;
        }}
        .summary-card.success .number {{
            color: #52c41a;
        }}
        .summary-card.error .number {{
            color: #ff4d4f;
        }}
        .summary-card .label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px 8px;
            text-align: left;
            border-bottom: 1px solid #e8e8e8;
        }}
        th {{
            background: #fafafa;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .no-data {{
            text-align: center;
            color: #999;
            padding: 40px !important;
        }}
        .more-info {{
            text-align: center;
            color: #1890ff;
            font-style: italic;
        }}
        .footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e8e8e8;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="time">生成时间: {generated_time}</div>
        </div>
        
        <div class="section">
            <div class="section-title">数据源信息</div>
            <div class="info-grid">
                <div class="info-card">
                    <h3>源数据库</h3>
                    <div class="value">
                        <strong>类型:</strong> {source_db_type}<br>
                        <strong>地址:</strong> {source_host}<br>
                        <strong>数据库:</strong> {source_database}
                    </div>
                </div>
                <div class="info-card">
                    <h3>目标数据库</h3>
                    <div class="value">
                        <strong>类型:</strong> {target_db_type}<br>
                        <strong>地址:</strong> {target_host}<br>
                        <strong>数据库:</strong> {target_database}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">比对汇总</div>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="number">{total_tables}</div>
                    <div class="label">比对表总数</div>
                </div>
                <div class="summary-card success">
                    <div class="number">{structure_same}</div>
                    <div class="label">结构一致</div>
                </div>
                <div class="summary-card error">
                    <div class="number">{structure_diff}</div>
                    <div class="label">结构差异</div>
                </div>
                <div class="summary-card success">
                    <div class="number">{data_same}</div>
                    <div class="label">数据一致</div>
                </div>
                <div class="summary-card error">
                    <div class="number">{data_diff}</div>
                    <div class="label">数据差异</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">结构差异明细 ({structure_diff_count}条)</div>
            <table>
                <thead>
                    <tr>
                        <th>表名</th>
                        <th>差异类型</th>
                        <th>字段名</th>
                        <th>源库值</th>
                        <th>目标库值</th>
                        <th>差异说明</th>
                    </tr>
                </thead>
                <tbody>
                    {structure_rows}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <div class="section-title">数据差异明细 ({data_diff_count}条)</div>
            <table>
                <thead>
                    <tr>
                        <th>表名</th>
                        <th>差异类型</th>
                        <th>主键值</th>
                        <th>差异字段</th>
                        <th>源库值</th>
                        <th>目标库值</th>
                    </tr>
                </thead>
                <tbody>
                    {data_rows}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            数据库自动化比对工具 - 报告由系统自动生成
        </div>
    </div>
</body>
</html>'''
