# 技能系统模块 - 包含技能相关的类和管理器
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

# ==================== 技能枚举和数据结构 ====================

# 技能属性枚举
class SkillAttribute(Enum):
    """技能属性枚举"""
    NETWORKING = "networking"
    EMPATHY = "共情"
    CONTENT = "content"
    PHYSICAL = "体力"
    PS = "PS"
    COURAGE = "勇气"
    INTEGRITY = "节操"
    RESILIENCE = "韧性"
    PATIENCE = "耐心"

class EffectType(Enum):
    """技能效果类型"""
    DAMAGE = "伤害"
    HEAL = "治疗"
    BUFF = "增益"
    DEBUFF = "减益"
    DODGE = "回避"
    REVIVE = "复活"
    DOT = "持续伤害"
    HOT = "持续治疗"
    SPECIAL = "特殊"
    IGNORE_DEFENSE = "无视防御伤害"

@dataclass(slots=True)
class SkillEffect:
    """技能效果"""
    effect_type: EffectType
    value: float
    duration: int = 1
    probability: float = 1.0
    target: str = "enemy"  # "self", "ally", "all_allies", "enemy", "all_enemies"
    description: str = ""

@dataclass(slots=True)
class Skill:
    """技能类"""
    name: str
    attributes: List[SkillAttribute]
    effects: List[SkillEffect]
    sp_cost: int
    quote: str
    description: str = ""  # 技能描述
    
    def __str__(self):
        attrs = ", ".join([attr.value for attr in self.attributes])
        return f"{self.name} [{attrs}] - SP: {self.sp_cost}"

# 技能分类枚举
class SkillCategory:
    DIRECT_DAMAGE = "direct_damage"           # 直接伤害（无需SP发动，发动后积攒SP）
    CONTINUOUS_DAMAGE = "continuous_damage"   # 连续多回合伤害（无需SP发动，发动后积攒SP）
    DIRECT_HEAL = "direct_heal"              # 直接治疗（无需SP发动，发动后不积攒SP）
    CONTINUOUS_HEAL = "continuous_heal"       # 连续多回合治疗（无需SP发动，发动后不积攒SP）
    HEAL = "heal"                            # 通用治疗技能
    SELF_BUFF = "self_buff"                  # 改变己方属性多回合（无需SP发动，发动后不积攒SP）
    ENEMY_DEBUFF = "enemy_debuff"            # 改变敌方属性多回合（无需SP发动，发动后不积攒SP）
    TEAM_BUFF = "team_buff"                  # 改变团队属性多回合（无需SP发动，发动后不积攒SP）
    TEAM_DEBUFF = "team_debuff"              # 改变敌方团队属性多回合（无需SP发动，发动后不积攒SP）
    SPECIAL_ATTACK = "special_attack"         # 必杀技等（需SP发动，发动后不积攒SP）
    DIRECT_ATTACK = "direct_attack"          # 直接攻击技能
    DOT = "dot"                              # 持续伤害效果
    HOT = "hot"                              # 持续治疗效果
    TEAM_HEAL = "team_heal"                  # 团队治疗
    MULTI_HIT = "multi_hit"                  # 多段攻击
    REVIVE = "revive"                        # 复活技能
    MIXED_BUFF_DEBUFF = "mixed_buff_debuff"  # 混合增益/减益效果
    HOT_DOT = "hot_dot"                      # 持续治疗和伤害效果
    ULTIMATE = "ultimate"                    # 终极技能
    SPECIAL = "special"                      # 特殊技能
    STAT_CHANGE = "stat_change"              # 属性改变技能

# SP系统配置
SP_CONFIG = {
    "initial_sp": 0,           # 初始SP
    "max_sp": 100,            # 默认SP上限
    "max_sp_with_guidebook": 120,  # 使用EM guidebook后的SP上限
    "sp_gain_on_attack": 15,   # 攻击时获得的SP
    "sp_gain_on_defend": 10,   # 被攻击时获得的SP
}

# ==================== 技能数据库 ====================

# 统一技能数据库
UNIFIED_SKILLS_DATABASE = {
    # 基础技能
    "酒仙": {
        "power": 0,
        "type": "体力",
        "category": SkillCategory.DIRECT_HEAL,
        "description": "立即回复40%生命",
        "sp_cost": 0,
        "quote": "双倍IPA治疗失眠",
        "effects": {
            "heal_percentage": 0.4
        }
    },
    "鼓舞": {
        "power": 0,
        "type": "共情",
        "category": SkillCategory.CONTINUOUS_HEAL,
        "description": "连续3回合回复20%生命",
        "sp_cost": 0,
        "quote": "鼓舞士气提升战斗力",
        "effects": {
            "heal_percentage": 0.2,
            "turns": 3
        }
    },
    "鲁莽": {
        "power": 0,
        "type": "体力",
        "category": SkillCategory.SELF_BUFF,
        "description": "连续3回合攻击增加40%，防御降低40%",
        "sp_cost": 0,
        "quote": "干他",
        "effects": {
            "attack_multiplier": 1.4,
            "defense_multiplier": 0.6,
            "turns": 3
        }
    },
    "精神污染": {
        "power": 0,
        "type": "共情",
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "对手连续3回合攻击下降70%",
        "sp_cost": 0,
        "quote": "造成精神污染效果",
        "effects": {
            "target_attack_multiplier": 0.3,
            "turns": 3
        }
    },
    "治疗": {
        "power": 0,
        "type": "勇气",
        "category": SkillCategory.DIRECT_HEAL,
        "description": "恢复40%生命",
        "sp_cost": 0,
        "quote": "使用治疗技能恢复生命值",
        "effects": {
            "heal_percentage": 0.4
        }
    },
   
    
    # 必杀技
    "带队酗酒": {
        "power": 0,
        "type": "networking",
        "category": SkillCategory.TEAM_BUFF,
        "description": "消耗95SP，所有顾问攻击力提升35%，血量下降5%，从下一回合开始持续4回合",
        "sp_cost": 95,
        "quote": "我都两杯了，你快点",
        "effects": {
            "team_attack_multiplier": 1.35,
            "team_hp_cost": 0.05,
            "turns": 4
        }
    },
    "酒后逃逸": {
        "power": 0,
        "type": "networking",
        "category": SkillCategory.SELF_BUFF,
        "description": "消耗100SP，从下一回合开始回避任何技能3回合",
        "sp_cost": 100,
        "quote": "这不是回家的车，我要~跳车~",
        "effects": {
            "dodge_chance": 1.0,
            "turns": 3
        }
    },
    "小嘴抹毒": {
        "power": 0,
        "type": "networking",
        "category": SkillCategory.DOT,
        "description": "消耗80SP，对敌方从下一回合开始连续3回合造成自身攻击力的40%伤害",
        "sp_cost": 80,
        "quote": "所以那是你同事吗？",
        "effects": {
            "dot_percentage": 0.4,
            "turns": 3
        }
    },
    "茶颜悦色": {
        "power": 0,
        "type": ["networking", "耐心"],
        "category": SkillCategory.DIRECT_HEAL,
        "description": "恢复自身生命25%",
        "sp_cost": 0,
        "quote": "你要跟我比夹夹，还是跟我比茶茶",
        "effects": {
            "heal_percentage": 0.25
        }
    },
    "快乐小狗": {
        "power": 0,
        "type": ["networking", "耐心"],
        "category": SkillCategory.TEAM_HEAL,
        "description": "为我方全体顾问连续三回合恢复28%HP",
        "sp_cost": 0,
        "quote": "汪汪汪！大家都要健康快乐哦！",
        "effects": {
            "team_heal_percentage": 0.28,
            "turns": 3
        }
    },
    "躺平": {
        "power": 0,
        "type": "节操",
        "category": SkillCategory.DIRECT_HEAL,
        "description": "恢复自身生命35%",
        "sp_cost": 0,
        "quote": "他不会看细节的",
        "effects": {
            "heal_percentage": 0.35
        }
    },
    "绝世骰手": {
        "power": 0,
        "type": "networking",
        "category": SkillCategory.SPECIAL_ATTACK,
        "description": "消耗90SP，无视对手防御力造成50-200点随机伤害",
        "sp_cost": 90,
        "quote": "阿巴次阿巴次，阿巴次阿巴次，喝！",
        "effects": {
            "ignore_defense_damage_min": 50,
            "ignore_defense_damage_max": 200
        }
    },
    "小考拉之怒": {
        "power": 0,
        "type": ["共情", "耐心"],
        "category": SkillCategory.TEAM_HEAL,
        "description": "消耗50SP，恢复全体生命45%",
        "sp_cost": 50,
        "quote": "相机就是我的女朋友",
        "effects": {
            "team_heal_percentage": 0.45
        }
    },
    
    # 普通技能
    "初级扯皮": {
        "power": 0,
        "type": ["节操", "耐心"],
        "category": SkillCategory.SELF_BUFF,
        "description": "消耗14SP，有24%几率回避下次攻击",
        "sp_cost": 14,
        "quote": "我会努力的",
        "effects": {
            "dodge_chance": 0.24,
            "turns": 1
        }
    },
    "建模": {
        "power": 0,
        "type": ["结构化", "耐心", "content"],
        "category": SkillCategory.DOT,
        "description": "连续3回合造成自身攻击力的10%伤害，有15%几率麻痹对手1回合",
        "sp_cost": 0,
        "quote": "使用 wiki 上看到的公式凑数，有几率麻痹对手。",
        "effects": {
            "dot_percentage": 0.1,
            "turns": 3,
            "paralyze_chance": 0.15,
            "paralyze_turns": 1
        }
    },
    "循循善诱": {
        "power": 0,
        "type": ["耐心", "共情"],
        "category": SkillCategory.DOT,
        "description": "连续2回合造成自身攻击力的12%伤害，有10%几率石化对手1回合",
        "sp_cost": 0,
        "quote": "使用复杂的数学模型震慑对手，有几率石化对手。",
        "effects": {
            "dot_percentage": 0.12,
            "turns": 2,
            "petrify_chance": 0.1,
            "petrify_turns": 1
        }
    },
    "PUA": {
        "power": 0,
        "type": "共情",
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "敌方攻击力下降15%，持续2回合，有12%几率魅惑对手1回合，对成年顾问效力下降30%",
        "sp_cost": 0,
        "quote": "使用话术诱惑对手，有几率魅惑对手，对成年顾问效力下降。",
        "effects": {
            "target_attack_multiplier": 0.85,
            "turns": 2,
            "charm_chance": 0.12,
            "charm_turns": 1,
            "adult_penalty": 0.3
        }
    },
    
    # 更多必杀技
    "沉默的牛马": {
        "power": 0,
        "type": ["韧性", "耐心", "共情"],
        "category": SkillCategory.MULTI_HIT,
        "description": "消耗65SP，连续三次造成自身攻击力40%伤害，每次攻击40%几率附加10%伤害",
        "sp_cost": 65,
        "quote": "我去看了亚洲最大的gay吧",
        "effects": {
            "hit_count": 3,
            "damage_percentage": 0.4,
            "bonus_damage_chance": 0.4,
            "bonus_damage_percentage": 0.1
        }
    },
    "威士忌之友": {
        "power": 0,
        "type": ["韧性", "耐心", "共情"],
        "category": SkillCategory.REVIVE,
        "description": "消耗100SP，复活一位顾问，恢复其生命90%",
        "sp_cost": 100,
        "quote": "你能不能闻到泥煤味",
        "effects": {
            "revive_hp_percentage": 0.9
        }
    },
    "我要休产假了": {
        "power": 0,
        "type": ["节操", "体力"],
        "category": SkillCategory.SELF_BUFF,
        "description": "消耗50SP，攻击力提升50%，防御力提升200%，持续3回合",
        "sp_cost": 50,
        "quote": "来陪邱总上厕所呀",
        "effects": {
            "attack_multiplier": 1.5,
            "defense_multiplier": 3.0,
            "turns": 3
        }
    },
    "DGL逼我的": {
        "power": 0,
        "type": ["节操", "体力"],
        "category": SkillCategory.MULTI_HIT,
        "description": "消耗70SP，造成自身攻击力180%伤害，40%几率触发第二次120%伤害",
        "sp_cost": 70,
        "quote": "我两个基地一直都排名前三",
        "effects": {
            "first_hit_percentage": 1.8,
            "second_hit_chance": 0.4,
            "second_hit_percentage": 1.2
        }
    },
    "ValueConcern!": {
        "power": 0,
        "type": "勇气",
        "category": SkillCategory.SPECIAL,
        "description": "消耗90SP，自身不掉血2回合，攻击力变为80%，2回合后造成240%伤害，自身血量变为0",
        "sp_cost": 90,
        "quote": "我跟他也不熟",
        "effects": {
            "invincible_turns": 2,
            "attack_multiplier": 0.8,
            "final_damage_percentage": 2.4,
            "self_sacrifice": True
        }
    },
    
    # 从skill_system.py迁移的技能
    "酒精打击": {
        "power": 93,
        "type": ["networking", "体力"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力93%伤害，有18%几率造成1.5倍伤害",
        "sp_cost": 0,
        "quote": "你挣钱不就是来喝的吗",
        "effects": {
            "base_damage_percentage": 0.93,
            "crit_chance": 0.18,
            "crit_multiplier": 1.5
        }
    },
    "心灵震爆": {
        "power": 55,
        "type": "节操",
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力25%伤害",
        "sp_cost": 0,
        "quote": "你不干这个，我就投诉你",
        "effects": {
            "base_damage_percentage": 0.25
        }
    },
    "Empathy": {
        "power": 42,
        "type": [ "耐心", "共情"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力30%伤害，20%几率对自身产生动摇",
        "sp_cost": 0,
        "quote": "唉，是这样，呼噜噜",
        "effects": {
            "base_damage_percentage": 0.42,
            "self_debuff_chance": 0.20,
            "self_attack_multiplier": 0.9,
            "self_debuff_turns": 3
        }
    },
    "嘲讽": {
        "power": 15,
        "type": "勇气",
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力15%伤害，连续3回合使对手防御力下降30%",
        "sp_cost": 0,
        "quote": "造成自身攻击力15%伤害，连续3回合使对手防御力下降30%",
        "effects": {
            "base_damage_percentage": 0.15,
            "enemy_defense_debuff": 0.3,
            "enemy_defense_debuff_turns": 3
        }
    },
    "磨磨蹭蹭": {
        "power": 10,
        "type": ["耐心", "节操"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力10%伤害",
        "sp_cost": 0,
        "quote": "先去拿个外卖",
        "effects": {
            "base_damage_percentage": 0.10
        }
    },
    "27岁500强总监": {
        "power": 0,
        "type": "节操",
        "category": SkillCategory.DOT,
        "description": "从下一回合开始连续3回合造成自身攻击力30%伤害",
        "sp_cost": 75,
        "quote": "我是DML史上最年轻的总监",
        "effects": {
            "dot_percentage": 0.3,
            "turns": 3,
        }
    },
    "G总,你不懂OPS": {
        "power": 240,
        "type": ["content", "PS", "勇气"],
        "category": SkillCategory.SELF_BUFF,
        "description": "2回合后对敌方造成自身攻击力240%的巨额伤害",
        "sp_cost": 90,
        "quote": "这不是我想做的",
        "effects": {
            "attack_multiplier": 1.0,
            "turns": 2,
        }
    },
    "PTO": {
        "power": 0,
        "type": ["勇气", "节操"],
        "category": SkillCategory.DIRECT_HEAL,
        "description": "恢复自身生命40%",
        "sp_cost": 0,
        "quote": "我下周休假你 backup 一下",
        "effects": {
            "heal_percentage": 0.4,
        }
    },
    "code 诱惑": {
        "power": 0,
        "type": "节操",
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "敌方防御力下降18%，持续2回合",
        "sp_cost": 0,
        "quote": "使用 UT 诱惑对手，有几率魅惑对手，对 beach 上的顾问效力上升。",
        "effects": {
            "target_attack_multiplier": 1.0,
            "turns": 2,
        }
    },
    "信不信我投诉你": {
        "power": 75,
        "type": "节操",
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成目标当前HP的25%伤害",
        "sp_cost": 55,
        "quote": "你为什么没有发现我的错误！",
        "effects": {
            "current_hp_damage_percentage": 0.25
        }
    },
    "倒立攻击": {
        "power": 90,
        "type": ["体力", "PS"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力110%伤害",
        "sp_cost": 0,
        "quote": "书文总，来比倒立！",
        "effects": {
            "base_damage_percentage": 1.10
        }
    },
    "奶茶攻击": {
        "power": 0,
        "type": ["networking", "共情"],
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "敌方全体攻击力下降8%，从下一回合开始持续2回合",
        "sp_cost": 0,
        "quote": "给整个办公室都来吨吨桶，加12 分糖",
        "effects": {
            "target_attack_multiplier": 1.0,
            "turns": 2,
        }
    },
    "织条毯子": {
        "power": 20,
        "type": ["共情", "节操"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力20%伤害",
        "sp_cost": 0,
        "quote": "尽管目前有一点小问题，但是趋势是没有问题的",
        "effects": {
            "base_damage_percentage": 0.20
        }
    },
    "浆板下水": {
        "power": 85,
        "type": ["体力", "勇气"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力100~125%的随机伤害",
        "sp_cost": 0,
        "quote": "好像不用浆更快",
        "effects": {
            "damage_percentage_min": 1.00,
            "damage_percentage_max": 1.25
        }
    },
    "无锡的女武神": {
        "power": 0,
        "type": ["勇气", "韧性", "networking"],
        "category": SkillCategory.SELF_BUFF,
        "description": "恢复所有顾问血量,并使所有顾问攻击力在本场战斗中增加20%,自身血量降为1,四回合后自身血量恢复为100%, 自身攻击力翻倍,可以重新登场（该技能在一场战斗中只能使用一次）",
        "sp_cost": 95,
        "quote": "等着,两个月回来收拾你",
        "effects": {
            "heal_percentage": 1.0,
            "attack_multiplier": 2.0,
            "turns": 999,
            "all_allies_attack_buff": 0.2,
            "self_hp_to_1": True,
            "delayed_heal": {"turns": 4, "percentage": 1.0},
            "battle_unique": True
        }
    },
    "问题解决": {
        "power": 49,
        "type": ["PS", "content", "体力", "耐心"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成自身攻击力49%伤害",
        "sp_cost": 0,
        "quote": "今天谁也不许走",
        "effects": {
            "base_damage_percentage": 0.49
        }
    },
    "马总的关爱": {
        "power": 0,
        "type": ["共情", "体力"],
        "category": SkillCategory.DOT,
        "description": "从下一回合开始连续3回合造成自身攻击力40%伤害",
        "sp_cost": 65,
        "quote": "你的爱红烧牛肉味",
        "effects": {
            "dot_percentage": 0.4,
            "turns": 3,
        }
    },
    "骚扰专家": {
        "power": 0,
        "type": "节操",
        "category": SkillCategory.DOT,
        "description": "从下一回合开始连续5回合造成自身攻击力35%伤害",
        "sp_cost": 65,
        "quote": "傅老师，你帮我写一下述职报告",
        "effects": {
            "dot_percentage": 0.35,
            "turns": 5,
        }
    },
    "我有意见！": {
        "power": 50,
        "type": ["PS", "勇气", "content"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "对敌人造成50点伤害，对自身有反噬效果",
        "sp_cost": 25,
        "quote": "释放能量攻击对手，对自身伤害高，命中率却低下。",
        "effects": {
            "direct_damage": 50,
            "self_damage": 10
        }
    },
    "画饼术": {
        "power": 18,
        "type": ["共情", "节操"],
        "category": SkillCategory.SELF_BUFF,
        "description": "提升自身攻击力，持续3回合",
        "sp_cost": 15,
        "quote": "1个月你就能下",
        "effects": {
            "attack_multiplier": 1.3,
            "turns": 3
        }
    },
    "开始抬杠": {
        "power": 20,
        "type": ["结构化", "PS", "节操"],
        "category": SkillCategory.SELF_BUFF,
        "description": "提升自身防御力，降低敌人攻击力",
        "sp_cost": 12,
        "quote": "你的话题我们会后讨论，我们先看我的",
        "effects": {
            "defense_multiplier": 1.4,
            "target_attack_multiplier": 0.8,
            "turns": 2
        }
    },
    "哼哼唧唧": {
        "power": 15,
        "type": "节操",
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "降低敌人攻击力，持续2回合",
        "sp_cost": 10,
        "quote": "这个数据我要请示",
        "effects": {
            "target_attack_multiplier": 0.7,
            "turns": 2
        }
    },
    "表没对齐": {
        "power": 0,
        "type": "networking",
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "使敌方防御力下降65%",
        "sp_cost": 30,
        "quote": "你自己调整一下",
        "effects": {
            "target_defense_multiplier": 0.35,
            "turns": 3
        }
    },
    "情报总监上线": {
        "power": 0,
        "type": "networking",
        "category": SkillCategory.MIXED_BUFF_DEBUFF,
        "description": "使敌方防御力下降85%,我方攻击力提升20%",
        "sp_cost": 40,
        "quote": "我和你说哦",
        "effects": {
            "target_defense_multiplier": 0.15,
            "self_attack_multiplier": 1.2,
            "turns": 3
        }
    },
    "摸下腹肌~~": {
        "power": 0,
        "type": ["networking", "体力"],
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "使用后对手连续3回合攻击下降70%",
        "sp_cost": 75,
        "quote": "不是8块，是3圈！",
        "effects": {
            "target_attack_multiplier": 0.3,
            "turns": 3
        }
    },
    "我来给你讲下原理": {
        "power": 0,
        "type": "content",
        "category": SkillCategory.HOT_DOT,
        "description": "连续三回合恢复自己25%血量,敌方连续三回合掉血15%",
        "sp_cost": 65,
        "quote": "董事长是我哥们",
        "effects": {
            "heal_percentage": 0.25,
            "dot_percentage": 0.15,
            "turns": 3
        }
    },
    "我来自珠海": {
        "power": 150,
        "type": ["共情", "PS", "体力"],
        "category": SkillCategory.ULTIMATE,
        "description": "使用后对对手造成150%的伤害,对手HP<20%时直接进行直接将对手HP清0",
        "sp_cost": 50,
        "quote": "新伟你这样是不对的",
        "effects": {
            "damage_multiplier": 1.5,
            "execute_threshold": 0.2
        }
    },
    "无锡的羔羊": {
        "power": 200,
        "type": ["共情", "content", "韧性"],
        "category": SkillCategory.ULTIMATE,
        "description": "自身血量下降一半,使用后对对手造成200%的伤害,对手HP<30%时直接进行直接将对手HP清0",
        "sp_cost": 70,
        "quote": "你见过白油倒流没",
        "effects": {
            "self_hp_cost": 0.5,
            "damage_multiplier": 2.0,
            "execute_threshold": 0.3
        }
    },
    "来打羽毛球啊": {
        "power": 240,
        "type": ["content", "PS", "勇气"],
        "category": SkillCategory.ULTIMATE,
        "description": "自身不掉血2回合,期间攻击力变为80%,2回合后对敌方造成240%伤害,自身血量变为0",
        "sp_cost": 90,
        "quote": "实在是干不动了",
        "effects": {
            "invulnerable_turns": 2,
            "attack_multiplier_during": 0.8,
            "final_damage_multiplier": 2.4,
            "self_sacrifice": True
        }
    },
    "我和他谈笑风生": {
        "power": 35,
        "type": "节操",
        "category": SkillCategory.DOT,
        "description": "造成连续5回合35%伤害",
        "sp_cost": 80,
        "quote": "我离职的原因是不好意思让董事长天天飞上海找我",
        "effects": {
            "dot_percentage": 0.35,
            "turns": 5
        }
    },
    "我在XX时代": {
        "power": 85,
        "type": "节操",
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成当前对战顾问85%血量伤害",
        "sp_cost": 75,
        "quote": "那天我在仓库里,突然发现一颗烟头",
        "character": "平地挖坑刚子",
        "effects": {
            "damage_percentage": 0.85
        }
    },
    "感到冒犯": {
        "power": 11,
        "type": "节操",
        "category": SkillCategory.DOT,
        "description": "连续3回合造成伤害",
        "sp_cost": 8,
        "quote": "外包又出花样了",
        "effects": {
            "dot_damage": 11,
            "turns": 3
        }
    },
    "雪松杀手": {
        "power": 85,
        "type": "勇气",
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成85点直接伤害",
        "sp_cost": 5,
        "quote": "10个6！",
        "effects": {
            "direct_damage": 85
        }
    },
    "钓鱼执法": {
        "power": 75,
        "type": "networking",
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "造成75点伤害并降低敌人防御力60%2回合",
        "sp_cost": 30,
        "quote": "科科~我今天穿的好看吗",
        "effects": {
            "direct_damage": 75,
            "target_defense_multiplier": 0.6,
            "turns": 2
        }
    },
    "熬夜攻击": {
        "power": 15,
        "type": ["韧性", "体力"],
        "category": SkillCategory.DOT,
        "description": "连续4回合造成15点伤害",
        "sp_cost": 12,
        "quote": "今晚一定要搞出来",
        "effects": {
            "dot_damage": 15,
            "turns": 4
        }
    },
    "大海无量": {
        "power": 10,
        "type": ["韧性", "体力"],
        "category": SkillCategory.DOT,
        "description": "连续5回合造成10伤害",
        "sp_cost": 8,
        "quote": "我们全部都要打开",
        "effects": {
            "dot_damage": 10,
            "turns": 5
        }
    },
    "凌晨4点的太阳": {
        "power": 16,
        "type": ["韧性", "体力"],
        "category": SkillCategory.DOT,
        "description": "对目标从下一回合开始连续4回合造成自身攻击力的16%持续伤害，并使目标每回合SP减少10",
        "sp_cost": 45,
        "quote": "你见过珠海凌晨4点的太阳吗",
        "effects": {
            "dot_percentage": 0.16,
            "turns": 4,
            "sp_drain": 10
        }
    },
    "躺平才是王道": {
        "power": 0,
        "type": ["content", "勇气"],
        "category": SkillCategory.SELF_BUFF,
        "description": "从下一回合开始回避任何技能2回合",
        "sp_cost": 95,
        "quote": "你又不是朱总，我怕个Der",
        "effects": {
            "dodge_chance": 1.0,
            "turns": 2
        }
    },
    "无偿加班": {
        "power": 20,
        "type": "节操",
        "category": SkillCategory.DOT,
        "description": "连续3回合造成伤害",
        "sp_cost": 15,
        "quote": "五一你们休息两天了，也差不多了",
        "effects": {
            "dot_damage": 20,
            "turns": 3
        }
    },
    "既要又要还要": {
        "power": 11,
        "type": "节操",
        "category": SkillCategory.DOT,
        "description": "连续4回合造成伤害",
        "sp_cost": 12,
        "quote": "我相信群众里面一定有能人",
        "effects": {
            "dot_damage": 11,
            "turns": 4
        }
    },
    "拖欠费用": {
        "power": 25,
        "type": "节操",
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "造成伤害并降低敌人攻击力",
        "sp_cost": 18,
        "quote": "你凭什么拿这个钱",
        "effects": {
            "direct_damage": 25,
            "target_attack_multiplier": 0.7,
            "turns": 2
        }
    },
    "整风运动": {
        "power": 40,
        "type": ["节操", "PS"],
        "category": SkillCategory.TEAM_DEBUFF,
        "description": "对所有敌人造成伤害并降低其攻击力",
        "sp_cost": 35,
        "quote": "你告诉我，为什么W基地一年换了7个总经理",
        "effects": {
            "direct_damage": 40,
            "target_attack_multiplier": 0.6,
            "turns": 3
        }
    },
    "团队增殖": {
        "power": 15,
        "type": ["networking", "节操"],
        "category": SkillCategory.SELF_BUFF,
        "description": "提升团队整体攻击力",
        "sp_cost": 20,
        "quote": "我们组建了56人的全球团队，但是并不负责解决具体技术问题",
        "effects": {
            "attack_multiplier": 1.2,
            "turns": 4
        }
    },
    "技术创新": {
        "power": 80,
        "type": ["content", "PS", "结构化"],
        "category": SkillCategory.TEAM_BUFF,
        "description": "大幅提升团队攻击力和防御力",
        "sp_cost": 45,
        "quote": "该方案采用的都是市面上已有的技术，并没有见到你们的独创性",
        "effects": {
            "team_attack_multiplier": 1.5,
            "team_defense_multiplier": 1.3,
            "turns": 3
        }
    },
    "在你来前": {
        "power": 30,
        "type": "PS",
        "category": SkillCategory.ENEMY_DEBUFF,
        "description": "降低敌人士气，减少其攻击力和防御力",
        "sp_cost": 22,
        "quote": "你们来前我们就开始做了",
        "effects": {
            "target_attack_multiplier": 0.7,
            "target_defense_multiplier": 0.8,
            "turns": 3
        }
    },
    "李代桃僵": {
        "power": 24,
        "type": "节操",
        "category": SkillCategory.DIRECT_DAMAGE,
        "description": "造成24点伤害并有概率转移伤害",
        "sp_cost": 15,
        "quote": "老厂长你来回答一下。",
        "effects": {
            "direct_damage": 24,
            "redirect_chance": 0.3
        }
    },
    "腐蚀": {
        "power": 11,
        "type": ["节操", "体力"],
        "category": SkillCategory.DOT,
        "description": "连续4回合造成腐蚀伤害",
        "sp_cost": 10,
        "quote": "商后面是个啥字母来着",
        "effects": {
            "dot_damage": 11,
            "turns": 4,
            "defense_reduction": 0.1
        }
    },
    "天下兵马大元帅": {
        "power": 0,
        "type": ["勇气", "韧性", "体力"],
        "category": SkillCategory.SPECIAL,
        "description": "消耗90SP，提升自身攻击力50%、防御力20%持续2回合，并在第二回合造成400%伤害",
        "sp_cost": 90,
        "quote": "随我勤王！",
        "second_turn_quote": "万箭齐发",
        "is_multi_turn": True,
        "turn_count": 2,
        "effects": {
            "attack_multiplier": 1.5,
            "defense_multiplier": 1.2,
            "turns": 2,
            "delayed_damage_percentage": 4.0,
            "delayed_turns": 1
        }
    },
    "唧唧歪歪": {
        "power": 28,
        "type": ["共情"],
        "category": SkillCategory.DIRECT_DAMAGE,
        "sp_cost": 0,
        "quote": "",
        "description": "不停地抱怨和唠叨，造成精神伤害"
    },
    "扣除效益": {
        "power": 60,
        "type": ["节操"],
        "category": SkillCategory.SPECIAL,
        "sp_cost": 0,
        "quote": "所所所所有损失从你们费用里扣！",
        "description": "强制扣除对方的效益，造成大量伤害"
    },
    "深呼吸": {
        "power": 80,
        "type": ["节操"],
        "category": SkillCategory.SPECIAL,
        "sp_cost": 0,
        "quote": "你们要负全责！",
        "description": "深呼吸后爆发怒气，造成巨大伤害"
    }
}

# 必杀技台词数据库
ULTIMATE_LINES_DATABASE = {
    # 我方顾问台词
    "ally": {
        "Deric的阴影": "看见阴影了吗？那就是你的结局！",
        "酒精打击": "你挣钱不就是来喝的吗",
        "心灵震爆": "感受心灵的力量吧！",
        "精神污染": "让混乱占据你的内心！",
        # 整合的技能台词
        "带队酗酒": "我都两杯了，你快点",
        "酒后逃逸": "这不是回家的车，我要~跳车~",
        "小嘴抹毒": "所以那是你同事吗？",
        "茶颜悦色": "你要跟我比夹夹，还是跟我比茶茶",
        "快乐小狗": "轻一点，不要打扰我偷听JJZ骂人",
        "躺平": "他不会看细节的",
        "绝世骰手": "阿巴次阿巴次，阿巴次阿巴次，喝！",
        "小考拉之怒": "相机就是我的女朋友",
        "沉默的牛马": "我去看了亚洲最大的gay吧",
        "威士忌之友": "你能不能闻到泥煤味",
        "躺平才是王道": "你又不是朱总，我怕个Der",
        "我要休产假了": "来陪邱总上厕所呀",
        "DGL逼我的": "我两个基地一直都排名前三",
        "表没对齐": "你自己调整一下",
        "情报总监上线": "我和你说哦",
        "摸下腹肌~~": "不是8块，是3圈！",
        "我来给你讲下原理": "董事长是我哥们",
        "ValueConcern!": "我跟他也不熟",
        "马总的关爱": "你就在我办公室偷偷吃方便面吧",
        "我来自珠海": "新伟你这样是不对的",
        "无锡的羔羊": "你见过白油倒流没",
        "来打羽毛球啊": "实在是干不动了",
        "G总,你不懂OPS": "这不是我想做的",
        "27岁500强总监": "我是DML史上最年轻的总监",
        "我和他谈笑风生": "我离职的原因是不好意思让董事长天天飞上海找我",
        "信不信我投诉你": "你为什么没有发现我的错误！",
        "我在XX时代": "那天我在仓库里，突然发现一颗烟头",
        "骚扰专家": "傅老师，你帮我写一下述职报告",
        "深呼吸": "你们要负全责！",
        "扣除效益": "所所所所有损失从你们费用里扣！",
        "浆板下水": "不用浆好像还比较快啊",
        "倒立攻击": "书文总，我们比下倒立",
        "治疗": "使用治疗技能恢复生命值",
        "default": "这就是我的必杀技！"
    }
}

# ==================== 技能管理系统 ====================

class SkillManager:
    """统一的技能管理器"""
    
    def __init__(self):
        self.skills = {}
        self._load_unified_skills()
    
    def _load_unified_skills(self):
        """从UNIFIED_SKILLS_DATABASE加载所有技能"""
        for skill_name, skill_data in UNIFIED_SKILLS_DATABASE.items():
            # 根据技能类型确定属性
            skill_type = skill_data.get("type", "")
            attributes = self._get_skill_attributes(skill_type)
            
            # 转换效果
            effects = self._convert_skill_effects(skill_data)
            
            # 创建Skill对象
            skill = Skill(
                name=skill_name,
                attributes=attributes,
                effects=effects,
                sp_cost=skill_data.get("sp_cost", 0),
                quote=skill_data.get("quote", ""),
                description=skill_data.get("description", "")
            )
            
            # 添加到技能管理器
            self.skills[skill_name] = skill
    
    def _get_skill_attributes(self, skill_type) -> List[SkillAttribute]:
        """根据技能类型获取对应的属性"""
        attribute_map = {
            "体力": [SkillAttribute.PHYSICAL],
            "共情": [SkillAttribute.EMPATHY],
            "结构化": [SkillAttribute.PS],
            "PS": [SkillAttribute.PS],
            "networking": [SkillAttribute.NETWORKING],
            "节操": [SkillAttribute.INTEGRITY],
            "勇气": [SkillAttribute.COURAGE],
            "韧性": [SkillAttribute.RESILIENCE],
            "content": [SkillAttribute.CONTENT],
            "耐心": [SkillAttribute.PATIENCE]
        }
        
        # Handle both string and list types
        if isinstance(skill_type, list):
            # If skill_type is a list, get attributes for each type and combine them
            attributes = []
            for single_type in skill_type:
                attributes.extend(attribute_map.get(single_type, []))
            return attributes
        else:
            # If skill_type is a string, handle it as before
            return attribute_map.get(skill_type, [])
    
    def _convert_skill_effects(self, skill_data: Dict) -> List[SkillEffect]:
        """将技能数据转换为SkillEffect对象列表"""
        effects = []
        category = skill_data.get("category")
        skill_effects = skill_data.get("effects", {})
        
        # 直接治疗
        if category == SkillCategory.DIRECT_HEAL:
            heal_percentage = skill_effects.get("heal_percentage", 0) * 100
            effects.append(SkillEffect(
                EffectType.HEAL, heal_percentage, 1, 1.0, "self", 
                f"恢复{heal_percentage}%生命"
            ))
        
        # 持续治疗
        elif category == SkillCategory.CONTINUOUS_HEAL:
            heal_percentage = skill_effects.get("heal_percentage", 0) * 100
            turns = skill_effects.get("turns", 1)
            effects.append(SkillEffect(
                EffectType.HOT, heal_percentage, turns, 1.0, "self", 
                f"连续{turns}回合恢复{heal_percentage}%生命"
            ))
        
        # 自身增益
        elif category == SkillCategory.SELF_BUFF:
            turns = skill_effects.get("turns", 1)
            
            # 攻击力变化
            attack_mult = skill_effects.get("attack_multiplier", 1.0)
            if attack_mult != 1.0:
                buff_value = (attack_mult - 1.0) * 100
                effects.append(SkillEffect(
                    EffectType.BUFF, buff_value, turns, 1.0, "self", 
                    f"攻击力变化{buff_value:+.0f}%"
                ))
            
            # 防御力变化
            defense_mult = skill_effects.get("defense_multiplier", 1.0)
            if defense_mult != 1.0:
                buff_value = (defense_mult - 1.0) * 100
                effects.append(SkillEffect(
                    EffectType.BUFF, buff_value, turns, 1.0, "self", 
                    f"防御力变化{buff_value:+.0f}%"
                ))
            
            # 回避能力
            dodge_chance = skill_effects.get("dodge_chance", 0)
            if dodge_chance > 0:
                effects.append(SkillEffect(
                    EffectType.DODGE, dodge_chance * 100, turns, 1.0, "self", 
                    f"回避率{dodge_chance*100:.0f}%"
                ))
        
        # 敌方减益
        elif category == SkillCategory.ENEMY_DEBUFF:
            turns = skill_effects.get("turns", 1)
            target_attack_mult = skill_effects.get("target_attack_multiplier", 1.0)
            if target_attack_mult != 1.0:
                debuff_value = (1.0 - target_attack_mult) * 100
                effects.append(SkillEffect(
                    EffectType.DEBUFF, debuff_value, turns, 1.0, "enemy", 
                    f"攻击力下降{debuff_value:.0f}%"
                ))
        
        # 特殊攻击
        elif category == SkillCategory.SPECIAL_ATTACK:
            base_damage = skill_effects.get("base_damage", 0)
            if base_damage > 0:
                effects.append(SkillEffect(
                    EffectType.DAMAGE, base_damage, 1, 1.0, "enemy", 
                    f"造成{base_damage}点伤害"
                ))
            
            # 斩杀效果
            execute_threshold = skill_effects.get("execute_threshold", 0)
            if execute_threshold > 0:
                effects.append(SkillEffect(
                    EffectType.SPECIAL, execute_threshold * 100, 1, 1.0, "enemy", 
                    f"HP低于{execute_threshold*100:.0f}%时直接击败"
                ))
            
            # 无视防御伤害
            min_damage = skill_effects.get("ignore_defense_damage_min", 0)
            max_damage = skill_effects.get("ignore_defense_damage_max", 0)
            if min_damage > 0 and max_damage > 0:
                effects.append(SkillEffect(
                    EffectType.IGNORE_DEFENSE, min_damage, max_damage, 1.0, "enemy", 
                    f"无视防御造成{min_damage}-{max_damage}点伤害"
                ))
        
        # 直接伤害
        elif category == SkillCategory.DIRECT_DAMAGE:
            power = skill_data.get("power", 0)
            skill_effects = skill_data.get("effects", {})
            
            # 检查是否有随机伤害百分比范围
            damage_percentage_min = skill_effects.get("damage_percentage_min", 0)
            damage_percentage_max = skill_effects.get("damage_percentage_max", 0)
            
            if damage_percentage_min > 0 and damage_percentage_max > 0:
                # 随机伤害百分比范围
                effects.append(SkillEffect(
                    EffectType.DAMAGE, damage_percentage_min * 100, damage_percentage_max * 100, 1.0, "enemy", 
                    f"造成{int(damage_percentage_min * 100)}%-{int(damage_percentage_max * 100)}%攻击力伤害"
                ))
            else:
                # 固定伤害百分比
                base_damage_percentage = skill_effects.get("base_damage_percentage", power / 100.0 if power > 0 else 0)
                
                if base_damage_percentage > 0:
                    effects.append(SkillEffect(
                        EffectType.DAMAGE, base_damage_percentage * 100, 1, 1.0, "enemy", 
                        f"造成{int(base_damage_percentage * 100)}%攻击力伤害"
                    ))
            
            # 暴击效果
            crit_chance = skill_effects.get("crit_chance", 0)
            if crit_chance > 0:
                crit_multiplier = skill_effects.get("crit_multiplier", 1.0)
                effects.append(SkillEffect(
                    EffectType.SPECIAL, crit_chance * 100, 1, crit_multiplier, "enemy", 
                    f"{int(crit_chance * 100)}%几率造成{crit_multiplier}倍伤害"
                ))
        
        # 连续伤害
        elif category == SkillCategory.CONTINUOUS_DAMAGE:
            power = skill_data.get("power", 0)
            turns = skill_effects.get("turns", 3)  # 默认3回合
            if power > 0:
                effects.append(SkillEffect(
                    EffectType.DOT, power, turns, 1.0, "enemy", 
                    f"连续{turns}回合造成{power}%攻击力伤害"
                ))
        
        # 持续伤害
        elif category == SkillCategory.DOT:
            dot_percentage = skill_effects.get("dot_percentage", 0) * 100
            turns = skill_effects.get("turns", 1)
            effects.append(SkillEffect(
                EffectType.DOT, dot_percentage, turns, 1.0, "enemy", 
                f"连续{turns}回合造成{dot_percentage}%攻击力伤害"
            ))
        
        # 团队增益
        elif category == SkillCategory.TEAM_BUFF:
            turns = skill_effects.get("turns", 1)
            team_attack_mult = skill_effects.get("team_attack_multiplier", 1.0)
            if team_attack_mult != 1.0:
                buff_value = (team_attack_mult - 1.0) * 100
                effects.append(SkillEffect(
                    EffectType.BUFF, buff_value, turns, 1.0, "all_allies", 
                    f"全队攻击力提升{buff_value:.0f}%"
                ))
            
            team_hp_cost = skill_effects.get("team_hp_cost", 0)
            if team_hp_cost > 0:
                effects.append(SkillEffect(
                    EffectType.DEBUFF, team_hp_cost * 100, 1, 1.0, "all_allies", 
                    f"全队血量下降{team_hp_cost*100:.0f}%"
                ))
        
        # 团队治疗
        elif category == SkillCategory.TEAM_HEAL:
            team_heal_percentage = skill_effects.get("team_heal_percentage", 0) * 100
            turns = skill_effects.get("turns", 1)
            if turns > 1:
                effects.append(SkillEffect(
                    EffectType.HOT, team_heal_percentage, turns, 1.0, "all_allies", 
                    f"全队连续{turns}回合恢复{team_heal_percentage}%生命"
                ))
            else:
                effects.append(SkillEffect(
                    EffectType.HEAL, team_heal_percentage, 1, 1.0, "all_allies", 
                    f"全队恢复{team_heal_percentage}%生命"
                ))
        
        # 直接攻击
        elif category == SkillCategory.DIRECT_ATTACK:
            power = skill_data.get("power", 0)
            if power > 0:
                effects.append(SkillEffect(
                    EffectType.DAMAGE, power, 1, 1.0, "enemy", 
                    f"造成{power}%攻击力伤害"
                ))
        
        # 多段攻击
        elif category == SkillCategory.MULTI_HIT:
            power = skill_data.get("power", 0)
            hit_count = skill_effects.get("hit_count", 3)  # 默认3次攻击
            if power > 0:
                for i in range(hit_count):
                    effects.append(SkillEffect(
                        EffectType.DAMAGE, power, 1, 1.0, "enemy", 
                        f"第{i+1}次攻击造成{power}%攻击力伤害"
                    ))
        
        # 复活技能
        elif category == SkillCategory.REVIVE:
            heal_percentage = skill_effects.get("revive_heal_percentage", 90)
            effects.append(SkillEffect(
                EffectType.HEAL, heal_percentage, 1, 1.0, "ally_fainted", 
                f"复活倒下的顾问并恢复{heal_percentage}%生命"
            ))
        
        # 混合增益减益效果
        elif category == SkillCategory.MIXED_BUFF_DEBUFF:
            # 这种技能需要特殊处理，暂时添加占位符效果
            effects.append(SkillEffect(
                EffectType.SPECIAL, 0, 1, 1.0, "mixed", 
                "混合增益减益效果"
            ))
        
        # 持续治疗和伤害效果
        elif category == SkillCategory.HOT_DOT:
            # 这种技能需要特殊处理，暂时添加占位符效果
            effects.append(SkillEffect(
                EffectType.SPECIAL, 0, 1, 1.0, "mixed", 
                "持续治疗和伤害效果"
            ))
        
        # 终极技能
        elif category == SkillCategory.ULTIMATE:
            power = skill_data.get("power", 0)
            if power > 0:
                effects.append(SkillEffect(
                    EffectType.DAMAGE, power, 1, 1.0, "enemy", 
                    f"终极技能造成{power}%攻击力伤害"
                ))
        
        return effects
    
    
    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(skill_name)
    
    def get_all_skills(self) -> Dict[str, Skill]:
        """获取所有技能"""
        return self.skills
    
    def get_skills_by_attribute(self, attribute: SkillAttribute) -> List[Skill]:
        """根据属性获取技能"""
        return [skill for skill in self.skills.values() if attribute in skill.attributes]
    
    def use_skill(self, skill_name: str, user_stats: Dict, target_stats: Dict = None):
        """使用技能"""
        # 从UNIFIED_SKILLS_DATABASE获取技能信息
        skill_data = UNIFIED_SKILLS_DATABASE.get(skill_name, {})
        if not skill_data:
            return f"技能 {skill_name} 不存在"
        
        sp_cost = skill_data.get("sp_cost", 0)
        if user_stats.get("sp", 0) < sp_cost:
            return f"SP不足，需要 {sp_cost} SP"
        
        # 扣除SP
        user_stats["sp"] -= sp_cost
        
        # 显示台词
        quote = skill_data.get("quote", "")
        result = [f'"{quote}"'] if quote else []
        
        # 执行技能效果（如果有的话）
        effects = skill_data.get("effects", {})
        if effects:
            result.append(f"技能效果: {skill_data.get('description', '')}")
        
        return "\n".join(result)
    
    def use_skill_on_pokemon(self, skill_name: str, user_pokemon, target_pokemon=None, allies=None):
        """在Pokemon对象上使用技能（统一接口）"""
        # 直接使用统一的技能系统逻辑
        return self._use_unified_skill_logic(skill_name, user_pokemon, target_pokemon, allies)
    
    def _use_unified_skill_logic(self, skill_name: str, user_pokemon, target_pokemon=None, allies=None):
        """使用统一的技能系统逻辑"""
        return user_pokemon.use_skill(skill_name, target_pokemon, allies)
    
    def _apply_effect(self, effect: SkillEffect, user_stats: Dict, target_stats: Dict = None) -> str:
        """应用技能效果"""
        if random.random() > effect.probability:
            return f"技能效果未触发 (概率: {effect.probability * 100}%)"
        
        result = f"效果: {effect.description}"
        
        # 这里可以根据具体的游戏逻辑来实现各种效果
        # 目前只是示例实现
        if effect.effect_type == EffectType.DAMAGE:
            damage = int(user_stats.get("attack", 100) * effect.value / 100)
            result += f" - 造成 {damage} 点伤害"
        elif effect.effect_type == EffectType.IGNORE_DEFENSE:
            # 无视防御的伤害，使用固定伤害范围
            # effect.value 用作最小伤害，duration 用作最大伤害
            min_damage = int(effect.value)
            max_damage = int(effect.duration) if effect.duration > effect.value else int(effect.value + 150)
            damage = random.randint(min_damage, max_damage)
            result += f" - 无视防御造成 {damage} 点伤害"
        elif effect.effect_type == EffectType.HEAL:
            heal = int(user_stats.get("max_hp", 1000) * effect.value / 100)
            result += f" - 恢复 {heal} 点生命"
        elif effect.effect_type == EffectType.BUFF:
            result += f" - 属性变化 {effect.value}%"
        
        return result
    
    def _apply_pokemon_effect(self, effect: SkillEffect, user_pokemon, target_pokemon=None):
        """在Pokemon对象上应用技能效果"""
        if random.random() > effect.probability:
            return 0, [f"技能效果未触发 (概率: {effect.probability * 100}%)"]
        
        messages = []
        damage = 0
        
        if effect.effect_type == EffectType.DAMAGE:
            damage = int(user_pokemon.attack * effect.value / 100)
            if target_pokemon:
                actual_damage = max(1, damage - target_pokemon.defense // 2)
                target_pokemon.hp = max(0, target_pokemon.hp - actual_damage)
                messages.append(f"对{target_pokemon.name}造成{actual_damage}点伤害")
                damage = actual_damage
        
        elif effect.effect_type == EffectType.IGNORE_DEFENSE:
            min_damage = int(effect.value)
            max_damage = int(effect.duration) if effect.duration > effect.value else int(effect.value + 150)
            damage = random.randint(min_damage, max_damage)
            if target_pokemon:
                target_pokemon.hp = max(0, target_pokemon.hp - damage)
                messages.append(f"无视防御对{target_pokemon.name}造成{damage}点伤害")
        
        elif effect.effect_type == EffectType.HEAL:
            heal_amount = int(user_pokemon.max_hp * effect.value / 100)
            user_pokemon.hp = min(user_pokemon.max_hp, user_pokemon.hp + heal_amount)
            messages.append(f"{user_pokemon.name}恢复{heal_amount}点生命")
        
        elif effect.effect_type == EffectType.DOT:
            # 持续伤害效果需要在战斗系统中实现
            messages.append(f"对目标施加持续伤害效果")
        
        elif effect.effect_type == EffectType.HOT:
            # 持续治疗效果需要在战斗系统中实现
            messages.append(f"获得持续治疗效果")
        
        elif effect.effect_type == EffectType.BUFF or effect.effect_type == EffectType.DEBUFF:
            # 增益/减益效果需要在战斗系统中实现
            messages.append(f"属性变化效果: {effect.description}")
        
        elif effect.effect_type == EffectType.DODGE:
            # 回避效果需要在战斗系统中实现
            messages.append(f"获得回避效果")
        
        elif effect.effect_type == EffectType.SPECIAL:
            # 特殊效果
            messages.append(f"特殊效果: {effect.description}")
        
        return damage, messages

# 创建全局技能管理器实例
skill_manager = SkillManager()