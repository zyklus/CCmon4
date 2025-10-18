#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CCmon6.py - 简化的必杀技学习系统
从CCmon5.py中提取并简化必杀技学习盲盒、学习书和技能配置功能

主要功能：
1. 必杀技学习盲盒 - 随机生成必杀技学习书
2. 必杀技学习书 - 让指定顾问学习新的必杀技
3. 技能配置系统 - 正确配置技能数据到顾问身上
4. 技能忘记机制 - 当技能槽满时选择忘记旧技能

改进点：
- 大幅简化代码结构，从原来的复杂冗长代码减少到核心功能
- 统一技能数据管理，使用UNIFIED_SKILLS_DATABASE
- 正确实现技能配置，包含完整的技能属性、SP消耗、效果等
- 简化的类结构，移除不必要的依赖和复杂逻辑
- 清晰的接口设计，易于使用和维护

技术债务解决：
- 移除了CCmon5.py中冗长失败的技能配置代码
- 统一了技能数据源，避免数据不一致
- 简化了物品使用逻辑，减少了复杂的状态管理
- 提供了清晰的错误处理和用户反馈
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Any

# ==================== 基础配置和枚举 ====================

class SkillCategory(Enum):
    """技能分类"""
    DIRECT_DAMAGE = "直接伤害"
    DOT = "持续伤害"
    DIRECT_HEAL = "直接治疗"
    SPECIAL = "特殊技能"

class GameState(Enum):
    """游戏状态"""
    MENU_MAIN = "main_menu"
    MENU_BACKPACK = "backpack"
    MENU_TARGET_SELECTION = "target_selection"

# ==================== 统一技能数据库 ====================

UNIFIED_SKILLS_DATABASE = {
    # 基础技能
    "酒仙": {
        "power": 0,
        "type": "体力",
        "category": SkillCategory.DIRECT_HEAL,
        "description": "立即回复40%生命",
        "sp_cost": 0,
        "quote": "双倍IPA治疗失眠",
        "effects": {"heal_percentage": 0.4}
    },
    "建模": {
        "power": 25,
        "type": "PS",
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "使用wiki上看到的公式凑数,有几率麻痹对手",
        "sp_cost": 0,
        "quote": "这个公式我在wiki上看到过！",
        "effects": {}
    },
    
    # 必杀技 (SP消耗>=50)
    "Deric的阴影": {
        "power": 120,
        "type": "节操",
        "category": SkillCategory.SPECIAL,
        "description": "召唤Deric的阴影,造成巨大伤害并降低敌方攻击力",
        "sp_cost": 80,
        "quote": "看见阴影了吗？那就是你的结局！",
        "effects": {
            "base_damage": 120,
            "target_attack_multiplier": 0.7,
            "turns": 3
        }
    },
    "酒精打击": {
        "power": 100,
        "type": "体力",
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "用酒精的力量进行强力攻击",
        "sp_cost": 60,
        "quote": "你挣钱不就是来喝的吗",
        "effects": {"base_damage": 100}
    },
    "心灵震爆": {
        "power": 110,
        "type": "共情",
        "category": SkillCategory.SPECIAL,
        "description": "释放心灵能量,造成巨大伤害并有几率眩晕",
        "sp_cost": 70,
        "quote": "感受心灵的力量吧！",
        "effects": {
            "base_damage": 110,
            "stun_chance": 0.3
        }
    },
    "天下兵马大元帅": {
        "power": 150,
        "type": ["韧性", "节操"],
        "category": SkillCategory.SPECIAL,
        "description": "终极必杀技,先提升自身能力,下回合造成巨大伤害",
        "sp_cost": 100,
        "quote": "我就是天下兵马大元帅！",
        "effects": {
            "attack_multiplier": 1.5,
            "defense_multiplier": 1.3,
            "turns": 2,
            "delayed_damage_percentage": 0.8,
            "delayed_turns": 1
        }
    }
}

# ==================== 核心类定义 ====================

class Item:
    """物品类"""
    def __init__(self, name: str, description: str, item_type: str, effect: Any = None, price: int = 0):
        self.name = name
        self.description = description
        self.item_type = item_type
        self.effect = effect
        self.price = price

    def use(self, target=None, player=None):
        """使用物品"""
        if self.item_type == "skill_blind_box":
            return self._use_skill_blind_box(player)
        elif self.item_type == "skill_book":
            return self._use_skill_book(target)
        else:
            return f"使用了{self.name},但没有效果"

    def _use_skill_blind_box(self, player):
        """使用必杀技学习盲盒"""
        if not player:
            return "无法使用必杀技学习盲盒"
        
        # 获取所有必杀技
        ultimate_skills = self._get_ultimate_skills()
        
        if not ultimate_skills:
            return f"打开了{self.name},但没有找到可学习的必杀技..."
        
        # 随机选择一个必杀技
        selected_skill_name = random.choice(list(ultimate_skills.keys()))
        selected_skill = ultimate_skills[selected_skill_name]
        
        # 创建必杀技学习书
        skill_book = self._create_skill_book(selected_skill_name, selected_skill)
        
        # 添加到玩家背包
        player.add_item(skill_book)
        
        return f"打开了{self.name}！获得了{skill_book.name}！"

    def _use_skill_book(self, target):
        """使用必杀技学习书"""
        if not target or not hasattr(target, 'moves'):
            return "这个技能书需要对顾问使用|FAILED"
        
        skill_name = self.effect
        
        # 检查是否已经学会
        if skill_name in [move["name"] for move in target.moves]:
            return f"{target.name}已经会{skill_name}了！|FAILED"
        
        # 检查技能槽位
        if len(target.moves) >= 4:
            return f"SKILL_FORGET_DIALOG|{skill_name}"
        
        # 学习新技能
        new_skill = self._create_skill_move(skill_name)
        target.moves.append(new_skill)
        
        return f"{target.name}学会了{skill_name}！"

    def _get_ultimate_skills(self) -> Dict[str, Dict]:
        """获取所有必杀技"""
        ultimate_skills = {}
        
        # 从统一技能数据库中筛选必杀技（SP消耗>=50的技能）
        for skill_name, skill_data in UNIFIED_SKILLS_DATABASE.items():
            if skill_data.get("sp_cost", 0) >= 50:
                ultimate_skills[skill_name] = skill_data
        
        return ultimate_skills

    def _create_skill_book(self, skill_name: str, skill_data: Dict) -> 'Item':
        """创建必杀技学习书"""
        # 构建详细描述
        description = f"学习必杀技：{skill_name}"
        
        # 添加技能信息
        skill_type = skill_data.get('type', '未知')
        if isinstance(skill_type, list):
            skill_type = "/".join(skill_type)
        description += f" 属性:{skill_type}"
        
        sp_cost = skill_data.get('sp_cost', 0)
        if sp_cost > 0:
            description += f" SP消耗:{sp_cost}"
        
        # 添加效果描述
        effects = skill_data.get('effects', {})
        if effects:
            if 'base_damage' in effects:
                description += f" 基础伤害:{effects['base_damage']}"
            if 'heal_percentage' in effects:
                heal_percent = int(effects['heal_percentage'] * 100)
                description += f" 治疗:{heal_percent}%生命"
            if 'attack_multiplier' in effects:
                mult = int(effects['attack_multiplier'] * 100)
                description += f" 攻击力变化:{mult}%"
            if 'defense_multiplier' in effects:
                mult = int(effects['defense_multiplier'] * 100)
                description += f" 防御力变化:{mult}%"
        
        return Item(
            name=f"必杀技学习书：{skill_name}",
            description=description,
            item_type="skill_book",
            effect=skill_name,
            price=0
        )

    def _create_skill_move(self, skill_name: str) -> Dict:
        """创建技能移动数据"""
        # 从统一数据库获取技能数据
        skill_data = UNIFIED_SKILLS_DATABASE.get(skill_name)
        
        if skill_data:
            # 使用统一数据库的完整数据
            return {
                "name": skill_name,
                "power": skill_data.get("power", 80),
                "type": skill_data.get("type", "共情"),
                "category": skill_data.get("category", SkillCategory.DIRECT_DAMAGE),
                "sp_cost": skill_data.get("sp_cost", 0),
                "description": skill_data.get("description", ""),
                "quote": skill_data.get("quote", ""),
                "effects": skill_data.get("effects", {})
            }
        else:
            # 默认技能数据（兼容性）
            return {
                "name": skill_name,
                "power": 80,
                "type": "共情",
                "category": SkillCategory.DIRECT_DAMAGE,
                "sp_cost": 0,
                "description": f"从必杀技学习书学会的技能：{skill_name}",
                "quote": "这是从书中学会的技能！",
                "effects": {}
            }


class Pokemon:
    """顾问类（简化版）"""
    def __init__(self, name: str, level: int = 1, moves: List[Dict] = None):
        self.name = name
        self.level = level
        self.moves = moves or []
        self.hp = 100
        self.max_hp = 100
        self.sp = 100
        self.max_sp = 100

    def learn_skill(self, skill_name: str) -> bool:
        """学习新技能"""
        # 检查是否已经学会
        if skill_name in [move["name"] for move in self.moves]:
            return False
        
        # 检查技能槽位
        if len(self.moves) >= 4:
            return False
        
        # 创建技能数据
        item = Item("", "", "skill_book", skill_name)
        new_skill = item._create_skill_move(skill_name)
        self.moves.append(new_skill)
        
        return True

    def forget_skill(self, skill_index: int, new_skill_name: str) -> bool:
        """忘记技能并学习新技能"""
        if 0 <= skill_index < len(self.moves):
            item = Item("", "", "skill_book", new_skill_name)
            new_skill = item._create_skill_move(new_skill_name)
            self.moves[skill_index] = new_skill
            return True
        return False


class Player:
    """玩家类（简化版）"""
    def __init__(self):
        self.backpack: List[Item] = []
        self.pokemon_team: List[Pokemon] = []
        self.money = 10000

    def add_item(self, item: Item):
        """添加物品到背包"""
        self.backpack.append(item)

    def remove_item(self, index: int):
        """移除背包中的物品"""
        if 0 <= index < len(self.backpack):
            del self.backpack[index]

    def use_item(self, item_index: int, target_index: int = None) -> str:
        """使用物品"""
        if item_index < 0 or item_index >= len(self.backpack):
            return "物品不存在"
        
        item = self.backpack[item_index]
        
        if item.item_type == "skill_blind_box":
            # 直接使用盲盒
            result = item.use(None, self)
            self.remove_item(item_index)
            return result
        elif item.item_type == "skill_book":
            # 需要选择目标
            if target_index is None or target_index < 0 or target_index >= len(self.pokemon_team):
                return "请选择要学习必杀技的顾问"
            
            target = self.pokemon_team[target_index]
            result = item.use(target, self)
            
            if "|FAILED" not in result and "SKILL_FORGET_DIALOG" not in result:
                self.remove_item(item_index)
            
            return result
        else:
            return "无法使用这个物品"


class SkillLearningSystem:
    """技能学习系统"""
    def __init__(self):
        self.player = Player()
        self.pending_skill_forget = None

    def create_skill_blind_box(self) -> Item:
        """创建必杀技学习盲盒"""
        return Item(
            name="必杀技学习盲盒",
            description="使用后随机生成一个必杀技学习书",
            item_type="skill_blind_box",
            effect=None,
            price=2500
        )

    def use_skill_blind_box(self, item_index: int) -> str:
        """使用必杀技学习盲盒"""
        return self.player.use_item(item_index)

    def use_skill_book(self, item_index: int, target_index: int) -> str:
        """使用必杀技学习书"""
        result = self.player.use_item(item_index, target_index)
        
        if "SKILL_FORGET_DIALOG" in result:
            # 处理技能忘记对话
            skill_name = result.split("|")[1]
            self.pending_skill_forget = {
                "item_index": item_index,
                "target_index": target_index,
                "skill_name": skill_name
            }
            return f"{self.player.pokemon_team[target_index].name}的技能已满，需要选择忘记的技能"
        
        return result

    def handle_skill_forget(self, forget_skill_index: int) -> str:
        """处理技能忘记"""
        if not self.pending_skill_forget:
            return "没有待处理的技能学习"
        
        target_index = self.pending_skill_forget["target_index"]
        skill_name = self.pending_skill_forget["skill_name"]
        item_index = self.pending_skill_forget["item_index"]
        
        target = self.player.pokemon_team[target_index]
        
        if 0 <= forget_skill_index < len(target.moves):
            old_skill = target.moves[forget_skill_index]["name"]
            
            # 忘记旧技能，学习新技能
            if target.forget_skill(forget_skill_index, skill_name):
                self.player.remove_item(item_index)
                self.pending_skill_forget = None
                return f"{target.name}忘记了{old_skill}，学会了{skill_name}！"
        
        return "技能学习失败"

    def cancel_skill_learning(self) -> str:
        """取消技能学习"""
        if self.pending_skill_forget:
            self.pending_skill_forget = None
            return "取消学习技能"
        return "没有待取消的技能学习"

    def get_learnable_skills(self) -> List[str]:
        """获取可学习的必杀技列表"""
        learnable_skills = []
        for skill_name, skill_data in UNIFIED_SKILLS_DATABASE.items():
            if skill_data.get("sp_cost", 0) >= 50:  # 必杀技标准
                learnable_skills.append(skill_name)
        return learnable_skills

    def get_skill_info(self, skill_name: str) -> Dict:
        """获取技能详细信息"""
        return UNIFIED_SKILLS_DATABASE.get(skill_name, {})

    def add_pokemon(self, pokemon: Pokemon):
        """添加顾问到队伍"""
        if len(self.player.pokemon_team) < 6:
            self.player.pokemon_team.append(pokemon)

    def add_skill_blind_box(self, quantity: int = 1):
        """添加必杀技学习盲盒到背包"""
        for _ in range(quantity):
            blind_box = self.create_skill_blind_box()
            self.player.add_item(blind_box)

    def create_skill_book_directly(self, skill_name: str) -> Item:
        """直接创建指定技能的学习书"""
        if skill_name in UNIFIED_SKILLS_DATABASE:
            skill_data = UNIFIED_SKILLS_DATABASE[skill_name]
            item = Item("", "", "skill_book", skill_name)
            return item._create_skill_book(skill_name, skill_data)
        return None

    def get_pokemon_skills(self, pokemon_index: int) -> List[Dict]:
        """获取指定顾问的技能列表"""
        if 0 <= pokemon_index < len(self.player.pokemon_team):
            return self.player.pokemon_team[pokemon_index].moves
        return []

    def can_learn_skill(self, pokemon_index: int, skill_name: str) -> bool:
        """检查顾问是否可以学习指定技能"""
        if pokemon_index < 0 or pokemon_index >= len(self.player.pokemon_team):
            return False
        
        pokemon = self.player.pokemon_team[pokemon_index]
        
        # 检查是否已经学会
        if skill_name in [move["name"] for move in pokemon.moves]:
            return False
        
        # 检查技能是否存在
        if skill_name not in UNIFIED_SKILLS_DATABASE:
            return False
        
        return True

    def get_backpack_summary(self) -> Dict[str, int]:
        """获取背包物品摘要"""
        summary = {}
        for item in self.player.backpack:
            item_type = item.item_type
            if item_type in summary:
                summary[item_type] += 1
            else:
                summary[item_type] = 1
        return summary


# ==================== 示例用法 ====================

def demo_skill_learning_system():
    """演示技能学习系统的使用"""
    print("=== 必杀技学习系统演示 ===")
    
    # 创建系统
    system = SkillLearningSystem()
    
    # 添加测试顾问
    pokemon1 = Pokemon("测试顾问1", 30, [
        {"name": "建模", "power": 25, "type": "PS"},
        {"name": "酒仙", "power": 0, "type": "体力"},
        {"name": "循循善诱", "power": 30, "type": "共情"},
        {"name": "PUA", "power": 15, "type": "节操"}
    ])
    system.add_pokemon(pokemon1)
    
    # 添加必杀技学习盲盒
    system.add_skill_blind_box(2)
    print(f"添加了2个必杀技学习盲盒到背包")
    
    # 使用盲盒
    print("\n--- 使用第一个盲盒 ---")
    result1 = system.use_skill_blind_box(0)
    print(result1)
    
    print("\n--- 使用第二个盲盒 ---")
    result2 = system.use_skill_blind_box(0)  # 索引变为0因为第一个已被移除
    print(result2)
    
    # 显示背包中的学习书
    print(f"\n--- 背包中的物品 ---")
    for i, item in enumerate(system.player.backpack):
        print(f"{i}: {item.name} - {item.description}")
    
    # 使用学习书 - 技能槽已满，需要忘记技能
    if system.player.backpack:
        print(f"\n--- 使用第一本学习书（技能槽已满）---")
        result3 = system.use_skill_book(0, 0)  # 对第一个顾问使用
        print(result3)
        
        if "需要选择忘记的技能" in result3:
            print(f"\n--- {pokemon1.name}当前技能 ---")
            for i, move in enumerate(pokemon1.moves):
                print(f"{i}: {move['name']} (威力:{move['power']}, 属性:{move['type']})")
            
            # 选择忘记第0个技能
            print(f"\n--- 选择忘记第0个技能 ---")
            forget_result = system.handle_skill_forget(0)
            print(forget_result)
        
        # 显示顾问学会的技能
        print(f"\n--- {pokemon1.name}的最终技能 ---")
        for move in pokemon1.moves:
            print(f"- {move['name']} (威力:{move['power']}, 属性:{move['type']})")
            if move['name'] in UNIFIED_SKILLS_DATABASE:
                skill_data = UNIFIED_SKILLS_DATABASE[move['name']]
                if skill_data.get('sp_cost', 0) > 0:
                    print(f"  SP消耗: {skill_data['sp_cost']}")
                if skill_data.get('description'):
                    print(f"  描述: {skill_data['description']}")
    
    # 获取可学习技能列表
    print(f"\n--- 可学习的必杀技 ---")
    learnable_skills = system.get_learnable_skills()
    for skill in learnable_skills:
        skill_info = system.get_skill_info(skill)
        can_learn = system.can_learn_skill(0, skill)
        status = "✓可学习" if can_learn else "✗已学会"
        print(f"- {skill} (SP消耗:{skill_info.get('sp_cost', 0)}) {status}")
    
    # 显示背包摘要
    print(f"\n--- 背包摘要 ---")
    summary = system.get_backpack_summary()
    for item_type, count in summary.items():
        type_name = {"skill_book": "必杀技学习书", "skill_blind_box": "必杀技学习盲盒"}.get(item_type, item_type)
        print(f"- {type_name}: {count}个")
    
    # 测试直接创建学习书
    print(f"\n--- 直接创建天下兵马大元帅学习书 ---")
    ultimate_book = system.create_skill_book_directly("天下兵马大元帅")
    if ultimate_book:
        system.player.add_item(ultimate_book)
        print(f"创建了: {ultimate_book.name}")
        print(f"描述: {ultimate_book.description}")


if __name__ == "__main__":
    demo_skill_learning_system()