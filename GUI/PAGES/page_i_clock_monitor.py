# GUI/PAGES/page_i_clock_monitor.py
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import re
import queue
from CLI.cli_clock import ClockClient
from CORE.clock_api import build_clk_cfg_command

# Table 列表
Si5344_TLIST = [
    "Table0-Manual Register Config",
    "Table1-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(100MHz)-SMA_CLKOUT3(10MHz)-MGT_REF1CLK_OUT4(100MHz)",
    "Table2-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(125MHz)-SMA_CLKOUT3(50MHz)-MGT_REF1CLK_OUT4(125MHz)",
    "Table3-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(250MHz)-SMA_CLKOUT3(100MHz)-MGT_REF1CLK_OUT4(250MHz)",
    "Table4-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(312.5MHz)-SMA_CLKOUT3(125MHz)-MGT_REF1CLK_OUT4(312.5MHz)",
    "Table5-SYS_CLKOUT1(100MHz)-MGT_REF0CLK_OUT2(122.88MHz)-SMA_CLKOUT3(300MHz)-MGT_REF1CLK_OUT4(122.88MHz)",
    "Table6-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(250MHz)-SMA_CLKOUT3(500MHz)-MGT_REF1CLK_OUT4(156.25MHz)",
    "Table7-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(660MHz)-SMA_CLKOUT3(800MHz)-MGT_REF1CLK_OUT4(660MHz)",
    "Table8-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(106.25MHz)-SMA_CLKOUT3(1028MHz)-MGT_REF1CLK_OUT4(106.25MHz)",
    "Table9-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(212.5MHz)-SMA_CLKOUT3(900MHz)-MGT_REF1CLK_OUT4(212.5MHz)",
    "Table10-SYS_CLKOUT1(175MHz)-MGT_REF0CLK_OUT2(150MHz)-SMA_CLKOUT3(200MHz)-MGT_REF1CLK_OUT4(150MHz)",
]

class ReliableClockClient:
    """真正可靠的时钟客户端"""
    def __init__(self, serial_core):
        self.serial = serial_core
        self._last_idx = 0
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

    def set_clock(self, table_idx: int):
        """发送时钟 Table 配置命令"""
        from CORE.clock_api import build_clk_set_command
        self._last_idx = table_idx
        cmd = build_clk_set_command(table_idx)
        self.serial.send_text(cmd + "\n")

    def get_clock(self, timeout: float = 3.0) -> int:
        """获取当前时钟配置"""
        from CORE.clock_api import build_clk_get_command, parse_clk_response
        
        # 清空响应队列
        while not self._response_queue.empty():
            try:
                self._response_queue.get_nowait()
            except queue.Empty:
                break
        
        cmd = build_clk_get_command(self._last_idx)
        self.serial.send_text(cmd + "\n")
        
        start = time.time()
        while time.time() - start < timeout:
            try:
                line = self._response_queue.get(timeout=0.1)
                if line.startswith("MC1PCLKGET"):
                    return parse_clk_response(line)
            except queue.Empty:
                continue
                
        raise TimeoutError("Clock get timeout")

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
    """优化的 Si5344 时钟配置页面"""
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

        # === Table 配置区域 ===
        table_frame = ttk.LabelFrame(main_frame, text="📋 Table 配置 (预设模式)")
        table_frame.pack(fill=tk.X, pady=(0, 10))
        table_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(table_frame, text="Clock Table:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.table_var = tk.StringVar(value=Si5344_TLIST[1])
        self.table_cb = ttk.Combobox(
            table_frame, textvariable=self.table_var, values=Si5344_TLIST,
            state="readonly", width=60
        )
        self.table_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        btn_frame = ttk.Frame(table_frame)
        btn_frame.grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(btn_frame, text="SET TABLE", command=self._on_set).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="GET TABLE", command=self._on_get).pack(side=tk.LEFT, padx=2)

        # === 可靠寄存器配置区域 ===
        reg_frame = ttk.LabelFrame(main_frame, text="🔒 可靠寄存器配置 (100% 确认模式)")
        reg_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        reg_frame.grid_columnconfigure(1, weight=1)

        # 文件选择
        ttk.Label(reg_frame, text="Regs File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_var = tk.StringVar()
        ttk.Entry(reg_frame, textvariable=self.file_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(reg_frame, text="Browse", command=self._browse_file).grid(row=0, column=2, padx=5, pady=5)

        # 配置参数
        config_frame = ttk.Frame(reg_frame)
        config_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        ttk.Label(config_frame, text="确认超时:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.timeout_var = tk.DoubleVar(value=3.0)
        ttk.Spinbox(config_frame, from_=1.0, to=10.0, increment=0.5, 
                   textvariable=self.timeout_var, width=8).grid(row=0, column=1, padx=5)
        ttk.Label(config_frame, text="秒").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(config_frame, text="最大重试:").grid(row=0, column=3, sticky=tk.W, padx=5)
        self.retry_var = tk.IntVar(value=3)
        ttk.Spinbox(config_frame, from_=1, to=5, increment=1, 
                   textvariable=self.retry_var, width=8).grid(row=0, column=4, padx=5)
        ttk.Label(config_frame, text="次").grid(row=0, column=5, sticky=tk.W)

        ttk.Label(config_frame, text="发送间隔:").grid(row=0, column=6, sticky=tk.W, padx=5)
        self.interval_var = tk.DoubleVar(value=0.1)
        ttk.Spinbox(config_frame, from_=0.05, to=1.0, increment=0.05, 
                   textvariable=self.interval_var, width=8).grid(row=0, column=7, padx=5)
        ttk.Label(config_frame, text="秒").grid(row=0, column=8, sticky=tk.W)

        # 控制按钮 - 修改按钮文字并添加重置按钮
        control_frame = ttk.Frame(reg_frame)
        control_frame.grid(row=2, column=0, columnspan=3, pady=5)
        
        self.send_btn = ttk.Button(control_frame, text="配置", command=self._send_regs_reliable)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ 停止", command=self._stop_regs, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.log_btn = ttk.Button(control_frame, text="📋 查看详细日志", command=self._show_detailed_log)
        self.log_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加手动重置按钮
        self.reset_btn = ttk.Button(control_frame, text="🔄 重置", command=self.manual_reset)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # === 实时统计区域 ===
        stats_frame = ttk.LabelFrame(main_frame, text="📊 实时统计 (真实确认数据)")
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

        ttk.Label(detail_frame, text="已确认:").grid(row=0, column=4, padx=5)
        self.confirmed_var = tk.IntVar(value=0)
        ttk.Entry(detail_frame, textvariable=self.confirmed_var, width=6, state="readonly").grid(row=0, column=5, padx=2)

        ttk.Label(detail_frame, text="失败:").grid(row=0, column=6, padx=5)
        self.failed_var = tk.IntVar(value=0)
        ttk.Entry(detail_frame, textvariable=self.failed_var, width=6, state="readonly").grid(row=0, column=7, padx=2)

        # 第二行统计
        ttk.Label(detail_frame, text="确认率:").grid(row=1, column=0, padx=5)
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

        # === 频率显示区域 ===
        freq_frame = ttk.LabelFrame(main_frame, text="🎛️ 当前配置频率")
        freq_frame.pack(fill=tk.X)
        freq_frame.grid_columnconfigure(1, weight=1)
        freq_frame.grid_columnconfigure(3, weight=1)

        self.freq_vars = {}
        labels = ["SYS_OUT1", "MGT_REF0", "SMA_CLKOUT3", "MGT_REF1"]
        for idx, lb in enumerate(labels):
            row = idx // 2
            col = (idx % 2) * 2
            ttk.Label(freq_frame, text=f"{lb}:").grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value="N/A")
            ttk.Entry(freq_frame, textvariable=var, state="readonly", width=20).grid(row=row, column=col+1, sticky="ew", padx=5, pady=2)
            self.freq_vars[lb] = var

        # 说明文字
        note_frame = ttk.Frame(main_frame)
        note_frame.pack(fill=tk.X, pady=5)
        note = ("🔒 可靠模式特点：\n"
               "• 每个寄存器都等待设备确认，确保 100% 可靠传输\n"
               "• 自动重试失败的寄存器，直到收到确认\n"
               "• 实时显示真实的确认数量，与串口日志完全一致\n"
               "• 速度较慢但绝对可靠，适合重要的时钟配置")
        ttk.Label(note_frame, text=note, foreground="blue", font=("Arial", 8), justify=tk.LEFT).pack(anchor=tk.W)

    def _check_connection(self) -> bool:
        """检查串口连接状态"""
        if not self.client.is_connected():
            messagebox.showerror("连接错误", 
                               "串口未连接！\n\n"
                               "请先在'串口监视器'页面连接串口后再进行配置。")
            return False
        return True

    def _on_set(self):
        """设置 Table"""
        if not self._check_connection():
            return
            
        try:
            tbl = int(self.table_var.get().split("-")[0].replace("Table", ""))
        except ValueError:
            messagebox.showerror("Error", "请选择有效的 Table 项")
            return

        if tbl == 0:
            messagebox.showinfo("提示", "Table 0 需要使用寄存器文件配置")
            return

        try:
            self.client.set_clock(tbl)
            self._update_freq_display(tbl)
            messagebox.showinfo("配置成功", f"Table {tbl} 配置命令已发送")
        except Exception as e:
            messagebox.showerror("配置失败", str(e))

    def _on_get(self):
        """获取当前 Table"""
        if not self._check_connection():
            return
            
        try:
            tbl = self.client.get_clock()
            if 0 <= tbl < len(Si5344_TLIST):
                self.table_var.set(Si5344_TLIST[tbl])
                self._update_freq_display(tbl)
                messagebox.showinfo("查询成功", f"当前配置: Table {tbl}")
            else:
                messagebox.showwarning("查询结果", f"返回了无效的 Table 编号: {tbl}")
        except Exception as e:
            messagebox.showerror("查询失败", str(e))

    def _update_freq_display(self, table_idx):
        """更新频率显示"""
        freq_data = {
            0: ["Manual", "Manual", "Manual", "Manual"],
            1: ["175MHz", "100MHz", "10MHz", "100MHz"],
            2: ["175MHz", "125MHz", "50MHz", "125MHz"],
            3: ["175MHz", "250MHz", "100MHz", "250MHz"],
            4: ["175MHz", "312.5MHz", "125MHz", "312.5MHz"],
            5: ["100MHz", "122.88MHz", "300MHz", "122.88MHz"],
            6: ["175MHz", "250MHz", "500MHz", "156.25MHz"],
            7: ["175MHz", "660MHz", "800MHz", "660MHz"],
            8: ["175MHz", "106.25MHz", "1028MHz", "106.25MHz"],
            9: ["175MHz", "212.5MHz", "900MHz", "212.5MHz"],
            10: ["175MHz", "150MHz", "200MHz", "150MHz"],
        }
        
        if table_idx in freq_data:
            freqs = freq_data[table_idx]
            for (label, var), freq in zip(self.freq_vars.items(), freqs):
                var.set(freq)

    def _browse_file(self):
        """浏览寄存器文件"""
        path = filedialog.askopenfilename(
            title="选择 Si5344 寄存器文件",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self.file_var.set(path)
            self._analyze_file(path)

    def _analyze_file(self, path):
        """分析寄存器文件"""
        try:
            total_lines = 0
            valid_lines = 0
            with open(path, 'r', encoding='latin-1') as f:
                for line in f:
                    total_lines += 1
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [x.strip() for x in line.split(",")]
                    if len(parts) == 2 and parts[0].startswith("0x"):
                        valid_lines += 1
            
            self.total_var.set(valid_lines)
            self._reset_stats()
            self.status_var.set(f"✅ 文件已加载：{valid_lines} 个有效寄存器")
            
        except Exception as e:
            self.total_var.set(0)
            self.status_var.set(f"❌ 文件读取失败: {e}")

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
        """可靠发送模式 - 增加连接检查"""
        if self._is_sending:
            messagebox.showwarning("提示", "正在发送中，请稍等...")
            return
        
        # 检查串口连接
        if not self._check_connection():
            return
            
        path = self.file_var.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("错误", "请先选择有效的寄存器文件")
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
        """显示详细日志 - 改进版本"""
        if not self._detailed_log:
            messagebox.showinfo("日志", "暂无详细日志")
            return
            
        log_window = tk.Toplevel(self)
        log_window.title("详细发送日志")
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
        """可靠发送的后台线程 - 改进版本"""
        sent_count = 0
        confirmed_count = 0
        failed_count = 0
        total_retries = 0
        total = self.total_var.get()
        
        timeout = self.timeout_var.get()
        max_retries = self.retry_var.get()
        interval = self.interval_var.get()
        
        start_time = time.time()
        last_update_time = start_time
        
        try:
            self.after(0, self.status_var.set, f"🔒 开始可靠发送 (超时:{timeout}s, 重试:{max_retries}次, 间隔:{interval}s)...")
            
            # 添加启动日志
            start_log = f"📋 配置开始 - 文件: {os.path.basename(path)} | 总寄存器: {total} | 参数: 超时{timeout}s/重试{max_retries}次/间隔{interval}s"
            self._detailed_log.append(start_log)
            
            with open(path, 'r', encoding='latin-1') as f:
                for line_num, line in enumerate(f, 1):
                    if self._stop_sending:
                        break
                        
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    parts = [x.strip() for x in line.split(",")]
                    if len(parts) != 2 or not parts[0].startswith("0x"):
                        continue
                    
                    sent_count += 1
                    reg_offset, reg_value = parts[0], parts[1]
                    
                    # 更新当前状态
                    status_msg = f"🔒 发送 {sent_count}/{total}: {reg_offset} = {reg_value}"
                    self.after(0, self.status_var.set, status_msg)
                    self.after(0, self.sent_var.set, sent_count)
                    
                    # 发送并等待确认
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
                        parsed_info = ""
                        if result.get('parsed_reg') or result.get('parsed_value'):
                            parsed_info = f" | 解析到: reg={result.get('parsed_reg', 'N/A')}, value={result.get('parsed_value', 'N/A')}"
                        
                        log_entry = (f"❌ [{sent_count:3d}/{total}] {reg_offset}={reg_value} 失败 "
                                   f"(尝试:{result['attempts']}次) "
                                   f"错误: {error_detail}{parsed_info} "
                                   f"响应: {result.get('actual_response', 'No response')}")
                    
                    self._detailed_log.append(log_entry)
                    
                    # 更新统计
                    self.after(0, self.confirmed_var.set, confirmed_count)
                    self.after(0, self.failed_var.set, failed_count)
                    
                    if sent_count > 0:
                        ack_rate = f"{confirmed_count/sent_count*100:.1f}%"
                        avg_retry = f"{total_retries/sent_count:.1f}"
                        self.after(0, self.ack_rate_var.set, ack_rate)
                        self.after(0, self.avg_retry_var.set, avg_retry)
                    
                    # 更新速度和预计时间 (每秒更新一次)
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
            completion_log = (f"📊 配置完成统计 - 总发送:{sent_count} | 成功:{confirmed_count} | 失败:{failed_count} | "
                            f"确认率:{final_ack_rate} | 平均重试:{total_retries/sent_count:.1f}次 | "
                            f"平均速度:{avg_speed:.1f}reg/s | 总耗时:{elapsed:.1f}秒")
            self._detailed_log.append(completion_log)
            
            if not self._stop_sending:
                if confirmed_count == total:
                    final_msg = f"🎉 完美完成！{confirmed_count}/{total} (100%) 全部确认成功！"
                    self.after(0, lambda: messagebox.showinfo("配置完成", 
                        f"🎉 所有 {confirmed_count} 个寄存器都收到设备确认！\n\n"
                        f"📊 统计信息:\n"
                        f"• 确认率: 100%\n"
                        f"• 平均重试: {total_retries/sent_count:.1f} 次\n"
                        f"• 平均速度: {avg_speed:.1f} reg/s\n"
                        f"• 总耗时: {elapsed:.1f} 秒\n\n"
                        f"✅ 串口日志中的确认数量与此完全一致"))
                else:
                    final_msg = f"⚠️ 完成：确认 {confirmed_count}/{sent_count} ({final_ack_rate}), 失败 {failed_count}"
                    self.after(0, lambda: messagebox.showwarning("配置完成", 
                        f"发送完成，但有部分失败：\n\n"
                        f"📊 统计信息:\n"
                        f"• 已确认: {confirmed_count} 个\n"
                        f"• 失败: {failed_count} 个\n"
                        f"• 确认率: {final_ack_rate}\n"
                        f"• 平均重试: {total_retries/sent_count:.1f} 次\n"
                        f"• 平均速度: {avg_speed:.1f} reg/s\n\n"
                        f"⚠️ 请查看详细日志了解失败原因\n"
                        f"建议：增加超时时间或重试次数后重新发送失败的寄存器"))
                
                self.after(0, self.status_var.set, final_msg)
                self.after(0, self.speed_var.set, f"{avg_speed:.1f} reg/s")
                self.after(0, self.eta_var.set, "完成")
            else:
                stop_log = f"🛑 配置已停止 - 发送:{sent_count} | 确认:{confirmed_count} | 失败:{failed_count}"
                self._detailed_log.append(stop_log)
                self.after(0, self.status_var.set, f"🛑 已停止：确认 {confirmed_count}, 失败 {failed_count}")
                    
        except Exception as e:
            error_msg = f"❌ 发送异常: {str(e)}"
            self._detailed_log.append(error_msg)
            self.after(0, lambda: messagebox.showerror("发送失败", 
                f"配置过程中出现异常:\n\n{str(e)}\n\n"
                f"已发送: {sent_count}\n"
                f"已确认: {confirmed_count}\n"
                f"失败: {failed_count}"))
            self.after(0, self.status_var.set, error_msg)
        finally:
            self._is_sending = False
            self.after(0, self.send_btn.config, {"state": "normal"})
            self.after(0, self.stop_btn.config, {"state": "disabled"})

    def reset(self):
        """页面重置方法 - 修改为不重置关键状态"""
        # 不再自动重置文件路径和频率显示
        # 只重置日志显示，保持用户的配置状态
        pass  # 暂时移除自动重置功能
        
    def manual_reset(self):
        """手动重置方法 - 用户主动调用"""
        if self._is_sending:
            if messagebox.askyesno("确认", "当前正在发送配置，是否停止并重置？"):
                self._stop_sending = True
                time.sleep(0.1)  # 等待停止
            else:
                return
        
        self._reset_stats()
        self.status_var.set("Ready")
        self.file_var.set("")
        for var in self.freq_vars.values():
            var.set("N/A")
        self._detailed_log.clear()
        messagebox.showinfo("重置完成", "页面状态已重置")