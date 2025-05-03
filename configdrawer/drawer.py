# drawer.py
# 工作流显示器，负责可视化工作流

from PyQt6.QtWidgets import (QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout,
                             QMenu, QInputDialog, QMessageBox, QGraphicsItem,
                             QGraphicsTextItem,
                             QGraphicsPathItem, QSlider, QHBoxLayout, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont, QTransform


class NodeItem(QGraphicsItem):
    """节点图形项"""
    
    def __init__(self, name, x=0, y=0):
        super().__init__()
        self.name = name
        self.prompt = ""
        self.width = 120
        self.height = 60
        self.color = QColor(200, 230, 250)  # 浅蓝色
        self.border_color = QColor(70, 130, 180)  # 钢蓝色
        
        # 设置位置和标志
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # 创建文本项
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText(name)
        self.text_item.setPos(10, 10)
        
        # 提示词文本项
        self.prompt_item = QGraphicsTextItem(self)
        self.prompt_item.setPos(10, 30)
        self.prompt_item.setFont(QFont("Arial", 8))
        self.prompt_item.setDefaultTextColor(QColor(80, 80, 80))
    
    def boundingRect(self):
        """返回边界矩形"""
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter, option, widget):
        """绘制节点"""
        # 设置抗锯齿
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制矩形
        if self.isSelected():
            # 选中状态使用不同颜色
            painter.setPen(QPen(QColor(255, 165, 0), 2))  # 橙色边框
            painter.setBrush(QBrush(QColor(255, 230, 200)))  # 浅橙色填充
        else:
            painter.setPen(QPen(self.border_color, 1.5))
            painter.setBrush(QBrush(self.color))
        
        painter.drawRoundedRect(0, 0, self.width, self.height, 10, 10)
    
    def set_prompt(self, prompt):
        """设置提示词"""
        self.prompt = prompt
        
        # 截断过长的提示词
        display_prompt = prompt
        if len(prompt) > 20:
            display_prompt = prompt[:17] + "..."
        
        self.prompt_item.setPlainText(display_prompt)
    
    def itemChange(self, change, value):
        """处理项变化"""
        # 当节点位置改变时，更新连接
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # 通知场景中的所有连接更新
            for item in self.scene().items():
                if isinstance(item, ConnectionItem) and (item.source_node == self or item.target_node == self):
                    item.update_position()
        
        return super().itemChange(change, value)


class ConnectionItem(QGraphicsPathItem):
    """连接图形项"""
    
    def __init__(self, source_node, target_node, name=""):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self.name = name
        
        # 设置样式
        self.setPen(QPen(QColor(100, 100, 100), 1.5, Qt.PenStyle.SolidLine))
        self.setZValue(-1)  # 确保连接在节点下方
        
        # 创建文本项
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText(name)
        self.text_item.setFont(QFont("Arial", 8))
        
        # 初始化路径
        self.update_position()
    
    def update_position(self):
        """更新连接位置"""
        if not self.source_node or not self.target_node:
            return
        
        # 计算源节点和目标节点的中心点
        source_center = QPointF(self.source_node.pos().x() + self.source_node.width / 2,
                               self.source_node.pos().y() + self.source_node.height / 2)
        target_center = QPointF(self.target_node.pos().x() + self.target_node.width / 2,
                               self.target_node.pos().y() + self.target_node.height / 2)
        
        # 计算源节点和目标节点的边界点
        source_rect = QRectF(self.source_node.pos().x(), self.source_node.pos().y(),
                            self.source_node.width, self.source_node.height)
        target_rect = QRectF(self.target_node.pos().x(), self.target_node.pos().y(),
                            self.target_node.width, self.target_node.height)
        
        # 计算连接线的起点和终点
        line = QLineItem(source_center, target_center)
        source_point = self.intersect_rect(line, source_rect)
        target_point = self.intersect_rect(line, target_rect)
        
        # 创建路径
        path = QPainterPath()
        path.moveTo(source_point)
        
        # 计算控制点（用于创建曲线）
        dx = target_point.x() - source_point.x()
        dy = target_point.y() - source_point.y()
        ctrl1 = QPointF(source_point.x() + dx * 0.5, source_point.y())
        ctrl2 = QPointF(target_point.x() - dx * 0.5, target_point.y())
        
        # 绘制三次贝塞尔曲线
        path.cubicTo(ctrl1, ctrl2, target_point)
        
        # 绘制箭头
        self.add_arrow(path, target_point, ctrl2)
        
        # 设置路径
        self.setPath(path)
        
        # 更新文本位置（放在连接线的中间）
        text_pos = QPointF((source_point.x() + target_point.x()) / 2,
                          (source_point.y() + target_point.y()) / 2 - 15)
        self.text_item.setPos(text_pos)
    
    def intersect_rect(self, line, rect):
        """计算直线与矩形的交点"""
        # 简化实现：根据线的方向找到合适的边界点
        center = rect.center()
        start = line.p1()
        end = line.p2()
        
        # 计算方向向量
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        # 根据方向确定交点
        if abs(dx) > abs(dy):
            # 水平方向为主
            if dx > 0:
                # 向右
                return QPointF(rect.right(), center.y())
            else:
                # 向左
                return QPointF(rect.left(), center.y())
        else:
            # 垂直方向为主
            if dy > 0:
                # 向下
                return QPointF(center.x(), rect.bottom())
            else:
                # 向上
                return QPointF(center.x(), rect.top())
    
    def add_arrow(self, path, point, control_point):
        """添加箭头到路径"""
        # 计算箭头方向
        angle = self.calculate_angle(control_point, point)
        
        # 箭头大小
        arrow_size = 10
        
        # 计算箭头的两个点
        arrow1 = QPointF(point.x() - arrow_size * 0.8 * 1.5, point.y() - arrow_size * 0.8)
        arrow2 = QPointF(point.x() - arrow_size * 0.8 * 1.5, point.y() + arrow_size * 0.8)
        
        # 旋转箭头点
        arrow1 = self.rotate_point(arrow1, point, angle)
        arrow2 = self.rotate_point(arrow2, point, angle)
        
        # 添加箭头到路径
        arrow_path = QPainterPath()
        arrow_path.moveTo(point)
        arrow_path.lineTo(arrow1)
        arrow_path.lineTo(arrow2)
        arrow_path.lineTo(point)
        
        # 合并路径
        path.addPath(arrow_path)
    
    def calculate_angle(self, p1, p2):
        """计算两点之间的角度"""
        return 0  # 简化实现
    
    def rotate_point(self, p, center, angle):
        """围绕中心点旋转一个点"""
        return p  # 简化实现


class QLineItem:
    """简单的线段类，用于计算"""
    
    def __init__(self, p1, p2):
        self.p1_val = p1
        self.p2_val = p2
    
    def p1(self):
        return self.p1_val
    
    def p2(self):
        return self.p2_val


class ConfigDrawer(QWidget):
    """工作流配置绘制器"""
    # 定义信号，传递工作流文本
    workflow_updated = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # 存储节点和连接
        self.nodes = {}
        self.connections = []
        
        # 连接创建状态
        self.connection_mode = False
        self.source_node = None
        
        # 缩放因子
        self.scale_factor = 1.0
    
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建控制面板
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加缩放控制
        zoom_label = QLabel("缩放:")
        control_layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 200)  # 50% 到 200%
        self.zoom_slider.setValue(100)  # 默认 100%
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        control_layout.addWidget(self.zoom_slider)
        
        self.zoom_value_label = QLabel("100%")
        self.zoom_value_label.setMinimumWidth(50)
        control_layout.addWidget(self.zoom_value_label)
        
        # 添加控制面板到主布局
        main_layout.addWidget(control_panel)
        
        # 创建图形视图和场景
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)  # 允许框选
        
        # 设置视图大小策略
        self.view.setMinimumSize(600, 400)
        
        # 添加视图到主布局
        main_layout.addWidget(self.view)
        
        # 设置主布局
        self.setLayout(main_layout)
    
    def zoom_changed(self, value):
        """缩放值改变处理"""
        self.scale_factor = value / 100.0
        self.zoom_value_label.setText(f"{value}%")
        
        # 应用变换
        transform = QTransform()
        transform.scale(self.scale_factor, self.scale_factor)
        self.view.setTransform(transform)
    
    def add_node(self, name, x=100, y=100, prompt=""):
        """添加节点"""
        node = NodeItem(name, x, y)
        node.set_prompt(prompt)
        self.scene.addItem(node)
        self.nodes[name] = node
        return node
    
    def add_connection(self, source_name, target_name, connection_name=""):
        """添加连接"""
        if source_name in self.nodes and target_name in self.nodes:
            source_node = self.nodes[source_name]
            target_node = self.nodes[target_name]
            
            # 创建连接
            connection = ConnectionItem(source_node, target_node, connection_name)
            self.scene.addItem(connection)
            self.connections.append(connection)
            
            # 发出工作流更新信号，传递工作流文本
            workflow_text = self.generate_workflow_text()
            self.workflow_updated.emit(workflow_text)
            
            return connection
        return None
        
    def generate_workflow_text(self):
        """生成工作流文本
        
        Returns:
            工作流定义文本
        """
        workflow_lines = []
        for connection in self.connections:
            source_name = connection.source_node.name
            source_prompt = connection.source_node.prompt
            target_name = connection.target_node.name
            target_prompt = connection.target_node.prompt
            message = connection.name
            
            # 格式化为工作流语法
            line = f'{source_name} |"{source_prompt}"|--> {target_name} |"{target_prompt}"| : {{{message}}}'
            workflow_lines.append(line)
        
        return '\n'.join(workflow_lines)
    
    def clear(self):
        """清空画布"""
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()
    
    def get_workflow_data(self):
        """获取工作流数据"""
        workflow_data = []
        for connection in self.connections:
            source_name = connection.source_node.name
            source_prompt = connection.source_node.prompt
            target_name = connection.target_node.name
            target_prompt = connection.target_node.prompt
            connection_name = connection.name
            
            workflow_data.append({
                'source': source_name,
                'source_prompt': source_prompt,
                'target': target_name,
                'target_prompt': target_prompt,
                'connection': connection_name
            })
        return workflow_data
    
    # 重写事件处理方法
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if self.connection_mode and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # 在连接模式下，按住Shift键选择目标节点
            pos = self.view.mapToScene(event.pos())
            items = self.scene.items(pos)
            
            for item in items:
                if isinstance(item, NodeItem) and item != self.source_node:
                    # 弹出对话框输入连接名称
                    connection_name, ok = QInputDialog.getText(
                        self, "创建连接", "请输入连接名称:"
                    )
                    
                    if ok and connection_name:
                        # 创建连接
                        self.add_connection(
                            self.source_node.name, 
                            item.name, 
                            connection_name
                        )
                    
                    # 退出连接模式
                    self.connection_mode = False
                    self.source_node = None
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    break
        
        # 将事件传递给视图
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        # 获取鼠标位置下的图形项
        pos = self.view.mapToScene(event.pos())
        items = self.scene.items(pos)
        
        # 创建右键菜单
        menu = QMenu(self)
        
        for item in items:
            if isinstance(item, NodeItem):
                # 节点右键菜单
                create_connection_action = menu.addAction("创建连接")
                edit_prompt_action = menu.addAction("编辑提示词")
                delete_action = menu.addAction("删除节点")
                
                # 显示菜单并获取选择的动作
                action = menu.exec(event.globalPos())
                
                if action == create_connection_action:
                    # 进入连接创建模式
                    self.connection_mode = True
                    self.source_node = item
                    self.setCursor(Qt.CursorShape.CrossCursor)  # 改变鼠标样式
                    QMessageBox.information(self, "创建连接", "请按住Shift键并点击目标节点")
                
                elif action == edit_prompt_action:
                    # 编辑节点提示词
                    prompt, ok = QInputDialog.getText(
                        self, "编辑提示词", "请输入节点提示词:", 
                        text=item.prompt
                    )
                    
                    if ok:
                        item.set_prompt(prompt)
                        # 发出工作流更新信号，传递工作流文本
                        workflow_text = self.generate_workflow_text()
                        self.workflow_updated.emit(workflow_text)
                
                elif action == delete_action:
                    # 删除节点及相关连接
                    self.delete_node(item)
                
                return
        
        # 空白区域右键菜单
        add_node_action = menu.addAction("添加节点")
        
        action = menu.exec(event.globalPos())
        
        if action == add_node_action:
            # 添加新节点
            node_name, ok = QInputDialog.getText(
                self, "添加节点", "请输入节点名称:"
            )
            
            if ok and node_name:
                self.add_node(node_name, pos.x(), pos.y())
                # 发出工作流更新信号，传递工作流文本
                workflow_text = self.generate_workflow_text()
                self.workflow_updated.emit(workflow_text)
    
    def delete_node(self, node):
        """删除节点及相关连接"""
        # 删除与该节点相关的所有连接
        connections_to_remove = []
        for connection in self.connections:
            if connection.source_node == node or connection.target_node == node:
                self.scene.removeItem(connection)
                connections_to_remove.append(connection)
        
        for connection in connections_to_remove:
            self.connections.remove(connection)
        
        # 删除节点
        self.scene.removeItem(node)
        for name, node_item in list(self.nodes.items()):
            if node_item == node:
                del self.nodes[name]
                break
        
        # 发出工作流更新信号，传递工作流文本
        workflow_text = self.generate_workflow_text()
        self.workflow_updated.emit(workflow_text)
    
    def load_workflow(self, workflow_text: str):
        """从工作流文本加载并更新绘图
        
        Args:
            workflow_text: 工作流定义文本
        """
        # 使用WorkflowParser解析工作流文本
        from workflow.parser import WorkflowParser
        parser = WorkflowParser()
        
        if parser.parse(workflow_text):
            # 获取所有Agent和连接
            agents = parser.get_agents()
            connections = parser.get_connections()
            
            # 转换为工作流数据格式
            workflow_data = []
            for source, target, message in connections:
                workflow_data.append({
                    'source': source,
                    'source_prompt': parser.get_agent_prompt(source),
                    'target': target,
                    'target_prompt': parser.get_agent_prompt(target),
                    'connection': message
                })
            
            # 更新绘图
            self.update_from_workflow_data(workflow_data)
        else:
            # 解析失败，不更新绘图
            print("工作流解析失败:", parser.get_errors())
    
    def update_from_workflow_data(self, workflow_data):
        """从工作流数据更新绘图"""
        self.clear()
        
        # 创建所有节点
        node_positions = {}  # 记录节点位置
        x, y = 100, 100
        
        for item in workflow_data:
            source_name = item['source']
            target_name = item['target']
            
            # 添加源节点（如果不存在）
            if source_name not in self.nodes:
                if source_name in node_positions:
                    pos_x, pos_y = node_positions[source_name]
                else:
                    pos_x, pos_y = x, y
                    node_positions[source_name] = (pos_x, pos_y)
                    x += 150  # 水平排列节点
                
                source_node = self.add_node(source_name, pos_x, pos_y)
                if 'source_prompt' in item:
                    source_node.set_prompt(item['source_prompt'])
            
            # 添加目标节点（如果不存在）
            if target_name not in self.nodes:
                if target_name in node_positions:
                    pos_x, pos_y = node_positions[target_name]
                else:
                    pos_x, pos_y = x, y + 100  # 下一行
                    node_positions[target_name] = (pos_x, pos_y)
                    x += 150  # 水平排列节点
                
                target_node = self.add_node(target_name, pos_x, pos_y)
                if 'target_prompt' in item:
                    target_node.set_prompt(item['target_prompt'])
        
        # 创建所有连接
        for item in workflow_data:
            source_name = item['source']
            target_name = item['target']
            connection_name = item.get('connection', '')
            
            self.add_connection(source_name, target_name, connection_name)
    
    def wheelEvent(self, event):
        """鼠标滚轮事件 - 用于缩放"""
        # 获取滚轮增量
        delta = event.angleDelta().y()
        
        # 计算新的缩放值
        if delta > 0:
            # 放大
            new_value = min(self.zoom_slider.value() + 10, self.zoom_slider.maximum())
        else:
            # 缩小
            new_value = max(self.zoom_slider.value() - 10, self.zoom_slider.minimum())
        
        # 设置滑块值，会触发zoom_changed
        self.zoom_slider.setValue(new_value)
        
        # 阻止事件传递
        event.accept()

