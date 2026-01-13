# -*- coding: utf-8 -*-
import sys
import json
import math
import copy
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtPrintSupport import QPrinter

# --- Configuration & Constants ---
DEFAULT_FONT = "SimSun"
DEFAULT_FONT_SIZE = 24
COLUMN_SPACING = 10
LINE_HEIGHT_RATIO = 1.2
ASSETS_DIR = "assets"  # 素材库目录

# Vertically sensitive characters (Simple Heuristic for demo)
ROTATE_CHARS = {'—', '…', '(', ')', '[', ']', '{', '}', '《', '》', '-', '_'}
OFFSET_CHARS = {'，', '。', '、', '：', '；', '！', '？', ',', '.', '!', '?'}

class AssetManager:
    """素材管理器"""
    def __init__(self):
        self.assets_file = os.path.join(ASSETS_DIR, "assets.json")
        self.ensure_assets_dir()
        self.load_assets()
    
    def ensure_assets_dir(self):
        """确保素材目录存在"""
        if not os.path.exists(ASSETS_DIR):
            os.makedirs(ASSETS_DIR)
            print(f"创建素材目录: {ASSETS_DIR}")
        else:
            print(f"素材目录已存在 {ASSETS_DIR}")
    
    def load_assets(self):
        """加载素材库"""
        print(f"加载素材库 {self.assets_file}")
        if os.path.exists(self.assets_file):
            try:
                with open(self.assets_file, 'r', encoding='utf-8') as f:
                    self.assets = json.load(f)
                print(f"成功加载素材库 文字{len(self.assets.get('texts', []))}条 图片{len(self.assets.get('images', []))}条 组合{len(self.assets.get('groups', []))}条")
            except Exception as e:
                print(f"加载素材库失败 {e}")
                self.assets = {"texts": [], "images": [], "groups": []}
        else:
            print("素材库文件不存在，创建新的")
            self.assets = {"texts": [], "images": [], "groups": []}
    
    def save_assets(self):
        """保存素材库"""
        print(f"保存素材库到: {self.assets_file}")
        print(f"素材数据: 文字{len(self.assets.get('texts', []))}条 图片{len(self.assets.get('images', []))}条 组合{len(self.assets.get('groups', []))}条")
        with open(self.assets_file, 'w', encoding='utf-8') as f:
            json.dump(self.assets, f, indent=2, ensure_ascii=False)
        print("素材库保存完成")
    
    def add_text_asset(self, text_item):
        """添加文字素材"""
        print(f"开始保存文字素材 {text_item.full_text[:20]}")
        asset_data = {
            'id': len(self.assets['texts']),
            'name': text_item.full_text[:20] + ('...' if len(text_item.full_text) > 20 else ''),
            'text': text_item.full_text,
            'font_size': text_item.font_size,
            'box_height': text_item.box_height,
            'font_family': text_item.font_family,
            'text_color': text_item.text_color.name(),
            'created_time': QDateTime.currentDateTime().toString()
        }
        self.assets['texts'].append(asset_data)
        print(f"文字素材数据: {asset_data}")
        self.save_assets()
        print(f"当前文字素材总数: {len(self.assets['texts'])}")
        return asset_data
    
    def add_image_asset(self, image_item):
        """添加图片素材"""
        print(f"开始保存图片素材 {image_item.file_path}")
        # 复制图片到素材目录
        original_path = image_item.file_path
        filename = os.path.basename(original_path)
        asset_path = os.path.join(ASSETS_DIR, f"img_{len(self.assets['images'])}_{filename}")
        
        try:
            # 复制文件
            import shutil
            shutil.copy2(original_path, asset_path)
            print(f"图片已复制到: {asset_path}")
            
            asset_data = {
                'id': len(self.assets['images']),
                'name': filename,
                'path': asset_path,
                'original_path': original_path,
                'width': image_item.target_width,
                'created_time': QDateTime.currentDateTime().toString()
            }
            self.assets['images'].append(asset_data)
            print(f"图片素材数据: {asset_data}")
            self.save_assets()
            print(f"当前图片素材总数: {len(self.assets['images'])}")
            return asset_data
        except Exception as e:
            print(f"复制图片失败: {e}")
            return None
    
    def get_text_assets(self):
        """获取所有文字素材"""
        return self.assets.get('texts', [])
    
    def get_image_assets(self):
        """获取所有图片素材"""
        return self.assets.get('images', [])
    
    def add_group_asset(self, items, scene):
        """添加组合素材(支持父子关系和图文连接)"""
        if not items:
            return None
        
        # 创建项目到索引的映射
        item_to_index = {item: idx for idx, item in enumerate(items)}
        
        # 保存所有项目的数据
        items_data = []
        for idx, item in enumerate(items):
            if isinstance(item, VTextItem):
                item_data = {
                    'type': 'VTextItem',
                    'text': item.full_text,
                    'font_size': item.font_size,
                    'box_height': item.box_height,
                    'font_family': item.font_family,
                    'text_color': item.text_color.name(),
                    'chars_per_column': item.chars_per_column,
                    'column_spacing': item.column_spacing,
                    'auto_height': item.auto_height,
                    'manual_line_break': item.manual_line_break,
                    'scene_pos': (item.scenePos().x(), item.scenePos().y()),
                    'local_pos': (item.x(), item.y()),
                    'parent_index': item_to_index.get(item.parentItem(), -1) if isinstance(item.parentItem(), BaseElement) else -1
                }
                items_data.append(item_data)
            elif isinstance(item, VImageItem):
                # 复制图片文件
                original_path = item.file_path
                filename = os.path.basename(original_path)
                asset_path = os.path.join(ASSETS_DIR, f"group_{len(self.assets['groups'])}_{idx}_{filename}")
                
                try:
                    import shutil
                    shutil.copy2(original_path, asset_path)
                    
                    item_data = {
                        'type': 'VImageItem',
                        'path': asset_path,
                        'original_path': original_path,
                        'width': item.target_width,
                        'scene_pos': (item.scenePos().x(), item.scenePos().y()),
                        'local_pos': (item.x(), item.y()),
                        'parent_index': item_to_index.get(item.parentItem(), -1) if isinstance(item.parentItem(), BaseElement) else -1
                    }
                    items_data.append(item_data)
                except Exception as e:
                    print(f"复制图片失败: {e}")
                    return None
        
        # 保存图文连接关系
        image_text_connections = []
        for conn in scene.image_text_connectors:
            img_idx = item_to_index.get(conn.image_item, -1)
            text_idx = item_to_index.get(conn.text_item, -1)
            if img_idx != -1 and text_idx != -1:
                image_text_connections.append((img_idx, text_idx))
        
        # 生成组合名称
        text_count = sum(1 for item in items if isinstance(item, VTextItem))
        image_count = sum(1 for item in items if isinstance(item, VImageItem))
        group_name = f"组合_{text_count}文字_{image_count}图片"
        
        # 创建组合素材数据
        group_asset = {
            'id': len(self.assets['groups']),
            'name': group_name,
            'items': items_data,
            'image_text_connections': image_text_connections,
            'item_count': len(items),
            'created_time': QDateTime.currentDateTime().toString()
        }
        
        self.assets['groups'].append(group_asset)
        self.save_assets()
        return group_asset
    
    def get_group_assets(self):
        """获取所有组合素材"""
        return self.assets.get('groups', [])
    
    def remove_group_asset(self, asset_id):
        """删除组合素材"""
        # 找到要删除的素材
        asset_to_remove = None
        for asset in self.assets['groups']:
            if asset['id'] == asset_id:
                asset_to_remove = asset
                break
        
        if asset_to_remove:
            # 删除相关的图片文件
            for item_data in asset_to_remove['items']:
                if item_data['type'] == 'VImageItem':
                    try:
                        if os.path.exists(item_data['path']):
                            os.remove(item_data['path'])
                    except:
                        pass
            
            # 从列表中删除
            self.assets['groups'] = [a for a in self.assets['groups'] if a['id'] != asset_id]
            self.save_assets()
    
    def remove_text_asset(self, asset_id):
        """删除文字素材"""
        self.assets['texts'] = [a for a in self.assets['texts'] if a['id'] != asset_id]
        self.save_assets()
    
    def remove_image_asset(self, asset_id):
        """删除图片素材"""
        # 找到要删除的素材
        asset_to_remove = None
        for asset in self.assets['images']:
            if asset['id'] == asset_id:
                asset_to_remove = asset
                break
        
        if asset_to_remove:
            # 删除文件
            try:
                if os.path.exists(asset_to_remove['path']):
                    os.remove(asset_to_remove['path'])
            except:
                pass
            
            # 从列表中删除
            self.assets['images'] = [a for a in self.assets['images'] if a['id'] != asset_id]
            self.save_assets()

class AssetLibraryWidget(QWidget):
    """素材库窗口"""
    def __init__(self, asset_manager, main_window):
        super().__init__()
        self.asset_manager = asset_manager
        self.main_window = main_window
        self.setup_ui()
        self.refresh_assets()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("素材库")
        self.setGeometry(100, 100, 400, 600)
        
        layout = QVBoxLayout()
        
        # 标签页
        self.tab_widget = QTabWidget()
        
        # 文字素材标签页
        self.text_tab = QWidget()
        text_layout = QVBoxLayout()
        
        # 文字素材列表
        self.text_list = QListWidget()
        self.text_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.text_list.itemDoubleClicked.connect(self.use_text_asset)
        text_layout.addWidget(QLabel("文字素材:"))
        text_layout.addWidget(self.text_list)
        
        # 文字操作按钮
        text_btn_layout = QHBoxLayout()
        btn_delete_text = QPushButton("删除选中")
        btn_delete_text.clicked.connect(self.delete_text_asset)
        text_btn_layout.addWidget(btn_delete_text)
        text_layout.addLayout(text_btn_layout)
        
        self.text_tab.setLayout(text_layout)
        self.tab_widget.addTab(self.text_tab, "文字")
        
        # 图片素材标签页
        self.image_tab = QWidget()
        image_layout = QVBoxLayout()
        
        # 图片素材列表
        self.image_list = QListWidget()
        self.image_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.image_list.setViewMode(QListView.ViewMode.IconMode)
        self.image_list.setIconSize(QSize(80, 80))
        self.image_list.itemDoubleClicked.connect(self.use_image_asset)
        image_layout.addWidget(QLabel("图片素材:"))
        image_layout.addWidget(self.image_list)
        
        # 图片操作按钮
        image_btn_layout = QHBoxLayout()
        btn_delete_image = QPushButton("删除选中")
        btn_delete_image.clicked.connect(self.delete_image_asset)
        image_btn_layout.addWidget(btn_delete_image)
        image_layout.addLayout(image_btn_layout)
        
        self.image_tab.setLayout(image_layout)
        self.tab_widget.addTab(self.image_tab, "图片")
        
        # 组合素材标签页
        self.group_tab = QWidget()
        group_layout = QVBoxLayout()
        
        # 组合素材列表
        self.group_list = QListWidget()
        self.group_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.group_list.itemDoubleClicked.connect(self.use_group_asset)
        group_layout.addWidget(QLabel("组合素材:"))
        group_layout.addWidget(self.group_list)
        
        # 组合操作按钮
        group_btn_layout = QHBoxLayout()
        btn_delete_group = QPushButton("删除选中")
        btn_delete_group.clicked.connect(self.delete_group_asset)
        group_btn_layout.addWidget(btn_delete_group)
        group_layout.addLayout(group_btn_layout)
        
        self.group_tab.setLayout(group_layout)
        self.tab_widget.addTab(self.group_tab, "组合")
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh_assets)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def refresh_assets(self):
        """刷新素材列表"""
        print("开始刷新素材库显示")
        
        # 重新加载素材数据
        self.asset_manager.load_assets()
        
        # 刷新文字素材
        self.text_list.clear()
        text_assets = self.asset_manager.get_text_assets()
        print(f"加载文字素材: {len(text_assets)} 条")
        for asset in text_assets:
            item = QListWidgetItem(asset['name'])
            item.setData(Qt.ItemDataRole.UserRole, asset)
            item.setToolTip(f"文字: {asset['text'][:50]}...\n字体: {asset['font_family']}\n大小: {asset['font_size']}")
            self.text_list.addItem(item)
        
        # 刷新图片素材
        self.image_list.clear()
        image_assets = self.asset_manager.get_image_assets()
        print(f"加载图片素材: {len(image_assets)} 条")
        for asset in image_assets:
            item = QListWidgetItem(asset['name'])
            item.setData(Qt.ItemDataRole.UserRole, asset)
            
            # 设置缩略图
            if os.path.exists(asset['path']):
                pixmap = QPixmap(asset['path'])
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    item.setIcon(QIcon(scaled_pixmap))
            
            item.setToolTip(f"图片: {asset['name']}\n尺寸: {asset['width']}px")
            self.image_list.addItem(item)
        
        # 刷新组合素材
        self.group_list.clear()
        group_assets = self.asset_manager.get_group_assets()
        print(f"加载组合素材: {len(group_assets)} 条")
        for asset in group_assets:
            item = QListWidgetItem(asset['name'])
            item.setData(Qt.ItemDataRole.UserRole, asset)
            
            # 创建详细信息
            details = f"包含 {asset['item_count']} 个元素\n"
            text_count = sum(1 for item_data in asset['items'] if item_data['type'] == 'VTextItem')
            image_count = sum(1 for item_data in asset['items'] if item_data['type'] == 'VImageItem')
            details += f"文字: {text_count} 条 图片: {image_count} 个\n"
            details += f"连接: {len(asset['image_text_connections'])} 条"
            
            item.setToolTip(details)
            self.group_list.addItem(item)
        
        print("素材库刷新完成")
    
    def use_text_asset(self, item):
        """使用文字素材"""
        asset = item.data(Qt.ItemDataRole.UserRole)
        if asset:
            # 创建文字项目
            text_item = VTextItem(
                asset['text'],
                asset['font_size'],
                asset['box_height']
            )
            text_item.font_family = asset['font_family']
            text_item.text_color = QColor(asset['text_color'])
            text_item.rebuild()
            
            # 添加到画布中央
            center = self.main_window.view.mapToScene(self.main_window.view.viewport().rect().center())
            text_item.setPos(center)
            self.main_window.scene.add_item_with_undo(text_item)
            print(f"已添加文字素材 {asset['name']}")
    
    def use_image_asset(self, item):
        """使用图片素材"""
        asset = item.data(Qt.ItemDataRole.UserRole)
        if asset and os.path.exists(asset['path']):
            # 创建图片项目
            image_item = VImageItem(asset['path'], asset['width'])
            
            # 添加到画布中央
            center = self.main_window.view.mapToScene(self.main_window.view.viewport().rect().center())
            image_item.setPos(center)
            self.main_window.scene.add_item_with_undo(image_item)
            print(f"已添加图片素材 {asset['name']}")
    
    def use_group_asset(self, item):
        """使用组合素材"""
        asset = item.data(Qt.ItemDataRole.UserRole)
        if asset:
            # 获取粘贴位置
            center = self.main_window.view.mapToScene(self.main_window.view.viewport().rect().center())
            
            # 计算所有项目的边界框，用于确定粘贴位置
            if asset['items']:
                min_x = min(item_data['scene_pos'][0] for item_data in asset['items'])
                min_y = min(item_data['scene_pos'][1] for item_data in asset['items'])
            else:
                min_x = min_y = 0
            
            base_x, base_y = center.x(), center.y()
            new_items = []
            
            # 第一步：创建所有项目
            for idx, item_data in enumerate(asset['items']):
                new_item = None
                
                if item_data['type'] == 'VTextItem':
                    new_item = VTextItem(
                        item_data['text'],
                        item_data['font_size'],
                        item_data['box_height']
                    )
                    new_item.font_family = item_data['font_family']
                    new_item.text_color = QColor(item_data['text_color'])
                    
                    # 恢复其他属性
                    if 'chars_per_column' in item_data:
                        new_item.chars_per_column = item_data['chars_per_column']
                    if 'column_spacing' in item_data:
                        new_item.column_spacing = item_data['column_spacing']
                    if 'auto_height' in item_data:
                        new_item.auto_height = item_data['auto_height']
                    if 'manual_line_break' in item_data:
                        new_item.manual_line_break = item_data['manual_line_break']
                    
                    new_item.rebuild()
                elif item_data['type'] == 'VImageItem':
                    if os.path.exists(item_data['path']):
                        new_item = VImageItem(item_data['path'], item_data['width'])
                
                if new_item:
                    # 计算相对于原始组合的偏移量，然后应用到新的基准位置
                    offset_x = item_data['scene_pos'][0] - min_x
                    offset_y = item_data['scene_pos'][1] - min_y
                    new_item.setPos(base_x + offset_x, base_y + offset_y)
                    
                    # 使用撤销系统添加元素
                    command = AddItemCommand(self.main_window.scene, new_item)
                    self.main_window.scene.undo_stack.push(command)
                    new_items.append(new_item)
            
            # 第二步：恢复父子关系
            for idx, item_data in enumerate(asset['items']):
                if item_data['parent_index'] != -1 and item_data['parent_index'] < len(new_items):
                    child_item = new_items[idx]
                    parent_item = new_items[item_data['parent_index']]
                    
                    # 保存当前场景坐标
                    current_scene_pos = child_item.scenePos()
                    # 设置父子关系
                    child_item.setParentItem(parent_item)
                    # 将场景坐标转换为父级的本地坐标
                    local_pos = parent_item.mapFromScene(current_scene_pos)
                    child_item.setPos(local_pos)
                    
                    # 创建父子连接线
                    self.main_window.scene.add_connector(parent_item, child_item)
            
            # 第三步：恢复图文连接
            for img_idx, text_idx in asset['image_text_connections']:
                if img_idx < len(new_items) and text_idx < len(new_items):
                    img_item = new_items[img_idx]
                    text_item = new_items[text_idx]
                    # 确保是正确的类型
                    if isinstance(img_item, VImageItem) and isinstance(text_item, VTextItem):
                        self.main_window.scene.add_image_text_connector(img_item, text_item)
                    elif isinstance(img_item, VTextItem) and isinstance(text_item, VImageItem):
                        self.main_window.scene.add_image_text_connector(text_item, img_item)
            
            print(f"已添加组合素材 {asset['name']} ({len(new_items)} 个元素)")
    
    def delete_text_asset(self):
        """删除选中的文字素材"""
        current_item = self.text_list.currentItem()
        if current_item:
            asset = current_item.data(Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(self, "确认删除", f"确定要删除文字素材'{asset['name']}' 吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self.asset_manager.remove_text_asset(asset['id'])
                self.refresh_assets()
    
    def delete_image_asset(self):
        """删除选中的图片素材"""
        current_item = self.image_list.currentItem()
        if current_item:
            asset = current_item.data(Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(self, "确认删除", f"确定要删除图片素材'{asset['name']}' 吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self.asset_manager.remove_image_asset(asset['id'])
                self.refresh_assets()
    
    def delete_group_asset(self):
        """删除选中的组合素材"""
        current_item = self.group_list.currentItem()
        if current_item:
            asset = current_item.data(Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(self, "确认删除", f"确定要删除组合素材'{asset['name']}' 吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self.asset_manager.remove_group_asset(asset['id'])
                self.refresh_assets()

class ProjectData:
    """Helper to serialize/deserialize project"""
    @staticmethod
    def save(scene, filepath):
        items_data = []
        # Store items with IDs to reconstruct hierarchy
        item_map = {} # item -> id
        
        # Assign IDs
        for idx, item in enumerate(scene.items()):
            if isinstance(item, (VTextItem, VImageItem)):
                item_map[item] = idx
        
        for item, item_id in item_map.items():
            data = {
                'id': item_id,
                'type': item.__class__.__name__,
                'x': item.x(),
                'y': item.y(),
                'parent_id': item_map.get(item.parentItem(), -1),
                'z': item.zValue()
            }
            if isinstance(item, VTextItem):
                data['text'] = item.full_text
                data['font_size'] = item.font_size
                data['box_height'] = item.box_height
                data['font_family'] = item.font_family
                data['text_color'] = item.text_color.name()
            elif isinstance(item, VImageItem):
                data['path'] = item.file_path
                data['width'] = item.target_width
            
            items_data.append(data)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(items_data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load(scene, filepath):
        scene.clear()
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # First pass: Create items
        id_map = {} # id -> item
        delayed_parents = []
        
        for d in data:
            item = None
            if d['type'] == 'VTextItem':
                item = VTextItem(d['text'], d['font_size'], d['box_height'])
                if 'font_family' in d: item.font_family = d['font_family']
                if 'text_color' in d: item.text_color = QColor(d['text_color'])
                item.rebuild() # Rebrand with new changes
            elif d['type'] == 'VImageItem':
                item = VImageItem(d['path'], d['width'])
            
            if item:
                item.setPos(d['x'], d['y'])
                item.setZValue(d.get('z', 0))
                scene.addItem(item)
                id_map[d['id']] = item
                if d['parent_id'] != -1:
                    delayed_parents.append((item, d['parent_id']))
        
        # Second pass: Restore hierarchy
        for item, pid in delayed_parents:
            if pid in id_map:
                # 保存当前场景坐标
                curr_scene_pos = item.scenePos()
                # 设置父级
                item.setParentItem(id_map[pid])
                # 将场景坐标转换为父级的本地坐标并设置
                local_pos = id_map[pid].mapFromScene(curr_scene_pos)
                item.setPos(local_pos)

# --- Undo/Redo System ---

class UndoCommand:
    """撤销命令基类"""
    def __init__(self, scene):
        self.scene = scene
    
    def execute(self):
        """执行命令"""
        pass
    
    def undo(self):
        """撤销命令"""
        pass

class AddItemCommand(UndoCommand):
    """添加元素命令"""
    def __init__(self, scene, item):
        super().__init__(scene)
        self.item = item
        self.item_data = None
    
    def execute(self):
        self.scene.addItem(self.item)
        # 确保连接点可见性正确设置
        if isinstance(self.item, (VTextItem, VImageItem)):
            self.item.set_connection_points_visible(self.scene.show_connection_points)
        # 保存状态用于撤销
        self.save_item_state()
    
    def undo(self):
        self.scene.removeItem(self.item)
    
    def save_item_state(self):
        """保存元素状态"""
        if isinstance(self.item, VTextItem):
            self.item_data = {
                'type': 'VTextItem',
                'text': self.item.full_text,
                'font_size': self.item.font_size,
                'box_height': self.item.box_height,
                'font_family': self.item.font_family,
                'text_color': self.item.text_color.name(),
                'pos': (self.item.x(), self.item.y())
            }
        elif isinstance(self.item, VImageItem):
            self.item_data = {
                'type': 'VImageItem',
                'path': self.item.file_path,
                'width': self.item.target_width,
                'pos': (self.item.x(), self.item.y())
            }

class DeleteItemCommand(UndoCommand):
    """删除元素命令"""
    def __init__(self, scene, item):
        super().__init__(scene)
        self.item = item
        self.item_data = None
        self.save_item_state()
    
    def execute(self):
        self.scene.removeItem(self.item)
    
    def undo(self):
        # 重新创建元素
        if self.item_data['type'] == 'VTextItem':
            new_item = VTextItem(
                self.item_data['text'],
                self.item_data['font_size'],
                self.item_data['box_height']
            )
            new_item.font_family = self.item_data['font_family']
            new_item.text_color = QColor(self.item_data['text_color'])
            new_item.rebuild()
        elif self.item_data['type'] == 'VImageItem':
            new_item = VImageItem(
                self.item_data['path'],
                self.item_data['width']
            )
        
        new_item.setPos(self.item_data['pos'][0], self.item_data['pos'][1])
        self.scene.addItem(new_item)
        self.item = new_item
    
    def save_item_state(self):
        """保存元素状态"""
        if isinstance(self.item, VTextItem):
            self.item_data = {
                'type': 'VTextItem',
                'text': self.item.full_text,
                'font_size': self.item.font_size,
                'box_height': self.item.box_height,
                'font_family': self.item.font_family,
                'text_color': self.item.text_color.name(),
                'pos': (self.item.x(), self.item.y())
            }
        elif isinstance(self.item, VImageItem):
            self.item_data = {
                'type': 'VImageItem',
                'path': self.item.file_path,
                'width': self.item.target_width,
                'pos': (self.item.x(), self.item.y())
            }

class UndoStack:
    """撤销栈管理器"""
    def __init__(self, max_size=50):
        self.commands = []
        self.current_index = -1
        self.max_size = max_size
    
    def push(self, command):
        """添加新命令"""
        # 删除当前位置之后的所有命令
        self.commands = self.commands[:self.current_index + 1]
        
        # 添加新命令
        self.commands.append(command)
        self.current_index += 1
        
        # 限制栈大小
        if len(self.commands) > self.max_size:
            self.commands.pop(0)
            self.current_index -= 1
        
        # 执行命令
        command.execute()
    
    def undo(self):
        """撤销"""
        if self.can_undo():
            command = self.commands[self.current_index]
            command.undo()
            self.current_index -= 1
            return True
        return False
    
    def redo(self):
        """重做"""
        if self.can_redo():
            self.current_index += 1
            command = self.commands[self.current_index]
            command.execute()
            return True
        return False
    
    def can_undo(self):
        """是否可以撤销"""
        return self.current_index >= 0
    
    def can_redo(self):
        """是否可以重做"""
        return self.current_index < len(self.commands) - 1
    
    def clear(self):
        """清空栈"""
        self.commands.clear()
        self.current_index = -1

# --- Graphics Items ---

class AnchorHandle(QGraphicsRectItem):
    """An anchor point for connectors"""
    def __init__(self, parent, role="bottom"):
        super().__init__(-4, -4, 8, 8, parent)
        self.setBrush(QBrush(QColor("red")))
        self.setPen(Qt.PenStyle.NoPen)
        self.role = role # top, bottom, left, right
        self.setVisible(False) # Show only when needed or strictly mainly logic
        
    def get_scene_pos(self):
        return self.mapToScene(0, 0)

class ConnectionPoint(QGraphicsEllipseItem):
    """可视化连接点"""
    def __init__(self, parent_item, point_type="image_top"):
        super().__init__(-8, -8, 16, 16)  # 16x16像素的圆点（更大）
        self.parent_element = parent_item
        self.point_type = point_type  # "image_top", "text_bottom"
        self.connected_lines = []  # 连接到此点的线条
        
        # 设置样式
        self.setBrush(QBrush(QColor(255, 100, 100, 200)))  # 半透明红色
        self.setPen(QPen(QColor(200, 50, 50), 3))  # 更粗的边框
        
        # 设置交互属性
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # 设置层级和父级
        self.setZValue(100)  # 显示在最上层
        self.setParentItem(parent_item)
        
        # 更新位置
        self.update_position()
        
        # 鼠标悬停效果
        self.setAcceptHoverEvents(True)
        
    def update_position(self):
        """更新连接点位置"""
        if not self.parent_element:
            return
            
        rect = self.parent_element.boundingRect()
        
        if self.point_type == "image_top":
            # 图片顶部中点
            self.setPos(rect.width()/2, 0)
        elif self.point_type == "text_bottom":
            # 文字底部中点
            self.setPos(rect.width()/2, rect.height())
    
    def hoverEnterEvent(self, event):
        """鼠标悬停进入"""
        self.setBrush(QBrush(QColor(255, 150, 150, 255)))  # 高亮显示
        self.setPen(QPen(QColor(255, 0, 0), 4))  # 更粗的悬停边框
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """鼠标悬停离开"""
        self.setBrush(QBrush(QColor(255, 100, 100, 200)))  # 恢复原样
        self.setPen(QPen(QColor(200, 50, 50), 3))  # 恢复原始粗细
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下开始连接"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.scene():
                self.scene().start_connection_from_point(self)
        super().mousePressEvent(event)
    
    def get_scene_center(self):
        """获取连接点在场景中的中心位置"""
        return self.mapToScene(0, 0)

class VGenericConnector(QGraphicsPathItem):
    """通用连接线 - 支持任意两个元素之间的连接"""
    def __init__(self, item1, item2, connection_type="generic"):
        super().__init__()
        self.item1 = item1
        self.item2 = item2
        self.connection_type = connection_type  # "image-image", "text-text", "generic"
        self.setZValue(-45)  # 比图文连接器层级稍低
        
        # 统一使用红色连接线
        pen = QPen(QColor(255, 0, 0, 200))  # 红色
        pen.setWidth(3)  # 更粗的线条
        pen.setStyle(Qt.PenStyle.SolidLine)
        self.setPen(pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        
    def update_path(self):
        if not self.item1.scene() or not self.item2.scene():
            return

        # 获取两个元素的连接点
        point1 = self.get_connection_point(self.item1)
        point2 = self.get_connection_point(self.item2)
        
        if not point1 or not point2:
            # 如果没有连接点，使用中心点
            rect1 = self.item1.boundingRect()
            pos1 = self.item1.scenePos()
            anchor1 = pos1 + QPointF(rect1.width()/2, rect1.height()/2)
            
            rect2 = self.item2.boundingRect()
            pos2 = self.item2.scenePos()
            anchor2 = pos2 + QPointF(rect2.width()/2, rect2.height()/2)
        else:
            anchor1 = point1.get_scene_center()
            anchor2 = point2.get_scene_center()
        
        path = QPainterPath()
        path.moveTo(anchor1)
        
        # 计算控制点，创建优美的曲线
        distance = (anchor2 - anchor1).manhattanLength()
        curve_offset = min(distance * 0.3, 80)
        
        # 根据相对位置调整控制点
        dx = anchor2.x() - anchor1.x()
        dy = anchor2.y() - anchor1.y()
        
        if abs(dx) > abs(dy):  # 水平方向为主
            ctrl1 = anchor1 + QPointF(curve_offset if dx > 0 else -curve_offset, 0)
            ctrl2 = anchor2 - QPointF(curve_offset if dx > 0 else -curve_offset, 0)
        else:  # 垂直方向为主
            ctrl1 = anchor1 + QPointF(0, curve_offset if dy > 0 else -curve_offset)
            ctrl2 = anchor2 - QPointF(0, curve_offset if dy > 0 else -curve_offset)
        
        path.cubicTo(ctrl1, ctrl2, anchor2)
        self.setPath(path)
    
    def get_connection_point(self, item):
        """获取元素的连接点"""
        for child in item.childItems():
            if isinstance(child, ConnectionPoint):
                return child
        return None

class VImageTextConnector(QGraphicsPathItem):
    """图文连接线- 连接图片顶部中点和文字底部中点"""
    def __init__(self, image_item, text_item):
        super().__init__()
        self.image_item = image_item
        self.text_item = text_item
        self.setZValue(-50)  # 比普通连接器层级高一条
        
        pen = QPen(QColor(255, 100, 100, 200))  # 稍微不同的红条
        pen.setWidth(3)  # 更粗的线条
        pen.setStyle(Qt.PenStyle.SolidLine)  # 实线而不是虚条
        self.setPen(pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        
    def update_path(self):
        if not self.image_item.scene() or not self.text_item.scene():
            return

        # 从连接点获取位置
        img_point = None
        text_point = None
        
        # 查找图片的连接点
        for child in self.image_item.childItems():
            if isinstance(child, ConnectionPoint) and child.point_type == "image_top":
                img_point = child
                break
        
        # 查找文字的连接点
        for child in self.text_item.childItems():
            if isinstance(child, ConnectionPoint) and child.point_type == "text_bottom":
                text_point = child
                break
        
        if not img_point or not text_point:
            # 如果没有连接点，使用原来的计算方条
            img_rect = self.image_item.boundingRect()
            img_pos = self.image_item.scenePos()
            img_anchor = img_pos + QPointF(img_rect.width()/2, 0)
            
            text_rect = self.text_item.boundingRect()
            text_pos = self.text_item.scenePos()
            text_anchor = text_pos + QPointF(text_rect.width()/2, text_rect.height())
        else:
            # 使用连接点的位置
            img_anchor = img_point.get_scene_center()
            text_anchor = text_point.get_scene_center()
        
        path = QPainterPath()
        path.moveTo(img_anchor)
        
        # 计算控制点，创建优美的曲条
        distance = (text_anchor - img_anchor).manhattanLength()
        curve_offset = min(distance * 0.3, 100)  # 曲线弯曲程度
        
        # 根据相对位置调整控制条
        if text_anchor.y() > img_anchor.y():  # 文字在图片下条
            ctrl1 = img_anchor + QPointF(0, curve_offset)
            ctrl2 = text_anchor - QPointF(0, curve_offset)
        else:  # 文字在图片上条
            ctrl1 = img_anchor - QPointF(0, curve_offset)
            ctrl2 = text_anchor + QPointF(0, curve_offset)
        
        path.cubicTo(ctrl1, ctrl2, text_anchor)
        self.setPath(path)

class VConnector(QGraphicsPathItem):
    """Dynamic Red Line Connector"""
    def __init__(self, parent_item, child_item):
        super().__init__()
        self.parent_element = parent_item
        self.child_element = child_item
        self.setZValue(-100)
        
        pen = QPen(QColor(255, 0, 0, 150))
        pen.setWidth(3)  # 更粗的线条
        pen.setStyle(Qt.PenStyle.DashLine)
        self.setPen(pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        
    def update_path(self):
        if not self.parent_element.scene() or not self.child_element.scene():
            return

        # Simple logic: closest points roughly
        # Or specifically: Parent Bottom -> Child Top
        p_anchor = self.parent_element.scenePos() + QPointF(self.parent_element.boundingRect().width()/2, self.parent_element.boundingRect().height())
        c_anchor = self.child_element.scenePos() + QPointF(self.child_element.boundingRect().width()/2, 0)
        
        if isinstance(self.parent_element, VTextItem):
            # Text grows down/left. Anchor at bottom of last col? Or center?
            # Let's use Bottom-Center of bounding rect for now
            pass
            
        path = QPainterPath()
        path.moveTo(p_anchor)
        # Bezier curve for smooth look
        ctrl1 = p_anchor + QPointF(0, 50)
        ctrl2 = c_anchor - QPointF(0, 50)
        path.cubicTo(ctrl1, ctrl2, c_anchor)
        self.setPath(path)

class BaseElement(QGraphicsItem):
    """Common base for Text and Image elements"""
    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.connectors = [] 

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update connectors
            if self.scene():
                self.scene().update_connectors(self)
                self.scene().update_image_text_connectors(self)
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        # 添加隐藏/显示连接点选项
        if hasattr(self, 'connection_point') and self.connection_point:
            if self.connection_point.isVisible():
                toggle_connection_point_action = menu.addAction("隐藏连接点 (Hide Connection Point)")
            else:
                toggle_connection_point_action = menu.addAction("显示连接点 (Show Connection Point)")
            menu.addSeparator()
        
        # 复制和删条
        copy_action = menu.addAction("复制 (Copy)")
        delete_action = menu.addAction("删除 (Delete)")
        save_as_asset_action = menu.addAction("保存为素条(Save as Asset)")
        menu.addSeparator()
        
        # 对齐功能
        selected_items = [item for item in self.scene().selectedItems() if isinstance(item, BaseElement)]
        if len(selected_items) >= 2:
            align_menu = menu.addMenu("对齐 (Align)")
            align_top_action = align_menu.addAction("顶部对齐")
            align_right_action = align_menu.addAction("右对齐")
            menu.addSeparator()
        
        unbind_action = menu.addAction("解除父级绑定 (Unbind)")
        set_parent_action = menu.addAction("设置父级 (Set Parent)")
        
        # 图文连接选项
        menu.addSeparator()
        connect_image_text_action = menu.addAction("图文连接 (Connect to Image/Text)")
        disconnect_image_text_action = menu.addAction("断开图文连接 (Disconnect Image/Text)")
        
        # 批量图文连接选项
        if len(selected_items) >= 2:
            batch_menu = menu.addMenu("批量连接 (Batch Connect)")
            auto_connect_action = batch_menu.addAction("智能连接")
            position_connect_action = batch_menu.addAction("位置连接")
            connect_to_text_action = batch_menu.addAction("连到文字")
            connect_to_image_action = batch_menu.addAction("连到图片")
            batch_menu.addSeparator()
            clear_connections_action = batch_menu.addAction("清除所有连接")
        
        action = menu.exec(event.screenPos())
        
        # 处理隐藏/显示连接点
        if hasattr(self, 'connection_point') and self.connection_point and action == toggle_connection_point_action:
            self.toggle_connection_point()
        elif action == copy_action:
            if self.scene():
                self.scene().copy_item(self)
        elif action == delete_action:
            if self.scene():
                self.scene().delete_item(self)
        elif action == save_as_asset_action:
            if self.scene():
                self.scene().save_item_as_asset(self)
        elif len(selected_items) >= 2:
            if action == align_top_action:
                self.scene().align_top(selected_items)
            elif action == align_right_action:
                self.scene().align_right(selected_items)
            elif action == auto_connect_action:
                self.scene().auto_connect_selected_items()
            elif action == position_connect_action:
                self.scene().connect_by_position()
            elif action == connect_to_text_action:
                self.scene().connect_all_images_to_text()
            elif action == connect_to_image_action:
                self.scene().connect_all_texts_to_image()
            elif action == clear_connections_action:
                self.scene().remove_all_image_text_connections()
        elif action == connect_image_text_action:
            if self.scene():
                self.scene().start_image_text_binding(self)
        elif action == disconnect_image_text_action:
            if self.scene():
                self.scene().remove_image_text_connectors(self)
        
        if action == unbind_action:
            # 保存当前场景坐标
            current_scene_pos = self.scenePos()
            self.setParentItem(None)
            # 恢复场景坐标
            self.setPos(current_scene_pos)
            # Remove connectors related to being a child
            if self.scene(): self.scene().remove_child_connectors(self)
        elif action == set_parent_action:
             if self.scene(): self.scene().start_binding_mode(self)

    def paint(self, painter, option, widget):
        # Draw a subtle selection border
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())
    
    def toggle_connection_point(self):
        """切换连接点的可见性"""
        if hasattr(self, 'connection_point') and self.connection_point:
            current_visible = self.connection_point.isVisible()
            self.connection_point.setVisible(not current_visible)
            element_type = "图片" if isinstance(self, VImageItem) else "文字"
            if current_visible:
                print(f"{element_type}连接点已隐藏")
            else:
                print(f"{element_type}连接点已显示")

class VTextItem(BaseElement):
    """Vertical Text Engine (Right-to-Left columns)"""
    def __init__(self, text="请输入文本", font_size=DEFAULT_FONT_SIZE, box_height=400):
        super().__init__()
        self.full_text = text
        self.font_size = font_size
        self.font_family = DEFAULT_FONT
        self.text_color = QColor(Qt.GlobalColor.black)
        self.box_height = box_height  # 保留作为最大高度限制
        self.chars_per_column = 15  # 每列字符数，可以调整
        self.auto_height = True  # 是否自动调整高度
        self.manual_line_break = True  # 是否启用手动换行（响应\n字符）
        
        # 列间距属性
        self.column_spacing = COLUMN_SPACING  # 列间距（所有列间距相同）
        
        self._rect = QRectF(0, 0, 100, 100)  # 初始值，会在rebuild中重新计算
        self.connection_point = None  # 连接线
        self.rebuild()
        self.create_connection_point()

    def rebuild(self):
        old_rect = self.boundingRect()
        
        # Clear child text items only
        scene = self.scene()
        child_items = self.childItems()
        for child in child_items:
            if not isinstance(child, (BaseElement, ConnectionPoint)):
                if scene:
                    scene.removeItem(child)
                else:
                    child.setParentItem(None)
            
        font = QFont(self.font_family, self.font_size)
        fm = QFontMetrics(font)
        char_h = fm.height()
        
        # 计算每列的步长（字体大小 + 列间距）
        col_step = self.font_size + self.column_spacing
        
        # 计算每列的实际高度限制
        if self.auto_height:
            effective_height = self.chars_per_column * char_h * LINE_HEIGHT_RATIO
        else:
            effective_height = self.box_height
        
        cursor_y = 0
        col_idx = 0
        generated_items = []
        
        for char in self.full_text:
            if char == '\n' and self.manual_line_break:
                cursor_y = 0
                col_idx += 1
                continue 
            elif char == '\n' and not self.manual_line_break:
                continue 
            
            is_rotated = char in ROTATE_CHARS
            is_offset = char in OFFSET_CHARS
            
            t = QGraphicsSimpleTextItem(char)
            t.setFont(font)
            t.setBrush(QBrush(self.text_color))
            
            if cursor_y + char_h > effective_height:
                cursor_y = 0
                col_idx += 1
            
            # 计算列的x位置（从右到左排列）
            x_local = -(col_idx * col_step)
            y_pos = cursor_y
            
            if is_rotated:
                t.setTransformOriginPoint(t.boundingRect().center())
                t.setRotation(90)
            
            final_x = x_local
            final_y = y_pos
            
            if is_offset:
                final_x += self.font_size * 0.4
                final_y -= self.font_size * 0.4
                
            t.setParentItem(self) 
            t.setPos(final_x, final_y)
            generated_items.append(t)
            cursor_y += char_h * LINE_HEIGHT_RATIO

        total_cols = col_idx + 1
        total_width = total_cols * col_step
        
        # 调整所有字符位置，使第一列保持在右侧
        shift_x = total_width - col_step
        
        for item in generated_items:
            item.moveBy(shift_x, 0)
        
        if generated_items:
            max_y = 0
            for item in generated_items:
                item_bottom = item.y() + item.boundingRect().height()
                max_y = max(max_y, item_bottom)
            actual_height = max(max_y + 5, char_h) 
        else:
            actual_height = char_h
            
        self._rect = QRectF(0, 0, total_width, actual_height)
        
        new_width = total_width
        old_width = old_rect.width()
        dx = old_width - new_width
        
        if abs(dx) > 0.1: 
            self.moveBy(dx, 0)
        
        if self.connection_point:
            self.connection_point.update_position()
    
    def create_connection_point(self):
        """创建文字的连接点(底部中点)"""
        if not self.connection_point:
            self.connection_point = ConnectionPoint(self, "text_bottom")
            if self.scene():
                visible = self.scene().show_connection_points
                self.connection_point.setVisible(visible)
            else:
                self.connection_point.setVisible(True)
    
    def set_connection_points_visible(self, visible):
        """设置连接点可见性"""
        if self.connection_point:
            self.connection_point.setVisible(visible)
        
    def contextMenuEvent(self, event):
        menu = QMenu()
        action_font = menu.addAction("设置字体 (Font)")
        action_color = menu.addAction("设置颜色 (Color)")
        action_chars_per_col = menu.addAction("设置每列字数 (Chars per Column)")
        action_column_spacing = menu.addAction("设置列间距 (Column Spacing)")
        menu.addSeparator()
        
        # 添加隐藏/显示连接点选项
        if self.connection_point and self.connection_point.isVisible():
            toggle_connection_point_action = menu.addAction("隐藏连接点 (Hide Connection Point)")
        else:
            toggle_connection_point_action = menu.addAction("显示连接点 (Show Connection Point)")
        menu.addSeparator()
        
        copy_action = menu.addAction("复制 (Copy)")
        delete_action = menu.addAction("删除 (Delete)")
        save_as_asset_action = menu.addAction("保存为素材(Save as Asset)")
        menu.addSeparator()
        
        selected_items = [item for item in self.scene().selectedItems() if isinstance(item, BaseElement)]
        if len(selected_items) >= 2:
            align_menu = menu.addMenu("对齐 (Align)")
            align_top_action = align_menu.addAction("顶部对齐")
            align_right_action = align_menu.addAction("右对齐")
            menu.addSeparator()
        
        unbind_action = menu.addAction("解除父级绑定 (Unbind)")
        set_parent_action = menu.addAction("设置父级 (Set Parent)")
        menu.addSeparator()
        connect_image_text_action = menu.addAction("图文连接 (Connect to Image/Text)")
        disconnect_image_text_action = menu.addAction("断开图文连接 (Disconnect Image/Text)")
        
        if len(selected_items) >= 2:
            batch_menu = menu.addMenu("批量连接 (Batch Connect)")
            auto_connect_action = batch_menu.addAction("智能连接")
            position_connect_action = batch_menu.addAction("位置连接")
            connect_to_text_action = batch_menu.addAction("连到文字")
            connect_to_image_action = batch_menu.addAction("连到图片")
            batch_menu.addSeparator()
            clear_connections_action = batch_menu.addAction("清除所有连接")
        
        action = menu.exec(event.screenPos())
        
        if action == action_font:
            self.change_font_settings()
        elif action == action_color:
            self.change_color_settings()
        elif action == action_chars_per_col:
            self.change_chars_per_column_settings()
        elif action == action_column_spacing:
            self.change_column_spacing_settings()
        elif action == toggle_connection_point_action:
            self.toggle_connection_point()
        elif action == copy_action:
            if self.scene():
                self.scene().copy_item(self)
        elif action == delete_action:
            if self.scene():
                self.scene().delete_item(self)
        elif action == save_as_asset_action:
            if self.scene():
                self.scene().save_item_as_asset(self)
        elif len(selected_items) >= 2:
            if action == align_top_action:
                self.scene().align_top(selected_items)
            elif action == align_right_action:
                self.scene().align_right(selected_items)
            elif action == auto_connect_action:
                self.scene().auto_connect_selected_items()
            elif action == position_connect_action:
                self.scene().connect_by_position()
            elif action == connect_to_text_action:
                self.scene().connect_all_images_to_text()
            elif action == connect_to_image_action:
                self.scene().connect_all_texts_to_image()
            elif action == clear_connections_action:
                self.scene().remove_all_image_text_connections()
        elif action == connect_image_text_action:
            if self.scene():
                self.scene().start_image_text_binding(self)
        elif action == disconnect_image_text_action:
            if self.scene():
                self.scene().remove_image_text_connectors(self)
        
        if action == unbind_action:
            current_scene_pos = self.scenePos()
            self.setParentItem(None)
            self.setPos(current_scene_pos)
            if self.scene(): self.scene().remove_child_connectors(self)
        elif action == set_parent_action:
             if self.scene(): self.scene().start_binding_mode(self)

    def change_font_settings(self):
        current_font = QFont(self.font_family, self.font_size)
        font, ok = QFontDialog.getFont(current_font, None, "选择字体")
        if ok:
            self.font_family = font.family()
            self.font_size = font.pointSize()
            self.rebuild()
            if self.scene(): self.scene().update_connectors(self)

    def change_color_settings(self):
        color = QColorDialog.getColor(self.text_color, None, "选择颜色")
        if color.isValid():
            self.text_color = color
            self.rebuild()
    
    def change_chars_per_column_settings(self):
        """设置每列字符数"""
        chars_count, ok = QInputDialog.getInt(None, "设置每列字符数", "每列字符数", self.chars_per_column, 5, 50)
        if ok:
            self.chars_per_column = chars_count
            self.rebuild()
            if self.scene(): 
                self.scene().update_connectors(self)
    
    def change_column_spacing_settings(self):
        """设置列间距"""
        spacing, ok = QInputDialog.getInt(None, "设置列间距", "列间距 (像素):", self.column_spacing, 0, 200)
        if ok:
            self.column_spacing = spacing
            self.rebuild()
            if self.scene():
                self.scene().update_connectors(self)
            print(f"列间距已设置为: {self.column_spacing}px")
    
    def toggle_connection_point(self):
        """切换连接点的可见性"""
        if self.connection_point:
            current_visible = self.connection_point.isVisible()
            self.connection_point.setVisible(not current_visible)
            if current_visible:
                print("文字连接点已隐藏")
            else:
                print("文字连接点已显示")

    def mouseDoubleClickEvent(self, event):
        text, ok = QInputDialog.getMultiLineText(None, "编辑文本", "请输入排版内容", self.full_text)
        if ok:
            self.full_text = text
            self.rebuild()
            if self.scene():
                self.scene().update_connectors(self)

    def boundingRect(self):
        return self._rect

class VImageItem(BaseElement):
    """Image Item that fits into columns"""
    def __init__(self, path, target_width=DEFAULT_FONT_SIZE):
        super().__init__()
        self.file_path = path
        self.target_width = target_width
        self.connection_point = None 
        
        pix = QPixmap(path)
        if not pix.isNull():
            ratio = pix.height() / pix.width()
            target_h = target_width * ratio
            self.p_item = QGraphicsPixmapItem(pix.scaled(int(target_width), int(target_h), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.p_item.setParentItem(self)
            self._rect = QRectF(0, 0, target_width, target_h)
        
        self.create_connection_point()
    
    def create_connection_point(self):
        """创建图片的连接点(顶部中点)"""
        if not self.connection_point:
            self.connection_point = ConnectionPoint(self, "image_top")
            if self.scene():
                visible = self.scene().show_connection_points
                self.connection_point.setVisible(visible)
            else:
                self.connection_point.setVisible(True)
    
    def set_connection_points_visible(self, visible):
        """设置连接点可见性"""
        if self.connection_point:
            self.connection_point.setVisible(visible)
    
    def toggle_connection_point(self):
        """切换连接点的可见性"""
        if self.connection_point:
            current_visible = self.connection_point.isVisible()
            self.connection_point.setVisible(not current_visible)
            if current_visible:
                print("图片连接点已隐藏")
            else:
                print("图片连接点已显示")
    
    def boundingRect(self):
        return self._rect

# --- Canvas & Scene ---

class LayoutScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(QColor(45, 45, 48))) 
        self.grid_pen = QPen(QColor(220, 220, 220, 100))
        self.binding_source = None
        self.connectors = []
        self.image_text_connectors = []  
        self.show_grid = True  
        self.show_connectors = True  
        self.show_image_text_connectors = True  
        self.undo_stack = UndoStack()  
        self.clipboard_items = []  
        self.clipboard_image_text_connections = []  
        self.show_connection_points = True  
        self.connection_mode = False  
        self.connection_source_point = None  
        self.asset_manager = AssetManager()  
        self.image_text_binding_mode = False  
        self.image_text_source = None  

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor(60, 60, 60))
        canvas_rect = self.sceneRect()
        shadow_rect = canvas_rect.translated(5, 5)
        painter.fillRect(shadow_rect, QColor(30, 30, 30, 150))
        painter.fillRect(canvas_rect, QColor(250, 250, 245))
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawRect(canvas_rect)

        if self.show_grid:
            painter.setPen(self.grid_pen)
            c_left = int(canvas_rect.left())
            c_right = int(canvas_rect.right())
            c_top = int(canvas_rect.top())
            c_bottom = int(canvas_rect.bottom())
            step = 50
            for x in range(c_left, c_right + 1, step):
                painter.drawLine(x, c_top, x, c_bottom)
            for y in range(c_top, c_bottom + 1, step):
                painter.drawLine(c_left, y, c_right, y)
            
    def start_binding_mode(self, item):
        self.binding_source = item
        views = self.views()
        if views:
            views[0].setCursor(Qt.CursorShape.CrossCursor)
        print("Select parent for binding...")

    def mousePressEvent(self, event):
        if self.binding_source:
            item = self.itemAt(event.scenePos(), QTransform())
            while item and not isinstance(item, BaseElement):
                item = item.parentItem()
            
            if item and item != self.binding_source:
                old_pos = self.binding_source.scenePos()
                self.binding_source.setParentItem(item)
                self.binding_source.setPos(item.mapFromScene(old_pos))
                self.add_connector(item, self.binding_source)
                print(f"Bound {self.binding_source} to {item}")
            
            self.binding_source = None
            if self.views(): self.views()[0].setCursor(Qt.CursorShape.ArrowCursor)
            return
        
        if self.image_text_binding_mode:
            item = self.itemAt(event.scenePos(), QTransform())
            while item and not isinstance(item, BaseElement):
                item = item.parentItem()
            
            if item and item != self.image_text_source:
                source_is_image = isinstance(self.image_text_source, VImageItem)
                target_is_text = isinstance(item, VTextItem)
                source_is_text = isinstance(self.image_text_source, VTextItem)
                target_is_image = isinstance(item, VImageItem)
                
                if (source_is_image and target_is_text) or (source_is_text and target_is_image):
                    if source_is_image:
                        self.add_image_text_connector(self.image_text_source, item)
                    else:
                        self.add_image_text_connector(item, self.image_text_source)
                else:
                    print("图文连接只能在图片和文字之间建立")
            
            self.image_text_binding_mode = False
            self.image_text_source = None
            if self.views(): self.views()[0].setCursor(Qt.CursorShape.ArrowCursor)
            return
            
        super().mousePressEvent(event)

    def add_connector(self, parent, child):
        self.remove_child_connectors(child)
        conn = VConnector(parent, child)
        self.addItem(conn)
        self.connectors.append(conn)
        conn.update_path()
        conn.setVisible(self.show_connectors)

    def remove_child_connectors(self, child):
        to_rem = [c for c in self.connectors if c.child_element == child]
        for c in to_rem:
            self.removeItem(c)
            self.connectors.remove(c)

    def update_connectors(self, item_moved):
        for c in self.connectors:
            if c.parent_element == item_moved or c.child_element == item_moved:
                c.update_path()

    def update_all_connectors(self):
        for c in self.connectors:
            c.update_path()
            c.setVisible(self.show_connectors)
    
    def set_connectors_visible(self, visible):
        """控制所有连接器的可见性"""
        self.show_connectors = visible
        for c in self.connectors:
            c.setVisible(visible)
    
    def set_image_text_connectors_visible(self, visible):
        """控制图文连接器的可见性"""
        self.show_image_text_connectors = visible
        for c in self.image_text_connectors:
            c.setVisible(visible)
    
    def set_connection_points_visible(self, visible):
        """控制所有连接点的可见性"""
        self.show_connection_points = visible
        for item in self.items():
            if isinstance(item, (VTextItem, VImageItem)):
                item.set_connection_points_visible(visible)
    
    def start_connection_from_point(self, point):
        """从连接点开始连接"""
        if self.connection_mode and self.connection_source_point:
            self.complete_connection(self.connection_source_point, point)
            self.connection_mode = False
            self.connection_source_point = None
            if self.views():
                self.views()[0].setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.connection_mode = True
            self.connection_source_point = point
            if self.views():
                self.views()[0].setCursor(Qt.CursorShape.CrossCursor)
            print("连接模式：点击另一个连接点完成连接")
    
    def complete_connection(self, source_point, target_point):
        """完成两个连接点之间的连接"""
        if source_point == target_point:
            print("不能连接到自身")
            return
        
        source_item = source_point.parent_element
        target_item = target_point.parent_element
        
        if isinstance(source_item, VImageItem) and isinstance(target_item, VTextItem):
            self.add_image_text_connector(source_item, target_item)
        elif isinstance(source_item, VTextItem) and isinstance(target_item, VImageItem):
            self.add_image_text_connector(target_item, source_item)
        elif isinstance(source_item, VImageItem) and isinstance(target_item, VImageItem):
            # 图片和图片之间的连接
            self.add_image_image_connector(source_item, target_item)
        elif isinstance(source_item, VTextItem) and isinstance(target_item, VTextItem):
            # 文字和文字之间的连接
            self.add_text_text_connector(source_item, target_item)
        else:
            print("连接类型不支持")
    
    def toggle_connection_points(self):
        """切换连接点显示状态"""
        self.show_connection_points = not self.show_connection_points
        self.set_connection_points_visible(self.show_connection_points)
        print(f"连接点显示 {'开启' if self.show_connection_points else '关闭'}")
    
    def save_item_as_asset(self, item):
        """保存元素为素材"""
        if isinstance(item, VTextItem):
            asset = self.asset_manager.add_text_asset(item)
            if asset:
                print(f"文字素材已保存 {asset['name']}")
                self.refresh_asset_library()
        elif isinstance(item, VImageItem):
            asset = self.asset_manager.add_image_asset(item)
            if asset:
                print(f"图片素材已保存 {asset['name']}")
                self.refresh_asset_library()
            else:
                print("保存图片素材失败")
    
    def save_group_as_asset(self, items=None):
        """保存组合为素材"""
        if items is None:
            items = [item for item in self.selectedItems() if isinstance(item, BaseElement)]
        
        if len(items) < 2:
            print("请选择至少两个元素来保存组合素材")
            return
        
        asset = self.asset_manager.add_group_asset(items, self)
        if asset:
            print(f"组合素材已保存 {asset['name']} (包含 {len(items)} 个元素)")
            self.refresh_asset_library()
        else:
            print("保存组合素材失败")
    
    def refresh_asset_library(self):
        """刷新素材库窗口"""
        if self.views():
            view = self.views()[0]
            widget = view
            while widget:
                if hasattr(widget, 'asset_library'):
                    if widget.asset_library and widget.asset_library.isVisible():
                        widget.asset_library.refresh_assets()
                    break
                widget = widget.parent()
    
    def start_image_text_binding(self, item):
        """开始图文连接模式"""
        if isinstance(item, (VImageItem, VTextItem)):
            self.image_text_binding_mode = True
            self.image_text_source = item
            views = self.views()
            if views:
                views[0].setCursor(Qt.CursorShape.CrossCursor)
            print(f"图文连接模式：请选择要连接的{'文字' if isinstance(item, VImageItem) else '图片'}")
    
    def add_image_text_connector(self, image_item, text_item):
        """添加图文连接线"""
        for conn in self.image_text_connectors:
            if ((conn.image_item == image_item and conn.text_item == text_item) or
                (conn.image_item == text_item and conn.text_item == image_item)):
                print("这两个元素已经连接")
                return
        
        conn = VImageTextConnector(image_item, text_item)
        self.addItem(conn)
        self.image_text_connectors.append(conn)
        conn.update_path()
        conn.setVisible(self.show_image_text_connectors)
        print("图文连接已创建")
    
    def add_image_image_connector(self, image1, image2):
        """添加图片-图片连接线"""
        # 检查是否已经存在连接
        for conn in self.image_text_connectors:
            if hasattr(conn, 'item1') and hasattr(conn, 'item2'):
                if ((conn.item1 == image1 and conn.item2 == image2) or
                    (conn.item1 == image2 and conn.item2 == image1)):
                    print("这两个图片已经连接")
                    return
        
        conn = VGenericConnector(image1, image2, "image-image")
        self.addItem(conn)
        self.image_text_connectors.append(conn)
        conn.update_path()
        conn.setVisible(self.show_image_text_connectors)
        print("图片-图片连接已创建")
    
    def add_text_text_connector(self, text1, text2):
        """添加文字-文字连接线"""
        # 检查是否已经存在连接
        for conn in self.image_text_connectors:
            if hasattr(conn, 'item1') and hasattr(conn, 'item2'):
                if ((conn.item1 == text1 and conn.item2 == text2) or
                    (conn.item1 == text2 and conn.item2 == text1)):
                    print("这两个文字已经连接")
                    return
        
        conn = VGenericConnector(text1, text2, "text-text")
        self.addItem(conn)
        self.image_text_connectors.append(conn)
        conn.update_path()
        conn.setVisible(self.show_image_text_connectors)
        print("文字-文字连接已创建")
    
    def remove_image_text_connectors(self, item):
        """移除与指定元素相关的所有连接线"""
        to_remove = []
        for conn in self.image_text_connectors:
            # 检查图文连接器
            if hasattr(conn, 'image_item') and hasattr(conn, 'text_item'):
                if conn.image_item == item or conn.text_item == item:
                    to_remove.append(conn)
            # 检查通用连接器
            elif hasattr(conn, 'item1') and hasattr(conn, 'item2'):
                if conn.item1 == item or conn.item2 == item:
                    to_remove.append(conn)
        
        for conn in to_remove:
            self.removeItem(conn)
            self.image_text_connectors.remove(conn)
    
    def update_image_text_connectors(self, item):
        """更新与指定元素相关的所有连接线"""
        for conn in self.image_text_connectors:
            # 检查图文连接器
            if hasattr(conn, 'image_item') and hasattr(conn, 'text_item'):
                if conn.image_item == item or conn.text_item == item:
                    conn.update_path()
            # 检查通用连接器
            elif hasattr(conn, 'item1') and hasattr(conn, 'item2'):
                if conn.item1 == item or conn.item2 == item:
                    conn.update_path()
    
    def update_all_image_text_connectors(self):
        """更新所有图文连接器"""
        for conn in self.image_text_connectors:
            conn.update_path()
            conn.setVisible(self.show_image_text_connectors)
    
    def auto_connect_selected_items(self):
        """自动连接选中的图片和文字"""
        selected = self.selectedItems()
        images = [item for item in selected if isinstance(item, VImageItem)]
        texts = [item for item in selected if isinstance(item, VTextItem)]
        
        if not images or not texts:
            print("请同时选中图片和文字进行自动连接")
            return
        
        connections_made = 0
        if len(images) == len(texts):
            used_texts = set()
            for img in images:
                closest_text = None
                min_distance = float('inf')
                for text in texts:
                    if text in used_texts: continue
                    img_pos = img.scenePos()
                    text_pos = text.scenePos()
                    distance = ((img_pos.x() - text_pos.x()) ** 2 + (img_pos.y() - text_pos.y()) ** 2) ** 0.5
                    if distance < min_distance:
                        min_distance = distance
                        closest_text = text
                if closest_text:
                    self.add_image_text_connector(img, closest_text)
                    used_texts.add(closest_text)
                    connections_made += 1
        else:
            if len(images) == 1:
                img = images[0]
                for text in texts:
                    self.add_image_text_connector(img, text)
                    connections_made += 1
            elif len(texts) == 1:
                text = texts[0]
                for img in images:
                    self.add_image_text_connector(img, text)
                    connections_made += 1
        print(f"自动创建了 {connections_made} 个图文连接")
    
    def connect_by_position(self):
        """按位置连接：上下相邻的图片和文字自动连接"""
        selected = self.selectedItems()
        items = [item for item in selected if isinstance(item, (VImageItem, VTextItem))]
        if len(items) < 2: return
        items.sort(key=lambda item: item.scenePos().y())
        connections_made = 0
        for i in range(len(items) - 1):
            current = items[i]
            next_item = items[i + 1]
            if ((isinstance(current, VImageItem) and isinstance(next_item, VTextItem)) or
                (isinstance(current, VTextItem) and isinstance(next_item, VImageItem))):
                distance = abs(next_item.scenePos().y() - current.scenePos().y())
                if distance < 200:
                    if isinstance(current, VImageItem):
                        self.add_image_text_connector(current, next_item)
                    else:
                        self.add_image_text_connector(next_item, current)
                    connections_made += 1
        print(f"按位置创建了 {connections_made} 个图文连接")
    
    def connect_all_images_to_text(self):
        """将所有选中的图片连接到一个文字"""
        selected = self.selectedItems()
        images = [item for item in selected if isinstance(item, VImageItem)]
        texts = [item for item in selected if isinstance(item, VTextItem)]
        if len(texts) != 1 or not images: return
        target_text = texts[0]
        for img in images:
            self.add_image_text_connector(img, target_text)
        print(f"已将选中图片连接到文字")
    
    def connect_all_texts_to_image(self):
        """将所有选中的文字连接到一个图片"""
        selected = self.selectedItems()
        images = [item for item in selected if isinstance(item, VImageItem)]
        texts = [item for item in selected if isinstance(item, VTextItem)]
        if len(images) != 1 or not texts: return
        target_image = images[0]
        for text in texts:
            self.add_image_text_connector(target_image, text)
        print(f"已将选中文字连接到图片")
    
    def remove_all_image_text_connections(self):
        """移除所有图文连接"""
        count = len(self.image_text_connectors)
        for conn in self.image_text_connectors[:]:
            self.removeItem(conn)
        self.image_text_connectors.clear()
        print(f"已移除 {count} 个图文连接")
    
    def copy_items(self, items):
        """复制多个元素到剪贴板"""
        if not items: return
        self.clipboard_items = []
        self.clipboard_image_text_connections = []
        item_to_index = {item: idx for idx, item in enumerate(items)}
        
        for idx, item in enumerate(items):
            if isinstance(item, VTextItem):
                item_data = {
                    'type': 'VTextItem',
                    'text': item.full_text,
                    'font_size': item.font_size,
                    'box_height': item.box_height,
                    'font_family': item.font_family,
                    'text_color': item.text_color.name(),
                    'scene_pos': (item.scenePos().x(), item.scenePos().y()),
                    'local_pos': (item.x(), item.y()),
                    'parent_index': item_to_index.get(item.parentItem(), -1) if isinstance(item.parentItem(), BaseElement) else -1
                }
                self.clipboard_items.append(item_data)
            elif isinstance(item, VImageItem):
                item_data = {
                    'type': 'VImageItem',
                    'path': item.file_path,
                    'width': item.target_width,
                    'scene_pos': (item.scenePos().x(), item.scenePos().y()),
                    'local_pos': (item.x(), item.y()),
                    'parent_index': item_to_index.get(item.parentItem(), -1) if isinstance(item.parentItem(), BaseElement) else -1
                }
                self.clipboard_items.append(item_data)
        
        for conn in self.image_text_connectors:
            img_idx = item_to_index.get(conn.image_item, -1)
            text_idx = item_to_index.get(conn.text_item, -1)
            if img_idx != -1 and text_idx != -1:
                self.clipboard_image_text_connections.append((img_idx, text_idx))
        print(f"已复制 {len(self.clipboard_items)} 个元素到剪贴板")
    
    def copy_item(self, item):
        self.copy_items([item])
    
    def paste_items(self, pos=None):
        """粘贴剪贴板中的所有元素"""
        if not self.clipboard_items: return []
        
        min_x = min(item['scene_pos'][0] for item in self.clipboard_items)
        min_y = min(item['scene_pos'][1] for item in self.clipboard_items)
        
        base_x, base_y = (pos.x(), pos.y()) if pos else (100, 100)
        new_items = []
        
        for idx, item_data in enumerate(self.clipboard_items):
            new_item = None
            if item_data['type'] == 'VTextItem':
                new_item = VTextItem(item_data['text'], item_data['font_size'], item_data['box_height'])
                new_item.font_family = item_data['font_family']
                new_item.text_color = QColor(item_data['text_color'])
                new_item.rebuild()
            elif item_data['type'] == 'VImageItem':
                new_item = VImageItem(item_data['path'], item_data['width'])
            
            if new_item:
                offset_x = item_data['scene_pos'][0] - min_x
                offset_y = item_data['scene_pos'][1] - min_y
                new_item.setPos(base_x + offset_x, base_y + offset_y)
                self.undo_stack.push(AddItemCommand(self, new_item))
                new_items.append(new_item)
        
        for idx, item_data in enumerate(self.clipboard_items):
            if item_data['parent_index'] != -1 and item_data['parent_index'] < len(new_items):
                child_item = new_items[idx]
                parent_item = new_items[item_data['parent_index']]
                current_scene_pos = child_item.scenePos()
                child_item.setParentItem(parent_item)
                child_item.setPos(parent_item.mapFromScene(current_scene_pos))
                self.add_connector(parent_item, child_item)
        
        for img_idx, text_idx in self.clipboard_image_text_connections:
            if img_idx < len(new_items) and text_idx < len(new_items):
                self.add_image_text_connector(new_items[img_idx], new_items[text_idx])
        return new_items
    
    def paste_item(self, pos=None):
        items = self.paste_items(pos)
        return items[0] if items else None
    
    def delete_item(self, item):
        self.undo_stack.push(DeleteItemCommand(self, item))
    
    def add_item_with_undo(self, item):
        self.undo_stack.push(AddItemCommand(self, item))
    
    def undo(self):
        self.undo_stack.undo()
    
    def redo(self):
        self.undo_stack.redo()
    
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                self.undo()
            elif event.key() == Qt.Key.Key_Y:
                self.redo()
            elif event.key() == Qt.Key.Key_C:
                selected = self.selectedItems()
                base_elements = [item for item in selected if isinstance(item, BaseElement)]
                if base_elements: self.copy_items(base_elements)
            elif event.key() == Qt.Key.Key_V:
                self.paste_items()
        elif event.key() == Qt.Key.Key_Delete:
            selected = self.selectedItems()
            for item in selected:
                if isinstance(item, BaseElement): self.delete_item(item)
        else:
            super().keyPressEvent(event)
    
    def align_top(self, items=None):
        if items is None: items = [item for item in self.selectedItems() if isinstance(item, BaseElement)]
        if len(items) < 2: return
        min_y = min(item.scenePos().y() for item in items)
        for item in items:
            current_pos = item.scenePos()
            new_scene_pos = QPointF(current_pos.x(), min_y)
            if item.parentItem():
                item.setPos(item.parentItem().mapFromScene(new_scene_pos))
            else:
                item.setPos(new_scene_pos)
        print(f"已对齐到顶部")
    
    def align_right(self, items=None):
        if items is None: items = [item for item in self.selectedItems() if isinstance(item, BaseElement)]
        if len(items) < 2: return
        max_right = max(item.scenePos().x() + item.boundingRect().width() for item in items)
        for item in items:
            current_pos = item.scenePos()
            new_x = max_right - item.boundingRect().width()
            new_scene_pos = QPointF(new_x, current_pos.y())
            if item.parentItem():
                item.setPos(item.parentItem().mapFromScene(new_scene_pos))
            else:
                item.setPos(new_scene_pos)
        print(f"已对齐到右边")
    
class LayoutView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setAcceptDrops(True)
        self._is_panning = False
        self._pan_start = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            scale = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale(scale, scale)
        else:
            super().wheelEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                img = VImageItem(path, target_width=DEFAULT_FONT_SIZE*4) 
                pos = self.mapToScene(event.position().toPoint())
                img.setPos(pos)
                self.scene().addItem(img)

# --- Main Window ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VertiLayout Pro - 竖排排版引擎")
        self.setGeometry(100, 100, 1400, 900)
        
        self.scene = LayoutScene()
        self.scene.setSceneRect(0, 0, 7054, 5021)
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.view = LayoutView(self.scene)
        self.asset_library = None 
        
        sidebar = QDockWidget("层级 & 属性", self)
        sidebar.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("排版元素")
        sidebar.setWidget(self.tree_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, sidebar)
        
        self.setCentralWidget(self.view)
        self.create_menu_bar()
        self.create_toolbars()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(2000)
        
        QTimer.singleShot(100, self.fit_view)
        print("Vertical Layout Engine Started...")
    
    def create_toolbars(self):
        toolbar1 = QToolBar("基本操作")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar1)
        
        btn_add_text = QAction("添加文本", self)
        btn_add_text.triggered.connect(self.add_text)
        toolbar1.addAction(btn_add_text)

        btn_add_img = QAction("插入图片", self)
        btn_add_img.triggered.connect(self.add_image)
        toolbar1.addAction(btn_add_img)
        toolbar1.addSeparator()
        
        toolbar1.addWidget(QLabel("字体:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(DEFAULT_FONT))
        self.font_combo.currentFontChanged.connect(self.change_selected_font)
        toolbar1.addWidget(self.font_combo)
        
        toolbar1.addWidget(QLabel("大小:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        self.font_size_spin.setValue(DEFAULT_FONT_SIZE)
        self.font_size_spin.setSuffix("px")
        self.font_size_spin.valueChanged.connect(self.change_selected_font_size)
        toolbar1.addWidget(self.font_size_spin)
        
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 25)
        self.color_button.setStyleSheet("background-color: black; border: 1px solid gray;")
        self.color_button.clicked.connect(self.change_selected_color)
        toolbar1.addWidget(self.color_button)
        toolbar1.addSeparator()
        
        toolbar1.addWidget(QLabel("每列字数:"))
        self.chars_per_column_spin = QSpinBox()
        self.chars_per_column_spin.setRange(5, 50)
        self.chars_per_column_spin.setValue(15)
        self.chars_per_column_spin.setSuffix("字")
        self.chars_per_column_spin.valueChanged.connect(self.change_chars_per_column)
        toolbar1.addWidget(self.chars_per_column_spin)
        
        self.manual_line_break_btn = QPushButton("手动换行")
        self.manual_line_break_btn.setCheckable(True)
        self.manual_line_break_btn.setChecked(True)
        self.manual_line_break_btn.toggled.connect(self.toggle_manual_line_break)
        toolbar1.addWidget(self.manual_line_break_btn)
        toolbar1.addSeparator()
        
        btn_undo = QAction("撤销", self)
        btn_undo.setShortcut("Ctrl+Z")
        btn_undo.triggered.connect(self.undo)
        toolbar1.addAction(btn_undo)
        
        btn_redo = QAction("重做", self)
        btn_redo.setShortcut("Ctrl+Y")
        btn_redo.triggered.connect(self.redo)
        toolbar1.addAction(btn_redo)
        
        toolbar2 = QToolBar("图文连接")
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar2)
        
        btn_auto_connect = QAction("智能连接", self)
        btn_auto_connect.triggered.connect(self.auto_connect_selected)
        toolbar2.addAction(btn_auto_connect)
        
        btn_clear_connections = QAction("清除连接", self)
        btn_clear_connections.triggered.connect(self.clear_all_connections)
        toolbar2.addAction(btn_clear_connections)
        
        toolbar3 = QToolBar("素材和工程")
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar3)
        
        btn_asset_library = QAction("素材库", self)
        btn_asset_library.triggered.connect(self.open_asset_library)
        toolbar3.addAction(btn_asset_library)
        
        btn_save_group = QAction("保存组合", self)
        btn_save_group.triggered.connect(self.save_selected_as_group)
        toolbar3.addAction(btn_save_group)
        
        btn_save = QAction("保存工程", self)
        btn_save.triggered.connect(self.save_proj)
        toolbar3.addAction(btn_save)
        
        btn_export_img = QAction("导出图片", self)
        btn_export_img.triggered.connect(self.export_image)
        toolbar3.addAction(btn_export_img)

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        new_action = QAction('新建', self)
        new_action.triggered.connect(lambda: self.scene.clear())
        file_menu.addAction(new_action)
        
        save_action = QAction('保存工程', self)
        save_action.triggered.connect(self.save_proj)
        file_menu.addAction(save_action)
        
        # 添加素材菜单
        asset_menu = menubar.addMenu('素材')
        save_group_action = QAction('保存组合素材', self)
        save_group_action.setShortcut('Ctrl+G')
        save_group_action.triggered.connect(self.save_selected_as_group)
        asset_menu.addAction(save_group_action)
        
        open_library_action = QAction('打开素材库', self)
        open_library_action.triggered.connect(self.open_asset_library)
        asset_menu.addAction(open_library_action)

    def fit_view(self):
        rect = self.scene.sceneRect()
        self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.view.scale(0.95, 0.95)

    def add_text(self):
        t = VTextItem("此处输入竖排文字\n支持自动换行\n从右向左排列", 24, 400)
        t.setPos(500, 100)
        self.scene.add_item_with_undo(t)
        
    def add_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            img = VImageItem(path, target_width=DEFAULT_FONT_SIZE*4)
            img.setPos(500, 300)
            self.scene.add_item_with_undo(img)
    
    def undo(self):
        self.scene.undo()
    
    def redo(self):
        self.scene.redo()
    
    def align_top(self):
        self.scene.align_top()
    
    def align_right(self):
        self.scene.align_right()
    
    def auto_connect_selected(self):
        self.scene.auto_connect_selected_items()
    
    def clear_all_connections(self):
        self.scene.remove_all_image_text_connections()
    
    def toggle_connection_points(self):
        self.scene.toggle_connection_points()
    
    def open_asset_library(self):
        if not self.asset_library:
            self.asset_library = AssetLibraryWidget(self.scene.asset_manager, self)
        self.asset_library.show()
    
    def save_selected_as_group(self):
        self.scene.save_group_as_asset()
    
    def change_selected_font(self, font):
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, VTextItem)]
        for item in selected_items:
            item.font_family = font.family()
            item.rebuild()
    
    def change_selected_font_size(self, size):
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, VTextItem)]
        for item in selected_items:
            item.font_size = size
            item.rebuild()
    
    def change_selected_color(self):
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, VTextItem)]
        if not selected_items: return
        color = QColorDialog.getColor(selected_items[0].text_color, self, "选择文字颜色")
        if color.isValid():
            for item in selected_items:
                item.text_color = color
                item.rebuild()
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
    
    def toggle_manual_line_break(self, enabled):
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, VTextItem)]
        for item in selected_items:
            item.manual_line_break = enabled
            item.rebuild()
    
    def change_chars_per_column(self, chars_count):
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, VTextItem)]
        for item in selected_items:
            item.chars_per_column = chars_count
            item.rebuild()
    
    def update_font_controls(self):
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, VTextItem)]
        if selected_items:
            item = selected_items[0]
            self.font_combo.blockSignals(True)
            self.font_size_spin.blockSignals(True)
            self.font_combo.setCurrentFont(QFont(item.font_family))
            self.font_size_spin.setValue(item.font_size)
            self.font_combo.blockSignals(False)
            self.font_size_spin.blockSignals(False)
    
    def on_selection_changed(self):
        if hasattr(self, 'font_combo'): self.update_font_controls()
    
    def set_canvas_size(self):
        current_rect = self.scene.sceneRect()
        w, ok1 = QInputDialog.getInt(self, "画布宽度", "宽度:", int(current_rect.width()), 100, 10000)
        h, ok2 = QInputDialog.getInt(self, "画布高度", "高度:", int(current_rect.height()), 100, 10000)
        if ok1 and ok2: self.scene.setSceneRect(0, 0, w, h)

    def refresh_ui(self):
        try:
            self.tree_widget.clear()
            def add_node(item, parent_node):
                node = QTreeWidgetItem(parent_node)
                txt = "Image" if isinstance(item, VImageItem) else f"Txt: {item.full_text[:8]}..."
                node.setText(0, txt)
                for child in item.childItems():
                    if isinstance(child, BaseElement): add_node(child, node)
            for item in self.scene.items():
                if isinstance(item, BaseElement) and item.parentItem() is None:
                    add_node(item, self.tree_widget)
            self.tree_widget.expandAll()
            self.scene.update_all_connectors()
        except: pass

    def export_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Image", "", "PNG (*.png)")
        if path:
            # 保存当前设置
            original_show_grid = self.scene.show_grid
            original_show_connectors = self.scene.show_connectors
            original_show_connection_points = self.scene.show_connection_points
            
            # 导出时的设置：隐藏网格、父子连线和连接点，但保持图文连接线可见
            self.scene.show_grid = False
            self.scene.set_connectors_visible(False)  # 隐藏父子关系连线
            self.scene.set_connection_points_visible(False)  # 隐藏连接点
            # 图文连接器保持可见，不隐藏
            
            try:
                rect = self.scene.sceneRect()
                img = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32)
                img.fill(Qt.GlobalColor.white)
                p = QPainter(img)
                self.scene.render(p)
                p.end()
                img.save(path)
                print(f"图片已导出到: {path}")
            finally:
                # 恢复原始设置
                self.scene.show_grid = original_show_grid
                self.scene.set_connectors_visible(original_show_connectors)
                self.scene.set_connection_points_visible(original_show_connection_points)

    def save_proj(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "VLayout (*.vlayout)")
        if path: ProjectData.save(self.scene, path)

    def load_proj(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "VLayout (*.vlayout)")
        if path: ProjectData.load(self.scene, path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())