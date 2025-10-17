# 运行时模块交互详细分析

## 1. 游戏启动时的模块交互

### 初始化序列
```python
# CCmon5C.py 中的初始化过程
class PokemonGame:
    def __init__(self):
        # 1. 基础状态初始化
        self.state = GameState.EXPLORING
        
        # 2. 导入并使用技能管理器 (来自 skills.py)
        from skills import skill_manager
        self.skill_manager = skill_manager
        
        # 3. 创建战斗管理器实例 (来自 combat.py)
        self.combat_manager = CombatManager(self)
        
        # 4. 创建UI渲染器实例 (来自 ui_renderer.py)
        self.ui_renderer = UIRenderer(self)
```

### 依赖注入模式
- **主程序**作为依赖注入容器，将自身实例传递给各模块
- **战斗管理器**和**UI渲染器**都持有主程序的引用，可以访问游戏状态

## 2. 战斗系统的模块交互

### 战斗开始流程
```
用户遇敌 (CCmon5C.py)
    ↓
调用 combat_manager.start_battle()
    ↓
CombatManager 初始化战斗状态
    ↓
从 skills.py 获取敌人技能列表
    ↓
切换游戏状态到 BATTLE
    ↓
UI渲染器绘制战斗界面
```

### 技能使用流程
```
玩家选择技能 (ui_renderer.py)
    ↓
传递给 combat_manager.process_battle_turn()
    ↓
CombatManager 调用 skill_manager.use_skill_on_pokemon()
    ↓
SkillManager 计算技能效果
    ↓
返回伤害值和状态消息
    ↓
CombatManager 应用效果到目标
    ↓
UI渲染器显示战斗结果
```

## 3. UI系统的模块交互

### 渲染流程
```python
# 主游戏循环中的渲染调用
def render(self, screen):
    if self.state == GameState.BATTLE:
        # UIRenderer 调用多个子模块
        self.ui_renderer.draw_battle(screen)
            ↓
        # 内部调用链
        self.popup_renderer.draw_popup_frame()  # 弹窗渲染
        self.ui_utils.draw_progress_bar()       # 进度条
        self.draw_multiline_text()              # 文本渲染
```

### 事件处理流程
```
pygame事件 → CCmon5C.py.handle_input()
    ↓
根据游戏状态分发事件
    ↓
战斗状态 → combat_manager.handle_input()
探索状态 → 直接处理移动逻辑
菜单状态 → ui_renderer.handle_menu_input()
```

## 4. 数据流向分析

### 技能数据流
```
UNIFIED_SKILLS_DATABASE (skills.py)
    ↓ 读取
SkillManager.get_skill() (skills.py)
    ↓ 调用
CombatManager.process_battle_turn() (combat.py)
    ↓ 结果
PokemonGame.battle_messages (CCmon5C.py)
    ↓ 显示
UIRenderer.draw_battle() (ui_renderer.py)
```

### 游戏状态流
```
用户操作 → CCmon5C.py (状态变更)
    ↓ 通知
CombatManager (战斗状态)
    ↓ 同步
UIRenderer (界面更新)
```

## 5. 模块间通信机制

### 1. 直接方法调用
```python
# 主程序调用模块方法
self.combat_manager.start_battle(enemy)
self.ui_renderer.draw_exploration(screen)
```

### 2. 共享数据访问
```python
# 模块访问主程序数据
class CombatManager:
    def __init__(self, game_instance):
        self.game = game_instance  # 持有主程序引用
    
    def get_player_pokemon(self):
        return self.game.player.get_active_pokemon()
```

### 3. 事件驱动模式
```python
# 战斗结果通过修改主程序状态来通知UI
def end_battle(self):
    self.game.state = GameState.EXPLORING  # 状态变更
    self.game.battle_messages.append("战斗结束")  # 消息传递
```

## 6. 性能优化的交互设计

### 缓存机制
```python
# UI渲染器中的缓存
class UIRenderer:
    def __init__(self):
        self._cached_surfaces = {}  # 缓存渲染结果
    
    def draw_battle(self, screen):
        if self._battle_cache_dirty:
            self._update_battle_cache()  # 只在需要时更新
```

### 延迟加载
```python
# 技能系统的延迟初始化
class SkillManager:
    def __init__(self):
        self._skills = None  # 延迟加载
    
    def get_skill(self, name):
        if self._skills is None:
            self._load_skills()  # 首次使用时加载
```

## 7. 错误处理和容错机制

### 模块间错误传播
```python
# 战斗管理器的错误处理
def process_battle_turn(self):
    try:
        result = self.skill_manager.use_skill(skill_name)
    except SkillNotFoundError:
        self.game.battle_messages.append("技能不存在")
        return False
```

### 降级处理
```python
# UI渲染器的降级处理
def draw_pokemon_image(self, pokemon_name):
    try:
        return self.images.pokemon[pokemon_name]
    except KeyError:
        return self.create_default_image()  # 使用默认图像
```

## 8. 模块扩展性设计

### 插件化接口
```python
# 技能系统支持动态扩展
class SkillManager:
    def register_skill_plugin(self, plugin):
        """允许外部注册新技能"""
        self.plugins.append(plugin)
```

### 事件系统
```python
# 战斗系统的事件通知
class CombatManager:
    def __init__(self):
        self.event_listeners = []
    
    def notify_battle_end(self):
        for listener in self.event_listeners:
            listener.on_battle_end()
```

## 总结

这种模块化设计实现了：

1. **清晰的职责分离**：每个模块专注于特定功能
2. **松耦合架构**：模块间通过接口而非直接依赖交互
3. **高内聚设计**：相关功能集中在同一模块内
4. **可扩展性**：新功能可以作为新模块添加
5. **可测试性**：每个模块都可以独立测试
6. **可维护性**：修改一个模块不会影响其他模块

这种设计使得代码更加组织化、可维护，并且为未来的功能扩展提供了良好的基础。