import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# 创建图形
fig, ax = plt.subplots(1, 1, figsize=(14, 10))

# 定义颜色
colors = {
    'main': '#FF6B6B',      # 红色 - 主程序
    'skills': '#4ECDC4',    # 青色 - 技能系统
    'combat': '#45B7D1',    # 蓝色 - 战斗系统
    'ui': '#96CEB4',        # 绿色 - UI系统
    'utils': '#FFEAA7',     # 黄色 - 工具类
    'existing': '#DDA0DD'   # 紫色 - 现有模块
}

# 定义模块位置和大小
modules = {
    'CCmon5C.py\n(主程序)': {'pos': (7, 8), 'size': (2.5, 1.2), 'color': colors['main']},
    'skills.py\n(技能系统)': {'pos': (2, 6), 'size': (2.2, 1.2), 'color': colors['skills']},
    'combat.py\n(战斗管理)': {'pos': (7, 5.5), 'size': (2.2, 1.2), 'color': colors['combat']},
    'ui_renderer.py\n(UI渲染)': {'pos': (12, 6), 'size': (2.2, 1.2), 'color': colors['ui']},
    'popup_renderer.py\n(弹窗渲染)': {'pos': (12, 3.5), 'size': (2.2, 1), 'color': colors['utils']},
    'ui_utils.py\n(UI工具)': {'pos': (12, 1.5), 'size': (2.2, 1), 'color': colors['utils']},
    'scrollbar_component.py\n(滚动条组件)': {'pos': (9, 1.5), 'size': (2.2, 1), 'color': colors['utils']},
    'pygame\n(游戏引擎)': {'pos': (2, 1.5), 'size': (2, 1), 'color': colors['existing']},
    'random/sys/os\n(系统库)': {'pos': (5, 1.5), 'size': (2, 1), 'color': colors['existing']}
}

# 绘制模块
module_boxes = {}
for name, info in modules.items():
    x, y = info['pos']
    w, h = info['size']
    
    # 创建圆角矩形
    box = FancyBboxPatch(
        (x-w/2, y-h/2), w, h,
        boxstyle="round,pad=0.1",
        facecolor=info['color'],
        edgecolor='black',
        linewidth=2,
        alpha=0.8
    )
    ax.add_patch(box)
    
    # 添加文本
    ax.text(x, y, name, ha='center', va='center', 
           fontsize=10, fontweight='bold', wrap=True)
    
    module_boxes[name] = (x, y, w, h)

# 定义连接关系
connections = [
    # 主程序的依赖关系
    ('CCmon5C.py\n(主程序)', 'skills.py\n(技能系统)', 'imports & uses', 'blue'),
    ('CCmon5C.py\n(主程序)', 'combat.py\n(战斗管理)', 'imports & uses', 'blue'),
    ('CCmon5C.py\n(主程序)', 'ui_renderer.py\n(UI渲染)', 'imports & uses', 'blue'),
    
    # 战斗系统的依赖
    ('combat.py\n(战斗管理)', 'skills.py\n(技能系统)', 'uses skill_manager', 'green'),
    
    # UI系统的依赖
    ('ui_renderer.py\n(UI渲染)', 'popup_renderer.py\n(弹窗渲染)', 'uses', 'orange'),
    ('ui_renderer.py\n(UI渲染)', 'ui_utils.py\n(UI工具)', 'uses', 'orange'),
    
    # 底层依赖
    ('CCmon5C.py\n(主程序)', 'pygame\n(游戏引擎)', 'uses', 'gray'),
    ('CCmon5C.py\n(主程序)', 'random/sys/os\n(系统库)', 'uses', 'gray'),
    ('skills.py\n(技能系统)', 'random/sys/os\n(系统库)', 'uses', 'gray'),
    ('combat.py\n(战斗管理)', 'pygame\n(游戏引擎)', 'uses', 'gray'),
    ('ui_renderer.py\n(UI渲染)', 'pygame\n(游戏引擎)', 'uses', 'gray'),
    ('popup_renderer.py\n(弹窗渲染)', 'pygame\n(游戏引擎)', 'uses', 'gray'),
    ('ui_utils.py\n(UI工具)', 'pygame\n(游戏引擎)', 'uses', 'gray'),
]

# 绘制连接线
for source, target, label, color in connections:
    if source in module_boxes and target in module_boxes:
        x1, y1, w1, h1 = module_boxes[source]
        x2, y2, w2, h2 = module_boxes[target]
        
        # 计算连接点
        if x1 < x2:  # 从左到右
            start_x, start_y = x1 + w1/2, y1
            end_x, end_y = x2 - w2/2, y2
        elif x1 > x2:  # 从右到左
            start_x, start_y = x1 - w1/2, y1
            end_x, end_y = x2 + w2/2, y2
        else:  # 垂直连接
            if y1 > y2:  # 从上到下
                start_x, start_y = x1, y1 - h1/2
                end_x, end_y = x2, y2 + h2/2
            else:  # 从下到上
                start_x, start_y = x1, y1 + h1/2
                end_x, end_y = x2, y2 - h2/2
        
        # 绘制箭头
        arrow = patches.FancyArrowPatch(
            (start_x, start_y), (end_x, end_y),
            arrowstyle='->', mutation_scale=20,
            color=color, linewidth=1.5, alpha=0.7
        )
        ax.add_patch(arrow)
        
        # 添加标签
        mid_x, mid_y = (start_x + end_x) / 2, (start_y + end_y) / 2
        ax.text(mid_x, mid_y, label, ha='center', va='bottom', 
               fontsize=8, style='italic', 
               bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))

# 添加图例
legend_elements = [
    patches.Patch(color=colors['main'], label='主程序'),
    patches.Patch(color=colors['skills'], label='技能系统'),
    patches.Patch(color=colors['combat'], label='战斗系统'),
    patches.Patch(color=colors['ui'], label='UI系统'),
    patches.Patch(color=colors['utils'], label='工具模块'),
    patches.Patch(color=colors['existing'], label='外部依赖')
]

ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))

# 设置图形属性
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('顾问游戏模块化架构图', fontsize=16, fontweight='bold', pad=20)

# 添加说明文字
ax.text(8, 0.5, '模块依赖关系：蓝色=主要依赖，绿色=功能调用，橙色=UI依赖，灰色=系统依赖', 
        ha='center', va='center', fontsize=10, style='italic')

plt.tight_layout()
plt.savefig('/workspace/module_architecture.png', dpi=300, bbox_inches='tight')
plt.show()