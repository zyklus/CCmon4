# 顾问游戏模块化架构图

## 模块层次结构

```
                    ┌─────────────────────┐
                    │     CCmon5C.py      │
                    │     (主程序)        │
                    │  - 游戏循环         │
                    │  - 状态管理         │
                    │  - 事件分发         │
                    └─────────┬───────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
    │   skills.py     │ │ combat.py   │ │ ui_renderer.py  │
    │   (技能系统)    │ │ (战斗管理)  │ │  (UI渲染)       │
    │ - 技能数据库    │ │ - 战斗逻辑  │ │ - 界面渲染      │
    │ - 技能管理器    │ │ - 回合处理  │ │ - 事件处理      │
    │ - SP系统        │ │ - 动画管理  │ │ - 布局管理      │
    └─────────────────┘ └──────┬──────┘ └────────┬────────┘
                               │                 │
                               │ uses            │ uses
                               │                 │
                               ▼                 ▼
                    ┌─────────────────┐ ┌─────────────────┐
                    │   skills.py     │ │popup_renderer.py│
                    │ (skill_manager) │ │   ui_utils.py   │
                    └─────────────────┘ └─────────────────┘
                                        
                    ┌─────────────────────────────────────┐
                    │          底层依赖                   │
                    │ pygame, random, sys, os, json      │
                    └─────────────────────────────────────┘
```

## 模块详细说明

### 1. 主程序模块 (CCmon5C.py)
**职责**：
- 游戏主循环和状态管理
- 事件分发和协调各模块
- 游戏数据的持久化
- 初始化各个子系统

**关键类**：
- `PokemonGame`: 主游戏类
- `GameState`: 游戏状态枚举
- `Player`, `Pokemon`, `GameMap`: 核心数据类

### 2. 技能系统模块 (skills.py)
**职责**：
- 管理所有技能数据和逻辑
- 技能效果计算和应用
- SP系统管理

**关键组件**：
- `SkillManager`: 技能管理器
- `UNIFIED_SKILLS_DATABASE`: 技能数据库
- `SkillAttribute`, `EffectType`: 技能属性枚举
- `SP_CONFIG`: SP系统配置

### 3. 战斗管理模块 (combat.py)
**职责**：
- 战斗流程控制
- 回合制逻辑处理
- 战斗动画管理
- 经验值和奖励计算

**关键组件**：
- `CombatManager`: 战斗管理器
- `BattleAction`, `BattleResult`: 战斗枚举
- 战斗状态机逻辑

### 4. UI渲染模块 (ui_renderer.py)
**职责**：
- 所有界面的渲染
- UI布局管理
- 用户交互处理

**关键组件**：
- `UIRenderer`: 主UI渲染器
- 各种界面绘制方法
- 事件处理逻辑

### 5. 工具模块
**popup_renderer.py**: 弹窗渲染工具
**ui_utils.py**: UI通用工具函数
**scrollbar_component.py**: 滚动条组件

## 运行时交互流程

### 游戏启动流程
```
1. CCmon5C.py 初始化
   ├── 创建 CombatManager 实例
   ├── 创建 UIRenderer 实例  
   ├── 导入 skill_manager
   └── 初始化游戏数据

2. 进入主游戏循环
   ├── 事件处理
   ├── 游戏状态更新
   └── 界面渲染
```

### 战斗流程交互
```
1. 玩家遇敌 (CCmon5C.py)
   └── 调用 combat_manager.start_battle()

2. 战斗管理器处理 (combat.py)
   ├── 初始化战斗状态
   ├── 调用 skill_manager 获取技能信息
   └── 返回战斗界面状态

3. UI渲染 (ui_renderer.py)
   ├── 绘制战斗界面
   ├── 显示技能选项
   └── 处理用户输入

4. 技能使用 (skills.py)
   ├── 验证SP消耗
   ├── 计算技能效果
   └── 返回伤害/治疗结果

5. 战斗结算 (combat.py)
   ├── 应用技能效果
   ├── 检查战斗结束条件
   └── 计算经验值奖励
```

### 界面渲染流程
```
1. 主程序调用 (CCmon5C.py)
   └── ui_renderer.draw_xxx(screen)

2. UI渲染器 (ui_renderer.py)
   ├── 根据游戏状态选择渲染方法
   ├── 调用 popup_renderer 绘制弹窗
   ├── 调用 ui_utils 绘制UI元素
   └── 更新显示缓冲区

3. 工具模块协助
   ├── popup_renderer: 标准化弹窗
   ├── ui_utils: 通用UI组件
   └── scrollbar_component: 滚动条
```

## 模块间依赖关系

### 强依赖关系
- `CCmon5C.py` → `skills.py` (导入skill_manager)
- `CCmon5C.py` → `combat.py` (创建CombatManager实例)  
- `CCmon5C.py` → `ui_renderer.py` (创建UIRenderer实例)
- `combat.py` → `skills.py` (使用技能系统)

### 弱依赖关系
- `ui_renderer.py` → `popup_renderer.py` (可选使用)
- `ui_renderer.py` → `ui_utils.py` (工具函数)
- 所有模块 → `pygame` (底层图形库)

### 数据流向
```
用户输入 → CCmon5C.py → combat.py → skills.py
                    ↓
              ui_renderer.py ← popup_renderer.py
                    ↓              ↑
              ui_utils.py ←────────┘
```

## 模块化优势

1. **职责分离**: 每个模块负责特定功能
2. **降低耦合**: 模块间通过接口交互
3. **提高复用**: 工具模块可在多处使用
4. **便于测试**: 每个模块可独立测试
5. **易于维护**: 修改一个模块不影响其他模块
6. **支持扩展**: 新功能可以新模块形式添加