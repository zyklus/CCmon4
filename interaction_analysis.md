# 模块间实际运行时交互分析

## 模块关系图 (ASCII版本)

```
┌─────────────────────────────────────────────────────────────────┐
│                        CCmon5C.py (主程序)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  PokemonGame    │  │   GameState     │  │   Player/Map    │  │
│  │  - 游戏循环     │  │   - 状态管理   │  │   - 数据模型    │  │
│  │  - 事件分发     │  │   - 状态转换   │  │   - 业务逻辑    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────┬───────────────┬───────────────┬───────────────────┘
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   skills.py     │ │   combat.py     │ │ ui_renderer.py  │
│ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │
│ │SkillManager │ │ │ │CombatManager│ │ │ │ UIRenderer  │ │
│ │技能数据库   │ │ │ │战斗逻辑     │ │ │ │界面渲染     │ │
│ │SP系统       │ │ │ │回合处理     │◄─┼─┤ │事件处理     │ │
│ │效果计算     │ │ │ │动画管理     │ │ │ │布局管理     │ │
│ └─────────────┘ │ │ └─────────────┘ │ │ └─────────────┘ │
└─────────────────┘ └─────────────────┘ └─────────┬───────┘
          ▲                   │                   │
          └───────────────────┘                   ▼
                                        ┌─────────────────┐
                                        │  工具模块群     │
                                        │ ┌─────────────┐ │
                                        │ │popup_renderer│ │
                                        │ │ui_utils     │ │
                                        │ │scrollbar    │ │
                                        │ └─────────────┘ │
                                        └─────────────────┘
```

## 实际运行时交互流程

### 1. 游戏启动流程
```
程序启动
    ↓
pygame.init() 
    ↓
创建 PokemonGame 实例
    ├── 初始化基础状态 (state = EXPLORING)
    ├── 创建 CombatManager(self) 
    ├── 创建 UIRenderer(self)
    └── 导入 skill_manager (来自 skills.py)
    ↓
进入主游戏循环 game.run()
```

### 2. 战斗触发流程 (实际代码路径)
```python
# 1. 玩家移动遇敌 (CCmon5C.py)
def handle_exploration_input(self, event):
    # 移动逻辑...
    if encounter_enemy:
        self.start_battle("wild")

# 2. 开始战斗 (CCmon5C.py)  
def start_battle(self, battle_type="wild"):
    self.combat_manager.start_battle(battle_type, enemy_pokemon)
    self.state = GameState.BATTLE

# 3. 战斗管理器初始化 (combat.py)
def start_battle(self, battle_type, enemy_pokemon):
    self.is_boss_battle = battle_type in ["boss", "mini_boss"]
    # 设置战斗状态...
    
# 4. UI切换到战斗界面 (主循环中)
def render(self, screen):
    if self.state == GameState.BATTLE:
        self.ui_renderer.draw_battle(screen)
```

### 3. 技能使用的完整调用链
```python
# 1. 玩家点击技能按钮 (ui_renderer.py)
def handle_battle_input(self, event):
    if button_clicked == "skill_1":
        self.game.combat_manager.process_battle_turn(move_idx=0, action="attack")

# 2. 战斗管理器处理 (combat.py)
def process_battle_turn(self, move_idx=None, action=None):
    if action == "attack":
        move = player_pkm.moves[move_idx]
        # 调用技能系统
        damage, messages = skill_manager.use_skill_on_pokemon(
            move["name"], player_pkm, enemy_pkm, allies
        )

# 3. 技能管理器执行 (skills.py)
def use_skill_on_pokemon(self, skill_name, user_pokemon, target_pokemon, allies):
    skill_data = UNIFIED_SKILLS_DATABASE.get(skill_name)
    # 计算伤害和效果...
    return damage, messages

# 4. 结果返回并显示 (combat.py → ui_renderer.py)
self.game.battle_messages.append(message)
# UI渲染器在下一帧显示消息
```

### 4. 数据流向图
```
用户输入 → pygame事件 → CCmon5C.py.handle_input()
    ↓
根据游戏状态分发
    ├── EXPLORING → 移动/菜单处理
    ├── BATTLE → combat_manager.handle_input()
    └── MENU → ui_renderer.handle_menu()
    ↓
状态变更 → self.state = new_state
    ↓
主循环 render() → ui_renderer.draw_xxx()
    ↓
屏幕更新 → pygame.display.flip()
```

## 模块间的具体依赖关系

### 强依赖 (直接导入)
```python
# CCmon5C.py
from skills import skill_manager, UNIFIED_SKILLS_DATABASE
from combat import CombatManager  
from ui_renderer import UIRenderer

# combat.py  
from skills import skill_manager, UNIFIED_SKILLS_DATABASE, SkillCategory

# ui_renderer.py
from popup_renderer import PopupRenderer
from ui_utils import UIUtils
```

### 运行时依赖 (对象引用)
```python
# CombatManager 持有游戏实例引用
class CombatManager:
    def __init__(self, game_instance):
        self.game = game_instance  # 可访问 game.player, game.state 等

# UIRenderer 同样持有游戏实例引用  
class UIRenderer:
    def __init__(self, game_instance):
        self.game = game_instance  # 可访问游戏数据进行渲染
```

### 数据共享模式
```python
# 通过主程序实例共享数据
combat_manager.game.player.get_active_pokemon()  # 获取当前顾问
combat_manager.game.battle_messages.append(msg)  # 添加战斗消息
ui_renderer.game.state                           # 获取游戏状态
```

## 性能优化的交互设计

### 1. 缓存机制
```python
# UI渲染器中的缓存 (实际存在于代码中)
class UIRenderer:
    def draw_battle(self, screen):
        if self._battle_cache_dirty:
            self._update_battle_cache()
        screen.blit(self._cached_battle_surface, (0, 0))
```

### 2. 事件驱动更新
```python
# 只在状态变化时重新渲染
def update(self):
    if self.state != self._last_state:
        self._need_full_redraw = True
        self._last_state = self.state
```

### 3. 延迟计算
```python
# 技能效果只在使用时计算
def use_skill(self, skill_name):
    if skill_name not in self._calculated_effects:
        self._calculated_effects[skill_name] = self._calculate_effects(skill_name)
```

## 错误处理和容错

### 模块间错误传播
```python
# combat.py 中的错误处理
try:
    damage, messages = skill_manager.use_skill_on_pokemon(...)
except Exception as e:
    print(f"技能使用错误: {e}")
    self.game.battle_messages.append("技能使用失败")
```

### 降级处理
```python
# ui_renderer.py 中的降级处理
def draw_pokemon_image(self, pokemon_name):
    if pokemon_name in self.game.images.pokemon:
        return self.game.images.pokemon[pokemon_name]
    else:
        return self.create_default_pokemon_image()
```

## 模块化带来的实际好处

### 1. 代码组织清晰
- 技能相关代码全部在 `skills.py` 中
- 战斗逻辑全部在 `combat.py` 中  
- UI渲染全部在 `ui_renderer.py` 中

### 2. 便于调试和测试
```python
# 可以独立测试技能系统
from skills import skill_manager
result = skill_manager.use_skill("酒精打击", user, target)

# 可以独立测试战斗逻辑
from combat import CombatManager
combat = CombatManager(mock_game)
combat.start_battle("wild", mock_enemy)
```

### 3. 支持并行开发
- 不同开发者可以同时修改不同模块
- 减少代码冲突的可能性

### 4. 便于功能扩展
```python
# 添加新技能只需修改 skills.py
# 添加新战斗机制只需修改 combat.py
# 添加新UI界面只需修改 ui_renderer.py
```

这种模块化设计实现了代码的高内聚、低耦合，使得整个项目更加可维护和可扩展。