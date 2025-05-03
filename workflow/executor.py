# executor.py
# 工作流执行器，负责执行解析后的工作流

import time
from typing import Dict, List, Any
from classAgent import Agent, AgentFactory
from .parser import WorkflowParser

class WorkflowExecutor:
    """工作流执行器，负责执行解析后的工作流"""
    
    def __init__(self, workflow_parser: WorkflowParser, agent_factory = None):
        """初始化工作流执行器
        
        Args:
            workflow_parser: 工作流解析器实例
            agent_factory: Agent工厂实例
        """
        self.parser = workflow_parser
        self.agent_factory = agent_factory or AgentFactory()
        self.agents = {}  # Agent字典，键为Agent名称，值为Agent实例
        self.execution_history = []  # 执行历史
        self.current_step = 0  # 当前执行步骤
        self.status = 'ready'  # 执行状态: ready, running, completed, error
        self.error = None  # 执行错误
        
        # 导入日志记录器
        try:
            from utils.logger import AgentLogger
            self.logger = AgentLogger()
        except ImportError:
            self.logger = None
    
    def add_agent(self, name: str, agent: Agent) -> None:
        """添加Agent到执行器
        
        Args:
            name: Agent名称
            agent: Agent实例
        """
        self.agents[name] = agent
        
    def create_agents(self, agent_configs: Dict[str, Dict[str, str]]) -> None:
        """根据配置创建所有Agent
        
        Args:
            agent_configs: Agent配置字典，键为Agent名称，值为配置字典
        """
        for agent_name, config in agent_configs.items():
            # 获取工作流中定义的Agent提示词
            prompt = self.parser.get_agent_prompt(agent_name)
            
            # 创建Agent实例
            agent = self.agent_factory.create_agent_from_params(
                name=agent_name,
                api_type=config.get('api_type', 'openai'),
                system_prompt=config.get('system_prompt', ''),
                prompt=prompt
            )
            
            # 添加到Agent字典
            self.agents[agent_name] = agent
    
    def execute(self, initial_message: str = None, max_steps: int = 100, timeout: int = 300) -> Dict[str, Any]:
        """执行整个工作流
        
        Args:
            initial_message: 初始消息，如果提供，将发送给第一个Agent
            max_steps: 最大执行步骤数，防止无限循环
            timeout: 执行超时时间（秒）
            
        Returns:
            执行结果字典
        """
        if not self.parser.validate():
            self.status = 'error'
            self.error = "工作流验证失败: " + ", ".join(self.parser.get_errors())
            if self.logger:
                self.logger.log_error(self.error)
            return self._get_result()
        
        # 检查所有Agent是否都已添加
        parser_agents = self.parser.get_agents()
        if isinstance(parser_agents, dict):
            parser_agents = set(parser_agents.keys())
        missing_agents = parser_agents - set(self.agents.keys())
        if missing_agents:
            self.status = 'error'
            self.error = f"缺少以下Agent: {', '.join(missing_agents)}"
            if self.logger:
                self.logger.log_error(self.error)
            return self._get_result()
        
        # 重置执行状态
        self.reset()
        self.status = 'running'
        
        # 记录工作流开始执行
        if self.logger:
            self.logger.log_workflow_start(initial_message)
        
        # 获取工作流图
        graph = self.parser.get_graph()
        
        # 找到起始节点（入度为0的节点）
        start_nodes = [node for node, in_degree in graph.in_degree() if in_degree == 0]
        if not start_nodes:
            # 如果没有入度为0的节点，选择任意节点作为起始节点
            start_nodes = list(graph.nodes())[0:1]
        
        # 设置初始消息
        current_messages = {}
        if initial_message and start_nodes:
            current_messages[start_nodes[0]] = initial_message
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行工作流
        while self.current_step < max_steps and (time.time() - start_time) < timeout:
            # 检查是否还有消息需要处理
            if not current_messages:
                break
            
            # 处理当前步骤的所有消息
            next_messages = {}
            for agent_name, message in current_messages.items():
                try:
                    # 获取Agent
                    agent = self.agents.get(agent_name)
                    if not agent:
                        raise ValueError(f"找不到Agent: {agent_name}")
                    
                    # 发送消息并获取回复
                    response = agent.send_message(message)
                    
                    # 记录执行历史
                    self.execution_history.append({
                        'step': self.current_step,
                        'agent': agent_name,
                        'input': message,
                        'output': response,
                        'is_final': len(list(graph.out_edges(agent_name))) == 0  # 标记是否为最终Agent
                    })
                    
                    # 记录到日志
                    if self.logger:
                        self.logger.log_step(self.current_step, agent_name, message, response)
                    
                    # 获取下一步的目标Agent
                    for _, target, data in graph.out_edges(agent_name, data=True):
                        next_messages[target] = response
                
                except Exception as e:
                    self.status = 'error'
                    self.error = f"执行步骤 {self.current_step} 时出错: {str(e)}"
                    return self._get_result()
            
            # 更新当前步骤和消息
            self.current_step += 1
            current_messages = next_messages
        
        # 检查是否超时或超过最大步骤数
        if (time.time() - start_time) >= timeout:
            self.status = 'error'
            self.error = f"执行超时 ({timeout}秒)"
        elif self.current_step >= max_steps:
            self.status = 'error'
            self.error = f"超过最大执行步骤数 ({max_steps})"
        else:
            self.status = 'completed'
        
        return self._get_result()
    
    def execute_step(self, agent_name: str, message: str) -> Dict[str, Any]:
        """执行单个工作流步骤
        
        Args:
            agent_name: 要执行的Agent名称
            message: 发送给Agent的消息
            
        Returns:
            执行结果字典
        """
        try:
            # 获取Agent
            agent = self.agents.get(agent_name)
            if not agent:
                raise ValueError(f"找不到Agent: {agent_name}")
            
            # 发送消息并获取回复
            response = agent.send_message(message)
            
            # 记录执行历史
            self.execution_history.append({
                'step': self.current_step,
                'agent': agent_name,
                'input': message,
                'output': response
            })
            
            # 更新当前步骤
            self.current_step += 1
            
            # 获取下一步的目标Agent
            graph = self.parser.get_graph()
            next_agents = []
            for _, target, data in graph.out_edges(agent_name, data=True):
                next_agents.append({
                    'agent': target,
                    'message': response
                })
            
            return {
                'status': 'success',
                'agent': agent_name,
                'input': message,
                'output': response,
                'next_agents': next_agents
            }
            
        except Exception as e:
            self.status = 'error'
            self.error = f"执行步骤 {self.current_step} 时出错: {str(e)}"
            return {
                'status': 'error',
                'agent': agent_name,
                'input': message,
                'error': str(e)
            }
    
    def reset(self) -> None:
        """重置执行状态"""
        self.execution_history = []
        self.current_step = 0
        self.status = 'ready'
        self.error = None
    
    def get_status(self) -> str:
        """获取当前执行状态
        
        Returns:
            执行状态: ready, running, completed, error
        """
        return self.status
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史
        
        Returns:
            执行历史列表
        """
        return self.execution_history
    
    def _get_result(self) -> Dict[str, Any]:
        """获取执行结果
        
        Returns:
            执行结果字典
        """
        # 记录工作流执行结束
        if self.logger:
            self.logger.log_workflow_end(self.status, self.current_step)
            
        return {
            'status': self.status,
            'steps': self.current_step,
            'history': self.execution_history,
            'error': self.error,
            'log_file': self.logger.get_log_file_path() if self.logger else None
        }
    
    @staticmethod
    def create_from_config(workflow_config: List[str], agent_configs: List[Dict[str, Any]]) -> 'WorkflowExecutor':
        """从配置创建工作流执行器
        
        Args:
            workflow_config: 工作流配置列表，每个元素为一行工作流定义
            agent_configs: Agent配置列表，每个元素为一个Agent配置字典
            
        Returns:
            工作流执行器实例
        """
        # 创建工作流解析器
        parser = WorkflowParser()
        parser.parse('\n'.join(workflow_config))
        
        # 创建Agent
        agents = {}
        for config in agent_configs:
            # 这里使用的是字典参数版本的create_agent方法
            agent = AgentFactory.create_agent(config)
            if agent:
                agents[agent.name] = agent
        
        # 创建工作流执行器
        return WorkflowExecutor(parser, agents)