# agent_factory.py
# Agent工厂类，负责创建不同类型的Agent

from typing import Dict, Any, Optional, List
from .agent import Agent, OpenAIAgent, AzureOpenAIAgent, QwenAgent, DeepSeekAgent, OpenRouterAgent, SiliconFlowAgent
from config import config

class AgentFactory:
    """Agent工厂类，负责创建不同类型的Agent"""
    
    @staticmethod
    def create_agent_from_params(name: str, api_type: str, system_prompt: str, prompt: str = "") -> Agent:
        """根据单独参数创建Agent实例
        
        Args:
            name: Agent名称
            api_type: API类型，如'openai', 'azure'等
            system_prompt: 系统提示词
            prompt: Agent特定提示词
            
        Returns:
            Agent实例
        """
        api_type = api_type.lower()
        
        if api_type == 'openai':
            return OpenAIAgent(name, api_type, system_prompt, prompt)
        elif api_type == 'azure':
            return AzureOpenAIAgent(name, api_type, system_prompt, prompt)
        elif api_type == 'qwen':
            return QwenAgent(name, api_type, system_prompt, prompt)
        elif api_type == 'deepseek':
            return DeepSeekAgent(name, api_type, system_prompt, prompt)
        elif api_type == 'openrouter':
            return OpenRouterAgent(name, api_type, system_prompt, prompt)
        elif api_type == 'siliconflow':
            return SiliconFlowAgent(name, api_type, system_prompt, prompt)
        else:
            raise ValueError(f"不支持的API类型: {api_type}")
        # # 可以根据需要添加更多API类型
        #     api_key = api_config.get('api_key')
        #     if not api_key:
        #         print(f"错误: 未找到新模型 API 密钥，请检查配置")
        #         return None
        #     return NewModelAgent(name, system_prompt, api_key)
        # else:
        #     raise ValueError(f"不支持的API类型: {api_type}")
    
    @staticmethod
    def create_agent(agent_config: Dict[str, Any]) -> Optional[Agent]:
        """根据配置创建Agent
        
        Args:
            agent_config: Agent配置字典，包含name, api_type, system_prompt等
            
        Returns:
            创建的Agent实例，如果创建失败则返回None
        """
        name = agent_config.get('name')
        api_type = agent_config.get('api_type')
        system_prompt = agent_config.get('system_prompt')
        
        if not name or not api_type:
            print("错误: Agent配置缺少必要参数 'name' 或 'api_type'")
            return None
        
        # 获取API配置
        api_config = config.get_api_config(api_type)
        
        # 根据API类型创建不同的Agent
        api_type_lower = api_type.lower()
        
        if api_type_lower == 'openai':
            api_key = api_config.get('api_key')
            model = agent_config.get('model', 'gpt-3.5-turbo')
            
            if not api_key:
                print(f"错误: 未找到OpenAI API密钥，请检查配置")
                return None
            
            return OpenAIAgent(name, system_prompt, api_key, model)
            
        elif api_type_lower == 'azure':
            api_key = api_config.get('api_key')
            api_base = api_config.get('api_base')
            deployment_name = api_config.get('deployment_name')
            
            if not api_key or not api_base or not deployment_name:
                print(f"错误: Azure OpenAI配置不完整，请检查配置")
                return None
            
            return AzureOpenAIAgent(name, system_prompt, api_key, api_base, deployment_name)
        
        # 新增支持的API类型
        elif api_type_lower == 'qwen':
            api_key = api_config.get('api_key')
            model = agent_config.get('model', 'qwen-turbo')
            
            if not api_key:
                print(f"错误: 未找到Qwen API密钥，请检查配置")
                return None
            
            return QwenAgent(name, system_prompt, api_key, model)
            
        elif api_type_lower == 'deepseek':
            api_key = api_config.get('api_key')
            model = agent_config.get('model', 'deepseek-chat')
            
            if not api_key:
                print(f"错误: 未找到DeepSeek API密钥，请检查配置")
                return None
            
            return DeepSeekAgent(name, system_prompt, api_key, model)
            
        elif api_type_lower == 'openrouter':
            api_key = api_config.get('api_key')
            model = agent_config.get('model', 'openrouter-default')
            
            if not api_key:
                print(f"错误: 未找到OpenRouter API密钥，请检查配置")
                return None
            
            return OpenRouterAgent(name, system_prompt, api_key, model)
            
        elif api_type_lower == 'siliconflow':
            api_key = api_config.get('api_key')
            model = agent_config.get('model', 'siliconflow-default')
            
            if not api_key:
                print(f"错误: 未找到SiliconFlow API密钥，请检查配置")
                return None
            
            return SiliconFlowAgent(name, system_prompt, api_key, model)
        
        print(f"错误: 不支持的API类型: {api_type}")
        return None
    
    @staticmethod
    def create_agents_from_config(agents_config: List[Dict[str, Any]]) -> Dict[str, Agent]:
        """从配置列表创建多个Agent
        
        Args:
            agents_config: Agent配置列表
            
        Returns:
            Agent字典，键为Agent名称，值为Agent实例
        """
        agents = {}
        
        for agent_config in agents_config:
            agent = AgentFactory.create_agent(agent_config)
            if agent:
                agents[agent.name] = agent
        
        return agents