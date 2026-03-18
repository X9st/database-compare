#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库比对工具 - Python 后端服务
基于 Flask 提供 RESTful API
"""

import os
import sys
import uuid
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from comparator import DatabaseComparator
from storage import ConnectionStorage
from report_generator import ReportGenerator

app = Flask(__name__)
CORS(app)

# 存储比对任务状态
tasks = {}
tasks_lock = threading.Lock()


def run_comparison_task(task_id, task_config):
    """在后台线程中执行比对任务"""
    try:
        with tasks_lock:
            tasks[task_id]['status'] = 'running'
            tasks[task_id]['progress'] = 10
        
        # 获取源数据库和目标数据库配置
        source_config = task_config.get('source')
        target_config = task_config.get('target')
        tables = task_config.get('tables', [])
        options = task_config.get('options', {})
        
        # 更新进度
        with tasks_lock:
            tasks[task_id]['progress'] = 30
        
        # 获取表名映射（如果提供了）
        table_mapping = task_config.get('table_mapping')
        
        # 执行比对
        comparator = DatabaseComparator(source_config, target_config)
        result = comparator.compare_all(
            table_names=tables,
            table_mapping=table_mapping,
            compare_structure=options.get('structure', True),
            compare_columns=options.get('columns', True),
            compare_data=options.get('data', False)
        )
        
        # 更新任务状态为完成
        with tasks_lock:
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['progress'] = 100
            tasks[task_id]['result'] = result
            tasks[task_id]['completed_at'] = datetime.now().isoformat()
            
    except Exception as e:
        with tasks_lock:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = str(e)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'Python 后端服务运行正常',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/databases/supported', methods=['GET'])
def get_supported_databases():
    """获取支持的数据库类型及驱动状态"""
    databases = []
    
    for db_type in ['mysql', 'postgresql', 'sqlite', 'dameng', 'inceptor', 'kingbase']:
        supported, message = DatabaseManager.check_driver_support(db_type)
        databases.append({
            'type': db_type,
            'name': DatabaseManager.DB_NAMES.get(db_type, db_type),
            'supported': supported,
            'message': message
        })
    
    return jsonify({
        'success': True,
        'databases': databases
    })


@app.route('/api/databases/test-connection', methods=['POST'])
def test_connection():
    """测试数据库连接"""
    try:
        config = request.json
        db_manager = DatabaseManager(config)
        success, message = db_manager.test_connection()
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'连接测试失败: {str(e)}'
        }), 500


@app.route('/api/databases/tables', methods=['POST'])
def get_tables():
    """获取数据库表列表"""
    try:
        config = request.json
        db_manager = DatabaseManager(config)
        tables = db_manager.get_tables()
        
        return jsonify({
            'success': True,
            'tables': tables
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取表列表失败: {str(e)}'
        }), 500


@app.route('/api/comparison/start', methods=['POST'])
def start_comparison():
    """启动比对任务"""
    try:
        task_config = request.json
        task_id = str(uuid.uuid4())
        
        # 创建比对任务
        with tasks_lock:
            tasks[task_id] = {
                'id': task_id,
                'status': 'pending',
                'progress': 0,
                'config': task_config,
                'result': None,
                'created_at': datetime.now().isoformat()
            }
        
        # 在后台线程中执行比对任务
        thread = threading.Thread(
            target=run_comparison_task,
            args=(task_id, task_config)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '比对任务已启动'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动比对任务失败: {str(e)}'
        }), 500


@app.route('/api/comparison/<task_id>/progress', methods=['GET'])
def get_progress(task_id):
    """获取比对任务进度"""
    if task_id not in tasks:
        return jsonify({
            'success': False,
            'message': '任务不存在'
        }), 404
    
    task = tasks[task_id]
    return jsonify({
        'success': True,
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress']
    })


@app.route('/api/comparison/<task_id>/result', methods=['GET'])
def get_result(task_id):
    """获取比对结果"""
    if task_id not in tasks:
        return jsonify({
            'success': False,
            'message': '任务不存在'
        }), 404
    
    task = tasks[task_id]
    return jsonify({
        'success': True,
        'task_id': task_id,
        'status': task['status'],
        'result': task['result']
    })


@app.route('/api/connections', methods=['GET'])
def get_connections():
    """获取所有保存的数据库连接"""
    try:
        storage = ConnectionStorage()
        connections = storage.get_all()
        return jsonify({
            'success': True,
            'connections': connections
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取连接列表失败: {str(e)}'
        }), 500


@app.route('/api/connections', methods=['POST'])
def save_connection():
    """保存数据库连接配置"""
    try:
        connection = request.json
        storage = ConnectionStorage()
        saved = storage.save(connection)
        
        return jsonify({
            'success': True,
            'connection': saved
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存连接失败: {str(e)}'
        }), 500


@app.route('/api/connections/<connection_id>', methods=['DELETE'])
def delete_connection(connection_id):
    """删除数据库连接配置"""
    try:
        storage = ConnectionStorage()
        storage.delete(connection_id)
        
        return jsonify({
            'success': True,
            'message': '连接已删除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除连接失败: {str(e)}'
        }), 500


@app.route('/api/comparison/<task_id>/export/<format>', methods=['GET'])
def export_report(task_id, format):
    """导出比对报告"""
    try:
        if task_id not in tasks:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        task = tasks[task_id]
        result = task.get('result')
        config = task.get('config', {})
        
        if not result:
            return jsonify({
                'success': False,
                'message': '任务尚未完成，无法导出报告'
            }), 400
        
        # 创建报告生成器
        generator = ReportGenerator(result, config)
        
        # 创建导出目录
        export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'html':
            # 生成 HTML 报告
            filename = f'comparison_report_{task_id[:8]}_{timestamp}.html'
            filepath = os.path.join(export_dir, filename)
            
            html_content = generator.generate_html()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return jsonify({
                'success': True,
                'format': 'html',
                'filename': filename,
                'path': filepath
            })
        
        elif format == 'excel':
            # 生成 Excel 报告
            filename = f'comparison_report_{task_id[:8]}_{timestamp}.xlsx'
            filepath = os.path.join(export_dir, filename)
            
            generator.generate_excel(filepath)
            
            return jsonify({
                'success': True,
                'format': 'excel',
                'filename': filename,
                'path': filepath
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的导出格式: {format}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'导出报告失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    # 确保数据目录存在
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 启动 Flask 服务
    app.run(host='127.0.0.1', port=5000, debug=False)
