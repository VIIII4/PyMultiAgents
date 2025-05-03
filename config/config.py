# config.py
# 负责加载环境变量和配置

import os
import dotenv
from typing import Dict, Optional, List

# 导入资源路径处理模块
try:
    from utils.resource_path import get_config_path
except ImportError:
    # 如果无法导入，使用默认路径处理
    def get_config_path(filename=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if filename:
            return os.path.join(current_dir, filename)
        return current_dir

class Config:
    """配置管理类，负责加载和管理API密钥等配置"""
    
    def __init__(self, env_path: str = None):
        """初始化配置管理器
        
        Args:
            env_path: .env文件路径，默认为config/.env
        """
        if env_path is None:
            # 使用资源路径处理模块获取.env文件路径
            env_path = get_config_path('.env')
        
        # 加载环境变量
        self.loaded = dotenv.load_dotenv(env_path)
        if not self.loaded:
            print(f"警告: 无法加载环境变量文件: {env_path}")
            # 尝试加载示例配置
            example_env_path = get_config_path('.env.example')
            if os.path.exists(example_env_path):
                print(f"尝试加载示例配置: {example_env_path}")
                dotenv.load_dotenv(example_env_path)
    
    def get_api_key(self, api_type: str) -> Optional[str]:
        """获取指定类型的API密钥
        
        Args:
            api_type: API类型，如'openai', 'azure'等
            
        Returns:
            API密钥，如果不存在则返回None
        """
        api_type = api_type.lower()
        if api_type == 'openai':
            return os.getenv('OPENAI_API_KEY')
        elif api_type == 'azure':
            return os.getenv('AZURE_API_KEY')
        elif api_type == 'qwen':
            return os.getenv('QWEN_API_KEY')
        elif api_type == 'deepseek':
            return os.getenv('DEEPSEEK_API_KEY')
        elif api_type == 'openrouter':
            return os.getenv('OPENROUTER_API_KEY')
        elif api_type == 'siliconflow':
            return os.getenv('SILICONFLOW_API_KEY')
        return None
    
    def get_api_config(self, api_type: str) -> Dict[str, str]:
        """获取指定类型的API完整配置
        
        Args:
            api_type: API类型，如'openai', 'azure'等
            
        Returns:
            API配置字典
        """
        api_type = api_type.lower()
        config = {}
        
        if api_type == 'openai':
            config['api_key'] = os.getenv('OPENAI_API_KEY')
        elif api_type == 'azure':
            config['api_key'] = os.getenv('AZURE_API_KEY')
            config['api_base'] = os.getenv('AZURE_API_BASE')
            config['deployment_name'] = os.getenv('AZURE_DEPLOYMENT_NAME')
        elif api_type == 'qwen':
            config['api_key'] = os.getenv('QWEN_API_KEY')
            config['api_base'] = os.getenv('QWEN_API_BASE')
        elif api_type == 'deepseek':
            config['api_key'] = os.getenv('DEEPSEEK_API_KEY')
            config['api_base'] = os.getenv('DEEPSEEK_API_BASE')
        elif api_type == 'openrouter':
            config['api_key'] = os.getenv('OPENROUTER_API_KEY')
        elif api_type == 'siliconflow':
            config['api_key'] = os.getenv('SILICONFLOW_API_KEY')
            config['api_base'] = os.getenv('SILICONFLOW_API_BASE')
        
        return config
    
    def get_available_api_types(self) -> List[str]:
        """获取所有可用的API类型
        
        Returns:
            API类型列表
        """
        api_types = []
        if os.getenv('OPENAI_API_KEY'):
            api_types.append('openai')
        if os.getenv('AZURE_API_KEY'):
            api_types.append('azure')
        if os.getenv('QWEN_API_KEY'):
            api_types.append('qwen')
        if os.getenv('DEEPSEEK_API_KEY'):
            api_types.append('deepseek')
        if os.getenv('OPENROUTER_API_KEY'):
            api_types.append('openrouter')
        if os.getenv('SILICONFLOW_API_KEY'):
            api_types.append('siliconflow')
        return api_types

# 创建默认配置实例
config = Config()