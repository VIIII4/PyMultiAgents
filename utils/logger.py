# utils/logger.py
# 日志工具模块

import os
import sys
import logging
from datetime import datetime


# 导入资源路径处理模块
try:
    from utils.resource_path import get_logs_dir
except ImportError:
    # 如果无法导入，使用默认路径处理
    def get_logs_dir():
        # 获取项目根目录
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # PyInstaller打包环境
            root_dir = sys._MEIPASS
        elif getattr(sys, 'oxidized', False):
            # PyOxidizer打包环境
            root_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            # 开发环境
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        log_dir = os.path.join(root_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

class AgentLogger:
    """Agent日志记录器，用于记录Agent的处理过程"""
    
    def __init__(self, log_dir=None):
        """初始化日志记录器
        
        Args:
            log_dir: 日志目录，默认为logs
        """
        # 创建日志目录
        if log_dir is None:
            log_dir = get_logs_dir()
        
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建日志文件名，使用当前时间
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"workflow_{timestamp}.log")
        
        # 配置日志记录器
        self.logger = logging.getLogger("agent_workflow")
        self.logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
    
    def log_step(self, step: int, agent: str, input_msg: str, output: str) -> None:
        """记录执行步骤
        
        Args:
            step: 步骤编号
            agent: Agent名称
            input_msg: 输入消息
            output: 输出结果
        """
        self.logger.info(f"===== 步骤 {step} =====")
        self.logger.info(f"Agent: {agent}")
        self.logger.info(f"输入: {input_msg}")
        self.logger.info(f"输出: {output}")
        self.logger.info("====================")
    
    def log_error(self, error: str) -> None:
        """记录错误信息
        
        Args:
            error: 错误信息
        """
        self.logger.error(f"错误: {error}")
    
    def log_workflow_start(self, initial_message: str) -> None:
        """记录工作流开始执行
        
        Args:
            initial_message: 初始消息
        """
        self.logger.info("========== 工作流开始执行 ===========")
        self.logger.info(f"初始消息: {initial_message}")
    
    def log_workflow_end(self, status: str, steps: int) -> None:
        """记录工作流执行结束
        
        Args:
            status: 执行状态
            steps: 执行步骤数
        """
        self.logger.info("========== 工作流执行结束 ===========")
        self.logger.info(f"状态: {status}")
        self.logger.info(f"执行步骤: {steps}")
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径
        
        Returns:
            日志文件路径
        """
        return self.log_file