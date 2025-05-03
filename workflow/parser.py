# parser.py
# 工作流解析器，负责解析类似mermaid flowchart的配置

import re
import networkx as nx
from typing import Set, Dict, List, Tuple, Any

class WorkflowParser:
    """工作流解析器，负责解析类似mermaid flowchart的配置"""
    
    def __init__(self):
        """初始化工作流解析器"""
        self.graph = nx.DiGraph()  # 使用有向图表示工作流
        self.agents = {}  # 工作流中的Agent集合，键为名称，值为提示词
        self.connections = []  # 工作流中的连接
        self.errors = []  # 解析错误
    
    def parse(self, workflow_text: str) -> bool:
        """解析工作流定义文本
        
        Args:
            workflow_text: 工作流定义文本，支持新语法格式
            
        Returns:
            解析是否成功
        """
        # 清空之前的解析结果
        self.graph.clear()
        self.agents.clear()
        self.connections.clear()
        self.errors.clear()
        
        # 按行解析工作流定义
        lines = workflow_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # 跳过空行和注释
            
            # 解析新语法: "Agent第一个 |要俏皮一点| --> Agent第二个 |要凸显逻辑|: {展示}"
            connection_pattern = r'(?P<source>[\w\s]+)\s*\|\"?(?P<source_prompt>[^\|]+)\"?\|\s*-->\s*(?P<target>[\w\s]+)\s*\|\"?(?P<target_prompt>[^\|]+)\"?\|\s*:\s*\{(?P<message>[^\}]+)\}'
            # 根据实际情况进一步优化正则表达式
            match = re.match(connection_pattern, line)
            
            if match:
                source = match.group(1).strip()
                source_prompt = match.group(2) or ""
                target = match.group(3).strip()
                target_prompt = match.group(4) or ""
                message = match.group(5).strip()
                
                # 添加Agent节点和提示词
                self.agents[source] = source_prompt
                self.agents[target] = target_prompt
                
                # 添加连接
                self.connections.append((source, target, message))
                
                # 更新图
                self.graph.add_node(source, prompt=source_prompt)
                self.graph.add_node(target, prompt=target_prompt)
                self.graph.add_edge(source, target, message=message)
            else:
                # 尝试解析旧语法: "AgentA --> AgentB: 消息内容"
                old_pattern = r'([\w\s]+)\s*-->\s*([\w\s]+)\s*:\s*(.+)'
                old_match = re.match(old_pattern, line)
                
                if old_match:
                    source = old_match.group(1).strip()
                    target = old_match.group(2).strip()
                    message = old_match.group(3).strip()
                    
                    # 添加Agent节点
                    self.agents[source] = ""
                    self.agents[target] = ""
                    
                    # 添加连接
                    self.connections.append((source, target, message))
                    
                    # 更新图
                    self.graph.add_node(source, prompt="")
                    self.graph.add_node(target, prompt="")
                    self.graph.add_edge(source, target, message=message)
                else:
                    self.errors.append(f"无法解析行: {line}")
        
        # 验证工作流
        return self.validate()
    
    def get_agent_prompt(self, agent_name: str) -> str:
        """获取Agent的提示词
        
        Args:
            agent_name: Agent名称
            
        Returns:
            Agent提示词
        """
        return self.agents.get(agent_name, "")
    
    def get_agents(self) -> Set[str]:
        """获取工作流中的所有Agent名称
        
        Returns:
            Agent名称集合
        """
        return set(self.agents.keys())
    
    def validate(self) -> bool:
        """验证工作流的有效性
        
        Returns:
            工作流是否有效
        """
        # 检查是否有节点
        if not self.agents:
            self.errors.append("工作流中没有定义任何Agent")
            return False
        
        # 检查是否有连接
        if not self.connections:
            self.errors.append("工作流中没有定义任何连接")
            return False
        
        # 检查是否有循环依赖
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                cycle_str = ' -> '.join(cycles[0]) + ' -> ' + cycles[0][0]
                self.errors.append(f"工作流中存在循环依赖: {cycle_str}")
                return False
        except nx.NetworkXNoCycle:
            pass  # 没有循环，这是好的
        
        return True
    
    def get_graph(self) -> nx.DiGraph:
        """获取解析后的工作流图
        
        Returns:
            工作流图
        """
        return self.graph
    
    def get_agents(self) -> set:
        """获取工作流中的Agent集合
        
        Returns:
            Agent集合
        """
        return self.agents
    
    def get_connections(self) -> List[Tuple[str, str, str]]:
        """获取工作流中的连接列表
        
        Returns:
            连接列表，每个连接为(source, target, message)的元组
        """
        return self.connections
    
    def get_errors(self) -> List[str]:
        """获取解析错误列表
        
        Returns:
            错误列表
        """
        return self.errors
    
    def to_dict(self) -> Dict[str, Any]:
        """将工作流转换为字典表示
        
        Returns:
            工作流的字典表示
        """
        return {
            'agents': list(self.agents),
            'connections': [
                {
                    'source': source,
                    'target': target,
                    'message': message
                }
                for source, target, message in self.connections
            ]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'WorkflowParser':
        """从字典创建工作流解析器
        
        Args:
            data: 工作流的字典表示
            
        Returns:
            工作流解析器实例
        """
        parser = WorkflowParser()
        
        # 添加Agent节点
        for agent in data.get('agents', []):
            parser.agents.add(agent)
            parser.graph.add_node(agent)
        
        # 添加连接
        for conn in data.get('connections', []):
            source = conn.get('source')
            target = conn.get('target')
            message = conn.get('message')
            
            if source and target and message:
                parser.connections.append((source, target, message))
                parser.graph.add_edge(source, target, message=message)
        
        return parser