# GUI/PAGES/page_j_power_temp_monitor.py

"""
电流、功耗、温度监控GUI页面
支持实时数据显示和CSV导出功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import os
import sys
import csv
from datetime import datetime
from collections import deque

# 添加 CORE 路径到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
core_dir = os.path.join(project_root, 'CORE')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

from CORE.power_temp_api import PowerTempMonitor, PowerTempEventHandler, create_power_temp_monitor

import logging

class PowerTempGUIEventHandler(PowerTempEventHandler):
    """GUI电流功耗温度事件处理器"""
    
    def __init__(self, gui_page):
        self.gui_page = gui_page
        
    def on_power_data_received(self, data: dict) -> None:
        """电流功耗数据接收事件处理"""
        self.gui_page.root.after(0, self._update_power_data, data)
        
    def on_temperature_data_received(self, data: dict) -> None:
        """温度数据接收事件处理"""
        self.gui_page.root.after(0, self._update_temperature_data, data)
        
    def on_config_response_received(self, data: dict) -> None:
        """配置响应事件处理"""
        self.gui_page.root.after(0, self._update_config_response, data)
        
    def on_error(self, error: str) -> None:
        """错误事件处理"""
        self.gui_page.root.after(0, self._update_error, error)
        
    def _update_power_data(self, data):
        # 即使页面不可见也要处理数据（用于CSV保存）
        self.gui_page.update_power_display(data)
        
    def _update_temperature_data(self, data):
        # 即使页面不可见也要处理数据（用于CSV保存）
        self.gui_page.update_temperature_display(data)
        
    def _update_config_response(self, data):
        self.gui_page.update_config_display(data)
        
    def _update_error(self, error):
        self.gui_page.show_error(error)

class PageJPowerTempMonitor(ttk.Frame):
    """电流、功耗、温度监控页面"""
    
    def __init__(self, parent, serial_core):
        super().__init__(parent)
        self.serial_core = serial_core
        self.root = parent.winfo_toplevel()
        
        # 初始化监控器
        self.power_temp_monitor = create_power_temp_monitor(self.serial_core)
        self.gui_handler = PowerTempGUIEventHandler(self)
        self.power_temp_monitor.add_event_handler(self.gui_handler)
        
        # 添加串口数据处理
        if self.serial_core:
            self.serial_core.add_event_handler(self)
        # 串口接收缓冲区，用于拼接断包数据
        self._buffer = ""
        
        # 界面状态控制
        self.monitoring_active = False
        self.auto_save_enabled = tk.BooleanVar()
        self.auto_save_interval_var = tk.StringVar(value="60")
        
        # 通道颜色映射（用于数据显示）
        self.channel_colors = {
            "VCCO_34": "#FF0000", "VCCO_16": "#FF8000", "VCCO_15": "#FFFF00",
            "VCCO_14": "#80FF00", "VCCO_13": "#00FF00", "VCCO_0": "#00FF80",
            "VCCADC": "#00FFFF", "MGTAVTT": "#0080FF", "MGTAVCC": "#0000FF",
            "VCCAUX": "#8000FF", "VCCRAM": "#FF00FF", "VCCINT": "#FF0080"
        }
        
        # CSV自动保存定时器
        self.csv_save_timer = None
        
        self.build_ui()
        self.start_update_timer()
        
    def build_ui(self):
        """构建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 上部控制面板
        self.build_control_panel(main_frame)
        
        # 下部数据显示区（取消图表区）
        self.build_data_display_area(main_frame)
        
    def build_control_panel(self, parent):
        """构建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="📊 监控控制", padding=5)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # === 第一行：通道配置 ===
        config_row = ttk.Frame(control_frame)
        config_row.pack(fill=tk.X, pady=2)
        
        # 通道选择区域
        channels_frame = ttk.LabelFrame(config_row, text="电源通道配置", padding=3)
        channels_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 创建通道复选框 (4行3列)
        self.channel_vars = {}
        channels_grid = ttk.Frame(channels_frame)
        channels_grid.pack(fill=tk.X)
        
        power_channels = self.power_temp_monitor.config.power_channels
        for i, channel in enumerate(power_channels):
            row = i // 3
            col = i % 3
            
            var = tk.BooleanVar()
            self.channel_vars[channel] = var
            
            # 带颜色标识的复选框
            cb = ttk.Checkbutton(
                channels_grid,
                text=channel,
                variable=var,
                command=lambda ch=channel: self.on_channel_toggled(ch)
            )
            cb.grid(row=row, column=col, padx=5, pady=1, sticky=tk.W)
        
        # 通道控制按钮
        btn_frame = ttk.Frame(channels_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_frame, text="全选", command=self.select_all_channels, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="全清", command=self.clear_all_channels, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="SET", command=self.send_config_set, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="GET", command=self.send_config_get, width=8).pack(side=tk.LEFT, padx=2)
        
        # 控制按钮区域 - 整合所有监控控制功能
        control_btns_frame = ttk.LabelFrame(config_row, text="监控控制", padding=3)
        control_btns_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        control_grid = ttk.Frame(control_btns_frame)
        control_grid.pack()
        
        # 第一行：开始/停止监控
        self.start_btn = ttk.Button(control_grid, text="🟢 开始监控", command=self.start_monitoring, width=12)
        self.start_btn.grid(row=0, column=0, padx=2, pady=2)
        
        self.stop_btn = ttk.Button(control_grid, text="🔴 停止监控", command=self.stop_monitoring, width=12, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=2, pady=2)
        
        # 第二行：数据管理  
        ttk.Button(control_grid, text="🧹 清空数据", command=self.clear_all_data, width=12).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(control_grid, text="📊 刷新表格", command=self.refresh_display, width=12).grid(row=1, column=1, padx=2, pady=2)
        
        # 第三行：诊断工具
        ttk.Button(control_grid, text="📋 显示配置", command=self.show_channel_config, width=12).grid(row=2, column=0, padx=2, pady=2)
        
        # === 第二行：CSV自动保存控制 ===
        csv_control_row = ttk.Frame(control_frame)
        csv_control_row.pack(fill=tk.X, pady=2)
        
        # CSV导出控制 - 移到右上角
        csv_frame = ttk.LabelFrame(csv_control_row, text="CSV自动保存", padding=3)
        csv_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        csv_grid = ttk.Frame(csv_frame)
        csv_grid.pack()
        
        # 自动保存选项
        ttk.Checkbutton(csv_grid, text="启用自动保存", variable=self.auto_save_enabled, command=self.toggle_auto_save).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        ttk.Label(csv_grid, text="间隔(秒):").grid(row=1, column=0, sticky=tk.W)
        interval_entry = ttk.Entry(csv_grid, textvariable=self.auto_save_interval_var, width=8)
        interval_entry.grid(row=1, column=1, padx=2)
        
        ttk.Button(csv_grid, text="💾 立即导出", command=self.export_current_data, width=12).grid(row=1, column=2, padx=5)
        
    def build_data_display_area(self, parent):
        """构建数据显示区域"""
        data_frame = ttk.LabelFrame(parent, text="📈 实时数据监控", padding=5)
        data_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 创建标签页
        self.data_notebook = ttk.Notebook(data_frame)
        self.data_notebook.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # 电流功耗数据标签页
        power_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(power_frame, text="📊 电流功耗数据")
        
        # 数据显示表格
        power_display_frame = ttk.Frame(power_frame)
        power_display_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 使用Treeview创建更好的表格显示
        columns = ('通道', '电压(mV)', '电流(mA)', '功耗(mW)', '状态')
        self.power_tree = ttk.Treeview(power_display_frame, columns=columns, show='headings', height=12)
        
        # 设置列标题和宽度
        for col in columns:
            self.power_tree.heading(col, text=col)
            self.power_tree.column(col, width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        power_scrollbar = ttk.Scrollbar(power_display_frame, orient=tk.VERTICAL, command=self.power_tree.yview)
        self.power_tree.configure(yscrollcommand=power_scrollbar.set)
        
        self.power_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        power_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始化电流功耗表格
        self.init_power_tree()
        
        # 温度数据标签页
        temp_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(temp_frame, text="🌡️ 温度数据")
        
        # 温度显示区域
        temp_display_frame = ttk.Frame(temp_frame)
        temp_display_frame.pack(fill=tk.X, pady=20)
        
        # 大字体温度显示
        temp_grid = ttk.Frame(temp_display_frame)
        temp_grid.pack(expand=True)
        
        # 传感器温度
        sensor_frame = ttk.LabelFrame(temp_grid, text="EVB传感器温度", padding=10)
        sensor_frame.grid(row=0, column=0, padx=20, pady=10, sticky=tk.NSEW)
        
        self.temp_sensor_label = ttk.Label(sensor_frame, text="N/A °C", font=("Microsoft YaHei", 20, "bold"), foreground="blue", anchor=tk.CENTER)
        self.temp_sensor_label.pack(expand=True)
        
        # FPGA温度
        fpga_frame = ttk.LabelFrame(temp_grid, text="FPGA芯片温度", padding=10)
        fpga_frame.grid(row=0, column=1, padx=20, pady=10, sticky=tk.NSEW)
        
        self.temp_fpga_label = ttk.Label(fpga_frame, text="N/A °C", font=("Microsoft YaHei", 20, "bold"), foreground="red", anchor=tk.CENTER)
        self.temp_fpga_label.pack(expand=True)
        
        # 配置网格权重
        temp_grid.grid_columnconfigure(0, weight=1)
        temp_grid.grid_columnconfigure(1, weight=1)
        
        # 温度历史数据显示
        temp_history_frame = ttk.LabelFrame(temp_frame, text="温度历史记录", padding=5)
        temp_history_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 5))
        
        self.temp_history_text = scrolledtext.ScrolledText(temp_history_frame, height=8, wrap=tk.NONE, font=("Consolas", 9))
        self.temp_history_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态信息标签页
        status_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(status_frame, text="📋 状态信息")
        
        self.build_status_display(status_frame)
        
    def init_power_tree(self):
        """初始化电流功耗表格"""
        power_channels = self.power_temp_monitor.config.power_channels
        for i, channel in enumerate(power_channels):
            self.power_tree.insert('', 'end', iid=channel, values=(channel, '0.000', '0.000', '0.000', '未启用'))
            # 为奇偶行设置不同的标签（可选的视觉效果）
            if i % 2 == 0:
                self.power_tree.set(channel, '通道', channel)
                
    def build_status_display(self, parent):
        """构建状态显示"""
        status_grid = ttk.Frame(parent)
        status_grid.pack(fill=tk.X, pady=5)
        
        # 状态标签
        self.status_labels = {}
        
        labels_info = [
            ("串口状态", "gray", 0, 0),
            ("监控状态", "gray", 0, 2),
            ("后台运行", "gray", 0, 4),
            ("数据包数", "blue", 1, 0),
            ("数据点数", "blue", 1, 2),
            ("活跃通道", "green", 1, 4),
            ("CSV状态", "purple", 2, 0),
            ("自动保存", "orange", 2, 2)
        ]
        
        for label_text, color, row, col in labels_info:
            ttk.Label(status_grid, text=f"{label_text}:").grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.status_labels[label_text] = ttk.Label(status_grid, text="N/A", foreground=color, font=("Microsoft YaHei", 9, "bold"))
            self.status_labels[label_text].grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
        
    def build_chart_area(self, parent):
        """构建图表区域 - 已移除"""
        pass
        
    def setup_charts(self):
        """设置图表 - 已移除"""
        pass
        
    def on_display_type_changed(self, event=None):
        """显示类型改变事件 - 已移除"""
        pass
        
    def on_channel_toggled(self, channel):
        """通道切换事件"""
        enabled = self.channel_vars[channel].get()
        self.power_temp_monitor.config.set_channel_enabled(channel, enabled)
        self.log_message(f"通道 {channel} {'启用' if enabled else '禁用'}")
        
    def select_all_channels(self):
        """全选所有通道"""
        for var in self.channel_vars.values():
            var.set(True)
        self.power_temp_monitor.config.enable_all_channels()
        self.log_message("已选择所有通道")
        
    def clear_all_channels(self):
        """清除所有通道选择"""
        for var in self.channel_vars.values():
            var.set(False)
        self.power_temp_monitor.config.disable_all_channels()
        self.log_message("已清除所有通道选择")
        
    def send_config_set(self):
        """发送配置SET命令"""
        # 先同步所有通道状态到后端配置
        for channel, var in self.channel_vars.items():
            self.power_temp_monitor.config.set_channel_enabled(channel, var.get())
        
        # 显示当前配置
        config_str = self.power_temp_monitor.config.get_config_string()
        enabled_count = sum(1 for v in self.channel_vars.values() if v.get())
        
        if self.power_temp_monitor.send_power_config_set():
            self.log_message(f"配置SET命令已发送 - 启用 {enabled_count} 个通道")
        else:
            self.show_error("发送配置SET命令失败")
            
    def send_config_get(self):
        """发送配置GET命令"""
        if self.power_temp_monitor.send_power_config_get():
            self.log_message("配置GET命令已发送")
        else:
            self.show_error("发送配置GET命令失败")
            
    def start_monitoring(self):
        """开始监控"""
        if not self.serial_core or not self.serial_core.is_connected:
            messagebox.showwarning("警告", "请先连接串口")
            return
            
        self.monitoring_active = True
        self.power_temp_monitor.monitoring_enabled = True
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 启动CSV自动保存定时器
        if self.auto_save_enabled.get():
            self.start_csv_timer()
        
        self.log_message("开始电流功耗温度监控")
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        self.power_temp_monitor.monitoring_enabled = False
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # 停止CSV自动保存定时器
        self.stop_csv_timer()
        
        self.log_message("停止电流功耗温度监控")
        
    def toggle_plot_pause(self):
        """切换图表暂停 - 已移除"""
        pass
            
    def toggle_auto_save(self):
        """切换自动保存"""
        if self.auto_save_enabled.get():
            # 启用自动保存
            if self.monitoring_active:
                self.start_csv_timer()
            self.log_message("自动保存CSV已启用")
        else:
            # 禁用自动保存
            self.stop_csv_timer()
            self.log_message("自动保存CSV已禁用")
            
    def start_csv_timer(self):
        """启动CSV自动保存定时器"""
        if self.csv_save_timer:
            self.root.after_cancel(self.csv_save_timer)
        
        try:
            interval = int(self.auto_save_interval_var.get()) * 1000  # 转换为毫秒
            self.csv_save_timer = self.root.after(interval, self.auto_save_csv)
        except ValueError:
            messagebox.showwarning("警告", "保存间隔必须是有效数字")
            self.auto_save_enabled.set(False)
            
    def stop_csv_timer(self):
        """停止CSV自动保存定时器"""
        if self.csv_save_timer:
            self.root.after_cancel(self.csv_save_timer)
            self.csv_save_timer = None
            
    def auto_save_csv(self):
        """自动保存CSV"""
        if not self.auto_save_enabled.get() or not self.monitoring_active:
            return
            
        # 创建带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"power_temp_auto_{timestamp}.csv"
        
        # 确保logs目录存在
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        file_path = os.path.join(logs_dir, filename)
        
        if self.export_custom_csv(file_path):
            self.log_message(f"自动保存CSV成功: {filename}")
        else:
            self.log_message("自动保存CSV失败", "error")
        
        # 重新启动定时器
        if self.auto_save_enabled.get() and self.monitoring_active:
            self.start_csv_timer()
        
    def clear_all_data(self):
        """清空所有数据"""
        self.power_temp_monitor.data_processor.clear_all_data()
        
        # 重置电流功耗表格
        for channel in self.power_temp_monitor.config.power_channels:
            self.power_tree.set(channel, '通道', channel)
            self.power_tree.set(channel, '电压(mV)', '0.000')
            self.power_tree.set(channel, '电流(mA)', '0.000')
            self.power_tree.set(channel, '功耗(mW)', '0.000')
            self.power_tree.set(channel, '状态', '未启用')
        
        # 重置温度显示
        self.temp_sensor_label.config(text="N/A °C")
        self.temp_fpga_label.config(text="N/A °C")
        self.temp_history_text.delete('1.0', tk.END)
        
        self.log_message("所有数据已清空")
        
    def refresh_display(self):
        """刷新数据显示"""
        # 强制刷新表格显示
        latest_power_data = self.power_temp_monitor.data_processor.get_latest_power_data()
        latest_temp_data = self.power_temp_monitor.data_processor.get_latest_temperature_data()
        
        if latest_power_data:
            self.update_power_display(latest_power_data)
        if latest_temp_data:
            self.update_temperature_display(latest_temp_data)
        
        self.log_message("数据显示已刷新")
        
    def refresh_charts(self):
        """刷新图表 - 已移除，保持兼容性"""
        self.refresh_display()
        
    def export_current_data(self):
        """导出当前数据 - 自定义格式，分开显示电压、电流、功耗"""
        file_path = filedialog.asksaveasfilename(
            title="导出当前数据",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            if self.export_custom_csv(file_path):
                messagebox.showinfo("导出成功", f"数据已导出到:\n{file_path}")
                self.log_message(f"数据导出成功: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("导出失败", "导出数据时发生错误")
                
    def export_custom_csv(self, file_path):
        """自定义CSV导出格式 - 分开显示电压、电流、功耗"""
        try:
            import csv
            from datetime import datetime
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                header = ['时间戳']
                # 电压列
                for channel in self.power_temp_monitor.config.power_channels:
                    header.append(f'{channel}_电压(mV)')
                # 电流列
                for channel in self.power_temp_monitor.config.power_channels:
                    header.append(f'{channel}_电流(mA)')
                # 功耗列
                for channel in self.power_temp_monitor.config.power_channels:
                    header.append(f'{channel}_功耗(mW)')
                # 温度列
                header.extend(['传感器温度(°C)', 'FPGA温度(°C)'])
                writer.writerow(header)
                
                # 获取数据
                timestamps = list(self.power_temp_monitor.data_processor.timestamps)
                temp_timestamps = list(self.power_temp_monitor.data_processor.temp_timestamps)
                
                # 写入数据行
                for i, timestamp in enumerate(timestamps):
                    row = [timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]]
                    # 电压数据
                    for channel in self.power_temp_monitor.config.power_channels:
                        if i < len(self.power_temp_monitor.data_processor.voltage_data[channel]):
                            voltage_mv = self.power_temp_monitor.data_processor.voltage_data[channel][i] / 1000.0
                            row.append(f"{voltage_mv:.3f}")
                        else:
                            row.append("0.000")
                    # 电流数据
                    for channel in self.power_temp_monitor.config.power_channels:
                        if i < len(self.power_temp_monitor.data_processor.current_data[channel]):
                            current_ma = self.power_temp_monitor.data_processor.current_data[channel][i] / 1000.0
                            row.append(f"{current_ma:.3f}")
                        else:
                            row.append("0.000")
                    # 功耗数据
                    for channel in self.power_temp_monitor.config.power_channels:
                        if i < len(self.power_temp_monitor.data_processor.power_data[channel]):
                            power_mw = self.power_temp_monitor.data_processor.power_data[channel][i] / 1000.0
                            row.append(f"{power_mw:.3f}")
                        else:
                            row.append("0.000")
                    # 温度数据（查找最接近的时间戳）
                    if temp_timestamps:
                        closest_temp_idx = min(range(len(temp_timestamps)), key=lambda x: abs((temp_timestamps[x] - timestamp).total_seconds()))
                        if closest_temp_idx < len(self.power_temp_monitor.data_processor.temp_sensor_data):
                            sensor_temp = self.power_temp_monitor.data_processor.temp_sensor_data[closest_temp_idx]
                            fpga_temp = self.power_temp_monitor.data_processor.temp_fpga_data[closest_temp_idx]
                            row.extend([f"{sensor_temp:.3f}", f"{fpga_temp:.3f}"])
                        else:
                            row.extend(["0.000", "0.000"])
                    else:
                        row.extend(["0.000", "0.000"])
                    writer.writerow(row)
            self.log_message(f"自定义CSV导出成功: 共 {len(timestamps)} 行数据")
            return True
        except Exception as e:
            self.log_message(f"CSV导出失败: {e}", "error")
            return False
        
    def update_power_display(self, data):
        """更新电流功耗显示"""
        # 始终处理数据（即使页面不可见），确保CSV数据完整
        timestamp_str = data['timestamp'].strftime('%H:%M:%S')
        
        # 更新表格显示
        updated_channels = []
        for channel, values in data['channels'].items():
            if channel in self.power_temp_monitor.config.power_channels:
                # 转换单位：μV->mV, μA->mA, μW->mW
                voltage_mv = values['voltage'] / 1000.0  # μV -> mV
                current_ma = values['current'] / 1000.0  # μA -> mA
                power_mw = values['power'] / 1000.0      # μW -> mW
                # 判断状态
                if values['voltage'] >= 0 or values['current'] >= 0 or values['power'] >= 0:
                    status = "活跃"
                else:
                    status = "未启用" if self.channel_vars[channel].get() else "已关闭"
                # 更新Treeview行数据，保留3位小数
                try:
                    self.power_tree.set(channel, '通道', channel)
                    self.power_tree.set(channel, '电压(mV)', f"{voltage_mv:.3f}")
                    self.power_tree.set(channel, '电流(mA)', f"{current_ma:.3f}")
                    self.power_tree.set(channel, '功耗(mW)', f"{power_mw:.3f}")
                    self.power_tree.set(channel, '状态', status)
                    updated_channels.append(channel)
                except Exception as e:
                    pass
        
    def update_temperature_display(self, data):
        """更新温度显示"""
        # 始终处理数据（即使页面不可见），确保CSV数据完整
        # 更新温度标签
        self.temp_sensor_label.config(text=f"{data['temp_sensor']:.3f} °C")
        self.temp_fpga_label.config(text=f"{data['temp_fpga']:.3f} °C")
        # 添加到历史记录
        timestamp_str = data['timestamp'].strftime('%H:%M:%S.%f')[:-3]
        history_line = f"[{timestamp_str}] 传感器: {data['temp_sensor']:6.3f}°C, FPGA: {data['temp_fpga']:6.3f}°C\n"
        self.temp_history_text.insert(tk.END, history_line)
        self.temp_history_text.see(tk.END)
        # 限制历史记录行数
        lines = int(self.temp_history_text.index(tk.END).split('.')[0])
        if lines > 200:
            self.temp_history_text.delete('1.0', '50.0')
        
    def update_config_display(self, data):
        """更新配置显示"""
        self.log_message(f"收到配置响应: {data}")
        
    def update_charts(self):
        """更新图表 - 已移除"""
        pass
            
    def update_temperature_chart(self):
        """更新温度图表 - 已移除"""
        pass
        
    def update_power_charts(self):
        """更新电流/功耗图表 - 已移除"""
        pass
            
    def start_update_timer(self):
        """启动更新定时器"""
        self.update_status_display()
        self.root.after(1000, self.start_update_timer)  # 每秒更新一次
        
    def update_status_display(self):
        """更新状态显示"""
        try:
            # 串口状态
            if self.serial_core and self.serial_core.is_connected:
                self.status_labels["串口状态"].config(text="已连接", foreground="green")
            else:
                self.status_labels["串口状态"].config(text="未连接", foreground="red")
            # 监控状态
            if self.monitoring_active:
                self.status_labels["监控状态"].config(text="运行中", foreground="green")
            else:
                self.status_labels["监控状态"].config(text="已停止", foreground="red")
            # 后台运行状态
            try:
                current_notebook = self.root.children.get('!notebook')
                if current_notebook:
                    current_tab_text = current_notebook.tab('current', 'text').strip()
                    if self.monitoring_active and "电流功耗温度" not in current_tab_text:
                        self.status_labels["后台运行"].config(text="是", foreground="orange")
                    else:
                        self.status_labels["后台运行"].config(text="否", foreground="gray")
                else:
                    self.status_labels["后台运行"].config(text="未知", foreground="gray")
            except:
                self.status_labels["后台运行"].config(text="未知", foreground="gray")
            # 获取统计信息
            stats = self.power_temp_monitor.get_statistics()
            # 数据包数
            total_packets = stats['total_power_packets'] + stats['total_temp_packets']
            self.status_labels["数据包数"].config(text=str(total_packets))
            # 数据点数
            total_points = stats['power_data_points'] + stats['temp_data_points']
            self.status_labels["数据点数"].config(text=str(total_points))
            # 活跃通道
            enabled_channels = len(stats['enabled_channels'])
            self.status_labels["活跃通道"].config(text=f"{enabled_channels}/12")
            # CSV状态
            if self.auto_save_enabled.get():
                self.status_labels["CSV状态"].config(text="自动保存", foreground="green")
            else:
                self.status_labels["CSV状态"].config(text="手动保存", foreground="gray")
            # 自动保存状态
            if self.auto_save_enabled.get() and self.monitoring_active:
                try:
                    next_save = int(self.auto_save_interval_var.get())
                    self.status_labels["自动保存"].config(text=f"{next_save}s间隔", foreground="green")
                except:
                    self.status_labels["自动保存"].config(text="配置错误", foreground="red")
            else:
                self.status_labels["自动保存"].config(text="未启用", foreground="gray")
        except Exception as e:
            pass
    
    # 串口事件处理器接口实现
    def on_data_received(self, processed_data):
        """处理串口接收数据"""
        if 'ascii' in processed_data:
            data_chunk = processed_data['ascii']
            # 去除回车符，将换行统一为 '\n'
            data_chunk = data_chunk.replace('\r', '')
            # 累积数据到缓冲区
            self._buffer += data_chunk
            # 提取完整的数据帧（以换行 '\n' 为帧结束标志）
            while '\n' in self._buffer:
                line, self._buffer = self._buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                # 传递完整帧数据给监控器进行处理
                self.power_temp_monitor.process_received_data(line)
    
    def on_data_sent(self, data): 
        """串口数据发送事件（未使用）"""
        pass
    
    def on_connection_changed(self, connected, port=None): 
        """串口连接状态改变事件（未使用）"""
        pass
    
    def on_error(self, error):
        """串口错误事件（未使用）"""
        pass
    
    def show_error(self, error):
        """显示错误信息"""
        self.log_message(f"错误: {error}", "error")
        
    def show_channel_config(self):
        """显示当前通道配置"""
        config_str = self.power_temp_monitor.config.get_config_string()
        enabled_channels = [ch for ch, enabled in self.power_temp_monitor.config.channel_enabled.items() if enabled]
        msg = f"通道配置字符串:\n{config_str}\n\n"
        msg += f"启用的通道 ({len(enabled_channels)}/12):\n"
        msg += "\n".join([f"• {ch}" for ch in enabled_channels])
        messagebox.showinfo("通道配置", msg)
        self.log_message(f"当前启用 {len(enabled_channels)} 个通道: {', '.join(enabled_channels)}")
    
    def log_message(self, message, level="info"):
        """记录日志信息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        # 如果有日志文本框，也输出到文本框
        try:
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert(tk.END, log_line + "\n")
                self.log_text.see(tk.END)
        except:
            pass
    
    def reset(self):
        """页面重置方法 - 保持监控状态但清空显示"""
        # 记录调用信息
        if self.monitoring_active:
            # 监控正在运行，不停止监控，只更新按钮状态
            self.log_message("页面切换 - 电流功耗温度监控继续在后台运行")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            # 不清空数据，保持当前显示
        else:
            # 如果监控未运行，执行常规重置，清空显示数据
            for channel in self.power_temp_monitor.config.power_channels:
                self.power_tree.set(channel, '通道', channel)
                self.power_tree.set(channel, '电压(mV)', '0.000')
                self.power_tree.set(channel, '电流(mA)', '0.000')
                self.power_tree.set(channel, '功耗(mW)', '0.000')
                self.power_tree.set(channel, '状态', '未启用')
            # 重置温度显示
            self.temp_sensor_label.config(text="N/A °C")
            self.temp_fpga_label.config(text="N/A °C")
            # 清空温度历史记录
            self.temp_history_text.delete('1.0', tk.END)
            self.log_message("电流功耗温度监控页面已重置")
    
    def on_page_leave(self):
        """页面离开时调用 - 保持兼容（不执行操作）"""
        pass
            
    def on_page_enter(self):
        """页面进入时调用 - 保持兼容（不执行操作）"""
        pass
            
    def __del__(self):
        """析构函数 - 清理资源"""
        try:
            if hasattr(self, 'monitoring_active') and self.monitoring_active:
                self.stop_monitoring()
            if hasattr(self, 'csv_save_timer') and self.csv_save_timer:
                self.stop_csv_timer()
        except:
            pass