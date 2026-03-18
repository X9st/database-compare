#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据存储模块
用于保存数据库连接配置等数据
"""

import os
import json
import uuid
from typing import Dict, List, Optional


class ConnectionStorage:
    """数据库连接配置存储"""
    
    def __init__(self):
        """初始化存储"""
        self.data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'data'
        )
        os.makedirs(self.data_dir, exist_ok=True)
        self.file_path = os.path.join(self.data_dir, 'connections.json')
    
    def _load_data(self) -> List[Dict]:
        """加载数据"""
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_data(self, data: List[Dict]):
        """保存数据"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_all(self) -> List[Dict]:
        """获取所有连接配置"""
        connections = self._load_data()
        # 移除密码字段，只返回脱敏后的数据
        for conn in connections:
            if 'password' in conn:
                conn['password'] = '********'
        return connections
    
    def get_by_id(self, connection_id: str) -> Optional[Dict]:
        """根据 ID 获取连接配置"""
        connections = self._load_data()
        for conn in connections:
            if conn.get('id') == connection_id:
                return conn
        return None
    
    def save(self, connection: Dict) -> Dict:
        """
        保存连接配置
        
        Args:
            connection: 连接配置字典
            
        Returns:
            保存后的连接配置（包含生成的 ID）
        """
        connections = self._load_data()
        
        # 如果已有 ID，则更新；否则新建
        if 'id' in connection and connection['id']:
            # 更新现有连接
            for i, conn in enumerate(connections):
                if conn.get('id') == connection['id']:
                    connections[i] = connection
                    break
            else:
                # 未找到，作为新连接添加
                connection['id'] = str(uuid.uuid4())
                connections.append(connection)
        else:
            # 新建连接
            connection['id'] = str(uuid.uuid4())
            connections.append(connection)
        
        self._save_data(connections)
        return connection
    
    def delete(self, connection_id: str):
        """
        删除连接配置
        
        Args:
            connection_id: 连接 ID
        """
        connections = self._load_data()
        connections = [c for c in connections if c.get('id') != connection_id]
        self._save_data(connections)
