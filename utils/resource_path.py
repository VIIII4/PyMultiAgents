# resource_path.py
# 用于处理打包后的资源路径

import os
import sys
from typing import Optional

def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，兼容PyOxidizer打包环境
    
    Args:
        relative_path: 相对于应用根目录的路径
        
    Returns:
        资源文件的绝对路径
    """
    # 判断是否在打包环境中运行
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller打包环境
        base_path = sys._MEIPASS
    elif getattr(sys, 'oxidized', False):
        # PyOxidizer打包环境
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)

def ensure_dir_exists(dir_path: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        dir_path: 目录路径
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def get_logs_dir() -> str:
    """
    获取日志目录路径，确保目录存在
    
    Returns:
        日志目录的绝对路径
    """
    logs_dir = get_resource_path('logs')
    ensure_dir_exists(logs_dir)
    return logs_dir

def get_config_path(filename: Optional[str] = None) -> str:
    """
    获取配置文件路径
    
    Args:
        filename: 配置文件名，如果为None则返回配置目录
        
    Returns:
        配置文件或目录的绝对路径
    """
    config_dir = get_resource_path('config')
    ensure_dir_exists(config_dir)
    
    if filename:
        return os.path.join(config_dir, filename)
    return config_dir