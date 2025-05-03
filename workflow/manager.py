# manager.py
# 工作流管理器，负责保存和加载工作流配置

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class WorkflowManager:
    """工作流管理器，负责保存和加载工作流配置"""
    
    def __init__(self, config_dir: str = None):
        """初始化工作流管理器
        
        Args:
            config_dir: 配置文件目录，默认为'workflows'
        """
        if config_dir is None:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir = os.path.join(os.path.dirname(current_dir), 'workflows')
        else:
            self.config_dir = config_dir
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
    
    def save_workflow(self, name: str, workflow_text: str, description: str = "") -> bool:
        """保存工作流配置
        
        Args:
            name: 工作流名称
            workflow_text: 工作流定义文本
            description: 工作流描述
            
        Returns:
            保存是否成功
        """
        # 构建配置数据
        config = {
            "name": name,
            "description": description,
            "workflow": workflow_text,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 保存到文件
        file_path = os.path.join(self.config_dir, f"{name}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存工作流配置失败: {e}")
            return False
    
    def load_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        """加载工作流配置
        
        Args:
            name: 工作流名称
            
        Returns:
            工作流配置字典，如果不存在则返回None
        """
        file_path = os.path.join(self.config_dir, f"{name}.json")
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载工作流配置失败: {e}")
            return None
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有保存的工作流配置
        
        Returns:
            工作流配置列表
        """
        workflows = []
        for file_name in os.listdir(self.config_dir):
            if file_name.endswith('.json'):
                try:
                    with open(os.path.join(self.config_dir, file_name), 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        workflows.append({
                            "name": config.get("name", ""),
                            "description": config.get("description", ""),
                            "created_at": config.get("created_at", ""),
                            "updated_at": config.get("updated_at", "")
                        })
                except Exception:
                    pass
        return workflows
    
    def delete_workflow(self, name: str) -> bool:
        """删除工作流配置
        
        Args:
            name: 工作流名称
            
        Returns:
            删除是否成功
        """
        file_path = os.path.join(self.config_dir, f"{name}.json")
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"删除工作流配置失败: {e}")
            return False