# agent.py
# Agent基类定义

from abc import ABC, abstractmethod
from typing import Dict,List

class Agent(ABC):
    """Agent基类，定义Agent的基本接口"""
    
    def __init__(self, name: str, api_type: str, system_prompt: str, prompt: str = ""):
        """初始化Agent
        
        Args:
            name: Agent名称
            api_type: API类型，如'openai', 'azure'等
            system_prompt: 系统提示词
            prompt: Agent特定提示词，用于工作流中
        """
        self.name = name
        self.api_type = api_type
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.messages: list[dict[str, str]] = []
        # 初始化系统消息
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
    
    def get_prompt(self) -> str:
        """获取Agent提示词"""
        return self.prompt
    
    def set_prompt(self, prompt: str) -> None:
        """设置Agent提示词"""
        self.prompt = prompt
    
    @abstractmethod
    def send_message(self, content: str) -> str:
        """发送消息给LLM并获取回复
        
        Args:
            content: 消息内容
            
        Returns:
            LLM的回复
        """
        pass
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息到历史记录
        
        Args:
            role: 消息角色，如'user', 'assistant'等
            content: 消息内容
        """
        self.messages.append({"role": role, "content": content})
    
    def clear_messages(self) -> None:
        """清空消息历史，保留系统提示"""
        if self.system_prompt:
            self.messages = [{"role": "system", "content": self.system_prompt}]
        else:
            self.messages = []
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取消息历史
        
        Returns:
            消息历史列表
        """
        return self.messages


class OpenAIAgent(Agent):
    """OpenAI API Agent实现"""
    
    def __init__(self, name: str, system_prompt: str, api_key: str, model: str = "gpt-3.5-turbo"):
        """初始化OpenAI Agent
        
        Args:
            name: Agent名称
            system_prompt: 系统提示词
            api_key: OpenAI API密钥
            model: 模型名称
        """
        super().__init__(name, "openai", system_prompt)
        self.api_key = api_key
        self.model = model
    
    def send_message(self, content: str) -> str:
        """发送消息给OpenAI API并获取回复
        
        Args:
            content: 消息内容
            
        Returns:
            OpenAI的回复
        """
        import openai
        
        # 添加用户消息
        self.add_message("user", content)
        
        # 设置API密钥
        client = openai.OpenAI(api_key=self.api_key)
        
        # 发送请求
        response = client.chat.completions.create(
            model=self.model,
            messages=self.messages
        )
        
        # 获取回复
        reply = response.choices[0].message.content
        
        # 添加助手消息
        self.add_message("assistant", reply)
        
        return reply


class AzureOpenAIAgent(Agent):
    """Azure OpenAI API Agent实现"""
    
    def __init__(self, name: str, system_prompt: str, api_key: str, api_base: str, deployment_name: str):
        """初始化Azure OpenAI Agent
        
        Args:
            name: Agent名称
            system_prompt: 系统提示词
            api_key: Azure API密钥
            api_base: Azure API基础URL
            deployment_name: Azure部署名称
        """
        super().__init__(name, "azure", system_prompt)
        self.api_key = api_key
        self.api_base = api_base
        self.deployment_name = deployment_name
    
    def send_message(self, content: str) -> str:
        """发送消息给Azure OpenAI API并获取回复
        
        Args:
            content: 消息内容
            
        Returns:
            Azure OpenAI的回复
        """
        import openai
        
        # 添加用户消息
        self.add_message("user", content)
        
        # 设置Azure API
        client = openai.AzureOpenAI(
            api_key=self.api_key,
            api_version="2023-05-15",
            azure_endpoint=self.api_base
        )
        
        # 发送请求
        response = client.chat.completions.create(
            deployment_name=self.deployment_name,
            messages=self.messages
        )
        
        # 获取回复
        reply = response.choices[0].message.content
        
        # 添加助手消息
        self.add_message("assistant", reply)
        
        return reply


class QwenAgent(Agent):
    """Qwen API的Agent实现"""
    
    def __init__(self, name: str, api_type: str, system_prompt: str, prompt: str = ""):
        """初始化Qwen Agent
        
        Args:
            name: Agent名称
            api_type: API类型，固定为'qwen'
            system_prompt: 系统提示词
            prompt: Agent特定提示词
        """
        super().__init__(name, api_type, system_prompt, prompt)
        from config import config
        api_config = config.get_api_config('qwen')
        self.api_key = api_config.get('api_key')
        self.api_base = api_config.get('api_base')
        self.model = "qwen-max" # 默认使用qwen-max模型，可根据需要修改
    
    def send_message(self, content: str) -> str:
        """发送消息给Qwen LLM并获取回复
        
        Args:
            content: 消息内容
            
        Returns:
            Qwen的回复
        """
        import openai
        
        # 添加用户消息
        self.add_message("user", content)
        
        # 设置API
        client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # 发送请求
        response = client.chat.completions.create(
            model=self.model,
            messages=self.messages
        )
        
        # 获取回复
        reply = response.choices[0].message.content
        
        # 添加助手消息
        self.add_message("assistant", reply)
        
        return reply


class DeepSeekAgent(Agent):
    """DeepSeek API的Agent实现"""
    
    def __init__(self, name: str, api_type: str, system_prompt: str, prompt: str = ""):
        """初始化DeepSeek Agent
        
        Args:
            name: Agent名称
            api_type: API类型，固定为'deepseek'
            system_prompt: 系统提示词
            prompt: Agent特定提示词
        """
        super().__init__(name, api_type, system_prompt, prompt)
        from config import config
        api_config = config.get_api_config('deepseek')
        self.api_key = api_config.get('api_key')
        self.api_base = api_config.get('api_base')
        self.model = "deepseek-chat" # 默认使用deepseek-chat模型，可根据需要修改
    
    def send_message(self, content: str) -> str:
        """发送消息给DeepSeek LLM并获取回复
        
        Args:
            content: 消息内容
            
        Returns:
            DeepSeek的回复
        """
        import openai
        
        # 添加用户消息
        self.add_message("user", content)
        
        # 设置API
        client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # 发送请求
        response = client.chat.completions.create(
            model=self.model,
            messages=self.messages
        )
        
        # 获取回复
        reply = response.choices[0].message.content
        
        # 添加助手消息
        self.add_message("assistant", reply)
        
        return reply


class OpenRouterAgent(Agent):
    """OpenRouter API的Agent实现"""
    
    def __init__(self, name: str, api_type: str, system_prompt: str, prompt: str = "", model: str = "anthropic/claude-3-opus"):
        """初始化OpenRouter Agent
        
        Args:
            name: Agent名称
            api_type: API类型，固定为'openrouter'
            system_prompt: 系统提示词
            prompt: Agent特定提示词
            model: 模型名称，默认为'anthropic/claude-3-opus'
        """
        super().__init__(name, api_type, system_prompt, prompt)
        from config import config
        api_config = config.get_api_config('openrouter')
        self.api_key = api_config.get('api_key')
        self.model = model
    
    def send_message(self, content: str) -> str:
        """发送消息给OpenRouter LLM并获取回复
        
        Args:
            content: 消息内容
            
        Returns:
            OpenRouter的回复
        """
        import openai
        
        # 添加用户消息
        self.add_message("user", content)
        
        # 设置API
        client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # 发送请求
        response = client.chat.completions.create(
            model=self.model,
            messages=self.messages
        )
        
        # 获取回复
        reply = response.choices[0].message.content
        
        # 添加助手消息
        self.add_message("assistant", reply)
        
        return reply


class SiliconFlowAgent(Agent):
    """SiliconFlow API的Agent实现"""
    
    def __init__(self, name: str, api_type: str, system_prompt: str, prompt: str = ""):
        """初始化SiliconFlow Agent
        
        Args:
            name: Agent名称
            api_type: API类型，固定为'siliconflow'
            system_prompt: 系统提示词
            prompt: Agent特定提示词
        """
        super().__init__(name, api_type, system_prompt, prompt)
        from config import config
        api_config = config.get_api_config('siliconflow')
        self.api_key = api_config.get('api_key')
        self.api_base = api_config.get('api_base')
        self.model = "llama3-70b" # 默认使用llama3-70b模型，可根据需要修改
    
    def send_message(self, content: str) -> str:
        """发送消息给SiliconFlow LLM并获取回复
        
        Args:
            content: 消息内容
            
        Returns:
            SiliconFlow的回复
        """
        import openai
        
        # 添加用户消息
        self.add_message("user", content)
        
        # 设置API
        client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # 发送请求
        response = client.chat.completions.create(
            model=self.model,
            messages=self.messages
        )
        
        # 获取回复
        reply = response.choices[0].message.content
        
        # 添加助手消息
        self.add_message("assistant", reply)
        
        return reply


class SiliconFlowAgent(Agent):
    """SiliconFlow API的Agent实现"""

    def send_message(self, content: str) -> str:
        """发送消息给SiliconFlow LLM并获取回复"""
        # 实现SiliconFlow API调用
        pass