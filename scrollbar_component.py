# 统一滚动条组件 - 用于替换重复的滚动条渲染代码
import pygame

class ScrollbarComponent:
    """统一的滚动条组件，减少重复的滚动条渲染代码"""
    
    def __init__(self, x, y, width, height, total_items, visible_items):
        """
        初始化滚动条
        Args:
            x, y: 滚动条位置
            width, height: 滚动条尺寸
            total_items: 总项目数
            visible_items: 可见项目数
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.total_items = total_items
        self.visible_items = visible_items
        self.scroll_offset = 0
        self.dragging = False
        self.slider_rect = None
        
        # 滚动条样式配置
        self.bg_color = (200, 200, 200)
        self.slider_color = (100, 100, 100)
        self.slider_drag_color = (80, 80, 80)
        self.border_color = (0, 0, 0)
        
        self._update_slider()
    
    def _update_slider(self):
        """更新滑块位置和大小"""
        if self.total_items <= self.visible_items:
            self.slider_rect = None
            return
        
        max_scroll = max(0, self.total_items - self.visible_items)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        
        # 计算滑块大小和位置
        slider_height = max(20, int(self.rect.height * self.visible_items / self.total_items))
        if max_scroll > 0:
            slider_y = self.rect.y + int(self.scroll_offset * (self.rect.height - slider_height) / max_scroll)
        else:
            slider_y = self.rect.y
        
        self.slider_rect = pygame.Rect(self.rect.x, slider_y, self.rect.width, slider_height)
    
    def draw(self, screen):
        """绘制滚动条"""
        if self.total_items <= self.visible_items:
            return  # 不需要滚动条
        
        # 绘制滚动条背景
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 1)
        
        # 绘制滑块
        if self.slider_rect:
            slider_color = self.slider_drag_color if self.dragging else self.slider_color
            pygame.draw.rect(screen, slider_color, self.slider_rect)
            pygame.draw.rect(screen, self.border_color, self.slider_rect, 1)
    
    def handle_mouse_down(self, pos):
        """处理鼠标按下事件"""
        if not self.rect.collidepoint(pos):
            return False
        
        if self.slider_rect and self.slider_rect.collidepoint(pos):
            # 开始拖拽滑块
            self.dragging = True
            return True
        else:
            # 点击滚动条其他位置，跳转到相应位置
            if self.total_items > self.visible_items:
                click_y = pos[1] - self.rect.y
                scroll_ratio = click_y / self.rect.height
                max_scroll = self.total_items - self.visible_items
                self.scroll_offset = int(scroll_ratio * max_scroll)
                self._update_slider()
            return True
    
    def handle_mouse_up(self, pos):
        """处理鼠标释放事件"""
        if self.dragging:
            self.dragging = False
            return True
        return False
    
    def handle_mouse_motion(self, pos):
        """处理鼠标移动事件（拖拽）"""
        if not self.dragging or not self.slider_rect:
            return False
        
        # 计算新的滚动位置
        max_scroll = self.total_items - self.visible_items
        if max_scroll > 0:
            slider_height = self.slider_rect.height
            drag_range = self.rect.height - slider_height
            
            if drag_range > 0:
                relative_y = pos[1] - self.rect.y - slider_height // 2
                scroll_ratio = max(0, min(1, relative_y / drag_range))
                self.scroll_offset = int(scroll_ratio * max_scroll)
                self._update_slider()
        
        return True
    
    def handle_scroll(self, direction):
        """处理滚轮滚动"""
        if self.total_items <= self.visible_items:
            return False
        
        old_offset = self.scroll_offset
        self.scroll_offset += direction * 3  # 滚动速度
        self._update_slider()
        
        return old_offset != self.scroll_offset
    
    def get_visible_range(self):
        """获取当前可见的项目范围"""
        start = self.scroll_offset
        end = min(start + self.visible_items, self.total_items)
        return start, end
    
    def update_items(self, total_items, visible_items):
        """更新项目数量"""
        self.total_items = total_items
        self.visible_items = visible_items
        self._update_slider()
    
    def is_needed(self):
        """判断是否需要显示滚动条"""
        return self.total_items > self.visible_items