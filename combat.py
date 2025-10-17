# 战斗交互模块 - 包含战斗逻辑和交互系统
import pygame
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from skills import skill_manager, UNIFIED_SKILLS_DATABASE, SkillCategory, SP_CONFIG, ULTIMATE_LINES_DATABASE

# 战斗相关的枚举
class BattleAction(Enum):
    """战斗行动枚举"""
    ATTACK = "attack"
    CATCH = "catch"
    FLEE = "flee"
    USE_ITEM = "use_item"
    SWITCH_POKEMON = "switch_pokemon"

class BattleResult(Enum):
    """战斗结果枚举"""
    PLAYER_VICTORY = "player_victory"
    PLAYER_DEFEAT = "player_defeat"
    FLEE_SUCCESS = "flee_success"
    CAPTURE_SUCCESS = "capture_success"
    ONGOING = "ongoing"

# ==================== 战斗管理器 ====================

class CombatManager:
    """战斗管理器 - 处理所有战斗相关的逻辑"""
    
    def __init__(self, game_instance):
        """初始化战斗管理器"""
        self.game = game_instance
        self.current_turn = None
        self.battle_step = 0
        self.animation_timer = 0
        self.animation_delay = 1000
        self.is_boss_battle = False
        self.ally_line_display = False
        self.enemy_line_display = False
        self.ally_ultimate_line = None
        self.enemy_ultimate_line = None
    
    def safe_get_player_pokemon(self):
        """安全地获取玩家当前顾问"""
        if (hasattr(self.game, 'player') and 
            hasattr(self.game.player, 'get_active_pokemon')):
            return self.game.player.get_active_pokemon()
        return None
    
    def safe_get_player_attr(self, attr_name, default_value=None):
        """安全地获取玩家属性"""
        if (hasattr(self.game, 'player') and 
            hasattr(self.game.player, attr_name)):
            return getattr(self.game.player, attr_name)
        return default_value
        
    def start_battle(self, battle_type="wild", enemy_pokemon=None):
        """
        开始战斗
        
        Args:
            battle_type: 战斗类型 ("wild", "mini_boss", "stage_boss")
            enemy_pokemon: 敌方顾问对象（可选）
        """
        self.is_boss_battle = battle_type in ["boss", "mini_boss", "stage_boss"]
        
        # 重置战斗回合计数器
        player_pkm = self.safe_get_player_pokemon()
        if player_pkm and hasattr(player_pkm, 'battle_turn_counter'):
            player_pkm.battle_turn_counter = 0
        
        # 清除必杀技台词显示
        self.ally_line_display = False
        self.enemy_line_display = False
        self.ally_ultimate_line = None
        self.enemy_ultimate_line = None
        
        if enemy_pokemon:
            # 使用提供的敌方顾问
            if self.is_boss_battle:
                self.game.boss_pokemon = enemy_pokemon
                self.game.wild_pokemon = None
            else:
                self.game.wild_pokemon = enemy_pokemon
                self.game.boss_pokemon = None
        else:
            # 生成敌方顾问
            enemy_pokemon = self._generate_enemy_pokemon(battle_type)
            if self.is_boss_battle:
                self.game.boss_pokemon = enemy_pokemon
                self.game.wild_pokemon = None
            else:
                self.game.wild_pokemon = enemy_pokemon
                self.game.boss_pokemon = None
        
        # 设置战斗状态
        if self.is_boss_battle:
            self.game.state = self._get_boss_battle_state()
        else:
            self.game.state = self._get_battle_state()
        
        # 设置战斗消息
        enemy = enemy_pokemon
        if enemy:
            advantages = ", ".join(enemy.advantages)
            disadvantages = ", ".join(enemy.disadvantages)
            if self.is_boss_battle:
                self.game.battle_messages = [
                    f"强大的{enemy.name} (Lv.{enemy.level})出现了！",
                    f"这是一场BOSS战！",
                    f"优点: {advantages}, 缺点: {disadvantages}"
                ]
            else:
                self.game.battle_messages = [
                    f"野生的{enemy.name} (Lv.{enemy.level})出现了！",
                    f"优点: {advantages}, 缺点: {disadvantages}"
                ]
    
    def process_battle_turn(self, move_idx=None, action=None, ball_type="normal", item=None, item_index=None, switch_index=None):
        """
        处理战斗回合
        
        Args:
            move_idx: 技能索引
            action: 行动类型
            ball_type: 精灵球类型
            item: 使用的物品
            item_index: 物品索引
            switch_index: 切换的顾问索引
        """
        try:
            # 安全地获取玩家顾问
            player_pkm = self.safe_get_player_pokemon()
            enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
            
            if not player_pkm or not enemy_pkm:
                return
            
            # 设置动画状态
            self.battle_step = 0
            self.animation_timer = pygame.time.get_ticks()
            
            self.current_turn = {
                "move_idx": move_idx,
                "action": action,
                "ball_type": ball_type,
                "item": item,
                "item_index": item_index,
                "switch_index": switch_index,
                "damage": 0,
                "type_multiplier": 1.0,
                "enemy_damage": 0,
                "enemy_type_multiplier": 1.0,
                "capture_success": False,
                "leveled_up": False,
                "evolution_messages": [],
                "drop_item_message": None
            }
        except Exception as e:
            print(f"处理战斗回合时出错: {e}")
            self.game.battle_messages.append("战斗发生错误！")
    
    def update_battle_animation(self):
        """更新战斗动画"""
        current_time = pygame.time.get_ticks()
        if current_time - self.animation_timer < self.animation_delay:
            return
        
        try:
            player_pkm = self.game.player.get_active_pokemon()
            enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
            
            if not player_pkm or not enemy_pkm or not self.current_turn:
                self.end_battle()
                return
            
            self.animation_timer = current_time
            
            # 根据战斗步骤执行不同的逻辑
            if self.battle_step == 0:
                self._handle_player_action()
            elif self.battle_step == 1:
                self._handle_damage_calculation()
            elif self.battle_step == 2:
                self._handle_enemy_defeat()
            elif self.battle_step == 3:
                self._handle_capture_result()
            elif self.battle_step == 4:
                self._handle_enemy_attack()
            elif self.battle_step == 5:
                self._handle_player_defeat()
            elif self.battle_step == 6:
                self._handle_battle_end()
            elif self.battle_step == 7:
                self._handle_turn_end()
            elif self.battle_step == 8:
                self._handle_evolution()
                
        except Exception as e:
            print(f"战斗动画更新出错: {e}")
            self.game.battle_messages.append("战斗发生错误！")
    
    def _handle_player_action(self):
        """处理玩家行动"""
        action = self.current_turn.get("action")
        
        if action == BattleAction.ATTACK.value:
            self._handle_player_attack()
        elif action == BattleAction.CATCH.value:
            self._handle_catch_attempt()
        elif action == BattleAction.FLEE.value:
            self._handle_flee_attempt()
        elif action == BattleAction.USE_ITEM.value:
            self._handle_item_use()
        elif action == BattleAction.SWITCH_POKEMON.value:
            self._handle_pokemon_switch()
    
    def _handle_player_attack(self):
        """处理玩家攻击"""
        player_pkm = self.game.player.get_active_pokemon()
        enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
        move_idx = self.current_turn.get("move_idx")
        
        if move_idx is not None and move_idx < len(player_pkm.moves):
            move = player_pkm.moves[move_idx]
            
            # 使用统一的技能管理器
            if move["name"] in UNIFIED_SKILLS_DATABASE:
                allies = [pokemon for pokemon in self.game.player.pokemon_team if not pokemon.is_fainted()]
                damage, skill_messages = skill_manager.use_skill_on_pokemon(move["name"], player_pkm, enemy_pkm, allies)
                self.current_turn["damage"] = damage if damage is not None else 0
                
                # 检查是否为必杀技
                skill_data = UNIFIED_SKILLS_DATABASE.get(move["name"], {})
                if skill_data.get("category") == SkillCategory.SPECIAL_ATTACK:
                    self.ally_ultimate_line = ULTIMATE_LINES_DATABASE["ally"].get(move["name"], ULTIMATE_LINES_DATABASE["ally"]["default"])
                    self.ally_line_display = True
                
                # 显示技能台词
                quote = skill_data.get("quote", "")
                if quote and quote.strip():
                    self.ally_ultimate_line = quote
                    self.ally_line_display = True
                
                for msg in skill_messages:
                    self.game.battle_messages.append(msg)
                
                # SP获得逻辑
                if skill_data["category"] in [SkillCategory.DIRECT_DAMAGE, SkillCategory.CONTINUOUS_DAMAGE, 
                                            SkillCategory.DOT, SkillCategory.SPECIAL_ATTACK, SkillCategory.MULTI_HIT]:
                    sp_gained = player_pkm.gain_sp(SP_CONFIG["sp_gain_on_attack"])
                    self.game.battle_messages.append(f"{player_pkm.name}获得了{sp_gained}点SP！")
                    if enemy_pkm:
                        sp_gained = enemy_pkm.gain_sp(SP_CONFIG["sp_gain_on_defend"])
                        self.game.battle_messages.append(f"{enemy_pkm.name}获得了{sp_gained}点SP！")
            else:
                self.game.battle_messages.append(f"技能 {move['name']} 无效！")
                self.current_turn["damage"] = 0
        
        self.battle_step = 1
    
    def _handle_catch_attempt(self):
        """处理捕捉尝试"""
        if self.is_boss_battle:
            self.game.battle_messages.append("无法捕捉BOSS！")
            self.battle_step = 7
            return
        
        enemy_pkm = self.game.wild_pokemon
        ball_type = self.current_turn.get("ball_type", "normal")
        
        if ball_type == "master" and self.game.player.master_balls > 0:
            self.game.player.master_balls -= 1
            if "大师球" in self.game.player.inventory:
                self.game.player.inventory["大师球"] = self.game.player.master_balls
            self.game.battle_messages.append(f"使用了大师球！剩余：{self.game.player.master_balls}个")
            self.current_turn["capture_success"] = True
            self.battle_step = 3
        elif ball_type == "normal" and self.game.player.pokeballs > 0:
            self.game.player.pokeballs -= 1
            if "精灵球" in self.game.player.inventory:
                self.game.player.inventory["精灵球"] = self.game.player.pokeballs
            self.game.battle_messages.append(f"使用了精灵球！剩余：{self.game.player.pokeballs}个")
            
            # 计算捕捉成功率
            player_pkm = self.game.player.get_active_pokemon()
            level_factor = 1.0 + (player_pkm.level - enemy_pkm.level) * 0.1
            capture_rate = (1 - enemy_pkm.get_hp_percentage()) * 0.5 * level_factor + 0.1
            self.current_turn["capture_success"] = random.random() < capture_rate
            self.battle_step = 3
        else:
            self.game.battle_messages.append("没有相应的精灵球了！")
            self.battle_step = 7
    
    def _handle_flee_attempt(self):
        """处理逃跑尝试"""
        player_pkm = self.game.player.get_active_pokemon()
        enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
        
        # BOSS战逃跑成功率低
        if self.is_boss_battle:
            flee_chance = 0.1
        else:
            level_diff = player_pkm.level - enemy_pkm.level
            flee_chance = 0.5 + level_diff * 0.05
            flee_chance = max(0.3, min(0.9, flee_chance))
        
        if random.random() < flee_chance:
            self.game.battle_messages.append("成功逃跑了！")
            self.battle_step = 6
        else:
            self.game.battle_messages.append("逃跑失败！")
            self._execute_enemy_attack()
            self.battle_step = 4
        
        self.animation_delay = 1500
    
    def _handle_item_use(self):
        """处理物品使用"""
        item = self.current_turn.get("item")
        item_index = self.current_turn.get("item_index")
        
        if item:
            player_pkm = self.game.player.get_active_pokemon()
            result = item.use(player_pkm, self.game.player)
            self.game.battle_messages.append(result)
            if item_index is not None:
                self.game.player.remove_item(item_index)
            self.game.battle_messages.append("使用物品后，当前回合结束！")
            self.game.notification_system.add_notification(f"战斗中使用了{item.name}！", "success")
        else:
            self.game.battle_messages.append("无法使用物品")
            self.game.notification_system.add_notification("战斗中无法使用物品！", "warning")
        
        self.battle_step = 7
        self.animation_delay = 1000
    
    def _handle_pokemon_switch(self):
        """处理顾问切换"""
        self.battle_step = 7
        self.animation_delay = 1000
    
    def _handle_damage_calculation(self):
        """处理伤害计算"""
        self.battle_step = 2
        self.animation_delay = 1000
    
    def _handle_enemy_defeat(self):
        """处理敌方顾问被击败"""
        enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
        
        if enemy_pkm.is_fainted():
            self.game.battle_messages.append(f"{enemy_pkm.name}倒下了！")
            
            # 经验值奖励
            self._award_experience(enemy_pkm)
            
            # 处理奖励
            drop_messages = self._generate_battle_drop()
            for msg in drop_messages:
                self.game.battle_messages.append(msg)
            
            # 检查是否有顾问在进化
            if any(p.is_evolving for p in self.game.player.pokemon_team):
                self.battle_step = 8
                self.animation_delay = 2000
            else:
                self.battle_step = 6
                self.animation_delay = 2000
        else:
            self._execute_enemy_attack()
            self.battle_step = 4
            self.animation_delay = 1000
    
    def _handle_capture_result(self):
        """处理捕捉结果"""
        enemy_pkm = self.game.wild_pokemon
        
        if self.current_turn["capture_success"]:
            # 创建新的Pokemon实例而不是直接添加enemy_pkm
            from CCmon5C import Pokemon  # 导入Pokemon类
            captured_pokemon = Pokemon(enemy_pkm.name, level=enemy_pkm.level)
            self.game.player.add_pokemon(captured_pokemon)
            self.game.battle_messages.append(f"成功捕捉{enemy_pkm.name} (Lv.{enemy_pkm.level})！")
            self.battle_step = 6
            self.animation_delay = 2000
        else:
            self.game.battle_messages.append(f"{enemy_pkm.name}挣脱了精灵球！")
            self._execute_enemy_attack()
            self.battle_step = 4
            self.animation_delay = 1000
    
    def _handle_enemy_attack(self):
        """处理敌方攻击后的逻辑"""
        self.battle_step = 5
        self.animation_delay = 1000
    
    def _handle_player_defeat(self):
        """处理玩家顾问被击败"""
        player_pkm = self.game.player.get_active_pokemon()
        
        if player_pkm.is_fainted():
            self.game.battle_messages.append(f"你的{player_pkm.name}倒下了！")
            next_pkm = self.game.player.get_active_pokemon()
            if not next_pkm:
                self.game.battle_messages.append("你的顾问全部倒下了！")
                self.battle_step = 6
                self.animation_delay = 2000
            else:
                advantages = ", ".join(next_pkm.advantages)
                disadvantages = ", ".join(next_pkm.disadvantages)
                self.game.battle_messages.append(f"派出了{next_pkm.name} (Lv.{next_pkm.level})！")
                self.game.battle_messages.append(f"优点: {advantages}, 缺点: {disadvantages}")
                self.battle_step = 7
                self.animation_delay = 1000
        else:
            self.battle_step = 7
            self.animation_delay = 1000
    
    def _handle_battle_end(self):
        """处理战斗结束"""
        # 所有顾问倒下，恢复HP到1点并结束战斗
        self._revive_all_pokemon()
        self.end_battle()
    
    def _handle_turn_end(self):
        """处理回合结束"""
        player_pkm = self.game.player.get_active_pokemon()
        enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
        
        # 增加回合计数器
        if player_pkm:
            player_pkm.increment_battle_turn()
        if enemy_pkm:
            enemy_pkm.increment_battle_turn()
        
        # 应用状态效果
        if player_pkm:
            status_messages = player_pkm.apply_status_effects(enemy_pkm)
            for msg in status_messages:
                self.game.battle_messages.append(msg)
        
        if enemy_pkm:
            status_messages = enemy_pkm.apply_status_effects(player_pkm)
            for msg in status_messages:
                self.game.battle_messages.append(msg)
        
        # 返回到战斗状态
        from CCmon5C import GameState  # 导入GameState枚举
        self.game.state = GameState.BATTLE if not self.is_boss_battle else GameState.BOSS_BATTLE
        self.animation_delay = 1000
    
    def _handle_evolution(self):
        """处理进化"""
        evolving_pkm = None
        for pkm in self.game.player.pokemon_team:
            if pkm.is_evolving:
                evolving_pkm = pkm
                break
        
        if evolving_pkm:
            evolution_msg = evolving_pkm.perform_evolution()
            self.game.battle_messages.append(evolution_msg)
        
        self.battle_step = 6
        self.animation_delay = 2000
    
    def _execute_enemy_attack(self):
        """执行敌方攻击"""
        player_pkm = self.game.player.get_active_pokemon()
        enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
        
        # 清除敌方必杀技台词显示
        self.enemy_line_display = False
        self.enemy_ultimate_line = None
        
        enemy_move = random.choice(enemy_pkm.moves)
        
        # 使用统一的技能管理器
        if enemy_move["name"] in UNIFIED_SKILLS_DATABASE:
            skill_data = UNIFIED_SKILLS_DATABASE.get(enemy_move["name"], {})
            if skill_data.get("category") in [SkillCategory.SELF_BUFF, SkillCategory.DIRECT_HEAL, SkillCategory.CONTINUOUS_HEAL]:
                # 对自己使用的技能
                damage, skill_messages = skill_manager.use_skill_on_pokemon(enemy_move["name"], enemy_pkm, enemy_pkm)
            else:
                # 对玩家使用的技能
                damage, skill_messages = skill_manager.use_skill_on_pokemon(enemy_move["name"], enemy_pkm, player_pkm)
            
            self.current_turn["enemy_damage"] = damage if damage is not None else 0
            
            # 检查是否为必杀技
            if skill_data.get("category") == SkillCategory.SPECIAL_ATTACK:
                self.enemy_ultimate_line = ULTIMATE_LINES_DATABASE["ally"].get(enemy_move["name"], ULTIMATE_LINES_DATABASE["ally"]["default"])
                self.enemy_line_display = True
            
            # 显示技能台词
            quote = skill_data.get("quote", "")
            if quote and quote.strip():
                self.enemy_ultimate_line = quote
                self.enemy_line_display = True
            
            for msg in skill_messages:
                self.game.battle_messages.append(msg)
            
            # 敌方SP获得逻辑
            if skill_data["category"] in [SkillCategory.DIRECT_DAMAGE, SkillCategory.CONTINUOUS_DAMAGE, 
                                        SkillCategory.DOT, SkillCategory.SPECIAL_ATTACK, SkillCategory.MULTI_HIT]:
                sp_gained = enemy_pkm.gain_sp(SP_CONFIG["sp_gain_on_attack"])
                self.game.battle_messages.append(f"{enemy_pkm.name}获得了{sp_gained}点SP！")
                sp_gained = player_pkm.gain_sp(SP_CONFIG["sp_gain_on_defend"])
                self.game.battle_messages.append(f"{player_pkm.name}获得了{sp_gained}点SP！")
        else:
            # 技能不在数据库中
            self.current_turn["enemy_damage"] = 0
            enemy_move_type = UNIFIED_SKILLS_DATABASE.get(enemy_move['name'], {}).get('type', '')
            self.game.battle_messages.append(f"{enemy_pkm.name} (Lv.{enemy_pkm.level})使用了{enemy_move['name']}({enemy_move_type}属性)！")
    
    def _award_experience(self, defeated_enemy):
        """奖励经验值"""
        player_pkm = self.game.player.get_active_pokemon()
        
        # 导入经验配置
        from CCmon5C import ExperienceConfig
        
        base_exp = ExperienceConfig.get_battle_exp_reward(defeated_enemy.level, player_pkm.level)
        
        # BOSS战获得更多经验
        exp_multiplier = 2.5 if self.is_boss_battle else 1.0
        exp_gained = int(base_exp * exp_multiplier)
        
        # 为队伍中的所有顾问分配经验值
        team_level_ups = []
        team_evolution_messages = []
        
        for pokemon in self.game.player.pokemon_team:
            if not pokemon.is_fainted():
                leveled_up, evolution_messages = pokemon.gain_exp(exp_gained)
                if leveled_up:
                    team_level_ups.append(pokemon)
                if evolution_messages:
                    team_evolution_messages.extend(evolution_messages)
        
        # 显示经验获得消息
        alive_count = len([p for p in self.game.player.pokemon_team if not p.is_fainted()])
        if alive_count == 1:
            self.game.battle_messages.append(f"你的{player_pkm.name}获得了{exp_gained}点经验值！")
        else:
            self.game.battle_messages.append(f"队伍中{alive_count}位顾问各自获得了{exp_gained}点经验值！")
        
        # 显示升级信息
        for pokemon in team_level_ups:
            self.game.battle_messages.append(f"你的{pokemon.name}升级到Lv.{pokemon.level}了！")
            self.game.battle_messages.append(f"HP: {pokemon.max_hp}, 攻击: {pokemon.attack}, 防御: {pokemon.defense}")
        
        # 保存升级和进化信息
        self.current_turn["leveled_up"] = len(team_level_ups) > 0
        self.current_turn["evolution_messages"] = team_evolution_messages
        
        # 显示进化消息
        for evo_msg in team_evolution_messages:
            self.game.battle_messages.append(evo_msg)
            self.game.battle_messages.append(f"HP和能力都提升了！")
    
    def _generate_battle_drop(self):
        """生成战斗掉落物品"""
        if self.is_boss_battle and self.game.boss_pokemon:
            return self._generate_boss_rewards()
        else:
            return self._generate_wild_rewards()
    
    def _generate_boss_rewards(self):
        """生成BOSS战奖励"""
        from CCmon5C import PokemonConfig, ItemConfig, Item, Pokemon
        
        boss_name = self.game.boss_pokemon.name
        boss_data = next((b for b in PokemonConfig.mini_bosses + PokemonConfig.stage_bosses 
                         if b["name"] == boss_name), None)
        
        if boss_data and "reward" in boss_data:
            messages = []
            
            # 奖励顾问
            if "pokemon" in boss_data["reward"]:
                pkm_name = boss_data["reward"]["pokemon"]
                self.game.player.add_pokemon(Pokemon(pkm_name, level=10))
                messages.append(f"获得了新顾问: {pkm_name}！")
            
            # 奖励物品
            if "items" in boss_data["reward"]:
                for item_name in boss_data["reward"]["items"]:
                    item_data = ItemConfig.get_item_data(item_name)
                    if item_data:
                        new_item = Item(
                            item_data["name"],
                            item_data["description"],
                            item_data["item_type"],
                            item_data["effect"],
                            item_data.get("price", 0)
                        )
                        self.game.player.add_item(new_item)
                        
                        if item_data["item_type"] == "pokeball":
                            self.game.player.pokeballs += item_data["effect"]
                            if "精灵球" in self.game.player.inventory:
                                self.game.player.inventory["精灵球"] = self.game.player.pokeballs
                            messages.append(f"获得了{item_data['name']}！现在有{self.game.player.pokeballs}个精灵球。")
                        else:
                            messages.append(f"获得了{item_data['name']}！已添加到背包。")
            
            # 如果是大BOSS，提升游戏阶段
            if any(boss_name == b["name"] for b in PokemonConfig.stage_bosses):
                self.game.player.stage += 1
                messages.append(f"恭喜！你已进入第{self.game.player.stage}阶段！")
            
            return messages
        
        return []
    
    def _generate_wild_rewards(self):
        """生成野生战斗奖励"""
        from CCmon5C import ItemConfig, Item
        
        if random.random() < 0.8:
            # 基于稀有度的加权随机选择
            weights = []
            for name in ItemConfig.drop_pool_names:
                item_data = ItemConfig.get_item_data(name)
                weights.append(item_data.get("rarity", 1) if item_data else 1)
            
            total_rarity = sum(weights)
            rand_val = random.uniform(0, total_rarity)
            
            cumulative = 0
            for i, weight in enumerate(weights):
                cumulative += weight
                if rand_val <= cumulative:
                    item_name = ItemConfig.drop_pool_names[i]
                    item_data = ItemConfig.get_item_data(item_name)
                    if item_data:
                        new_item = Item(
                            item_data["name"],
                            item_data["description"],
                            item_data["item_type"],
                            item_data["effect"],
                            item_data.get("price", 0)
                        )
                        self.game.player.add_item(new_item)
                        
                        if item_data["item_type"] == "pokeball":
                            self.game.player.pokeballs += item_data["effect"]
                            if "精灵球" in self.game.player.inventory:
                                self.game.player.inventory["精灵球"] = self.game.player.pokeballs
                            return [f"太棒了！野生的顾问留下了{item_data['name']}！现在有{self.game.player.pokeballs}个精灵球。"]
                        return [f"太棒了！野生的顾问留下了{item_data['name']}！已添加到背包。"]
                    break
        
        # 没有获得物品
        consolation_messages = [
            "野生的顾问逃走了，什么也没留下...",
            "虽然没获得物品，但你的顾问获得了宝贵的战斗经验！",
            "对方什么也没留下，但你感觉顾问变得更强了！"
        ]
        return [random.choice(consolation_messages)]
    
    def _revive_all_pokemon(self):
        """将所有顾问的HP恢复到1点"""
        for pokemon in self.game.player.pokemon_team:
            if pokemon.is_fainted():
                pokemon.hp = 1
        self.game.battle_messages.append("所有顾问的HP恢复到1点！")
    
    def end_battle(self):
        """结束战斗"""
        try:
            # 清除必杀技台词显示
            self.ally_line_display = False
            self.enemy_line_display = False
            self.ally_ultimate_line = None
            self.enemy_ultimate_line = None
            
            # 判断战斗结果
            player_victory = False
            enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
            
            # 检查是否通过击败敌方顾问获胜
            if enemy_pkm and enemy_pkm.is_fainted():
                player_victory = True
            
            # 检查是否通过捕捉成功获胜
            if (self.current_turn and 
                self.current_turn.get("action") == "catch" and 
                self.current_turn.get("capture_success", False)):
                player_victory = True
            
            # 修复顾问HP bug
            for pokemon in self.game.player.pokemon_team:
                if pokemon.is_fainted():
                    pokemon.hp = 1
            
            # BOSS战胜利处理
            if self.is_boss_battle and player_victory:
                self._handle_boss_victory()
            
            # 清理战斗状态
            self._cleanup_battle_state()
            
            # 返回探索状态
            from CCmon5C import GameState
            self.game.state = GameState.EXPLORING
            
        except Exception as e:
            print(f"结束战斗时出错: {e}")
            from CCmon5C import GameState
            self.game.state = GameState.EXPLORING
    
    def _handle_boss_victory(self):
        """处理BOSS战胜利"""
        from CCmon5C import PokemonConfig
        
        boss_name = self.game.boss_pokemon.name if self.game.boss_pokemon else ""
        is_mini_boss = any(boss_name == b["name"] for b in PokemonConfig.mini_bosses)
        
        if is_mini_boss:
            self.game.player.mini_bosses_defeated += 1
            self.game.battle_messages.append(f"击败了小BOSS！已击败{self.game.player.mini_bosses_defeated}个小BOSS")
        else:
            self.game.battle_messages.append("击败了阶段BOSS！")
        
        # 允许地图刷新
        if hasattr(self.game, 'map'):
            self.game.map.can_refresh = True
            self.game.map.refresh_map()
        
        # 刷新商店
        if hasattr(self.game, 'shop'):
            self.game.shop.refresh_shop()
    
    def _cleanup_battle_state(self):
        """清理战斗状态"""
        self.current_turn = None
        self.battle_step = 0
        self.animation_timer = 0
        self.is_boss_battle = False
        
        # 清理战斗相关的游戏状态
        if hasattr(self.game, 'wild_pokemon'):
            self.game.wild_pokemon = None
        if hasattr(self.game, 'boss_pokemon'):
            self.game.boss_pokemon = None
        if hasattr(self.game, 'battle_buttons'):
            self.game.battle_buttons = []
        if hasattr(self.game, 'move_buttons'):
            self.game.move_buttons = []
    
    def can_use_skill(self, pokemon, skill_name):
        """检查是否可以使用技能"""
        if skill_name not in UNIFIED_SKILLS_DATABASE:
            return False, "技能不存在"
        
        skill_data = UNIFIED_SKILLS_DATABASE[skill_name]
        sp_cost = skill_data.get("sp_cost", 0)
        
        if sp_cost > pokemon.sp:
            return False, f"SP不足，需要{sp_cost}点SP"
        
        return True, ""
    
    def _generate_enemy_pokemon(self, battle_type):
        """生成敌方Pokemon"""
        from CCmon5C import Pokemon, PokemonConfig
        
        if battle_type == "wild":
            # 生成野生Pokemon
            return self._generate_wild_pokemon()
        elif battle_type == "mini_boss":
            # 生成小BOSS
            return self._generate_mini_boss()
        elif battle_type == "stage_boss":
            # 生成大BOSS
            return self._generate_stage_boss()
        else:
            # 默认生成野生Pokemon
            return self._generate_wild_pokemon()
    
    def _generate_wild_pokemon(self):
        """生成野生Pokemon"""
        from CCmon5C import Pokemon, PokemonConfig
        import random
        
        # 获取所有可用的Pokemon名称
        available_names = list(PokemonConfig.base_data.keys())
        
        # 随机选择一个Pokemon
        pokemon_name = random.choice(available_names)
        
        # 计算等级
        player_pkm = self.safe_get_player_pokemon()
        if player_pkm and hasattr(self.game, 'map'):
            level = self.game.map.get_wild_pokemon_level(
                self.game.player.x, 
                self.game.player.y, 
                player_pkm.level
            )
        else:
            level = 5  # 默认等级
        
        return Pokemon(pokemon_name, level=level)
    
    def _generate_mini_boss(self):
        """生成小BOSS"""
        from CCmon5C import Pokemon, PokemonConfig
        import random
        
        # 从小BOSS配置中随机选择
        mini_boss_data = random.choice(PokemonConfig.mini_bosses)
        return Pokemon(mini_boss_data["name"], level=mini_boss_data["level"])
    
    def _generate_stage_boss(self):
        """生成大BOSS"""
        from CCmon5C import Pokemon, PokemonConfig
        
        # 根据玩家当前阶段选择大BOSS
        player_stage = getattr(self.game.player, 'stage', 1)
        
        # 查找对应阶段的BOSS
        for boss_data in PokemonConfig.stage_bosses:
            if boss_data["stage"] == player_stage:
                return Pokemon(boss_data["name"], level=boss_data["level"])
        
        # 如果没找到对应阶段的BOSS，使用第一个
        if PokemonConfig.stage_bosses:
            boss_data = PokemonConfig.stage_bosses[0]
            return Pokemon(boss_data["name"], level=boss_data["level"])
        
        # 如果没有BOSS配置，生成一个默认的
        return self._generate_wild_pokemon()
    
    def _get_battle_state(self):
        """获取普通战斗状态"""
        # 导入GameState枚举
        try:
            from CCmon5C import GameState
            return GameState.BATTLE
        except ImportError:
            return 1  # 假设BATTLE状态的值是1
    
    def _get_boss_battle_state(self):
        """获取BOSS战斗状态"""
        # 导入GameState枚举
        try:
            from CCmon5C import GameState
            return GameState.BOSS_BATTLE
        except ImportError:
            return 2  # 假设BOSS_BATTLE状态的值是2
    
    def get_battle_result(self):
        """获取战斗结果"""
        if not self.current_turn:
            return BattleResult.ONGOING
        
        player_pkm = self.game.player.get_active_pokemon()
        enemy_pkm = self.game.boss_pokemon if self.is_boss_battle else self.game.wild_pokemon
        
        # 检查捕捉成功
        if (self.current_turn.get("action") == "catch" and 
            self.current_turn.get("capture_success", False)):
            return BattleResult.CAPTURE_SUCCESS
        
        # 检查逃跑成功
        if (self.current_turn.get("action") == "flee" and 
            self.battle_step == 6):
            return BattleResult.FLEE_SUCCESS
        
        # 检查敌方被击败
        if enemy_pkm and enemy_pkm.is_fainted():
            return BattleResult.PLAYER_VICTORY
        
        # 检查玩家全部顾问倒下
        if not player_pkm or all(p.is_fainted() for p in self.game.player.pokemon_team):
            return BattleResult.PLAYER_DEFEAT
        
        return BattleResult.ONGOING

# ==================== 战斗工具函数 ====================

def calculate_type_effectiveness(attacker_types, defender_types):
    """
    计算属性相克效果
    
    Args:
        attacker_types: 攻击方属性列表
        defender_types: 防御方属性列表
    
    Returns:
        float: 属性相克倍率
    """
    # 这里可以实现具体的属性相克逻辑
    # 目前返回默认值
    return 1.0

def calculate_damage(attacker, defender, move_power, type_multiplier=1.0):
    """
    计算伤害值
    
    Args:
        attacker: 攻击方顾问
        defender: 防御方顾问
        move_power: 技能威力
        type_multiplier: 属性相克倍率
    
    Returns:
        int: 最终伤害值
    """
    # 基础伤害计算
    base_damage = (attacker.attack * move_power / 100.0)
    
    # 应用防御
    defense_reduction = max(1, defender.defense // 2)
    damage = max(1, base_damage - defense_reduction)
    
    # 应用属性相克
    damage *= type_multiplier
    
    # 随机因子
    damage *= random.uniform(0.85, 1.0)
    
    return int(damage)

def calculate_capture_rate(pokemon, ball_type="normal"):
    """
    计算捕捉成功率
    
    Args:
        pokemon: 要捕捉的顾问
        ball_type: 精灵球类型
    
    Returns:
        float: 捕捉成功率 (0.0-1.0)
    """
    if ball_type == "master":
        return 1.0
    
    # 基础捕捉率基于HP百分比
    base_rate = 1.0 - pokemon.get_hp_percentage()
    
    # 精灵球类型修正
    ball_multiplier = {
        "normal": 1.0,
        "great": 1.5,
        "ultra": 2.0,
        "master": float('inf')
    }.get(ball_type, 1.0)
    
    capture_rate = base_rate * ball_multiplier * 0.5 + 0.1
    return min(1.0, max(0.1, capture_rate))