"""
串口监视器GUI页面 - 针对800x600窗口布局优化
保留所有原有功能，只优化布局结构
"""

from CORE.serial_api import SerialCore, SerialEventHandler, SerialConfig
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from datetime import datetime
import sys
import os

# 添加 CORE 路径到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
core_dir = os.path.join(project_root, 'CORE')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

class SerialMonitorEventHandler(SerialEventHandler):
    """串口监视器事件处理器 - 连接后端和前端"""
    
    def __init__(self, gui_page):
        self.gui_page = gui_page
        
    def on_data_received(self, processed_data):
        """数据接收事件处理"""
        # 使用 GUI 线程安全的方式更新界面
        self.gui_page.root.after(0, self._update_received_data, processed_data)
        
    def on_data_sent(self, data):
        """数据发送事件处理"""
        self.gui_page.root.after(0, self._update_sent_data, data)
        
    def on_connection_changed(self, connected, port=None):
        """连接状态变化事件处理"""
        self.gui_page.root.after(0, self._update_connection_status, connected, port)
        
    def on_error(self, error):
        """错误事件处理"""
        self.gui_page.root.after(0, self._update_error, error)
        
    def _update_received_data(self, processed_data):
        """更新接收数据显示"""
        self.gui_page.display_received_data(processed_data)
        
    def _update_sent_data(self, data):
        """更新发送数据显示"""
        self.gui_page.display_sent_data(data)
        
    def _update_connection_status(self, connected, port):
        """更新连接状态"""
        self.gui_page.update_connection_status(connected, port)
        
    def _update_error(self, error):
        """更新错误信息"""
        self.gui_page.show_error(error)

class PageESerialMonitor(ttk.Frame):
    """串口监视器页面 - 800x600布局优化版本"""
    
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.root = parent.winfo_toplevel()  # 获取顶级窗口
        
        # 初始化状态变量（在构建UI之前）
        self.is_connected = False
        self.auto_scroll = True
        self.hex_display = False
        
        # 初始化控制变量
        self.scroll_var = tk.BooleanVar(value=self.auto_scroll)
        self.hex_var = tk.BooleanVar(value=self.hex_display)
        
        # 是否暂停终端显示
        self.pause_display = False
        
        # 初始化串口监视器后端
        if SerialCore is None:
            self.show_import_error()
            return
            
        self.serial_core = SerialCore()
        self.event_handler = SerialMonitorEventHandler(self)
        self.serial_core.add_event_handler(self.event_handler)
        
        # 确保日志目录存在
        self.ensure_log_directory()
        
        self.build_ui()
        self.update_statistics_timer()
        
    def ensure_log_directory(self):
        """确保日志目录存在"""
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except Exception as e:
            print(f"创建日志目录失败: {e}")
        
    def show_import_error(self):
        """显示导入错误"""
        error_label = ttk.Label(self, text="错误: 无法加载串口监视器模块\n请检查 CLI/cli_moni.py 文件是否存在", 
                               foreground="red", font=("Microsoft YaHei", 12))
        error_label.pack(expand=True)
        
    def build_ui(self):
        """构建用户界面 - 优化为上下布局"""
        # 主要布局 - 上下分割更适合800x600
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # 上部分：控制面板（紧凑布局）
        self.build_control_panel(main_frame)
        
        # 下部分：显示区域（主要区域）
        self.build_display_area(main_frame)
        
    def build_control_panel(self, parent):
        """构建顶部控制面板 - 紧凑多行布局"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # === 第一行：串口配置和连接控制 ===
        row1_frame = ttk.Frame(control_frame)
        row1_frame.pack(fill=tk.X, pady=2)
        
        # 串口配置组
        config_group = ttk.LabelFrame(row1_frame, text="串口配置", padding=3)
        config_group.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        
        # 配置项紧凑排列
        config_inner = ttk.Frame(config_group)
        config_inner.pack(fill=tk.X)
        
        # 第一小行：端口和波特率
        row1_1 = ttk.Frame(config_inner)
        row1_1.pack(fill=tk.X, pady=1)
        
        ttk.Label(row1_1, text="端口:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=self.serial_core.config.port)
        self.port_combo = ttk.Combobox(row1_1, textvariable=self.port_var, width=10, font=("Microsoft YaHei", 8))
        self.port_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row1_1, text="波特率:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT, padx=(10, 0))
        self.baud_var = tk.StringVar(value=str(self.serial_core.config.baudrate))
        baud_combo = ttk.Combobox(row1_1, textvariable=self.baud_var, width=8, font=("Microsoft YaHei", 8))
        baud_combo['values'] = ('9600', '19200', '38400', '57600', '115200', '230400')
        baud_combo.pack(side=tk.LEFT, padx=2)
        
        # 第二小行：数据位、停止位、校验位
        row1_2 = ttk.Frame(config_inner)
        row1_2.pack(fill=tk.X, pady=1)
        
        ttk.Label(row1_2, text="数据位:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT)
        self.databits_var = tk.StringVar(value=str(self.serial_core.config.databits))
        databits_combo = ttk.Combobox(row1_2, textvariable=self.databits_var, width=6, font=("Microsoft YaHei", 8))
        databits_combo['values'] = ('5', '6', '7', '8')
        databits_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row1_2, text="停止位:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT, padx=(5, 0))
        self.stopbits_var = tk.StringVar(value=str(self.serial_core.config.stopbits))
        stopbits_combo = ttk.Combobox(row1_2, textvariable=self.stopbits_var, width=6, font=("Microsoft YaHei", 8))
        stopbits_combo['values'] = ('1', '1.5', '2')
        stopbits_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row1_2, text="校验位:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT, padx=(5, 0))
        self.parity_var = tk.StringVar(value=self.serial_core.config.parity)
        parity_combo = ttk.Combobox(row1_2, textvariable=self.parity_var, width=6, font=("Microsoft YaHei", 8))
        parity_combo['values'] = ('N', 'E', 'O', 'M', 'S')
        parity_combo.pack(side=tk.LEFT, padx=2)
        
        # 连接控制组
        connect_group = ttk.LabelFrame(row1_frame, text="连接控制", padding=3)
        connect_group.pack(side=tk.RIGHT, padx=(3, 0))
        
        btn_grid = ttk.Frame(connect_group)
        btn_grid.pack()
        
        self.connect_btn = ttk.Button(btn_grid, text="连接", command=self.connect_serial, width=6)
        self.connect_btn.grid(row=0, column=0, padx=1, pady=1)
        
        self.disconnect_btn = ttk.Button(btn_grid, text="断开", command=self.disconnect_serial, state=tk.DISABLED, width=6)
        self.disconnect_btn.grid(row=0, column=1, padx=1, pady=1)
        
        refresh_btn = ttk.Button(btn_grid, text="刷新", command=self.refresh_ports, width=6)
        refresh_btn.grid(row=1, column=0, padx=1, pady=1)
        
        test_btn = ttk.Button(btn_grid, text="测试", command=self.test_connection, width=6)
        test_btn.grid(row=1, column=1, padx=1, pady=1)
        
        # === 第二行：发送控制 ===
        row2_frame = ttk.Frame(control_frame)
        row2_frame.pack(fill=tk.X, pady=2)
        
        send_group = ttk.LabelFrame(row2_frame, text="📤 发送数据", padding=3)
        send_group.pack(fill=tk.X)
        
        # 文本发送行
        text_frame = ttk.Frame(send_group)
        text_frame.pack(fill=tk.X, pady=1)
        
        ttk.Label(text_frame, text="文本:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT)
        self.send_text_var = tk.StringVar()
        send_entry = ttk.Entry(text_frame, textvariable=self.send_text_var, font=("Consolas", 9))
        send_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,5))
        send_entry.bind('<Return>', self.send_text_data)
        
        # 发送按钮行
        btn_frame = ttk.Frame(send_group)
        btn_frame.pack(fill=tk.X, pady=1)
        
        ttk.Button(btn_frame, text="发送", command=self.send_text_data, width=6).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_frame, text="+CR", command=lambda: self.send_text_data(add_cr=True), width=5).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_frame, text="+LF", command=lambda: self.send_text_data(add_lf=True), width=5).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_frame, text="+CRLF", command=lambda: self.send_text_data(add_crlf=True), width=6).pack(side=tk.LEFT, padx=1)
        
        # 十六进制发送行
        hex_frame = ttk.Frame(send_group)
        hex_frame.pack(fill=tk.X, pady=1)
        
        ttk.Label(hex_frame, text="HEX:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT)
        self.send_hex_var = tk.StringVar()
        hex_entry = ttk.Entry(hex_frame, textvariable=self.send_hex_var, font=("Consolas", 9))
        hex_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,5))
        
        ttk.Button(hex_frame, text="发送HEX", command=self.send_hex_data, width=8).pack(side=tk.RIGHT)
        
        # === 第三行：工具和状态 ===
        row3_frame = ttk.Frame(control_frame)
        row3_frame.pack(fill=tk.X, pady=2)
        
        # 左侧：工具按钮（包含自动滚动）
        tool_group = ttk.LabelFrame(row3_frame, text="工具", padding=3)
        tool_group.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        
        tool_frame = ttk.Frame(tool_group)
        tool_frame.pack(fill=tk.X)
        
        # 第一行工具按钮
        tool_row1 = ttk.Frame(tool_frame)
        tool_row1.pack(fill=tk.X, pady=1)
        
        ttk.Button(tool_row1, text="清空显示", command=self.clear_display, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(tool_row1, text="复制全部", command=self.copy_all_data, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(tool_row1, text="保存数据", command=self.save_display_data, width=8).pack(side=tk.LEFT, padx=1)
        
        # 暂停/恢复 终端显示
        self.pause_btn = ttk.Button(tool_row1, text="暂停显示", command=self.toggle_pause, width=8)
        self.pause_btn.pack(side=tk.LEFT, padx=1)
        
        # 第二行：自动滚动选项
        tool_row2 = ttk.Frame(tool_frame)
        tool_row2.pack(fill=tk.X, pady=1)
        
        self.scroll_var = tk.BooleanVar(value=self.auto_scroll)
        ttk.Checkbutton(tool_row2, text="自动滚动", variable=self.scroll_var).pack(side=tk.LEFT)
                
        # 右侧：日志和状态
        status_group = ttk.LabelFrame(row3_frame, text="状态", padding=3)
        status_group.pack(side=tk.RIGHT, padx=(3, 0))
        
        status_frame = ttk.Frame(status_group)
        status_frame.pack()
        
        # 日志控制
        self.log_var = tk.BooleanVar()
        log_cb = ttk.Checkbutton(status_frame, text="自动日志记录", variable=self.log_var, command=self.toggle_auto_logging)
        log_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        self.log_status_label = ttk.Label(status_frame, text="日志: 未启用", foreground="gray", font=("Microsoft YaHei", 8))
        self.log_status_label.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        # 日志控制按钮（手动操作）
        ttk.Button(status_frame, text="手动新建", command=self.new_log_file, width=8).grid(row=2, column=0, padx=1, pady=1)
        ttk.Button(status_frame, text="手动追加", command=self.append_log_file, width=8).grid(row=2, column=1, padx=1, pady=1)
        
        # === 第四行：发送历史（紧凑版本）===
        row4_frame = ttk.Frame(control_frame)
        row4_frame.pack(fill=tk.X, pady=2)
        
        history_group = ttk.LabelFrame(row4_frame, text="发送历史", padding=3)
        history_group.pack(fill=tk.X)
        
        history_inner = ttk.Frame(history_group)
        history_inner.pack(fill=tk.X)
        
        self.history_listbox = tk.Listbox(history_inner, height=2, font=("Consolas", 8))
        self.history_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.history_listbox.bind('<Double-Button-1>', self.load_from_history)
        
        ttk.Button(history_inner, text="清空历史", command=self.clear_history, width=8).pack(side=tk.RIGHT, padx=(3,0))
        
        # === 第五行：统计信息 ===
        row5_frame = ttk.Frame(control_frame)
        row5_frame.pack(fill=tk.X, pady=2)
        
        stats_group = ttk.LabelFrame(row5_frame, text="📊 统计", padding=3)
        stats_group.pack(fill=tk.X)
        
        stats_frame = ttk.Frame(stats_group)
        stats_frame.pack(fill=tk.X)
        
        # 统计标签
        self.stats_labels = {}
        
        ttk.Label(stats_frame, text="状态:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT)
        self.stats_labels["状态"] = ttk.Label(stats_frame, text="未连接", font=("Microsoft YaHei", 8), foreground="red")
        self.stats_labels["状态"].pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(stats_frame, text="接收:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT)
        self.stats_labels["接收"] = ttk.Label(stats_frame, text="0", font=("Microsoft YaHei", 8), foreground="blue")
        self.stats_labels["接收"].pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(stats_frame, text="包数:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT)
        self.stats_labels["包数"] = ttk.Label(stats_frame, text="0", font=("Microsoft YaHei", 8), foreground="blue")
        self.stats_labels["包数"].pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(stats_frame, text="日志:", font=("Microsoft YaHei", 8)).pack(side=tk.LEFT)
        self.stats_labels["日志"] = ttk.Label(stats_frame, text="0", font=("Microsoft YaHei", 8), foreground="blue")
        self.stats_labels["日志"].pack(side=tk.LEFT, padx=(2, 10))
        
        # 延迟调用刷新端口
        self.root.after(100, self.refresh_ports)
        
    def build_display_area(self, parent):
        """构建显示区域"""
        display_frame = ttk.Frame(parent)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标签页显示区
        self.notebook = ttk.Notebook(display_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # ASCII 显示标签页
        ascii_frame = ttk.Frame(self.notebook)
        self.notebook.add(ascii_frame, text="ASCII 终端")
        
        self.ascii_text = scrolledtext.ScrolledText(ascii_frame, wrap=tk.WORD, 
                                                   font=("Consolas", 9), state=tk.NORMAL)
        self.ascii_text.pack(fill=tk.BOTH, expand=True)
        
        # 十六进制显示标签页
        hex_frame = ttk.Frame(self.notebook)
        self.notebook.add(hex_frame, text="十六进制")
        
        # 十六进制显示使用两列布局
        hex_paned = ttk.PanedWindow(hex_frame, orient=tk.HORIZONTAL)
        hex_paned.pack(fill=tk.BOTH, expand=True)
        
        # 十六进制数据
        hex_data_frame = ttk.Frame(hex_paned)
        hex_paned.add(hex_data_frame, weight=3)
        
        ttk.Label(hex_data_frame, text="十六进制数据", font=("Microsoft YaHei", 8)).pack()
        self.hex_text = scrolledtext.ScrolledText(hex_data_frame, wrap=tk.NONE, 
                                                 font=("Consolas", 8))
        self.hex_text.pack(fill=tk.BOTH, expand=True)
        
        # ASCII 对应
        ascii_data_frame = ttk.Frame(hex_paned)
        hex_paned.add(ascii_data_frame, weight=1)
        
        ttk.Label(ascii_data_frame, text="ASCII", font=("Microsoft YaHei", 8)).pack()
        self.hex_ascii_text = scrolledtext.ScrolledText(ascii_data_frame, wrap=tk.NONE, 
                                                       font=("Consolas", 8))
        self.hex_ascii_text.pack(fill=tk.BOTH, expand=True)
        
        # 日志显示标签页
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="详细日志")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                 font=("Consolas", 8))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置文本框颜色和标签
        self.configure_text_tags()
        
    def configure_text_tags(self):
        """配置文本显示标签"""
        # ASCII 文本标签
        self.ascii_text.tag_config("received", foreground="black")
        self.ascii_text.tag_config("sent", foreground="blue")
        self.ascii_text.tag_config("timestamp", foreground="gray")
        
        # 十六进制文本标签
        self.hex_text.tag_config("received", foreground="green")
        self.hex_text.tag_config("sent", foreground="blue")
        self.hex_text.tag_config("address", foreground="purple")
        
        # 日志文本标签
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("debug", foreground="gray")
        
    def refresh_ports(self):
        """刷新串口列表"""
        try:
            if not hasattr(self, 'serial_core') or not self.serial_core:
                print("串口核心模块未初始化")
                return
                
            ports = self.serial_core.get_available_ports()
            port_list = [port['device'] for port in ports]
            
            if hasattr(self, 'port_combo') and self.port_combo:
                self.port_combo['values'] = port_list
                
                if port_list and not self.port_var.get():
                    self.port_var.set(port_list[0])
                    
            self.log_message(f"刷新串口列表: 发现 {len(port_list)} 个端口")
            
        except Exception as e:
            error_msg = f"刷新串口列表失败: {e}"
            self.log_message(error_msg, "error")
            print(error_msg)
    
    def test_connection(self):
        """测试串口连接"""
        self.update_serial_config()
        
        result = self.serial_core.test_connection()
        
        if result['success']:
            details = result['details']
            message = f"串口连接测试成功!\n\n"
            message += f"端口: {details['port']}\n"
            message += f"波特率: {details['baudrate']}\n"
            message += f"数据位: {details['bytesize']}\n"
            message += f"停止位: {details['stopbits']}\n"
            message += f"校验位: {details['parity']}\n"
            message += f"输入缓冲区: {details['in_waiting']} 字节\n"
                
            messagebox.showinfo("连接测试", message)
            self.log_message("串口连接测试成功")
        else:
            messagebox.showerror("连接测试失败", f"错误: {result['error']}")
            self.log_message(f"串口连接测试失败: {result['error']}", "error")
    
    def connect_serial(self):
        """连接串口"""
        if self.is_connected:
            self.log_message("串口已经连接", "warning")
            return
            
        self.update_serial_config()
        
        if self.serial_core.connect():
            self.log_message(f"成功连接到 {self.serial_core.config.port}")
        else:
            self.log_message("串口连接失败", "error")
    
    def disconnect_serial(self):
        """断开串口连接"""
        if not self.is_connected:
            return
            
        self.serial_core.disconnect()
        self.log_message("串口连接已断开")
    
    def update_serial_config(self):
        """更新串口配置"""
        try:
            self.serial_core.config.port = self.port_var.get()
            self.serial_core.config.baudrate = int(self.baud_var.get())
            self.serial_core.config.databits = int(self.databits_var.get())
            self.serial_core.config.stopbits = float(self.stopbits_var.get())
            self.serial_core.config.parity = self.parity_var.get()
        except ValueError as e:
            self.log_message(f"配置参数错误: {e}", "error")
    
    def send_text_data(self, event=None, add_cr=False, add_lf=False, add_crlf=False):
        """发送文本数据"""
        text = self.send_text_var.get().strip()
        if not text:
            return
            
        # 添加结束符
        if add_cr:
            text += '\r'
        elif add_lf:
            text += '\n'
        elif add_crlf:
            text += '\r\n'
            
        if self.serial_core.send_text(text):
            self.send_text_var.set("")  # 清空输入框
            self.update_send_history(text)
        else:
            self.log_message("发送文本失败", "error")
    
    def send_hex_data(self):
        """发送十六进制数据"""
        hex_str = self.send_hex_var.get().strip()
        if not hex_str:
            return
            
        if self.serial_core.send_hex(hex_str):
            self.send_hex_var.set("")  # 清空输入框
            self.update_send_history(f"HEX: {hex_str}")
        else:
            self.log_message("发送十六进制数据失败", "error")
    
    def update_send_history(self, item):
        """更新发送历史"""
        self.history_listbox.insert(0, item)
        
        # 限制历史记录数量
        if self.history_listbox.size() > 20:
            self.history_listbox.delete(20, tk.END)
    
    def load_from_history(self, event):
        """从历史记录加载"""
        selection = self.history_listbox.curselection()
        if selection:
            item = self.history_listbox.get(selection[0])
            if item.startswith("HEX: "):
                self.send_hex_var.set(item[5:])
            else:
                self.send_text_var.set(item)
    
    def clear_history(self):
        """清空发送历史"""
        self.history_listbox.delete(0, tk.END)
        self.serial_core.clear_send_history()
    
    def toggle_auto_logging(self):
        """切换自动日志记录"""
        if self.log_var.get():
            # 启用自动日志记录 - 创建基于时间戳的日志文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"serial_log_{timestamp}.log"
            
            # 确保日志目录存在
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            log_path = os.path.join(log_dir, log_filename)
            
            if self.serial_core.log_manager.start_logging(log_path, append_mode=False):
                self.log_message(f"自动日志已启用: {log_filename}")
                self.update_log_status()
            else:
                self.log_var.set(False)  # 如果失败，取消勾选
                self.log_message("自动日志启用失败", "error")
        else:
            # 停用日志记录
            if self.serial_core.log_manager.is_logging:
                self.serial_core.log_manager.stop_logging()
                self.log_message("自动日志已停用")
                self.update_log_status()
    
    def new_log_file(self):
        """手动新建日志文件"""
        file_path = filedialog.asksaveasfilename(
            title="新建日志文件",
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            # 如果自动日志正在运行，先停止它
            if self.log_var.get():
                self.log_var.set(False)
                if self.serial_core.log_manager.is_logging:
                    self.serial_core.log_manager.stop_logging()
                    
            if self.serial_core.log_manager.start_logging(file_path, append_mode=False):
                self.update_log_status()
                self.log_message(f"手动日志文件已创建: {os.path.basename(file_path)}")
    
    def append_log_file(self):
        """手动追加日志文件"""
        file_path = filedialog.askopenfilename(
            title="选择日志文件追加",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            # 如果自动日志正在运行，先停止它
            if self.log_var.get():
                self.log_var.set(False)
                if self.serial_core.log_manager.is_logging:
                    self.serial_core.log_manager.stop_logging()
                    
            if self.serial_core.log_manager.start_logging(file_path, append_mode=True):
                self.update_log_status()
                self.log_message(f"手动追加日志文件: {os.path.basename(file_path)}")
    
    def update_log_status(self):
        """更新日志状态显示"""
        if self.serial_core.log_manager.is_logging:
            filename = os.path.basename(self.serial_core.log_manager.log_path)
            self.log_status_label.config(text=f"日志: {filename}", foreground="green")
        else:
            self.log_status_label.config(text="日志: 未启用", foreground="gray")
    
    def toggle_pause(self):
        """切换暂停/恢复终端显示"""
        self.pause_display = not self.pause_display
        self.pause_btn.config(text="恢复显示" if self.pause_display else "暂停显示")
    
    def clear_display(self):
        """清空所有显示"""
        self.ascii_text.delete('1.0', tk.END)
        self.hex_text.delete('1.0', tk.END)
        self.hex_ascii_text.delete('1.0', tk.END)
        self.log_text.delete('1.0', tk.END)
        
        # 重置数据处理器统计
        if hasattr(self.serial_core, 'data_processor'):
            self.serial_core.data_processor.reset_session_stats()
        self.log_message("显示已清空（日志文件记录继续）")
    
    def copy_all_data(self):
        """复制所有数据到剪贴板"""
        current_tab = self.notebook.index(self.notebook.select())
        
        if current_tab == 0:  # ASCII 标签页
            text = self.ascii_text.get('1.0', tk.END)
        elif current_tab == 1:  # 十六进制标签页
            text = self.hex_text.get('1.0', tk.END)
        elif current_tab == 2:  # 日志标签页
            text = self.log_text.get('1.0', tk.END)
        else:
            return
            
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log_message("数据已复制到剪贴板")
    
    def save_display_data(self):
        """保存显示数据到文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存数据",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                current_tab = self.notebook.index(self.notebook.select())
                
                if current_tab == 0:  # ASCII 标签页
                    text = self.ascii_text.get('1.0', tk.END)
                elif current_tab == 1:  # 十六进制标签页
                    text = self.hex_text.get('1.0', tk.END)
                elif current_tab == 2:  # 日志标签页
                    text = self.log_text.get('1.0', tk.END)
                else:
                    return
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                    
                self.log_message(f"数据已保存: {file_path}")
                
            except Exception as e:
                self.log_message(f"保存数据失败: {e}", "error")
    
    def display_received_data(self, processed_data): 
        """显示接收到的数据"""
        if self.pause_display:
            return
        
        timestamp = processed_data['timestamp'].strftime('%H:%M:%S.%f')[:-3]
        raw_data = processed_data['raw_data']
        ascii_data = processed_data['ascii']
        hex_data = processed_data['hex']
        printable_text = processed_data['printable_text']
        
        # ASCII 终端显示 - 简化为普通ASCII模式
        display_text = ascii_data
        self.ascii_text.insert(tk.END, display_text, "received")
        
        if self.scroll_var.get():
            self.ascii_text.see(tk.END)
            
        # 十六进制标签页显示
        hex_line = f"[{timestamp}] RX: {hex_data}\n"
        self.hex_text.insert(tk.END, hex_line, "received")
        
        ascii_line = f"[{timestamp}] RX: {printable_text}\n"
        self.hex_ascii_text.insert(tk.END, ascii_line, "received")
        
        if self.scroll_var.get():
            self.hex_text.see(tk.END)
            self.hex_ascii_text.see(tk.END)
            
        # 限制显示行数
        self.limit_text_lines(self.ascii_text)
        self.limit_text_lines(self.hex_text)
        self.limit_text_lines(self.hex_ascii_text)
        
        # 详细日志
        log_msg = f"[{timestamp}] 接收 {len(raw_data)} 字节: {hex_data}"
        self.log_message(log_msg, "info")

    def display_sent_data(self, data):
        """显示发送的数据"""
        if self.pause_display:
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        hex_data = data.hex().upper()
        
        try:
            ascii_data = data.decode('utf-8', errors='replace')
        except:
            ascii_data = data.decode('latin-1', errors='replace')
        
        # ASCII 终端显示 - 简化为普通ASCII模式
        if ascii_data.strip():  # 只有非空数据才显示
            self.ascii_text.insert(tk.END, ascii_data, "sent")
        
        if self.scroll_var.get():
            self.ascii_text.see(tk.END)
            
        # 十六进制标签页显示
        hex_line = f"[{timestamp}] TX: {hex_data}\n"
        self.hex_text.insert(tk.END, hex_line, "sent")
        
        printable_text = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
        ascii_line = f"[{timestamp}] TX: {printable_text}\n"
        self.hex_ascii_text.insert(tk.END, ascii_line, "sent")
        
        if self.scroll_var.get():
            self.hex_text.see(tk.END)
            self.hex_ascii_text.see(tk.END)
            
        # 详细日志
        log_msg = f"[{timestamp}] 发送 {len(data)} 字节: {hex_data}"
        self.log_message(log_msg, "info")
    
    def update_connection_status(self, connected, port=None):
        """更新连接状态"""
        self.is_connected = connected
        
        if connected:
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            
            status_text = f"已连接 ({port})"
            self.stats_labels["状态"].config(text=status_text, foreground="green")
            self.log_message(f"串口连接成功: {port}")
        else:
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.stats_labels["状态"].config(text="未连接", foreground="red")
            self.log_message("串口连接已断开")
    
    def show_error(self, error):
        """显示错误信息"""
        self.log_message(f"错误: {error}", "error")
    
    def log_message(self, message, level="info"):
        """记录日志消息"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_line = f"[{timestamp}] {message}\n"
        
        # 安全检查：确保log_text控件存在
        if hasattr(self, 'log_text') and self.log_text:
            try:
                self.log_text.insert(tk.END, log_line, level)
                if self.scroll_var.get():
                    self.log_text.see(tk.END)
                    
                self.limit_text_lines(self.log_text)
            except Exception as e:
                # 如果日志记录失败，打印到控制台
                print(f"日志记录失败: {e} - 消息: {message}")
        else:
            # 如果日志控件还没创建，先打印到控制台
            print(f"[{timestamp}] {message}")
    
    def limit_text_lines(self, text_widget, max_lines=1000):
        """限制文本组件的行数"""
        lines = int(text_widget.index(tk.END).split('.')[0])
        if lines > max_lines:
            text_widget.delete('1.0', f'{lines - max_lines}.0')
    
    def update_statistics_timer(self):
        """定时更新统计信息"""
        try:
            stats = self.serial_core.get_statistics()
            
            self.stats_labels["接收"].config(text=str(stats['session_bytes']))
            self.stats_labels["包数"].config(text=str(stats['packet_count']))
            self.stats_labels["日志"].config(text=str(stats['log_bytes']))
            
            # 更新日志状态
            self.update_log_status()
            
        except Exception as e:
            pass  # 忽略更新统计信息时的错误
            
        # 每500毫秒更新一次
        self.root.after(500, self.update_statistics_timer)
    
    def reset(self):
        """页面重置方法 - 框架要求"""
        if hasattr(self, 'log_text'):
            self.log_text.delete('1.0', tk.END)
        self.log_message("串口监视器页面已重置")
    
    def __del__(self):
        """析构函数 - 清理资源"""
        try:
            if hasattr(self, 'serial_core') and self.serial_core:
                self.serial_core.disconnect()
        except:
            pass