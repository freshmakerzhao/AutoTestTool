# GUI/PAGES/page_i_clock_monitor.py
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import re
import queue
from CLI.cli_clock import ClockClient
from CORE.module_clock import build_clk_cfg_command

class ReliableClockClient:
    """真正可靠的时钟客户端"""
    def __init__(self, serial_core):
        self.serial = serial_core
        self._response_queue = queue.Queue()
        self._raw_buffer = ""  # 添加原始数据缓冲区
        self._ack_patterns = [
            r'MC1P recv clk reg set reg ([0-9a-f]+) value ([0-9a-f]+)',
            r'CLKCFG.*reg\s+([0-9a-f]{4}).*value\s+([0-9a-f]+)',
            r'reg.*set.*reg\s+([0-9a-f]{4}).*value\s+([0-9a-f]+)',
        ]
        self._setup_response_handler()

    def _setup_response_handler(self):
        """设置响应处理器"""
        self.serial.add_event_handler(self)

    def on_data_received(self, data_dict):
        """接收串口数据并放入队列 - 改进版本"""
        if 'ascii' in data_dict:
            # 将数据添加到原始缓冲区
            self._raw_buffer += data_dict['ascii']
            
            # 按行分割并处理完整行
            lines = self._raw_buffer.split('\n')
            # 保留最后一个可能不完整的行
            self._raw_buffer = lines[-1]
            
            # 处理完整的行
            for line in lines[:-1]:
                line = line.strip()
                if line:
                    self._response_queue.put(line)

    def on_data_sent(self, data: bytes):
        pass

    def on_connection_changed(self, connected: bool, port: str = None):
        pass

    def on_error(self, error: str):
        pass

    def is_connected(self) -> bool:
        """检查串口连接状态"""
        return self.serial.is_connected

    def send_reg_direct(self, reg_offset: str, reg_value: str) -> dict:
        """
        直发模式：只发送寄存器，不等待确认
        返回发送结果信息
        """
        result = {
            "success": False,
            "attempts": 1,
            "error": None
        }
        
        try:
            # 发送命令
            cmd = build_clk_cfg_command(reg_offset, reg_value)
            if self.serial.send_text(cmd + "\n"):
                result["success"] = True
            else:
                result["error"] = "串口发送失败"
        except Exception as e:
            result["error"] = f"发送异常: {str(e)}"
        
        return result

    def send_reg_with_guaranteed_ack(self, reg_offset: str, reg_value: str, timeout: float = 5.0, max_retries: int = 3) -> dict:
        """
        发送寄存器并确保收到设备确认
        返回详细的结果信息
        """
        result = {
            "success": False,
            "attempts": 0,
            "ack_received": False,
            "actual_response": "",
            "parsed_reg": "",
            "parsed_value": "",
            "error": None
        }
        
        expected_reg = reg_offset.lower().replace("0x", "").zfill(4)  # 确保4位格式
        expected_val = reg_value.lower().replace("0x", "").zfill(2)   # 确保2位格式
        
        for attempt in range(max_retries):
            result["attempts"] = attempt + 1
            
            # 清空响应队列中的旧数据
            old_responses = []
            while not self._response_queue.empty():
                try:
                    old_responses.append(self._response_queue.get_nowait())
                except queue.Empty:
                    break
            
            # 清空原始缓冲区
            self._raw_buffer = ""
            
            # 发送命令
            cmd = build_clk_cfg_command(reg_offset, reg_value)
            self.serial.send_text(cmd + "\n")
            
            # 等待确认
            start = time.time()
            responses_collected = []
            
            while time.time() - start < timeout:
                try:
                    line = self._response_queue.get(timeout=0.1)
                    responses_collected.append(line)
                    result["actual_response"] = line  # 保存最后一个响应
                    
                    # 检查是否是我们期待的确认
                    line_lower = line.lower()
                    
                    # 主要模式：MC1P recv clk reg set reg xxxx value xx
                    main_match = re.search(r'MC1P recv clk reg set reg ([0-9a-f]+) value ([0-9a-f]+)', line_lower)
                    if main_match:
                        recv_reg = main_match.group(1).zfill(4)
                        recv_val = main_match.group(2).zfill(2)
                        
                        result["parsed_reg"] = recv_reg
                        result["parsed_value"] = recv_val
                        
                        if recv_reg == expected_reg and recv_val == expected_val:
                            result["success"] = True
                            result["ack_received"] = True
                            return result
                    
                    # 备用模式：检查其他可能的确认格式
                    for pattern in self._ack_patterns[1:]:
                        match = re.search(pattern, line_lower)
                        if match and len(match.groups()) >= 2:
                            recv_reg = match.group(1).zfill(4)
                            recv_val = match.group(2).zfill(2)
                            
                            result["parsed_reg"] = recv_reg
                            result["parsed_value"] = recv_val
                            
                            if recv_reg == expected_reg and recv_val == expected_val:
                                result["success"] = True
                                result["ack_received"] = True
                                return result
                    
                    # 检查错误响应
                    if any(err in line_lower for err in ["error", "fail", "nack", "invalid"]):
                        result["error"] = f"Device error: {line}"
                        break
                        
                except queue.Empty:
                    continue
            
            # 如果没有找到匹配，记录所有收集到的响应
            if not result["success"] and responses_collected:
                result["actual_response"] = " | ".join(responses_collected)
            
            # 本次尝试失败，等待一下再重试
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # 递增延迟
        
        if not result["success"]:
            result["error"] = result["error"] or f"No valid ACK received after {max_retries} attempts. Expected: reg={expected_reg}, value={expected_val}"
        
        return result

class PageIClockMonitor(ttk.Frame):
    """简化版Si5344时钟配置页面 - 只保留寄存器配置功能"""
    def __init__(self, parent, serial_core):
        super().__init__(parent)
        self.serial_core = serial_core  # 保存serial_core引用
        self.client = ReliableClockClient(serial_core)
        self._is_sending = False
        self._stop_sending = False
        self._detailed_log = []  # 详细日志
        self._build_ui()

    def _build_ui(self):
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === 时钟频点配置区域 ===
        config_frame = ttk.LabelFrame(main_frame, text="🔒 时钟频点配置 (100% 确认模式)")
        config_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        config_frame.grid_columnconfigure(1, weight=1)

        # 文件选择
        ttk.Label(config_frame, text="配置文件:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(config_frame, textvariable=self.file_var)
        file_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(config_frame, text="Browse", command=self._browse_file).grid(row=0, column=2, padx=5, pady=5)

        # 文件信息显示
        info_frame = ttk.Frame(config_frame)
        info_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        ttk.Label(info_frame, text="检测到寄存器数量:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.detected_regs_var = tk.StringVar(value="未选择文件")
        ttk.Entry(info_frame, textvariable=self.detected_regs_var, state="readonly", width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(info_frame, text="文件大小:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.file_size_var = tk.StringVar(value="--")
        ttk.Entry(info_frame, textvariable=self.file_size_var, state="readonly", width=10).grid(row=0, column=3, padx=5)

        # 发送模式选择
        mode_frame = ttk.Frame(config_frame)
        mode_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        ttk.Label(mode_frame, text="发送模式:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.mode_var = tk.StringVar(value="确认模式")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, width=20, state="readonly")
        mode_combo['values'] = ("确认模式 (等待设备确认)", "直发模式 (仅发送不等确认)")
        mode_combo.grid(row=0, column=1, padx=5, sticky="w")
        
        # 模式说明
        ttk.Label(mode_frame, text="💡 确认模式适用于支持recv回复的板子，直发模式适用于不回复的板子", 
                 foreground="blue", font=("Microsoft YaHei", 8)).grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=2)

        # 控制按钮
        control_frame = ttk.Frame(config_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=5)
        
        self.send_btn = ttk.Button(control_frame, text="📡 配置", command=self._send_regs_reliable)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ 停止", command=self._stop_regs, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.log_btn = ttk.Button(control_frame, text="📋 查看详细日志", command=self._show_detailed_log)
        self.log_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = ttk.Button(control_frame, text="🔄 重置", command=self.manual_reset)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # === 实时统计区域 ===
        stats_frame = ttk.LabelFrame(main_frame, text="📊 实时统计 (发送状态)")
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # 当前进度
        ttk.Label(stats_frame, text="当前状态:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Entry(stats_frame, textvariable=self.status_var, state="readonly").grid(row=0, column=1, columnspan=5, sticky="ew", padx=5, pady=2)
        stats_frame.grid_columnconfigure(1, weight=1)

        # 详细统计
        detail_frame = ttk.Frame(stats_frame)
        detail_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=5, pady=5)

        # 第一行统计
        ttk.Label(detail_frame, text="总寄存器:").grid(row=0, column=0, padx=5)
        self.total_var = tk.IntVar(value=0)
        ttk.Entry(detail_frame, textvariable=self.total_var, width=6, state="readonly").grid(row=0, column=1, padx=2)

        ttk.Label(detail_frame, text="已发送:").grid(row=0, column=2, padx=5)
        self.sent_var = tk.IntVar(value=0)
        ttk.Entry(detail_frame, textvariable=self.sent_var, width=6, state="readonly").grid(row=0, column=3, padx=2)

        ttk.Label(detail_frame, text="已成功:").grid(row=0, column=4, padx=5)
        self.confirmed_var = tk.IntVar(value=0)
        ttk.Entry(detail_frame, textvariable=self.confirmed_var, width=6, state="readonly").grid(row=0, column=5, padx=2)

        ttk.Label(detail_frame, text="失败:").grid(row=0, column=6, padx=5)
        self.failed_var = tk.IntVar(value=0)
        ttk.Entry(detail_frame, textvariable=self.failed_var, width=6, state="readonly").grid(row=0, column=7, padx=2)

        # 第二行统计
        ttk.Label(detail_frame, text="成功率:").grid(row=1, column=0, padx=5)
        self.ack_rate_var = tk.StringVar(value="0%")
        ttk.Entry(detail_frame, textvariable=self.ack_rate_var, width=8, state="readonly").grid(row=1, column=1, padx=2)

        ttk.Label(detail_frame, text="平均重试:").grid(row=1, column=2, padx=5)
        self.avg_retry_var = tk.StringVar(value="0")
        ttk.Entry(detail_frame, textvariable=self.avg_retry_var, width=8, state="readonly").grid(row=1, column=3, padx=2)

        ttk.Label(detail_frame, text="速度:").grid(row=1, column=4, padx=5)
        self.speed_var = tk.StringVar(value="0 reg/s")
        ttk.Entry(detail_frame, textvariable=self.speed_var, width=10, state="readonly").grid(row=1, column=5, padx=2)

        ttk.Label(detail_frame, text="预计剩余:").grid(row=1, column=6, padx=5)
        self.eta_var = tk.StringVar(value="--:--")
        ttk.Entry(detail_frame, textvariable=self.eta_var, width=8, state="readonly").grid(row=1, column=7, padx=2)

        # 说明文字
        note_frame = ttk.Frame(main_frame)
        note_frame.pack(fill=tk.X, pady=5)
        note = ("🔒 时钟频点配置特点：\n"
               "• 自动检测配置文件中的寄存器数量（常见465个，支持其他数量）\n"
               "• 支持两种模式：确认模式（等待设备recv回复）和直发模式（仅发送）\n"
               "• 确认模式：适用于支持recv回复的板子，确保100%可靠传输\n"
               "• 直发模式：适用于不回复recv的板子，快速批量发送")
        ttk.Label(note_frame, text=note, foreground="blue", font=("Microsoft YaHei", 8), justify=tk.LEFT).pack(anchor=tk.W)

    def _check_connection(self) -> bool:
        """检查串口连接状态"""
        if not self.client.is_connected():
            messagebox.showerror("连接错误", 
                               "串口未连接！\n\n"
                               "请先在'串口监视器'页面连接串口后再进行配置。")
            return False
        return True

    def _browse_file(self):
        """浏览寄存器文件"""
        path = filedialog.askopenfilename(
            title="选择时钟频点配置文件",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self.file_var.set(path)
            self._analyze_file(path)

    def _analyze_file(self, path):
        """分析寄存器文件并自动检测数量"""
        try:
            total_lines = 0
            valid_regs = 0
            comment_lines = 0
            empty_lines = 0
            file_size = os.path.getsize(path)
            
            with open(path, 'r', encoding='latin-1') as f:
                for line in f:
                    total_lines += 1
                    line = line.strip()
                    
                    if not line:
                        empty_lines += 1
                        continue
                    
                    if line.startswith("#"):
                        comment_lines += 1
                        continue
                    
                    # 检查有效的寄存器行格式 (地址,数据)
                    parts = [x.strip() for x in line.split(",")]
                    if len(parts) == 2:
                        addr_part = parts[0].strip()
                        data_part = parts[1].strip()
                        
                        # 检查地址格式 (0x开头的十六进制)
                        if addr_part.startswith("0x") and len(addr_part) >= 3:
                            try:
                                # 验证是否为有效的十六进制地址
                                int(addr_part, 16)
                                # 验证数据部分是否为有效的十六进制
                                if data_part.startswith("0x"):
                                    int(data_part, 16)
                                    valid_regs += 1
                                elif len(data_part) <= 4:  # 可能是不带0x前缀的十六进制
                                    int(data_part, 16)
                                    valid_regs += 1
                            except ValueError:
                                # 不是有效的十六进制，跳过
                                pass
            
            # 更新显示
            self.total_var.set(valid_regs)
            self.detected_regs_var.set(f"{valid_regs} 个")
            
            # 格式化文件大小
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size/1024:.1f} KB"
            else:
                size_str = f"{file_size/(1024*1024):.1f} MB"
            self.file_size_var.set(size_str)
            
            self._reset_stats()
            
            # 详细的状态信息
            status_msg = (f"✅ 文件已分析完成 | "
                         f"有效寄存器: {valid_regs} 个 | "
                         f"总行数: {total_lines} | "
                         f"注释行: {comment_lines} | "
                         f"空行: {empty_lines}")
            self.status_var.set(status_msg)
            
            # 如果检测到常见的寄存器数量，给出提示
            if valid_regs == 465:
                messagebox.showinfo("文件分析", 
                                  f"✅ 检测到标准的Si5344配置文件\n\n"
                                  f"📊 文件信息:\n"
                                  f"• 有效寄存器: {valid_regs} 个 (标准数量)\n"
                                  f"• 文件大小: {size_str}\n"
                                  f"• 总行数: {total_lines}\n"
                                  f"• 注释行: {comment_lines}\n"
                                  f"• 空行: {empty_lines}\n\n"
                                  f"🔧 可以开始配置")
            elif valid_regs > 0:
                messagebox.showinfo("文件分析", 
                                  f"✅ 检测到时钟配置文件\n\n"
                                  f"📊 文件信息:\n"
                                  f"• 有效寄存器: {valid_regs} 个\n"
                                  f"• 文件大小: {size_str}\n"
                                  f"• 总行数: {total_lines}\n"
                                  f"• 注释行: {comment_lines}\n"
                                  f"• 空行: {empty_lines}\n\n"
                                  f"⚠️ 注意: 这不是标准数量(465个)，请确认文件正确")
            else:
                messagebox.showwarning("文件分析", 
                                     f"⚠️ 未检测到有效的寄存器配置\n\n"
                                     f"文件应包含格式如下的行:\n"
                                     f"0x1234,0x56\n"
                                     f"或\n"
                                     f"0x1234,56\n\n"
                                     f"请检查文件格式是否正确")
            
        except Exception as e:
            self.total_var.set(0)
            self.detected_regs_var.set("检测失败")
            self.file_size_var.set("--")
            self.status_var.set(f"❌ 文件分析失败: {e}")
            messagebox.showerror("文件分析失败", f"无法分析文件:\n{str(e)}")

    def _reset_stats(self):
        """重置统计信息"""
        self.sent_var.set(0)
        self.confirmed_var.set(0)
        self.failed_var.set(0)
        self.ack_rate_var.set("0%")
        self.avg_retry_var.set("0")
        self.speed_var.set("0 reg/s")
        self.eta_var.set("--:--")
        self._detailed_log.clear()

    def _send_regs_reliable(self):
        """可靠发送模式"""
        if self._is_sending:
            messagebox.showwarning("提示", "正在发送中，请稍等...")
            return
        
        # 检查串口连接
        if not self._check_connection():
            return
            
        path = self.file_var.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("错误", "请先选择有效的配置文件")
            return
        
        # 检查是否检测到寄存器
        if self.total_var.get() <= 0:
            messagebox.showerror("错误", "文件中未检测到有效的寄存器配置")
            return
            
        self._stop_sending = False
        self._is_sending = True
        self.send_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._reset_stats()
        
        threading.Thread(target=self._do_reliable_send, args=(path,), daemon=True).start()

    def _stop_regs(self):
        """停止发送"""
        self._stop_sending = True
        self.after(0, self.status_var.set, "🛑 正在停止...")

    def _show_detailed_log(self):
        """显示详细日志"""
        if not self._detailed_log:
            messagebox.showinfo("日志", "暂无详细日志")
            return
            
        log_window = tk.Toplevel(self)
        log_window.title("详细配置日志")
        log_window.geometry("1000x600")
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(log_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加控制按钮
        btn_frame = ttk.Frame(log_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def copy_log():
            log_window.clipboard_clear()
            log_window.clipboard_append(text_widget.get('1.0', tk.END))
            messagebox.showinfo("复制成功", "日志已复制到剪贴板")
        
        def save_log():
            file_path = filedialog.asksaveasfilename(
                title="保存日志",
                defaultextension=".log",
                filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text_widget.get('1.0', tk.END))
                    messagebox.showinfo("保存成功", f"日志已保存到: {file_path}")
                except Exception as e:
                    messagebox.showerror("保存失败", str(e))
        
        ttk.Button(btn_frame, text="复制全部", command=copy_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存日志", command=save_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=log_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 填充日志内容，并添加颜色标记
        for entry in self._detailed_log:
            if "✅" in entry:
                text_widget.insert(tk.END, entry + "\n", "success")
            elif "❌" in entry:
                text_widget.insert(tk.END, entry + "\n", "error")
            elif "⚠️" in entry:
                text_widget.insert(tk.END, entry + "\n", "warning")
            else:
                text_widget.insert(tk.END, entry + "\n")
        
        # 配置文本颜色
        text_widget.tag_config("success", foreground="green")
        text_widget.tag_config("error", foreground="red")
        text_widget.tag_config("warning", foreground="orange")
        
        text_widget.config(state=tk.DISABLED)
        text_widget.see(tk.END)  # 滚动到底部

    def _do_reliable_send(self, path):
        """可靠发送的后台线程 - 支持确认模式和直发模式"""
        sent_count = 0
        confirmed_count = 0
        failed_count = 0
        total_retries = 0
        total = self.total_var.get()
        
        # 根据模式选择参数
        is_confirm_mode = "确认模式" in self.mode_var.get()
        
        # 固定参数设置
        timeout = 3.0 if is_confirm_mode else 0.0
        max_retries = 3 if is_confirm_mode else 1
        interval = 0.05  # 发送间隔固定为0.05秒
        
        start_time = time.time()
        last_update_time = start_time
        
        try:
            mode_desc = "确认模式" if is_confirm_mode else "直发模式"
            self.after(0, self.status_var.set, f"🔒 开始时钟频点配置 ({mode_desc})...")
            
            # 添加启动日志
            start_log = f"📋 时钟频点配置开始 - 文件: {os.path.basename(path)} | 总寄存器: {total} | 模式: {mode_desc}"
            self._detailed_log.append(start_log)
            
            with open(path, 'r', encoding='latin-1') as f:
                for line_num, line in enumerate(f, 1):
                    if self._stop_sending:
                        break
                        
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    # 解析寄存器配置行
                    parts = [x.strip() for x in line.split(",")]
                    if len(parts) != 2:
                        continue
                    
                    addr_part = parts[0].strip()
                    data_part = parts[1].strip()
                    
                    # 验证地址格式
                    if not addr_part.startswith("0x"):
                        continue
                    
                    # 确保数据部分有0x前缀
                    if not data_part.startswith("0x"):
                        data_part = "0x" + data_part
                    
                    try:
                        # 验证是否为有效的十六进制
                        int(addr_part, 16)
                        int(data_part, 16)
                    except ValueError:
                        continue
                    
                    sent_count += 1
                    reg_offset, reg_value = addr_part, data_part
                    
                    # 更新当前状态
                    status_msg = f"🔒 发送 {sent_count}/{total}: {reg_offset} = {reg_value}"
                    self.after(0, self.status_var.set, status_msg)
                    self.after(0, self.sent_var.set, sent_count)
                    
                    # 根据模式选择发送方法
                    if is_confirm_mode:
                        # 确认模式：等待设备确认
                        result = self.client.send_reg_with_guaranteed_ack(
                            reg_offset, reg_value, timeout=timeout, max_retries=max_retries
                        )
                        total_retries += result["attempts"]
                        
                        if result["success"]:
                            confirmed_count += 1
                            log_entry = (f"✅ [{sent_count:3d}/{total}] {reg_offset}={reg_value} 成功 "
                                       f"(尝试:{result['attempts']}次) "
                                       f"收到确认: {result['actual_response']}")
                        else:
                            failed_count += 1
                            error_detail = result.get('error', 'Unknown error')
                            log_entry = (f"❌ [{sent_count:3d}/{total}] {reg_offset}={reg_value} 失败 "
                                       f"(尝试:{result['attempts']}次) "
                                       f"错误: {error_detail}")
                    else:
                        # 直发模式：只发送不等确认
                        result = self.client.send_reg_direct(reg_offset, reg_value)
                        total_retries += result["attempts"]
                        
                        if result["success"]:
                            confirmed_count += 1  # 直发模式认为发送成功就是确认
                            log_entry = f"✅ [{sent_count:3d}/{total}] {reg_offset}={reg_value} 已发送"
                        else:
                            failed_count += 1
                            error_detail = result.get('error', 'Unknown error')
                            log_entry = f"❌ [{sent_count:3d}/{total}] {reg_offset}={reg_value} 发送失败: {error_detail}"
                    
                    self._detailed_log.append(log_entry)
                    
                    # 更新统计
                    self.after(0, self.confirmed_var.set, confirmed_count)
                    self.after(0, self.failed_var.set, failed_count)
                    
                    if sent_count > 0:
                        ack_rate = f"{confirmed_count/sent_count*100:.1f}%"
                        avg_retry = f"{total_retries/sent_count:.1f}"
                        self.after(0, self.ack_rate_var.set, ack_rate)
                        self.after(0, self.avg_retry_var.set, avg_retry)
                    
                    # 更新速度和预计时间
                    current_time = time.time()
                    if current_time - last_update_time >= 1.0:
                        elapsed = current_time - start_time
                        speed = sent_count / elapsed if elapsed > 0 else 0
                        remaining = total - sent_count
                        eta_seconds = remaining / speed if speed > 0 else 0
                        eta_time = f"{int(eta_seconds//60):02d}:{int(eta_seconds%60):02d}"
                        
                        self.after(0, self.speed_var.set, f"{speed:.1f} reg/s")
                        self.after(0, self.eta_var.set, eta_time)
                        last_update_time = current_time
                    
                    if self._stop_sending:
                        break
                    
                    # 发送间隔
                    time.sleep(interval)
            
            # 完成处理
            elapsed = time.time() - start_time
            avg_speed = sent_count / elapsed if elapsed > 0 else 0
            final_ack_rate = f"{confirmed_count/sent_count*100:.1f}%" if sent_count > 0 else "0%"
            
            # 添加完成日志
            completion_log = (f"📊 时钟频点配置完成 - 模式:{mode_desc} | 总发送:{sent_count} | 成功:{confirmed_count} | 失败:{failed_count} | "
                            f"成功率:{final_ack_rate} | 平均速度:{avg_speed:.1f}reg/s | 总耗时:{elapsed:.1f}秒")
            self._detailed_log.append(completion_log)
            
            if not self._stop_sending:
                if confirmed_count == total:
                    final_msg = f"🎉 时钟频点配置完美完成！{confirmed_count}/{total} (100%) 全部成功！"
                    success_text = "确认成功" if is_confirm_mode else "发送成功"
                    self.after(0, lambda: messagebox.showinfo("配置完成", 
                        f"🎉 所有 {confirmed_count} 个寄存器都{success_text}！\n\n"
                        f"📊 统计信息:\n"
                        f"• 成功率: 100%\n"
                        f"• 发送模式: {mode_desc}\n"
                        f"• 平均速度: {avg_speed:.1f} reg/s\n"
                        f"• 总耗时: {elapsed:.1f} 秒\n\n"
                        f"✅ 时钟频点配置成功完成！"))
                else:
                    final_msg = f"⚠️ 配置完成：成功 {confirmed_count}/{sent_count} ({final_ack_rate}), 失败 {failed_count}"
                    self.after(0, lambda: messagebox.showwarning("配置完成", 
                        f"配置完成，但有部分失败：\n\n"
                        f"📊 统计信息:\n"
                        f"• 已成功: {confirmed_count} 个\n"
                        f"• 失败: {failed_count} 个\n"
                        f"• 成功率: {final_ack_rate}\n"
                        f"• 发送模式: {mode_desc}\n"
                        f"• 平均速度: {avg_speed:.1f} reg/s\n\n"
                        f"⚠️ 请查看详细日志了解失败原因"))
                
                self.after(0, self.status_var.set, final_msg)
                self.after(0, self.speed_var.set, f"{avg_speed:.1f} reg/s")
                self.after(0, self.eta_var.set, "完成")
            else:
                stop_log = f"🛑 配置已停止 - 发送:{sent_count} | 成功:{confirmed_count} | 失败:{failed_count}"
                self._detailed_log.append(stop_log)
                self.after(0, self.status_var.set, f"🛑 已停止：成功 {confirmed_count}, 失败 {failed_count}")
                    
        except Exception as e:
            error_msg = f"❌ 配置异常: {str(e)}"
            self._detailed_log.append(error_msg)
            self.after(0, lambda: messagebox.showerror("配置失败", 
                f"配置过程中出现异常:\n\n{str(e)}\n\n"
                f"已发送: {sent_count}\n"
                f"已成功: {confirmed_count}\n"
                f"失败: {failed_count}"))
            self.after(0, self.status_var.set, error_msg)
        finally:
            self._is_sending = False
            self.after(0, self.send_btn.config, {"state": "normal"})
            self.after(0, self.stop_btn.config, {"state": "disabled"})

    def reset(self):
        """页面重置方法"""
        pass

    def manual_reset(self):
        """手动重置方法"""
        if self._is_sending:
            if messagebox.askyesno("确认", "当前正在发送配置，是否停止并重置？"):
                self._stop_sending = True
                time.sleep(0.1)
            else:
                return
        
        self._reset_stats()
        self.status_var.set("Ready")
        self.file_var.set("")
        self.detected_regs_var.set("未选择文件")
        self.file_size_var.set("--")
        self._detailed_log.clear()
        messagebox.showinfo("重置完成", "页面状态已重置")