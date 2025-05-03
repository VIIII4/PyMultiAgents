# app.py
# 主应用入口和GUI界面

import sys
import os,re
import json
from typing import Dict, List, Any

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
                             QTabWidget, QSplitter, QMessageBox, QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat

# 导入自定义模块
from configdrawer import ConfigDrawer

from config.config import Config
from classAgent import AgentFactory
from workflow import WorkflowParser, WorkflowExecutor

# 加载配置
config = Config()

class WorkflowSyntaxHighlighter(QSyntaxHighlighter):
    """工作流语法高亮器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Agent名称格式
        agent_format = QTextCharFormat()
        agent_format.setForeground(QColor(0, 0, 255))  # 蓝色
        agent_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'\b[A-Za-z0-9_]+\b(?=\s*-->)', agent_format))
        self.highlighting_rules.append((r'(?:-->\s*)\b([A-Za-z0-9_]+)\b', agent_format))

        # 消息格式
        message_format = QTextCharFormat()
        message_format.setForeground(QColor(0, 128, 0))  # 绿色
        self.highlighting_rules.append((r':\s*(.*)$', message_format))
        
        # 冒号格式
        colon_format = QTextCharFormat()
        colon_format.setForeground(QColor(128, 0, 128))  # 紫色
        self.highlighting_rules.append((r':', colon_format))
    
    def highlightBlock(self, text):
        # 修正正则表达式，避免使用非固定宽度的后行断言
        pattern = r'修正后的正则表达式'
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, format)

class AgentConfigWidget(QWidget):
    """Agent配置界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agents = []  # Agent配置列表
        self.initUI()
    
    def initUI(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # Agent列表
        self.agent_list = QTextEdit()
        self.agent_list.setReadOnly(True)
        layout.addWidget(QLabel("已配置的Agent:"))
        layout.addWidget(self.agent_list)
        
        # Agent配置表单
        form_group = QGroupBox("添加新Agent")
        form_layout = QVBoxLayout()
        
        # Agent名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        form_layout.addLayout(name_layout)
        
        # API类型
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API类型:"))
        self.api_combo = QComboBox()
        self.api_combo.addItems(["openai", "azure", "Qwen", "DeepSeek", "OpenRouter", "SiliconFlow"])
        api_layout.addWidget(self.api_combo)
        form_layout.addLayout(api_layout)
        
        # 模型选择（仅OpenAI）
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_edit = QLineEdit()
        model_layout.addWidget(self.model_edit)
        form_layout.addLayout(model_layout)
        
        # 系统提示词
        form_layout.addWidget(QLabel("系统提示词:"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMinimumHeight(100)
        form_layout.addWidget(self.prompt_edit)
        
        # 添加按钮
        self.add_button = QPushButton("添加Agent")
        self.add_button.clicked.connect(self.add_agent)
        form_layout.addWidget(self.add_button)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        self.setLayout(layout)
        self.update_agent_list()
    
    def add_agent(self):
        """添加Agent"""
        name = self.name_edit.text().strip()
        api_type = self.api_combo.currentText()
        model = self.model_edit.text()
        system_prompt = self.prompt_edit.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "错误", "Agent名称不能为空")
            return
        
        # 检查名称是否已存在
        for agent in self.agents:
            if agent['name'] == name:
                QMessageBox.warning(self, "错误", f"Agent名称 '{name}' 已存在")
                return
        
        # 添加Agent配置
        agent_config = {
            'name': name,
            'api_type': api_type,
            'model': model,
            'system_prompt': system_prompt
        }
        self.agents.append(agent_config)
        
        # 清空表单 - 修复重置问题，确保所有字段被清空
        self.name_edit.clear()
        self.model_edit.clear()  # 添加模型字段清空
        self.prompt_edit.clear()
        self.api_combo.setCurrentIndex(0)  # 重置API类型选择框到第一项
        
        # 显示成功提示
        QMessageBox.information(self, "成功", f"Agent '{name}' 已添加")
        
        # 更新Agent列表
        self.update_agent_list()
    
    def update_agent_list(self):
        """更新Agent列表"""
        text = ""
        for i, agent in enumerate(self.agents):
            text += f"{i+1}. {agent['name']} ({agent['api_type']})"
            if agent.get('model'):
                text += f" - {agent['model']}"
            text += "\n"
        
        self.agent_list.setText(text)
    
    def get_agents(self) -> List[Dict[str, Any]]:
        """获取Agent配置列表"""
        return self.agents
    
    def set_agents(self, agents: List[Dict[str, Any]]):
        """设置Agent配置列表"""
        self.agents = agents
        self.update_agent_list()

class WorkflowWidget(QWidget):
    """工作流配置界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workflow_lines = []  # 工作流配置行
        self.initUI()
    
    def initUI(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 创建水平分割器，左侧是代码编辑，右侧是可视化绘制
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧 - 工作流代码编辑区
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("工作流定义 (类似mermaid flowchart语法):"))
        self.workflow_edit = QTextEdit()
        self.workflow_edit.setMinimumHeight(200)
        
        # 设置语法高亮
        self.highlighter = WorkflowSyntaxHighlighter(self.workflow_edit.document())
        
        left_layout.addWidget(self.workflow_edit)
        
        # 示例和帮助
        help_text = """示例语法:
AgentA |\"AgentA's Prompt\"|--> AgentB |\"AgentB's Prompt\"| : {'任务描述'}
AgentC |\"AgentC's Prompt\"|--> AgentD |\"AgentD's Prompt\"| : {'另一个任务描述'}

每行定义一个连接，格式为: 源Agent |\"源Agent的提示词\"|--> 目标Agent |\"目标Agent的提示词\"| : {'任务描述'}"""
        help_label = QLabel(help_text)
        help_label.setStyleSheet("color: gray; font-style: italic;")
        left_layout.addWidget(help_label)
        
        # 右侧 - 可视化绘制区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("可视化工作流绘制:"))
        
        # 创建ConfigDrawer实例
        self.config_drawer = ConfigDrawer()
        right_layout.addWidget(self.config_drawer)
        
        # 连接信号
        self.workflow_edit.textChanged.connect(self.code_to_visual)
        self.config_drawer.workflow_updated.connect(self.visual_to_code)
        
        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # 设置初始大小
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter)
        
        # 验证按钮
        self.validate_button = QPushButton("验证工作流")
        self.validate_button.clicked.connect(self.validate_workflow)
        layout.addWidget(self.validate_button)
        
        self.setLayout(layout)
    
    def validate_workflow(self):
        """验证工作流"""
        workflow_text = self.workflow_edit.toPlainText().strip()
        if not workflow_text:
            QMessageBox.warning(self, "错误", "工作流定义不能为空")
            return False
        
        # 解析工作流
        parser = WorkflowParser()
        if parser.parse(workflow_text):
            # 检查是否有未定义的Agent
            defined_agents = parser.get_agents()
            if not defined_agents:
                QMessageBox.warning(self, "错误", "工作流中没有定义任何Agent")
                return False
            QMessageBox.information(self, "成功", "工作流验证通过!")
            self.workflow_lines = workflow_text.split('\n')
            # 更新可视化绘制
            self.code_to_visual()
            return True
        else:
            QMessageBox.warning(self, "错误", "工作流验证失败:\n" + "\n".join(parser.get_errors()))
            return False
    
    def code_to_visual(self):
        """将代码转换为可视化绘制"""
        # 断开信号连接，防止循环更新
        self.workflow_edit.blockSignals(True)
        self.config_drawer.blockSignals(True)
        
        try:
            # 获取工作流文本
            workflow_text = self.workflow_edit.toPlainText().strip()
            if workflow_text:
                # 加载到可视化绘制器
                self.config_drawer.load_workflow(workflow_text)
        finally:
            # 恢复信号连接
            self.workflow_edit.blockSignals(False)
            self.config_drawer.blockSignals(False)
    
    def visual_to_code(self, workflow_text: str):
        """将可视化绘制转换为代码"""
        # 断开信号连接，防止循环更新
        self.workflow_edit.blockSignals(True)
        self.config_drawer.blockSignals(True)
        
        try:
            # 更新工作流编辑器
            self.workflow_edit.setText(workflow_text)
            self.workflow_lines = workflow_text.split('\n') if workflow_text else []
        finally:
            # 恢复信号连接
            self.workflow_edit.blockSignals(False)
            self.config_drawer.blockSignals(False)
    
    def get_workflow(self) -> List[str]:
        """获取工作流配置"""
        return self.workflow_edit.toPlainText().strip().split('\n')
    
    def set_workflow(self, workflow: List[str]):
        """设置工作流配置"""
        workflow_text = '\n'.join(workflow)
        self.workflow_edit.setText(workflow_text)
        self.workflow_lines = workflow
        # 更新可视化绘制
        self.code_to_visual()

class ExecutionWidget(QWidget):
    """工作流执行界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.executor = None  # 工作流执行器
        self.initUI()
    
    def initUI(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 初始消息
        init_layout = QHBoxLayout()
        init_layout.addWidget(QLabel("初始消息:"))
        self.init_message = QLineEdit()
        init_layout.addWidget(self.init_message)
        layout.addLayout(init_layout)
        
        # 执行按钮
        button_layout = QHBoxLayout()
        self.execute_button = QPushButton("执行工作流")
        self.execute_button.clicked.connect(self.execute_workflow)
        button_layout.addWidget(self.execute_button)
        
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_execution)
        button_layout.addWidget(self.reset_button)
        
        self.view_log_button = QPushButton("查看日志")
        self.view_log_button.clicked.connect(self.view_log)
        self.view_log_button.setEnabled(False)  # 初始状态下禁用
        button_layout.addWidget(self.view_log_button)
        
        layout.addLayout(button_layout)
        
        # 执行结果
        layout.addWidget(QLabel("执行结果:"))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        
        self.setLayout(layout)
        
        # 保存当前日志文件路径
        self.current_log_file = None
    
    def set_executor(self, executor: WorkflowExecutor):
        """设置工作流执行器"""
        self.executor = executor
    
    def execute_workflow(self):
        """执行工作流"""
        if not self.executor:
            QMessageBox.warning(self, "错误", "请先创建工作流执行器")
            return
        
        # 获取初始消息
        initial_message = self.init_message.text().strip()
        
        # 执行工作流
        result = self.executor.execute(initial_message)
        
        # 显示执行结果
        self.display_result(result)
    
    def reset_execution(self):
        """重置执行状态"""
        if self.executor:
            self.executor.reset()
            self.result_text.clear()
    
    def display_result(self, result: Dict[str, Any]):
        """显示执行结果，只显示最终Agent的输出"""
        status = result.get('status', '')
        steps = result.get('steps', 0)
        history = result.get('history', [])
        error = result.get('error', '')
        log_file = result.get('log_file', '')
        
        # 保存日志文件路径并启用查看日志按钮
        self.current_log_file = log_file
        self.view_log_button.setEnabled(bool(log_file))
        
        text = f"状态: {status}\n"
        text += f"执行步骤: {steps}\n"
        
        if error:
            text += f"错误: {error}\n\n"
        
        # 查找最终Agent的输出
        final_steps = [step for step in history if step.get('is_final', False)]
        
        if final_steps:
            final_step = final_steps[-1]  # 获取最后一个最终Agent的步骤
            text += "最终结果:\n"
            text += f"  Agent: {final_step.get('agent', '')}\n"
            text += f"  输出: {final_step.get('output', '')}\n\n"
        else:
            # 如果没有标记为最终的Agent，则显示最后一个Agent的输出
            if history:
                last_step = history[-1]
                text += "最终结果:\n"
                text += f"  Agent: {last_step.get('agent', '')}\n"
                text += f"  输出: {last_step.get('output', '')}\n\n"
        
        # 添加日志文件信息
        if log_file:
            text += f"详细执行日志已保存至: {log_file}\n"
            text += "(点击'查看日志'按钮可查看完整执行过程)\n"
        
        self.result_text.setText(text)
        
    def view_log(self):
        """查看日志文件"""
        if not self.current_log_file or not os.path.exists(self.current_log_file):
            QMessageBox.warning(self, "错误", "日志文件不存在")
            return
        
        try:
            # 在Windows系统中使用默认程序打开日志文件
            os.startfile(self.current_log_file)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开日志文件失败: {str(e)}")
            
    def reset_execution(self):
        """重置执行状态"""
        if self.executor:
            self.executor.reset()
            self.result_text.clear()
            self.current_log_file = None
            self.view_log_button.setEnabled(False)

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        """初始化界面"""
        self.setWindowTitle("MultiAgent 协作系统")
        self.setGeometry(100, 100, 1000, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        


        # 创建选项卡
        tabs = QTabWidget()
        
        # Agent配置选项卡
        self.agent_widget = AgentConfigWidget()
        tabs.addTab(self.agent_widget, "Agent配置")
        
        # 工作流配置选项卡
        self.workflow_widget = WorkflowWidget()
        tabs.addTab(self.workflow_widget, "工作流配置")
        
        # 执行选项卡
        self.execution_widget = ExecutionWidget()
        tabs.addTab(self.execution_widget, "执行工作流")
        
        main_layout.addWidget(tabs)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        # 保存配置按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_button)
        
        # 加载配置按钮
        load_button = QPushButton("加载配置")
        load_button.clicked.connect(self.load_config)
        button_layout.addWidget(load_button)
        
        # 创建工作流按钮
        create_button = QPushButton("创建工作流")
        create_button.clicked.connect(self.create_workflow)
        button_layout.addWidget(create_button)
        
        main_layout.addLayout(button_layout)
    
    def save_config(self):
        """保存配置"""
        # 获取保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        # 获取配置
        config = {
            'agents': self.agent_widget.get_agents(),
            'workflow': self.workflow_widget.get_workflow()
        }
        
        # 保存配置
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "配置已保存")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        # 获取加载路径
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载配置", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        # 加载配置
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 设置配置
            self.agent_widget.set_agents(config.get('agents', []))
            self.workflow_widget.set_workflow(config.get('workflow', []))
            
            QMessageBox.information(self, "成功", "配置已加载")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置失败: {str(e)}")
    
    def create_workflow(self):
        """创建工作流"""
        # 验证工作流
        if not self.workflow_widget.validate_workflow():
            return
        
        # 获取Agent配置和工作流配置
        agent_configs_list = self.agent_widget.get_agents()
        workflow_config = self.workflow_widget.get_workflow()
        workflow_text = '\n'.join(workflow_config)
        
        # 创建工作流解析器
        parser = WorkflowParser()
        if not parser.parse(workflow_text):
            QMessageBox.warning(self, "错误", "工作流解析失败: " + "\n".join(parser.get_errors()))
            return
        
        # 创建工作流执行器
        try:
            # 转换Agent配置列表为字典，键为Agent名称
            agent_configs = {}
            for config in agent_configs_list:
                agent_name = config.get('name')
                if agent_name:
                    agent_configs[agent_name] = config
            
            # 创建执行器
            executor = WorkflowExecutor(parser)
            
            # 创建并添加Agent
            factory = AgentFactory()
            for agent_name, config in agent_configs.items():
                # 获取工作流中定义的Agent提示词
                prompt = parser.get_agent_prompt(agent_name)
                
                # 创建Agent实例
                agent = factory.create_agent_from_params(
                    name=agent_name,
                    api_type=config.get('api_type', 'openai'),
                    system_prompt=config.get('system_prompt', ''),
                    prompt=prompt
                )
                
                # 添加到执行器
                executor.add_agent(agent_name, agent)
            
            self.execution_widget.set_executor(executor)
            QMessageBox.information(self, "成功", "工作流已创建，可以执行了")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"创建工作流失败: {str(e)}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()