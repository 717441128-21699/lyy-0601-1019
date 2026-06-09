import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import sys
import os
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import (
    ProjectInfo,
    MaterialList,
    TemplateGenerator,
    ContentValidator,
    PackageOutput,
    RecordManager,
    SubmissionPreview
)
from config import TRADING_SCENARIOS as SCENES, UPDATE_FREQUENCIES, REQUIRED_MATERIALS, OUTPUT_DIR


class DataTradingToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("数据要素交易材料生成自动化工具")
        self.root.geometry("1150x800")
        self.root.minsize(1050, 750)

        self.project_info = ProjectInfo()
        self.material_list = MaterialList()
        self.record_manager = RecordManager()
        self.generated_files = {}
        self.validation_result = None
        self.package_result = None
        self.submission_preview = None
        self.current_step = 0
        self._status_frame_widgets = {}
        self._fields_tree = None

        self.material_list.on_change_callback = self._on_materials_change

        self.project_name_var = tk.StringVar()
        self.project_code_var = tk.StringVar()
        self.project_id_var = tk.StringVar(value=self.project_info.project_id)
        self.source_var = tk.StringVar()
        self.freq_var = tk.StringVar()
        self.scene_var = tk.StringVar()
        self.contact_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.valid_from_var = tk.StringVar()
        self.valid_to_var = tk.StringVar()
        self.volume_var = tk.StringVar()

        self.steps = [
            ("项目信息", self._create_step1),
            ("材料清单", self._create_step2),
            ("模板生成", self._create_step3),
            ("内容校验", self._create_step4),
            ("打包输出", self._create_step5)
        ]

        self._setup_styles()
        self._create_main_layout()

    def _on_materials_change(self):
        if hasattr(self, 'materials_tree') and self.materials_tree.winfo_exists():
            self._refresh_materials_tree()
        if hasattr(self, '_status_frame_widgets') and self._status_frame_widgets:
            self._refresh_material_status()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Step.TFrame", background="#f5f7fa")
        style.configure("Nav.TButton", padding=10, font=('Microsoft YaHei', 10))
        style.configure("Primary.TButton", padding=10, font=('Microsoft YaHei', 10, 'bold'),
                        background="#4472C4", foreground="white")
        style.map("Primary.TButton",
                  background=[('active', '#335EA8'), ('disabled', '#B0B0B0')])
        style.configure("Success.TButton", padding=10, font=('Microsoft YaHei', 10, 'bold'),
                        background="#00B050", foreground="white")
        style.map("Success.TButton",
                  background=[('active', '#009040'), ('disabled', '#B0B0B0')])
        style.configure("StepIndicator.TLabel", font=('Microsoft YaHei', 10),
                        background="#f5f7fa", padding=10)
        style.configure("StepIndicator.Active.TLabel", font=('Microsoft YaHei', 10, 'bold'),
                        background="#4472C4", foreground="white", padding=10)
        style.configure("StepIndicator.Completed.TLabel", font=('Microsoft YaHei', 10),
                        background="#00B050", foreground="white", padding=10)
        style.configure("Section.TLabelframe", font=('Microsoft YaHei', 11, 'bold'))
        style.configure("Section.TLabelframe.Label", font=('Microsoft YaHei', 11, 'bold'))
        style.configure("Batch.TLabelframe", font=('Microsoft YaHei', 10, 'bold'),
                        bordercolor="#4472C4")
        style.configure("Batch.TLabelframe.Label", font=('Microsoft YaHei', 10, 'bold'),
                        foreground="#4472C4")

    def _create_main_layout(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header = ttk.Frame(main_container)
        header.pack(fill=tk.X, pady=(0, 10))
        title = ttk.Label(header, text="数据要素交易材料生成自动化工具",
                         font=('Microsoft YaHei', 18, 'bold'))
        title.pack(side=tk.LEFT)
        subtitle = ttk.Label(header, text="   按平台要求整理上架资料",
                            font=('Microsoft YaHei', 10), foreground="#666")
        subtitle.pack(side=tk.LEFT, padx=10)
        self.step_counter = ttk.Label(header, text=f"步骤 {self.current_step + 1}/{len(self.steps)}",
                                     font=('Microsoft YaHei', 10))
        self.step_counter.pack(side=tk.RIGHT)

        steps_container = ttk.Frame(main_container)
        steps_container.pack(fill=tk.X, pady=(0, 10))
        self.step_labels = []
        for i, (name, _) in enumerate(self.steps):
            lbl = ttk.Label(steps_container, text=f"{i + 1}. {name}",
                           style="StepIndicator.TLabel")
            lbl.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.step_labels.append(lbl)
            if i < len(self.steps) - 1:
                line = ttk.Separator(steps_container, orient='horizontal')
                line.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self._update_step_indicators()

        content_container = ttk.Frame(main_container, style="Step.TFrame")
        content_container.pack(fill=tk.BOTH, expand=True)
        self.content_container = content_container

        nav_container = ttk.Frame(main_container)
        nav_container.pack(fill=tk.X, pady=(10, 0))

        self.prev_btn = ttk.Button(nav_container, text="上一步", command=self._prev_step,
                                  style="Nav.TButton", state="disabled")
        self.prev_btn.pack(side=tk.LEFT)

        records_btn = ttk.Button(nav_container, text="查看历史记录", command=self._show_records,
                                style="Nav.TButton")
        records_btn.pack(side=tk.LEFT, padx=10)

        self.next_btn = ttk.Button(nav_container, text="下一步", command=self._next_step,
                                  style="Primary.TButton")
        self.next_btn.pack(side=tk.RIGHT)

        self._show_current_step()

    def _update_step_indicators(self):
        for i, lbl in enumerate(self.step_labels):
            if i < self.current_step:
                lbl.configure(style="StepIndicator.Completed.TLabel")
                lbl.configure(text=f"✓ {self.steps[i][0]}")
            elif i == self.current_step:
                lbl.configure(style="StepIndicator.Active.TLabel")
                lbl.configure(text=f"{i + 1}. {self.steps[i][0]}")
            else:
                lbl.configure(style="StepIndicator.TLabel")
                lbl.configure(text=f"{i + 1}. {self.steps[i][0]}")
        self.step_counter.configure(text=f"步骤 {self.current_step + 1}/{len(self.steps)}")

    def _show_current_step(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()
        _, create_func = self.steps[self.current_step]
        create_func()
        self._update_step_indicators()
        self.prev_btn.configure(state="normal" if self.current_step > 0 else "disabled")
        if self.current_step == len(self.steps) - 1:
            self.next_btn.configure(text="完成", command=self._finish)
        else:
            self.next_btn.configure(text="下一步", command=self._next_step)

    def _next_step(self):
        if self.current_step == 0:
            if not self._validate_step1():
                return
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._show_current_step()

    def _prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._show_current_step()

    def _finish(self):
        if messagebox.askyesno("完成", "是否完成全部操作并记录本次生成？"):
            if self.package_result and self.package_result.get("success"):
                self.record_manager.save_record(
                    self.project_info,
                    self.material_list,
                    self.generated_files,
                    self.validation_result.to_dict() if self.validation_result else {},
                    self.package_result.get("zip_path", ""),
                    self.material_list.current_batch_id or ""
                )
                messagebox.showinfo("成功", f"材料生成完成！\n\n压缩包路径：{self.package_result.get('zip_path')}\n\n记录已保存。")
            self.root.destroy()

    def _create_step1(self):
        canvas = tk.Canvas(self.content_container, bg="#f5f7fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Step.TFrame")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", padx=5, pady=5)

        basic_frame = ttk.LabelFrame(scrollable_frame, text="基本信息", style="Section.TLabelframe", padding=15)
        basic_frame.pack(fill=tk.X, padx=10, pady=10)

        self._create_label_entry_with_var(basic_frame, "项目编号", 0, 0,
                                        self.project_id_var,
                                        lambda v: setattr(self.project_info, 'project_id', v),
                                        state="readonly")
        self._create_label_entry_with_var(basic_frame, "数据产品名称 *", 0, 2,
                                        self.project_name_var,
                                        lambda v: setattr(self.project_info, 'product_name', v))
        self._create_label_entry_with_var(basic_frame, "产品编码", 1, 0,
                                        self.project_code_var,
                                        lambda v: setattr(self.project_info, 'product_code', v))
        self._create_label_entry_with_var(basic_frame, "数据来源 *", 1, 2,
                                        self.source_var,
                                        lambda v: setattr(self.project_info, 'data_source', v))
        self._create_label_combobox_with_var(basic_frame, "更新频率 *", 2, 0,
                                            UPDATE_FREQUENCIES,
                                            self.freq_var,
                                            lambda v: setattr(self.project_info, 'update_frequency', v))
        self._create_label_combobox_with_var(basic_frame, "交易场景 *", 2, 2,
                                            SCENES,
                                            self.scene_var,
                                            lambda v: setattr(self.project_info, 'scene', v))
        self._create_label_entry_with_var(basic_frame, "数据量级", 3, 0,
                                        self.volume_var,
                                        lambda v: setattr(self.project_info, 'data_volume', v))

        desc_frame = ttk.LabelFrame(scrollable_frame, text="产品描述", style="Section.TLabelframe", padding=15)
        desc_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(desc_frame, text="详细描述：").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.desc_text = scrolledtext.ScrolledText(desc_frame, height=5, font=('Microsoft YaHei', 10))
        self.desc_text.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        if self.project_info.data_description:
            self.desc_text.insert(tk.END, self.project_info.data_description)
        self.desc_text.bind('<KeyRelease>', lambda e: setattr(self.project_info, 'data_description',
                                                            self.desc_text.get("1.0", tk.END).strip()))
        desc_frame.columnconfigure(1, weight=1)
        desc_frame.columnconfigure(2, weight=1)

        usage_frame = ttk.LabelFrame(scrollable_frame, text="使用限制", style="Section.TLabelframe", padding=15)
        usage_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(usage_frame, text="使用限制说明：").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.limits_text = scrolledtext.ScrolledText(usage_frame, height=4, font=('Microsoft YaHei', 10))
        self.limits_text.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        if self.project_info.usage_limits:
            self.limits_text.insert(tk.END, self.project_info.usage_limits)
        self.limits_text.bind('<KeyRelease>', lambda e: setattr(self.project_info, 'usage_limits',
                                                               self.limits_text.get("1.0", tk.END).strip()))
        usage_frame.columnconfigure(1, weight=1)
        usage_frame.columnconfigure(2, weight=1)

        contact_frame = ttk.LabelFrame(scrollable_frame, text="联系信息", style="Section.TLabelframe", padding=15)
        contact_frame.pack(fill=tk.X, padx=10, pady=10)
        self._create_label_entry_with_var(contact_frame, "联系人 *", 0, 0,
                                        self.contact_var,
                                        lambda v: setattr(self.project_info, 'contact_person', v))
        self._create_label_entry_with_var(contact_frame, "联系电话 *", 0, 2,
                                        self.phone_var,
                                        lambda v: setattr(self.project_info, 'contact_phone', v))
        self._create_label_entry_with_var(contact_frame, "电子邮箱", 1, 0,
                                        self.email_var,
                                        lambda v: setattr(self.project_info, 'contact_email', v))

        validity_frame = ttk.LabelFrame(scrollable_frame, text="授权有效期", style="Section.TLabelframe", padding=15)
        validity_frame.pack(fill=tk.X, padx=10, pady=10)
        self._create_label_entry_with_var(validity_frame, "有效期开始 * (YYYY-MM-DD)", 0, 0,
                                        self.valid_from_var,
                                        lambda v: setattr(self.project_info, 'valid_from', v))
        self._create_label_entry_with_var(validity_frame, "有效期截止 * (YYYY-MM-DD)", 0, 2,
                                        self.valid_to_var,
                                        lambda v: setattr(self.project_info, 'valid_to', v))

        fields_frame = ttk.LabelFrame(scrollable_frame, text="样例字段", style="Section.TLabelframe", padding=15)
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fields_tree = ttk.Treeview(fields_frame, columns=("name", "type", "desc", "sample"), show="headings", height=5)
        self.fields_tree.heading("name", text="字段名称")
        self.fields_tree.heading("type", text="字段类型")
        self.fields_tree.heading("desc", text="描述")
        self.fields_tree.heading("sample", text="样例值")
        self.fields_tree.column("name", width=150)
        self.fields_tree.column("type", width=100)
        self.fields_tree.column("desc", width=200)
        self.fields_tree.column("sample", width=150)
        self.fields_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        for field in self.project_info.sample_fields:
            self.fields_tree.insert("", tk.END, values=(
                field.get("field_name", ""),
                field.get("field_type", ""),
                field.get("description", ""),
                field.get("sample_value", "")
            ))

        btn_frame = ttk.Frame(fields_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="添加字段", command=self._add_field_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除字段", command=self._remove_field).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导入示例字段", command=self._load_sample_fields).pack(side=tk.LEFT, padx=5)

        scrollable_frame.columnconfigure(0, weight=1)
        basic_frame.columnconfigure(1, weight=1)
        basic_frame.columnconfigure(3, weight=1)
        contact_frame.columnconfigure(1, weight=1)
        contact_frame.columnconfigure(3, weight=1)
        validity_frame.columnconfigure(1, weight=1)
        validity_frame.columnconfigure(3, weight=1)

    def _create_label_entry(self, parent, label, row, col, value, callback):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky=tk.W, pady=8, padx=5)
        var = tk.StringVar(value=value)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=col + 1, sticky=tk.EW, pady=8, padx=5)
        var.trace_add('write', lambda *args: callback(var.get()))

    def _create_label_combobox(self, parent, label, row, col, values, value, callback):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky=tk.W, pady=8, padx=5)
        var = tk.StringVar(value=value)
        cb = ttk.Combobox(parent, values=values, textvariable=var, state="readonly")
        cb.grid(row=row, column=col + 1, sticky=tk.EW, pady=8, padx=5)
        var.trace_add('write', lambda *args: callback(var.get()))

    def _create_label_entry_with_var(self, parent, label, row, col, var, callback, state="normal"):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky=tk.W, pady=8, padx=5)
        entry = ttk.Entry(parent, textvariable=var, state=state)
        entry.grid(row=row, column=col + 1, sticky=tk.EW, pady=8, padx=5)
        var.trace_add('write', lambda *args: callback(var.get()))

    def _create_label_combobox_with_var(self, parent, label, row, col, values, var, callback):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky=tk.W, pady=8, padx=5)
        cb = ttk.Combobox(parent, values=values, textvariable=var, state="readonly")
        cb.grid(row=row, column=col + 1, sticky=tk.EW, pady=8, padx=5)
        var.trace_add('write', lambda *args: callback(var.get()))

    def _add_field_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加字段")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="字段名称：").pack(pady=(20, 5))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).pack()

        ttk.Label(dialog, text="字段类型：").pack(pady=(10, 5))
        type_var = tk.StringVar(value="string")
        type_cb = ttk.Combobox(dialog, values=["string", "int", "float", "datetime", "boolean", "text"],
                              textvariable=type_var, state="readonly", width=28)
        type_cb.pack()

        ttk.Label(dialog, text="字段描述：").pack(pady=(10, 5))
        desc_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=desc_var, width=30).pack()

        ttk.Label(dialog, text="样例值：").pack(pady=(10, 5))
        sample_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=sample_var, width=30).pack()

        def save():
            if not name_var.get():
                messagebox.showerror("错误", "请输入字段名称")
                return
            self.project_info.add_sample_field(
                name_var.get(), type_var.get(), desc_var.get(), sample_var.get()
            )
            self.fields_tree.insert("", tk.END, values=(
                name_var.get(), type_var.get(), desc_var.get(), sample_var.get()
            ))
            dialog.destroy()

        ttk.Button(dialog, text="保存", command=save, style="Primary.TButton").pack(pady=20)

    def _remove_field(self):
        selected = self.fields_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要删除的字段")
            return
        for item in selected:
            values = self.fields_tree.item(item, 'values')
            self.fields_tree.delete(item)
            self.project_info.sample_fields = [
                f for f in self.project_info.sample_fields
                if f.get("field_name") != values[0]
            ]

    def _load_sample_fields(self):
        sample_fields = [
            {"field_name": "用户ID", "field_type": "string", "description": "用户唯一标识", "sample_value": "U100001"},
            {"field_name": "注册时间", "field_type": "datetime", "description": "用户注册时间", "sample_value": "2024-01-15 10:30:00"},
            {"field_name": "地区", "field_type": "string", "description": "用户所在地区", "sample_value": "北京市朝阳区"},
            {"field_name": "年龄段", "field_type": "string", "description": "用户年龄段划分", "sample_value": "25-34"},
            {"field_name": "消费等级", "field_type": "int", "description": "消费能力等级1-5", "sample_value": "3"}
        ]
        self.project_info.sample_fields = sample_fields
        for i in self.fields_tree.get_children():
            self.fields_tree.delete(i)
        for field in sample_fields:
            self.fields_tree.insert("", tk.END, values=(
                field.get("field_name", ""),
                field.get("field_type", ""),
                field.get("description", ""),
                field.get("sample_value", "")
            ))

    def _validate_step1(self):
        errors = self.project_info.validate_basic()
        if errors:
            messagebox.showerror("校验失败", "\n".join(errors))
            return False
        if not self.project_info.contact_person:
            messagebox.showwarning("提示", "请填写联系人信息，否则后续校验会报错")
        if not self.project_info.valid_from or not self.project_info.valid_to:
            messagebox.showwarning("提示", "请填写授权有效期，否则后续校验会报错")
        return True

    def _create_step2(self):
        main_frame = ttk.Frame(self.content_container, style="Step.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(main_frame, text="材料清单管理",
                 font=('Microsoft YaHei', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(main_frame,
                 text="根据平台要求，上架数据产品需要准备以下材料。请上传用户提供的材料，系统将自动生成可生成的材料。",
                 foreground="#666").pack(anchor=tk.W, pady=(0, 15))

        columns = ("code", "name", "required", "status", "source", "batch", "file")
        self.materials_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=10)
        self.materials_tree.heading("code", text="编码")
        self.materials_tree.heading("name", text="材料名称")
        self.materials_tree.heading("required", text="必填")
        self.materials_tree.heading("status", text="状态")
        self.materials_tree.heading("source", text="来源")
        self.materials_tree.heading("batch", text="批次")
        self.materials_tree.heading("file", text="文件路径")
        self.materials_tree.column("code", width=80, anchor=tk.CENTER)
        self.materials_tree.column("name", width=160)
        self.materials_tree.column("required", width=60, anchor=tk.CENTER)
        self.materials_tree.column("status", width=90, anchor=tk.CENTER)
        self.materials_tree.column("source", width=90, anchor=tk.CENTER)
        self.materials_tree.column("batch", width=130, anchor=tk.CENTER)
        self.materials_tree.column("file", width=280)
        self.materials_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        self._refresh_materials_tree()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="上传材料", command=self._upload_material, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="移除材料", command=self._remove_material, style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="打开文件", command=self._open_material_file, style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        status_frame = ttk.LabelFrame(main_frame, text="材料统计", style="Section.TLabelframe", padding=15)
        status_frame.pack(fill=tk.X, pady=15)
        self._status_frame_widgets["frame"] = status_frame

        self._status_frame_widgets["status_label"] = ttk.Label(status_frame, text="",
                                                               font=('Microsoft YaHei', 11, 'bold'))
        self._status_frame_widgets["status_label"].pack(anchor=tk.W)

        self._status_frame_widgets["missing_label"] = ttk.Label(status_frame, text="", foreground="#FF0000")
        self._status_frame_widgets["missing_label"].pack(anchor=tk.W, pady=5)

        self._status_frame_widgets["info_label"] = ttk.Label(status_frame, text="", foreground="#666")
        self._status_frame_widgets["info_label"].pack(anchor=tk.W, pady=5)

        self._refresh_material_status()

    def _refresh_materials_tree(self):
        if not hasattr(self, 'materials_tree') or not self.materials_tree.winfo_exists():
            return
        for i in self.materials_tree.get_children():
            self.materials_tree.delete(i)
        for item in self.material_list.items:
            status = "已准备" if item.provided or item.generated else "未准备"
            source = "自动生成" if item.generated else ("用户上传" if item.provided else "-")
            required = "是" if item.required else "否"
            file_path = item.file_path if item.file_path else "-"
            batch = item.batch_id if item.batch_id else "-"
            tags = ()
            if item.required and not item.provided and not item.generated:
                tags = ("missing",)
            self.materials_tree.insert("", tk.END, values=(
                item.code, item.name, required, status, source, batch, file_path
            ), tags=tags)
        self.materials_tree.tag_configure("missing", background="#FFEBEB")

    def _refresh_material_status(self):
        if not self._status_frame_widgets:
            return
        summary = self.material_list.get_summary()
        status_text = (
            f"材料总数：{summary['total']}   |   "
            f"必填材料：{summary['required']}   |   "
            f"已提供：{summary['provided']}   |   "
            f"自动生成：{summary['generated']}   |   "
            f"缺失必填：{summary['missing_required']}   |   "
            f"批次数量：{summary.get('batch_count', 0)}"
        )
        status_color = "#00B050" if summary["complete"] else "#FF0000"
        if "status_label" in self._status_frame_widgets and self._status_frame_widgets["status_label"].winfo_exists():
            self._status_frame_widgets["status_label"].configure(text=status_text, foreground=status_color)

        if not summary["complete"]:
            missing = self.material_list.get_missing_required()
            missing_names = "、".join([f"{m.name}({m.code})" for m in missing])
            if "missing_label" in self._status_frame_widgets and self._status_frame_widgets["missing_label"].winfo_exists():
                self._status_frame_widgets["missing_label"].configure(text=f"缺失必填材料：{missing_names}")
            if "info_label" in self._status_frame_widgets and self._status_frame_widgets["info_label"].winfo_exists():
                self._status_frame_widgets["info_label"].configure(
                    text="说明：CPMS(产品说明)、SQMS(授权说明)、YLDQ(样例字段清单) 将在下一步自动生成，其他必填材料需在此处上传。"
                )
        else:
            if "missing_label" in self._status_frame_widgets and self._status_frame_widgets["missing_label"].winfo_exists():
                self._status_frame_widgets["missing_label"].configure(text="✓ 所有必填材料已准备齐全", foreground="#00B050")
            if "info_label" in self._status_frame_widgets and self._status_frame_widgets["info_label"].winfo_exists():
                self._status_frame_widgets["info_label"].configure(text="")

    def _upload_material(self):
        selected = self.materials_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要上传的材料")
            return
        item = self.materials_tree.item(selected[0])
        code = item['values'][0]
        if code in ["CPMS", "SQMS", "YLDQ"]:
            messagebox.showinfo("提示", "此材料将在下一步由系统自动生成，无需手动上传")
            return
        file_path = filedialog.askopenfilename(
            title="选择材料文件",
            filetypes=[("所有文件", "*.*"), ("Word文档", "*.docx"), ("PDF文档", "*.pdf"),
                      ("Excel文档", "*.xlsx"), ("图片", "*.png;*.jpg;*.jpeg")]
        )
        if file_path:
            self.material_list.mark_provided(code, file_path)

    def _remove_material(self):
        selected = self.materials_tree.selection()
        if not selected:
            return
        item = self.materials_tree.item(selected[0])
        code = item['values'][0]
        mat_item = self.material_list.get_item(code)
        if mat_item and mat_item.generated:
            messagebox.showinfo("提示", "自动生成的材料无法在此移除，请在模板生成步骤管理")
            return
        if self.material_list.remove_material(code):
            messagebox.showinfo("成功", f"材料 {code} 已移除")

    def _open_material_file(self):
        selected = self.materials_tree.selection()
        if not selected:
            return
        item = self.materials_tree.item(selected[0])
        file_path = item['values'][6]
        if file_path and file_path != "-" and Path(file_path).exists():
            try:
                if sys.platform.startswith('win'):
                    os.startfile(file_path)
                elif sys.platform == 'darwin':
                    os.system(f'open "{file_path}"')
                else:
                    os.system(f'xdg-open "{file_path}"')
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件：{str(e)}")
        else:
            messagebox.showwarning("提示", "文件不存在或未上传")

    def _create_step3(self):
        main_frame = ttk.Frame(self.content_container, style="Step.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(main_frame, text="模板生成 - 批次管理",
                 font=('Microsoft YaHei', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(main_frame,
                 text="系统将根据您填写的项目信息，自动生成文档。支持批次管理，可选择生成策略。",
                 foreground="#666").pack(anchor=tk.W, pady=(0, 15))

        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_panel = ttk.Frame(main_frame, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)

        options_frame = ttk.LabelFrame(left_panel, text="生成选项", style="Section.TLabelframe", padding=15)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(options_frame, text="批次名称：").grid(row=0, column=0, sticky=tk.W, pady=8, padx=5)
        self.batch_name_var = tk.StringVar(value=f"批次_{datetime.now().strftime('%Y%m%d_%H%M')}")
        ttk.Entry(options_frame, textvariable=self.batch_name_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=8, padx=5)

        ttk.Label(options_frame, text="生成策略：").grid(row=1, column=0, sticky=tk.W, pady=8, padx=5)
        self.strategy_var = tk.StringVar(value="overwrite")
        strategy_frame = ttk.Frame(options_frame)
        strategy_frame.grid(row=1, column=1, sticky=tk.W, pady=8, padx=5)
        ttk.Radiobutton(strategy_frame, text="覆盖已有文件", variable=self.strategy_var, value="overwrite").pack(anchor=tk.W)
        ttk.Radiobutton(strategy_frame, text="另存为新版本", variable=self.strategy_var, value="new_version").pack(anchor=tk.W)
        ttk.Radiobutton(strategy_frame, text="仅更新选中材料", variable=self.strategy_var, value="update_selected").pack(anchor=tk.W)

        ttk.Label(options_frame, text="选择材料：").grid(row=2, column=0, sticky=tk.W, pady=8, padx=5)
        materials_frame = ttk.Frame(options_frame)
        materials_frame.grid(row=2, column=1, sticky=tk.W, pady=8, padx=5)
        self.gen_cpms = tk.BooleanVar(value=True)
        self.gen_sqms = tk.BooleanVar(value=True)
        self.gen_yldq = tk.BooleanVar(value=True)
        ttk.Checkbutton(materials_frame, text="产品说明 (CPMS)", variable=self.gen_cpms).pack(anchor=tk.W)
        ttk.Checkbutton(materials_frame, text="授权说明 (SQMS)", variable=self.gen_sqms).pack(anchor=tk.W)
        ttk.Checkbutton(materials_frame, text="样例字段清单 (YLDQ)", variable=self.gen_yldq).pack(anchor=tk.W)

        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="开始生成", command=self._generate_templates, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="打开输出目录", command=self._open_output_dir, style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="查看当前批次", command=self._view_current_batch, style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(left_panel, text="生成日志", style="Section.TLabelframe", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.gen_log = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 10))
        self.gen_log.pack(fill=tk.BOTH, expand=True)
        self.gen_log.insert(tk.END, "点击【开始生成】按钮，系统将按选定策略生成文档...\n")
        self.gen_log.configure(state="disabled")

        batch_frame = ttk.LabelFrame(right_panel, text="批次列表", style="Batch.TLabelframe", padding=10)
        batch_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("batch_id", "batch_name", "count", "strategy", "time")
        self.batch_tree = ttk.Treeview(batch_frame, columns=columns, show="headings", height=8)
        self.batch_tree.heading("batch_id", text="批次ID")
        self.batch_tree.heading("batch_name", text="批次名称")
        self.batch_tree.heading("count", text="文件数")
        self.batch_tree.heading("strategy", text="策略")
        self.batch_tree.heading("time", text="生成时间")
        self.batch_tree.column("batch_id", width=100)
        self.batch_tree.column("batch_name", width=100)
        self.batch_tree.column("count", width=50, anchor=tk.CENTER)
        self.batch_tree.column("strategy", width=70)
        self.batch_tree.column("time", width=100)
        self.batch_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.batch_tree.bind('<<TreeviewSelect>>', self._on_batch_select)

        batch_btn_frame = ttk.Frame(batch_frame)
        batch_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(batch_btn_frame, text="设为当前", command=self._set_current_batch).pack(side=tk.LEFT, padx=2)
        ttk.Button(batch_btn_frame, text="查看详情", command=self._view_batch_detail).pack(side=tk.LEFT, padx=2)

        self._refresh_batch_list()

        if self.material_list.batches:
            self.gen_log.configure(state="normal")
            self.gen_log.insert(tk.END, f"\n已有 {len(self.material_list.batches)} 个批次，可在右侧列表中查看和切换。\n")
            self.gen_log.configure(state="disabled")

    def _refresh_batch_list(self):
        if not hasattr(self, 'batch_tree') or not self.batch_tree.winfo_exists():
            return
        for i in self.batch_tree.get_children():
            self.batch_tree.delete(i)
        for batch in self.material_list.batches:
            count = len(self.material_list.get_batch_files(batch.batch_id))
            strategy_map = {
                "overwrite": "覆盖",
                "new_version": "新版本",
                "update_selected": "更新选中"
            }
            strategy = strategy_map.get(batch.strategy, batch.strategy)
            tags = ()
            if batch.batch_id == self.material_list.current_batch_id:
                tags = ("current",)
            self.batch_tree.insert("", tk.END, values=(
                batch.batch_id,
                batch.batch_name,
                count,
                strategy,
                batch.created_at[11:16]
            ), tags=tags)
        self.batch_tree.tag_configure("current", background="#E6F0FF")

    def _on_batch_select(self, event):
        pass

    def _set_current_batch(self):
        selected = self.batch_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择一个批次")
            return
        item = self.batch_tree.item(selected[0])
        batch_id = item['values'][0]
        self.material_list.set_current_batch(batch_id)
        self._refresh_batch_list()
        current_batch = self.material_list.get_current_batch()
        if current_batch:
            messagebox.showinfo("成功", f"已设置批次 [{current_batch.batch_name}] 为当前批次\n打包时将使用此批次确认过的文件")

    def _view_batch_detail(self):
        selected = self.batch_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择一个批次")
            return
        item = self.batch_tree.item(selected[0])
        batch_id = item['values'][0]
        batch = self.material_list.get_batch(batch_id)
        if not batch:
            return

        files = self.material_list.get_batch_files(batch_id)
        detail_text = f"批次名称：{batch.batch_name}\n"
        detail_text += f"批次ID：{batch.batch_id}\n"
        detail_text += f"创建时间：{batch.created_at}\n"
        detail_text += f"生成策略：{batch.strategy}\n"
        detail_text += f"材料编码：{', '.join(batch.material_codes)}\n"
        detail_text += f"\n包含文件（{len(files)}个）：\n"
        detail_text += "-" * 50 + "\n"
        for f in files:
            status = "✓ 已生成" if f.generated else ("✓ 已上传" if f.provided else "✗ 未准备")
            detail_text += f"[{f.code}] {f.name} - {status}\n"
            if f.file_path:
                detail_text += f"    文件：{Path(f.file_path).name}\n"
        detail_text += f"\n确认的文件（{len(batch.confirmed_files)}个）：\n"
        detail_text += "-" * 50 + "\n"
        for f in batch.confirmed_files:
            detail_text += f"  {Path(f).name}\n"

        dialog = tk.Toplevel(self.root)
        dialog.title(f"批次详情 - {batch.batch_name}")
        dialog.geometry("600x450")
        dialog.transient(self.root)

        text = scrolledtext.ScrolledText(dialog, font=('Consolas', 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, detail_text)
        text.configure(state="disabled")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def manage_confirmation():
            self._manage_batch_confirmation(batch_id)
            dialog.destroy()

        ttk.Button(btn_frame, text="管理确认文件", command=manage_confirmation, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=dialog.destroy).pack(side=tk.RIGHT)

    def _view_current_batch(self):
        current_batch = self.material_list.get_current_batch()
        if not current_batch:
            messagebox.showinfo("提示", "暂无当前批次，请先生成文档")
            return
        self._refresh_batch_list()
        for item in self.batch_tree.get_children():
            values = self.batch_tree.item(item, 'values')
            if values[0] == current_batch.batch_id:
                self.batch_tree.selection_set(item)
                self._view_batch_detail()
                break

    def _manage_batch_confirmation(self, batch_id):
        batch = self.material_list.get_batch(batch_id)
        if not batch:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"管理确认文件 - {batch.batch_name}")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="勾选要纳入本次打包的文件，取消勾选的文件不会被打包：",
                 font=('Microsoft YaHei', 10)).pack(anchor=tk.W, padx=15, pady=10)

        files_frame = ttk.Frame(dialog)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        scrollbar = ttk.Scrollbar(files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(files_frame, columns=("confirm", "code", "name", "source", "file"),
                           show="headings", height=12, yscrollcommand=scrollbar.set)
        tree.heading("confirm", text="打包")
        tree.heading("code", text="编码")
        tree.heading("name", text="材料名称")
        tree.heading("source", text="来源")
        tree.heading("file", text="文件名")
        tree.column("confirm", width=60, anchor=tk.CENTER)
        tree.column("code", width=80, anchor=tk.CENTER)
        tree.column("name", width=150)
        tree.column("source", width=90, anchor=tk.CENTER)
        tree.column("file", width=250)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)

        check_vars = {}
        all_files = []

        for key, filepath in self.generated_files.items():
            if key.endswith("_error") or not filepath:
                continue
            mat_code = {"product_desc": "CPMS", "auth_desc": "SQMS", "sample_fields": "YLDQ"}.get(key, "QTLY")
            mat_item = self.material_list.get_item(mat_code)
            all_files.append({
                "key": key,
                "code": mat_code,
                "name": mat_item.name if mat_item else key,
                "source": "自动生成",
                "path": filepath
            })

        for item in self.material_list.get_provided():
            if item.generated or not item.file_path:
                continue
            all_files.append({
                "key": f"user_{item.code}",
                "code": item.code,
                "name": item.name,
                "source": "用户上传",
                "path": item.file_path
            })

        for f in all_files:
            var = tk.BooleanVar(value=f["path"] in batch.confirmed_files)
            check_vars[f["key"]] = var
            tags = ("checked",) if var.get() else ()
            tree.insert("", tk.END, values=(
                "☑" if var.get() else "☐",
                f["code"],
                f["name"],
                f["source"],
                Path(f["path"]).name
            ), tags=tags)

        def toggle_check(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            values = tree.item(item, 'values')
            key = None
            for f in all_files:
                if f["code"] == values[1] and Path(f["path"]).name == values[4]:
                    key = f["key"]
                    break
            if key and key in check_vars:
                new_val = not check_vars[key].get()
                check_vars[key].set(new_val)
                tree.item(item, values=(
                    "☑" if new_val else "☐",
                    values[1], values[2], values[3], values[4]
                ), tags=("checked",) if new_val else ())

        tree.bind('<Button-1>', toggle_check)
        tree.tag_configure("checked", background="#E8F5E9")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=15, pady=15)

        def save_confirmation():
            confirmed = []
            for f in all_files:
                if check_vars.get(f["key"], tk.BooleanVar(value=False)).get():
                    confirmed.append(f["path"])
            self.material_list.confirm_batch_files(batch_id, confirmed)
            messagebox.showinfo("成功", f"已确认 {len(confirmed)} 个文件将纳入打包")
            dialog.destroy()

        def select_all():
            for key, var in check_vars.items():
                var.set(True)
            for item in tree.get_children():
                values = tree.item(item, 'values')
                tree.item(item, values=("☑", values[1], values[2], values[3], values[4]), tags=("checked",))

        def deselect_all():
            for key, var in check_vars.items():
                var.set(False)
            for item in tree.get_children():
                values = tree.item(item, 'values')
                tree.item(item, values=("☐", values[1], values[2], values[3], values[4]), tags=())

        ttk.Button(btn_frame, text="全选", command=select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="全不选", command=deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存", command=save_confirmation, style="Primary.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _generate_templates(self):
        self.gen_log.configure(state="normal")
        self.gen_log.delete("1.0", tk.END)

        selected_codes = []
        if self.gen_cpms.get():
            selected_codes.append("CPMS")
        if self.gen_sqms.get():
            selected_codes.append("SQMS")
        if self.gen_yldq.get():
            selected_codes.append("YLDQ")

        if not selected_codes:
            self.gen_log.insert(tk.END, "✗ 请至少选择一个要生成的材料\n")
            self.gen_log.configure(state="disabled")
            return

        strategy = self.strategy_var.get()
        batch_name = self.batch_name_var.get()
        strategy_name = {"overwrite": "覆盖已有", "new_version": "新版本", "update_selected": "更新选中"}.get(strategy, strategy)

        self.gen_log.insert(tk.END, f"开始生成文档...\n项目：{self.project_info.product_name}\n")
        self.gen_log.insert(tk.END, f"策略：{strategy_name}   批次：{batch_name}\n")
        self.gen_log.insert(tk.END, f"生成材料：{', '.join(selected_codes)}\n")
        self.gen_log.insert(tk.END, f"{'='*50}\n\n")

        generator = TemplateGenerator(self.project_info, self.material_list)

        try:
            results = generator.generate_all(
                strategy=strategy,
                selected_codes=selected_codes,
                batch_name=batch_name
            )

            generation_results = results.get("_generation_results", [])
            for gr in generation_results:
                success = gr.get("success", False)
                name = gr.get("material_name", "")
                code = gr.get("material_code", "")
                path = gr.get("file_path", "")
                is_new = gr.get("is_new", False)
                if success:
                    action = "新建" if is_new else "更新"
                    self.gen_log.insert(tk.END, f"[{code}] {name} - {action}完成 ✓\n")
                    self.gen_log.insert(tk.END, f"    文件：{Path(path).name}\n\n")
                else:
                    self.gen_log.insert(tk.END, f"[{code}] {name} - 失败 ✗\n")
                    self.gen_log.insert(tk.END, f"    错误：{gr.get('error_message', '未知错误')}\n\n")

            for key in ["product_desc", "auth_desc", "sample_fields"]:
                if key in results:
                    self.generated_files[key] = results[key]
                error_key = f"{key}_error"
                if error_key in results:
                    self.generated_files.pop(key, None)

            self.gen_log.insert(tk.END, f"{'='*50}\n")
            self.gen_log.insert(tk.END, f"批次 [{batch_name}] 创建完成！\n")
            self.gen_log.insert(tk.END, f"包含 {len([r for r in generation_results if r.get('success')])} 个文件\n")
            self.gen_log.insert(tk.END, f"请在右侧批次列表中查看和管理确认的文件。\n")
            self.gen_log.see(tk.END)

            self._refresh_batch_list()

        except Exception as e:
            self.gen_log.insert(tk.END, f"✗ 生成出错：{str(e)}\n")
            import traceback
            self.gen_log.insert(tk.END, traceback.format_exc())
            messagebox.showerror("生成失败", f"文档生成时出错：{str(e)}")
        finally:
            self.gen_log.configure(state="disabled")

    def _validate_step3(self):
        if not self.material_list.get_current_batch():
            if messagebox.askyesno("提示", "尚未创建任何生成批次，确定要继续吗？"):
                return True
            return False
        return True

    def _open_output_dir(self):
        output_path = OUTPUT_DIR / self.project_info.project_id
        output_path.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith('win'):
                os.startfile(str(output_path))
            elif sys.platform == 'darwin':
                os.system(f'open "{output_path}"')
            else:
                os.system(f'xdg-open "{output_path}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录：{str(e)}")

    def _create_step4(self):
        main_frame = ttk.Frame(self.content_container, style="Step.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(main_frame, text="内容校验",
                 font=('Microsoft YaHei', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(main_frame,
                 text="系统将检查联系人信息、有效期、必填材料和敏感描述等内容。",
                 foreground="#666").pack(anchor=tk.W, pady=(0, 15))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="开始校验", command=self._run_validation, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重新校验", command=self._run_validation, style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑敏感词库", command=self._edit_sensitive_words, style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        result_frame = ttk.LabelFrame(main_frame, text="校验结果", style="Section.TLabelframe", padding=15)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.validation_result_text = scrolledtext.ScrolledText(result_frame, height=15, font=('Microsoft YaHei', 10))
        self.validation_result_text.pack(fill=tk.BOTH, expand=True)
        self.validation_result_text.insert(tk.END, "点击【开始校验】按钮进行内容校验...\n")
        self.validation_result_text.configure(state="disabled")

        self.validation_summary = ttk.Label(main_frame, text="", font=('Microsoft YaHei', 11, 'bold'))
        self.validation_summary.pack(anchor=tk.W, pady=10)

    def _run_validation(self):
        validator = ContentValidator(self.project_info, self.material_list)
        self.validation_result = validator.validate_all()
        result = self.validation_result

        self.validation_result_text.configure(state="normal")
        self.validation_result_text.delete("1.0", tk.END)
        self.validation_result_text.insert(tk.END, f"内容校验报告\n{'='*60}\n\n")
        self.validation_result_text.insert(tk.END, f"校验时间：{self._current_time()}\n")
        self.validation_result_text.insert(tk.END, f"产品名称：{self.project_info.product_name}\n")
        if self.material_list.get_current_batch():
            self.validation_result_text.insert(tk.END, f"当前批次：{self.material_list.get_current_batch().batch_name}\n")
        self.validation_result_text.insert(tk.END, "\n")

        if result.errors:
            self.validation_result_text.insert(tk.END, f"【错误】({len(result.errors)}项)\n", "error")
            for i, err in enumerate(result.errors, 1):
                self.validation_result_text.insert(tk.END, f"  {i}. {err}\n", "error")
            self.validation_result_text.insert(tk.END, "\n")

        if result.warnings:
            self.validation_result_text.insert(tk.END, f"【警告】({len(result.warnings)}项)\n", "warning")
            for i, warn in enumerate(result.warnings, 1):
                self.validation_result_text.insert(tk.END, f"  {i}. {warn}\n", "warning")
            self.validation_result_text.insert(tk.END, "\n")

        if result.sensitive_hits:
            self.validation_result_text.insert(tk.END, f"【敏感词检测】({len(result.sensitive_hits)}处)\n", "sensitive")
            for i, hit in enumerate(result.sensitive_hits, 1):
                self.validation_result_text.insert(tk.END,
                    f"  {i}. '{hit['word']}' 在【{hit['location']}】中\n", "sensitive")
                self.validation_result_text.insert(tk.END, f"     上下文：{hit['context']}\n", "sensitive")
            self.validation_result_text.insert(tk.END, "\n")

        if not result.has_errors and not result.has_warnings:
            self.validation_result_text.insert(tk.END, "✓ 所有校验项通过，未发现问题。\n", "success")

        self.validation_result_text.tag_config("error", foreground="#FF0000", font=('Microsoft YaHei', 10, 'bold'))
        self.validation_result_text.tag_config("warning", foreground="#FFA500", font=('Microsoft YaHei', 10))
        self.validation_result_text.tag_config("sensitive", foreground="#FF6347", font=('Microsoft YaHei', 10))
        self.validation_result_text.tag_config("success", foreground="#00B050", font=('Microsoft YaHei', 10, 'bold'))
        self.validation_result_text.configure(state="disabled")

        if result.has_errors:
            self.validation_summary.configure(text=f"校验结果：存在 {len(result.errors)} 个错误，请修正后继续", foreground="#FF0000")
        elif result.has_warnings:
            self.validation_summary.configure(text=f"校验结果：存在 {len(result.warnings)} 个警告，建议检查后继续", foreground="#FFA500")
        else:
            self.validation_summary.configure(text="校验结果：全部通过 ✓", foreground="#00B050")

    def _edit_sensitive_words(self):
        from config import SENSITIVE_WORDS_FILE
        SENSITIVE_WORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith('win'):
                os.startfile(str(SENSITIVE_WORDS_FILE))
            elif sys.platform == 'darwin':
                os.system(f'open "{SENSITIVE_WORDS_FILE}"')
            else:
                os.system(f'xdg-open "{SENSITIVE_WORDS_FILE}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件：{str(e)}")

    def _current_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _create_step5(self):
        main_frame = ttk.Frame(self.content_container, style="Step.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(main_frame, text="打包输出 - 提交前检查",
                 font=('Microsoft YaHei', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(main_frame,
                 text="请先查看各项检查结果，确认无误后再生成压缩包。",
                 foreground="#666").pack(anchor=tk.W, pady=(0, 15))

        top_btn_frame = ttk.Frame(main_frame)
        top_btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(top_btn_frame, text="🔄 刷新检查", command=self._refresh_submission_preview,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(top_btn_frame, text="📋 管理确认文件", command=self._manage_current_batch_files,
                   style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        self.submit_status_frame = ttk.LabelFrame(main_frame, text="提交状态", style="Section.TLabelframe", padding=15)
        self.submit_status_frame.pack(fill=tk.X, pady=5)

        self.submit_status_label = ttk.Label(self.submit_status_frame, text="", font=('Microsoft YaHei', 12, 'bold'))
        self.submit_status_label.pack(anchor=tk.W)

        self.submit_reason_label = ttk.Label(self.submit_status_frame, text="", foreground="#666")
        self.submit_reason_label.pack(anchor=tk.W, pady=(5, 0))

        panels_frame = ttk.Frame(main_frame)
        panels_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        left_panel = ttk.Frame(panels_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_panel = ttk.Frame(panels_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        files_frame = ttk.LabelFrame(left_panel, text="📦 待打包文件", style="Section.TLabelframe", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.preview_files_list = tk.Listbox(files_frame, font=('Consolas', 10), height=8)
        self.preview_files_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        files_scroll = ttk.Scrollbar(files_frame, orient="vertical", command=self.preview_files_list.yview)
        files_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_files_list.configure(yscrollcommand=files_scroll.set)

        missing_frame = ttk.LabelFrame(left_panel, text="❌ 缺失材料", style="Section.TLabelframe", padding=10)
        missing_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.preview_missing_list = tk.Listbox(missing_frame, font=('Consolas', 10), height=6, foreground="#c62828")
        self.preview_missing_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        sensitive_frame = ttk.LabelFrame(left_panel, text="⚠️ 敏感词警告", style="Section.TLabelframe", padding=10)
        sensitive_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.preview_sensitive_list = tk.Listbox(sensitive_frame, font=('Consolas', 10), height=5, foreground="#ef6c00")
        self.preview_sensitive_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        errors_frame = ttk.LabelFrame(right_panel, text="❌ 校验错误", style="Section.TLabelframe", padding=10)
        errors_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.preview_errors_list = tk.Listbox(errors_frame, font=('Consolas', 10), height=7, foreground="#c62828")
        self.preview_errors_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        warnings_frame = ttk.LabelFrame(right_panel, text="⚠️ 校验警告", style="Section.TLabelframe", padding=10)
        warnings_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.preview_warnings_list = tk.Listbox(warnings_frame, font=('Consolas', 10), height=6, foreground="#ef6c00")
        self.preview_warnings_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        batch_info_frame = ttk.LabelFrame(right_panel, text="📊 批次信息", style="Section.TLabelframe", padding=10)
        batch_info_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.batch_info_text = scrolledtext.ScrolledText(batch_info_frame, font=('Consolas', 10), height=5)
        self.batch_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.batch_info_text.configure(state="disabled")

        self.ignore_errors_var = tk.BooleanVar(value=False)
        warning_frame = ttk.Frame(main_frame)
        warning_frame.pack(fill=tk.X, pady=5)
        self.warning_label = ttk.Label(warning_frame, text="", foreground="#FF0000", font=('Microsoft YaHei', 10, 'bold'))
        self.warning_label.pack(side=tk.LEFT)
        self.ignore_errors_check = ttk.Checkbutton(warning_frame, text="忽略错误继续打包", variable=self.ignore_errors_var)
        self.ignore_errors_check.pack(side=tk.LEFT, padx=20)
        self.ignore_errors_check.pack_forget()

        bottom_btn_frame = ttk.Frame(main_frame)
        bottom_btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(bottom_btn_frame, text="✅ 确认并生成压缩包", command=self._build_package,
                   style="Success.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frame, text="📄 查看提交清单", command=self._view_checklist,
                   style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frame, text="📦 打开压缩包", command=self._open_zip,
                   style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frame, text="📂 打开输出目录", command=self._open_output_dir,
                   style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="📝 打包日志", style="Section.TLabelframe", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.package_log = scrolledtext.ScrolledText(log_frame, height=8, font=('Consolas', 10))
        self.package_log.pack(fill=tk.BOTH, expand=True)
        self.package_log.insert(tk.END, "点击【刷新检查】按钮查看提交前检查结果...\n")
        self.package_log.configure(state="disabled")

        self.package_summary = ttk.Label(main_frame, text="", font=('Microsoft YaHei', 11, 'bold'))
        self.package_summary.pack(anchor=tk.W, pady=10)

        self._refresh_submission_preview()

    def _manage_current_batch_files(self):
        current_batch = self.material_list.get_current_batch()
        if not current_batch:
            if messagebox.askyesno("提示", "暂无当前批次，是否创建一个默认批次？"):
                self.material_list.create_batch(name="默认批次", strategy="overwrite")
                self._refresh_batch_list()
                current_batch = self.material_list.get_current_batch()
            else:
                return
        self._manage_batch_confirmation(current_batch.batch_id)
        self._refresh_submission_preview()

    def _refresh_submission_preview(self):
        try:
            packager = PackageOutput(self.project_info, self.material_list,
                                      self.generated_files, self.validation_result)
            preview = packager.get_submission_preview()
            self.submission_preview = preview
        except Exception as e:
            self._show_preview_error(f"获取预览数据失败: {str(e)}")
            return

        self._clear_all_preview_lists()

        current_batch = self.material_list.get_current_batch()
        self._update_batch_info(current_batch)
        self._update_submit_status(preview, current_batch)
        self._update_files_list(preview.files_to_include)
        self._update_missing_list(preview.missing_required, preview.missing_optional)
        self._update_sensitive_list(preview.sensitive_warnings)
        self._update_errors_list(preview.validation_errors)
        self._update_warnings_list(preview.validation_warnings)
        self._update_warning_display(preview)
        self._update_package_summary(preview)

    def _show_preview_error(self, error_msg):
        self._clear_all_preview_lists()
        self.submit_status_label.configure(text="✗ 预览加载失败", foreground="#c62828")
        self.submit_reason_label.configure(text=error_msg)
        self.preview_files_list.insert(tk.END, f"错误: {error_msg}")
        self.preview_files_list.insert(tk.END, "请检查项目信息和材料是否完整")
        self.preview_files_list.configure(foreground="#c62828")

    def _clear_all_preview_lists(self):
        for lst in [self.preview_files_list, self.preview_missing_list,
                    self.preview_sensitive_list, self.preview_errors_list,
                    self.preview_warnings_list]:
            lst.delete(0, tk.END)
            lst.configure(foreground="black")
        self.batch_info_text.configure(state="normal")
        self.batch_info_text.delete("1.0", tk.END)
        self.batch_info_text.configure(state="disabled")
        self.warning_label.configure(text="")
        self.ignore_errors_check.pack_forget()

    def _update_batch_info(self, current_batch):
        self.batch_info_text.configure(state="normal")
        self.batch_info_text.insert(tk.END, f"检查时间: {self._current_time()}\n")
        if current_batch:
            self.batch_info_text.insert(tk.END, f"当前批次: {current_batch.batch_name}\n")
            self.batch_info_text.insert(tk.END, f"批次ID: {current_batch.batch_id}\n")
            self.batch_info_text.insert(tk.END, f"生成策略: {current_batch.strategy}\n")
            self.batch_info_text.insert(tk.END, f"已确认文件: {len(current_batch.confirmed_files)} 个\n")
        else:
            self.batch_info_text.insert(tk.END, "当前批次: 未设置\n")
            self.batch_info_text.insert(tk.END, "提示: 请先在模板生成步骤创建批次\n")
        self.batch_info_text.configure(state="disabled")

    def _update_submit_status(self, preview, current_batch):
        reasons = []
        if preview.can_submit:
            self.submit_status_label.configure(text="✓ 可以提交", foreground="#2e7d32")
            self.submit_reason_label.configure(text="所有检查项通过，可以生成压缩包")
        else:
            self.submit_status_label.configure(text="✗ 暂不可提交", foreground="#c62828")
            if not current_batch:
                reasons.append("未设置批次")
            if not preview.files_to_include:
                reasons.append("无待打包文件")
            if preview.missing_required:
                reasons.append(f"{len(preview.missing_required)}个必填材料缺失")
            if preview.validation_errors:
                reasons.append(f"{len(preview.validation_errors)}个校验错误")
            if reasons:
                self.submit_reason_label.configure(text="原因: " + "、".join(reasons))
            else:
                self.submit_reason_label.configure(text="请检查各项内容后重试")

    def _update_files_list(self, files):
        if not files:
            self.preview_files_list.insert(tk.END, "(暂无待打包文件)")
            self.preview_files_list.insert(tk.END, "")
            self.preview_files_list.insert(tk.END, "可能原因:")
            self.preview_files_list.insert(tk.END, "  1. 尚未创建批次")
            self.preview_files_list.insert(tk.END, "  2. 尚未上传或生成材料")
            self.preview_files_list.insert(tk.END, "  3. 批次中未确认任何文件")
            self.preview_files_list.configure(foreground="#888")
            return

        for i, f in enumerate(files, 1):
            status = "✓" if f.get('confirmed') else "○"
            name = f.get('name', f.get('original_name', '未知文件'))
            source = f.get('source', '未知来源')
            size = f.get('size', '')
            line = f"{status} {name}"
            if size:
                line += f" ({size})"
            self.preview_files_list.insert(tk.END, line)
            self.preview_files_list.insert(tk.END, f"     来源: {source}")
            if f.get('original_path'):
                self.preview_files_list.insert(tk.END, f"     路径: {f['original_path']}")
            self.preview_files_list.insert(tk.END, "")

    def _update_missing_list(self, missing_required, missing_optional):
        if not missing_required and not missing_optional:
            self.preview_missing_list.insert(tk.END, "✓ 所有材料已齐全")
            self.preview_missing_list.configure(foreground="#2e7d32")
            return

        if missing_required:
            self.preview_missing_list.insert(tk.END, "【必填材料缺失】")
            for m in missing_required:
                self.preview_missing_list.insert(tk.END, f"  ✗ {m.code} - {m.name}")
            if missing_optional:
                self.preview_missing_list.insert(tk.END, "")

        if missing_optional:
            self.preview_missing_list.insert(tk.END, "【选填材料缺失】")
            for m in missing_optional:
                self.preview_missing_list.insert(tk.END, f"  ○ {m.code} - {m.name}")

    def _update_sensitive_list(self, warnings):
        if not warnings:
            self.preview_sensitive_list.insert(tk.END, "✓ 未检测到敏感词")
            self.preview_sensitive_list.configure(foreground="#2e7d32")
            return

        for i, w in enumerate(warnings, 1):
            file_name = w.get('file', '未知文件')
            words = ', '.join(w.get('words', []))
            line_no = w.get('line', '?')
            self.preview_sensitive_list.insert(tk.END, f"{i}. {file_name}")
            self.preview_sensitive_list.insert(tk.END, f"   敏感词: {words}")
            self.preview_sensitive_list.insert(tk.END, f"   位置: 第{line_no}行")
            self.preview_sensitive_list.insert(tk.END, "")

    def _update_errors_list(self, errors):
        if not errors:
            self.preview_errors_list.insert(tk.END, "✓ 无校验错误")
            self.preview_errors_list.configure(foreground="#2e7d32")
            return

        for i, e in enumerate(errors, 1):
            self.preview_errors_list.insert(tk.END, f"{i}. ✗ {e}")

    def _update_warnings_list(self, warnings):
        if not warnings:
            self.preview_warnings_list.insert(tk.END, "✓ 无校验警告")
            self.preview_warnings_list.configure(foreground="#2e7d32")
            return

        for i, w in enumerate(warnings, 1):
            self.preview_warnings_list.insert(tk.END, f"{i}. ⚠ {w}")

    def _update_warning_display(self, preview):
        if preview.validation_errors or preview.missing_required:
            self.warning_label.configure(text="⚠ 存在错误，建议返回修正后再打包")
            self.ignore_errors_check.pack(side=tk.LEFT, padx=20)
        else:
            self.warning_label.configure(text="")
            self.ignore_errors_check.pack_forget()

    def _update_validation_display(self, preview):
        self.val_errors_list.delete(0, tk.END)
        self.val_warnings_list.delete(0, tk.END)

        if preview.validation_errors:
            for e in preview.validation_errors:
                self.val_errors_list.insert(tk.END, f"✗ {e}")
        else:
            self.val_errors_list.insert(tk.END, "✓ 无错误")

        if preview.validation_warnings:
            for w in preview.validation_warnings:
                self.val_warnings_list.insert(tk.END, f"⚠ {w}")
        else:
            self.val_warnings_list.insert(tk.END, "✓ 无警告")

    def _update_package_summary(self, preview):
        if preview.can_submit:
            self.package_summary.configure(
                text=f"✓ 可以打包 - 共 {len(preview.files_to_include)} 个文件，无必填材料缺失",
                foreground="#2e7d32")
        else:
            issues = []
            if preview.missing_required:
                issues.append(f"{len(preview.missing_required)}个必填材料缺失")
            if preview.validation_errors:
                issues.append(f"{len(preview.validation_errors)}个校验错误")
            self.package_summary.configure(
                text=f"✗ 暂不可打包 - {', '.join(issues)}",
                foreground="#c62828")

    def _build_package(self):
        if not self.submission_preview:
            messagebox.showwarning("提示", "请先点击【刷新检查】生成预览")
            return

        if not self.submission_preview.can_submit and not self.ignore_errors_var.get():
            if not messagebox.askyesno("确认", "存在必填材料缺失或校验错误，确定要继续打包吗？"):
                return

        self.package_log.configure(state="normal")
        self.package_log.delete("1.0", tk.END)
        self.package_log.insert(tk.END, f"{'='*60}\n")
        self.package_log.insert(tk.END, f"开始打包\n")
        self.package_log.insert(tk.END, f"{'='*60}\n")
        self.package_log.insert(tk.END, f"时间: {self._current_time()}\n")
        self.package_log.insert(tk.END, f"项目: {self.project_info.product_name}\n")
        self.package_log.insert(tk.END, f"产品编码: {self.project_info.product_code}\n")

        current_batch = self.material_list.get_current_batch()
        if current_batch:
            self.package_log.insert(tk.END, f"批次: {current_batch.batch_name} ({current_batch.batch_id})\n")
        self.package_log.insert(tk.END, "\n")
        self.package_log.update()

        try:
            packager = PackageOutput(self.project_info, self.material_list,
                                      self.generated_files, self.validation_result)

            ignore_errors = self.ignore_errors_var.get() or not self.submission_preview.can_submit
            self.package_log.insert(tk.END, f"[1/4] 收集文件...\n")
            self.package_log.update()

            result = packager.build_package(ignore_errors=ignore_errors)

            if not result.get('success', True):
                error_msg = result.get('error', '未知错误')
                self.package_log.insert(tk.END, f"\n✗ 打包失败\n")
                self.package_log.insert(tk.END, f"错误原因: {error_msg}\n")
                self.package_log.configure(state="disabled")
                messagebox.showerror("打包失败", f"打包失败: {error_msg}")
                return

            self.package_log.insert(tk.END, f"[2/4] 生成提交清单...\n")
            self.package_log.insert(tk.END, f"[3/4] 创建压缩包...\n")
            self.package_log.insert(tk.END, f"[4/4] 保存记录...\n\n")
            self.package_log.update()

            self.package_log.insert(tk.END, f"✓ 打包完成！\n\n")
            self.package_log.insert(tk.END, f"📦 压缩包路径:\n   {result['zip_path']}\n\n")
            self.package_log.insert(tk.END, f"📄 提交清单:\n   {result['checklist_path']}\n\n")
            self.package_log.insert(tk.END, f"📊 包含文件: {result['file_count']} 个\n")

            if result.get('output_files'):
                self.package_log.insert(tk.END, "\n文件清单:\n")
                for i, f in enumerate(result['output_files'], 1):
                    self.package_log.insert(tk.END, f"  {i:2d}. {f.get('name', f.get('original_name', ''))}\n")

            self.last_zip_path = result['zip_path']
            self.last_checklist_path = result['checklist_path']
            self.package_result = result

            self._save_generation_record(result)

            self.package_log.insert(tk.END, f"\n✓ 记录已保存到历史记录\n")
            self.package_log.insert(tk.END, f"{'='*60}\n")
            self.package_log.configure(state="disabled")

            messagebox.showinfo("成功", f"打包完成！\n\n压缩包: {result['zip_path']}\n文件数: {result['file_count']}")

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.package_log.insert(tk.END, f"\n✗ 打包失败\n")
            self.package_log.insert(tk.END, f"错误类型: {type(e).__name__}\n")
            self.package_log.insert(tk.END, f"错误信息: {str(e)}\n")
            self.package_log.insert(tk.END, f"\n详细信息:\n{error_detail}\n")
            self.package_log.insert(tk.END, f"{'='*60}\n")
            self.package_log.configure(state="disabled")
            messagebox.showerror("打包失败", f"打包失败: {str(e)}\n\n请查看打包日志获取详细信息。")

    def _view_checklist(self):
        if hasattr(self, 'last_checklist_path') and self.last_checklist_path:
            if os.path.exists(self.last_checklist_path):
                os.startfile(self.last_checklist_path)
            else:
                messagebox.showwarning("提示", "清单文件不存在")
        else:
            messagebox.showwarning("提示", "请先生成压缩包")

    def _open_zip(self):
        if hasattr(self, 'last_zip_path') and self.last_zip_path:
            if os.path.exists(self.last_zip_path):
                os.startfile(os.path.dirname(self.last_zip_path))
            else:
                messagebox.showwarning("提示", "压缩包不存在")
        else:
            messagebox.showwarning("提示", "请先生成压缩包")

    def _save_generation_record(self, package_result):
        current_batch = self.material_list.get_current_batch()
        record = {
            "project_id": self.project_info.project_id,
            "product_code": self.project_info.product_code,
            "product_name": self.project_info.product_name,
            "contact_person": self.project_info.contact_person,
            "scene": self.project_info.scene,
            "created_at": self._current_time(),
            "batch_id": current_batch.batch_id if current_batch else "",
            "batch_name": current_batch.batch_name if current_batch else "",
            "project_info": self.project_info.to_dict(),
            "materials": self.material_list.to_dict(),
            "generated_files": self.generated_files,
            "validation_result": self.validation_result.to_dict() if self.validation_result else {},
            "zip_path": package_result['zip_path'],
            "checklist_path": package_result['checklist_path'],
            "file_count": package_result['file_count']
        }
        self.record_manager.add_record(record)

    def _show_records(self):
        win = tk.Toplevel(self.root)
        win.title("历史记录")
        win.geometry("1200x700")
        win.grab_set()

        search_frame = ttk.LabelFrame(win, text="筛选条件", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        row1 = ttk.Frame(search_frame)
        row1.pack(fill=tk.X, pady=5)

        ttk.Label(row1, text="项目编号:", width=10).pack(side=tk.LEFT)
        self.search_project_id = ttk.Entry(row1, width=20)
        self.search_project_id.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="产品编码:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.search_product_code = ttk.Entry(row1, width=20)
        self.search_product_code.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="产品名称:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.search_product_name = ttk.Entry(row1, width=25)
        self.search_product_name.pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(search_frame)
        row2.pack(fill=tk.X, pady=5)

        ttk.Label(row2, text="联系人:", width=10).pack(side=tk.LEFT)
        self.search_contact = ttk.Entry(row2, width=15)
        self.search_contact.pack(side=tk.LEFT, padx=5)

        ttk.Label(row2, text="交易场景:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.search_scene = ttk.Combobox(row2, values=[""] + SCENES, width=20, state="readonly")
        self.search_scene.pack(side=tk.LEFT, padx=5)
        self.search_scene.current(0)

        ttk.Label(row2, text="校验错误:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.search_has_errors = ttk.Combobox(row2, values=["", "有错误", "无错误"], width=12, state="readonly")
        self.search_has_errors.pack(side=tk.LEFT, padx=5)
        self.search_has_errors.current(0)

        row3 = ttk.Frame(search_frame)
        row3.pack(fill=tk.X, pady=5)

        ttk.Label(row3, text="开始日期:", width=10).pack(side=tk.LEFT)
        self.search_start_date = ttk.Entry(row3, width=18)
        self.search_start_date.pack(side=tk.LEFT, padx=5)
        self.search_start_date.insert(0, "")
        ttk.Label(row3, text="(YYYY-MM-DD)", foreground="#888").pack(side=tk.LEFT)

        ttk.Label(row3, text="结束日期:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.search_end_date = ttk.Entry(row3, width=18)
        self.search_end_date.pack(side=tk.LEFT, padx=5)
        self.search_end_date.insert(0, "")
        ttk.Label(row3, text="(YYYY-MM-DD)", foreground="#888").pack(side=tk.LEFT)

        btn_frame = ttk.Frame(search_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="🔍 搜索", command=self._do_search_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✕ 清除筛选", command=self._clear_search_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="↺ 刷新列表", command=self._refresh_records_list).pack(side=tk.LEFT, padx=5)

        columns = ("project_id", "product_code", "product_name", "contact_person",
                   "scene", "batch_name", "file_count", "created_at")
        self.records_tree = ttk.Treeview(win, columns=columns, show="headings", height=15)

        headings = [
            ("project_id", "项目编号", 120),
            ("product_code", "产品编码", 120),
            ("product_name", "产品名称", 200),
            ("contact_person", "联系人", 100),
            ("scene", "交易场景", 150),
            ("batch_name", "批次名称", 120),
            ("file_count", "文件数", 80),
            ("created_at", "生成时间", 180)
        ]
        for col, text, width in headings:
            self.records_tree.heading(col, text=text)
            self.records_tree.column(col, width=width, anchor="w")

        scrollbar = ttk.Scrollbar(win, orient="vertical", command=self.records_tree.yview)
        self.records_tree.configure(yscrollcommand=scrollbar.set)

        self.records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        action_frame = ttk.Frame(win)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(action_frame, text="查看详情", command=self._view_record_detail).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="恢复此记录", command=self._restore_selected_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="删除记录", command=self._delete_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="关闭", command=win.destroy).pack(side=tk.RIGHT, padx=5)

        self.records_tree.bind("<Double-1>", lambda e: self._view_record_detail())

        self._refresh_records_list()

    def _do_search_records(self):
        project_id = self.search_project_id.get().strip()
        product_code = self.search_product_code.get().strip()
        product_name = self.search_product_name.get().strip()
        contact_person = self.search_contact.get().strip()
        scene = self.search_scene.get().strip()
        start_date = self.search_start_date.get().strip()
        end_date = self.search_end_date.get().strip()
        has_errors_text = self.search_has_errors.get().strip()
        has_errors = ""
        if has_errors_text == "有错误":
            has_errors = "yes"
        elif has_errors_text == "无错误":
            has_errors = "no"

        records = self.record_manager.search_records(
            project_id=project_id,
            product_code=product_code,
            product_name=product_name,
            contact_person=contact_person,
            start_date=start_date,
            end_date=end_date,
            scene=scene,
            has_errors=has_errors
        )

        self._populate_records_tree(records)

    def _clear_search_filters(self):
        self.search_project_id.delete(0, tk.END)
        self.search_product_code.delete(0, tk.END)
        self.search_product_name.delete(0, tk.END)
        self.search_contact.delete(0, tk.END)
        self.search_scene.current(0)
        self.search_has_errors.current(0)
        self.search_start_date.delete(0, tk.END)
        self.search_end_date.delete(0, tk.END)
        self._refresh_records_list()

    def _refresh_records_list(self):
        records = self.record_manager.get_all_records()
        self._populate_records_tree(records)

    def _populate_records_tree(self, records):
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)

        for rec in sorted(records, key=lambda x: x.get('created_at', ''), reverse=True):
            self.records_tree.insert("", "end", values=(
                rec.get('project_id', ''),
                rec.get('product_code', ''),
                rec.get('product_name', ''),
                rec.get('contact_person', ''),
                rec.get('scene', ''),
                rec.get('batch_name', ''),
                rec.get('file_count', 0),
                rec.get('created_at', '')
            ))

    def _get_selected_record(self):
        selection = self.records_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一条记录")
            return None

        item = self.records_tree.item(selection[0])
        values = item['values']
        project_id = values[0]
        product_code = values[1]
        batch_name = values[5]
        created_at = values[7]

        all_records = self.record_manager.get_all_records()
        for rec in all_records:
            if (rec.get('project_id') == project_id and
                rec.get('product_code') == product_code and
                rec.get('batch_name') == batch_name and
                rec.get('created_at') == created_at):
                return rec

        for rec in all_records:
            if (rec.get('project_id') == project_id and
                rec.get('created_at') == created_at):
                return rec

        return None

    def _view_record_detail(self):
        record = self._get_selected_record()
        if not record:
            return

        win = tk.Toplevel(self.root)
        win.title(f"记录详情 - {record['product_name']}")
        win.geometry("950x700")
        win.grab_set()

        summary_frame = ttk.LabelFrame(win, text="📊 本次打包结果", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)

        vr = record.get('validation_result', {})
        passed = vr.get('passed', False)
        error_count = len(vr.get('errors', []))
        warning_count = len(vr.get('warnings', []))
        sensitive_count = len(vr.get('sensitive_warnings', []))

        row1 = ttk.Frame(summary_frame)
        row1.pack(fill=tk.X, pady=5)

        ttk.Label(row1, text="📦 压缩包:", width=12, font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)
        zip_path = record.get('zip_path', 'N/A')
        ttk.Label(row1, text=zip_path, foreground="#2e7d32").pack(side=tk.LEFT)

        row2 = ttk.Frame(summary_frame)
        row2.pack(fill=tk.X, pady=5)

        ttk.Label(row2, text="📄 提交清单:", width=12, font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)
        checklist_path = record.get('checklist_path', 'N/A')
        ttk.Label(row2, text=checklist_path, foreground="#2e7d32").pack(side=tk.LEFT)

        row3 = ttk.Frame(summary_frame)
        row3.pack(fill=tk.X, pady=5)

        ttk.Label(row3, text="📊 文件数量:", width=12, font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)
        file_count = record.get('file_count', 0)
        ttk.Label(row3, text=f"{file_count} 个文件", foreground="#2e7d32").pack(side=tk.LEFT)

        ttk.Label(row3, text="     ✅ 校验结论:", width=18, font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)
        if passed:
            status_text = "通过"
            status_color = "#2e7d32"
        else:
            status_text = f"未通过 ({error_count}个错误, {warning_count}个警告, {sensitive_count}个敏感词)"
            status_color = "#c62828"
        ttk.Label(row3, text=status_text, foreground=status_color, font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)

        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        info_frame = ttk.Frame(notebook, padding=10)
        notebook.add(info_frame, text="📋 项目信息")

        info_text = scrolledtext.ScrolledText(info_frame, font=('Consolas', 10))
        info_text.pack(fill=tk.BOTH, expand=True)

        info_text.insert(tk.END, "项目信息\n")
        info_text.insert(tk.END, f"{'='*60}\n\n")
        info_text.insert(tk.END, f"项目编号: {record.get('project_id', 'N/A')}\n")
        info_text.insert(tk.END, f"产品名称: {record.get('product_name', 'N/A')}\n")
        info_text.insert(tk.END, f"产品编码: {record.get('product_code', 'N/A')}\n")
        info_text.insert(tk.END, f"交易场景: {record.get('scene', 'N/A')}\n")
        info_text.insert(tk.END, f"联系人: {record.get('contact_person', 'N/A')}\n")
        info_text.insert(tk.END, f"生成时间: {record.get('created_at', 'N/A')}\n")
        info_text.insert(tk.END, f"批次: {record.get('batch_name', 'N/A')} ({record.get('batch_id', 'N/A')})\n\n")

        pi = record.get('project_info', {})
        for key, value in pi.items():
            if value:
                info_text.insert(tk.END, f"{key}: {value}\n")

        materials_frame = ttk.Frame(notebook, padding=10)
        notebook.add(materials_frame, text="📁 材料状态")

        mat_text = scrolledtext.ScrolledText(materials_frame, font=('Consolas', 10))
        mat_text.pack(fill=tk.BOTH, expand=True)

        mat_text.insert(tk.END, "材料清单\n")
        mat_text.insert(tk.END, f"{'='*60}\n\n")
        materials_data = record.get('materials', {})
        materials = materials_data.get('materials', materials_data.get('items', []))
        for m in materials:
            if m.get('generated'):
                status = "已生成"
                status_color = "#2e7d32"
            elif m.get('file_path'):
                status = "已上传"
                status_color = "#1565c0"
            else:
                status = "未上传"
                status_color = "#757575"
            req = "必填" if m.get('required') else "选填"
            batch_info = ""
            if m.get('batch_id'):
                batch_info = f" [批次: {m['batch_id']}]"
            mat_text.insert(tk.END, f"[{req}] {m['code']} - {m['name']} ")
            mat_text.insert(tk.END, f"({status}){batch_info}\n", f"status_{status}")
            if m.get('file_path'):
                mat_text.insert(tk.END, f"     📄 文件路径: {m['file_path']}\n")
            if m.get('generated_at'):
                mat_text.insert(tk.END, f"     🕐 生成时间: {m['generated_at']}\n")
            mat_text.insert(tk.END, "\n")

        mat_text.tag_configure("status_已生成", foreground="#2e7d32")
        mat_text.tag_configure("status_已上传", foreground="#1565c0")
        mat_text.tag_configure("status_未上传", foreground="#757575")

        val_frame = ttk.Frame(notebook, padding=10)
        notebook.add(val_frame, text="✅ 校验报告")

        val_text = scrolledtext.ScrolledText(val_frame, font=('Consolas', 10))
        val_text.pack(fill=tk.BOTH, expand=True)

        val_text.insert(tk.END, "校验报告\n")
        val_text.insert(tk.END, f"{'='*60}\n\n")
        val_text.insert(tk.END, f"校验时间: {vr.get('timestamp', 'N/A')}\n")
        val_text.insert(tk.END, f"校验结论: {'✅ 通过' if passed else '❌ 未通过'}\n")
        val_text.insert(tk.END, f"错误数量: {error_count} 个\n")
        val_text.insert(tk.END, f"警告数量: {warning_count} 个\n")
        val_text.insert(tk.END, f"敏感词警告: {sensitive_count} 个\n\n")

        if error_count > 0:
            val_text.insert(tk.END, "❌ 错误:\n", "error")
            for e in vr.get('errors', []):
                val_text.insert(tk.END, f"  ✗ {e}\n", "error")
            val_text.insert(tk.END, "\n")

        if warning_count > 0:
            val_text.insert(tk.END, "⚠️ 警告:\n", "warning")
            for w in vr.get('warnings', []):
                val_text.insert(tk.END, f"  ⚠ {w}\n", "warning")
            val_text.insert(tk.END, "\n")

        if sensitive_count > 0:
            val_text.insert(tk.END, "🚨 敏感词警告:\n", "sensitive")
            for sw in vr.get('sensitive_warnings', []):
                val_text.insert(tk.END, f"  📄 文件: {sw.get('file')}\n", "sensitive")
                val_text.insert(tk.END, f"     敏感词: {', '.join(sw.get('words', []))}\n", "sensitive")
                if sw.get('line'):
                    val_text.insert(tk.END, f"     位置: 第{sw['line']}行\n", "sensitive")
                val_text.insert(tk.END, "\n")

        if error_count == 0 and warning_count == 0 and sensitive_count == 0:
            val_text.insert(tk.END, "✅ 所有校验项通过，未发现问题。\n", "success")

        val_text.tag_configure("error", foreground="#c62828")
        val_text.tag_configure("warning", foreground="#ef6c00")
        val_text.tag_configure("sensitive", foreground="#d84315")
        val_text.tag_configure("success", foreground="#2e7d32")

        files_frame = ttk.Frame(notebook, padding=10)
        notebook.add(files_frame, text="📦 生成文件")

        files_text = scrolledtext.ScrolledText(files_frame, font=('Consolas', 10))
        files_text.pack(fill=tk.BOTH, expand=True)

        files_text.insert(tk.END, "生成的文件\n")
        files_text.insert(tk.END, f"{'='*60}\n\n")
        files_text.insert(tk.END, f"📦 压缩包路径: {zip_path}\n")
        files_text.insert(tk.END, f"📄 提交清单: {checklist_path}\n")
        files_text.insert(tk.END, f"📊 文件数量: {file_count} 个\n")
        files_text.insert(tk.END, f"🏷️  批次: {record.get('batch_name', 'N/A')} ({record.get('batch_id', 'N/A')})\n\n")

        gf = record.get('generated_files', {})
        if gf:
            files_text.insert(tk.END, "📝 生成文件清单:\n")
            for code, path in gf.items():
                files_text.insert(tk.END, f"  {code}: {path}\n")

        info_text.configure(state="disabled")
        mat_text.configure(state="disabled")
        val_text.configure(state="disabled")
        files_text.configure(state="disabled")

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="恢复此记录", command=lambda: self._restore_record_and_close(record, win)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="打开压缩包目录", command=lambda: self._open_record_zip(record)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _open_record_zip(self, record):
        zip_path = record.get('zip_path', '')
        if zip_path and os.path.exists(zip_path):
            os.startfile(os.path.dirname(zip_path))
        else:
            messagebox.showwarning("提示", "压缩包文件不存在")

    def _restore_selected_record(self):
        record = self._get_selected_record()
        if not record:
            return
        self._restore_record_and_close(record, None)

    def _restore_record_and_close(self, record, win):
        if not messagebox.askyesno("确认", "恢复记录将覆盖当前的所有信息，确定继续吗？"):
            return

        try:
            from core.content_validator import ValidationResult
            if self.validation_result is None:
                self.validation_result = ValidationResult()

            self.record_manager.restore_record(
                record,
                self.project_info,
                self.material_list,
                self.generated_files,
                self.validation_result
            )

            self.last_zip_path = record.get('zip_path', '')
            self.last_checklist_path = record.get('checklist_path', '')
            self.package_result = {
                'zip_path': self.last_zip_path,
                'checklist_path': self.last_checklist_path,
                'file_count': record.get('file_count', 0)
            }

            self._refresh_project_info_ui()
            self._refresh_materials_tree()
            self._refresh_material_status()
            self._refresh_batch_list()
            self._refresh_generated_files_list()
            self._refresh_validation_display()
            self._refresh_submission_preview()
            self._update_step_buttons()

            if win:
                win.destroy()

            messagebox.showinfo("成功", "记录已恢复！\n\n"
                                      f"项目: {record.get('product_name')}\n"
                                      f"批次: {record.get('batch_name', 'N/A')}\n"
                                      f"时间: {record.get('created_at')}\n\n"
                                      f"所有步骤（项目信息、材料清单、模板生成、\n"
                                      f"内容校验、打包输出）已同步到当时的状态。")

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            messagebox.showerror("错误", f"恢复失败: {str(e)}\n\n{error_detail}")

    def _refresh_validation_display(self):
        if self.validation_result is None:
            return

        result = self.validation_result

        if hasattr(self, 'validation_result_text') and self.validation_result_text.winfo_exists():
            self.validation_result_text.configure(state="normal")
            self.validation_result_text.delete("1.0", tk.END)
            self.validation_result_text.insert(tk.END, f"内容校验报告（历史恢复）\n{'='*60}\n\n")
            self.validation_result_text.insert(tk.END, f"校验时间：{result.timestamp or self._current_time()}\n")
            self.validation_result_text.insert(tk.END, f"产品名称：{self.project_info.product_name}\n")
            if self.material_list.get_current_batch():
                self.validation_result_text.insert(tk.END, f"当前批次：{self.material_list.get_current_batch().batch_name}\n")
            self.validation_result_text.insert(tk.END, "\n")

            if result.errors:
                self.validation_result_text.insert(tk.END, f"【错误】({len(result.errors)}项)\n", "error")
                for i, err in enumerate(result.errors, 1):
                    self.validation_result_text.insert(tk.END, f"  {i}. {err}\n", "error")
                self.validation_result_text.insert(tk.END, "\n")

            if result.warnings:
                self.validation_result_text.insert(tk.END, f"【警告】({len(result.warnings)}项)\n", "warning")
                for i, warn in enumerate(result.warnings, 1):
                    self.validation_result_text.insert(tk.END, f"  {i}. {warn}\n", "warning")
                self.validation_result_text.insert(tk.END, "\n")

            if result.sensitive_hits:
                self.validation_result_text.insert(tk.END, f"【敏感词检测】({len(result.sensitive_hits)}处)\n", "sensitive")
                for i, hit in enumerate(result.sensitive_hits, 1):
                    self.validation_result_text.insert(tk.END,
                        f"  {i}. '{hit['word']}' 在【{hit['location']}】中\n", "sensitive")
                    if 'context' in hit:
                        self.validation_result_text.insert(tk.END, f"     上下文：{hit['context']}\n", "sensitive")
                self.validation_result_text.insert(tk.END, "\n")

            if not result.has_errors and not result.has_warnings:
                self.validation_result_text.insert(tk.END, "✓ 所有校验项通过，未发现问题。\n", "success")

            self.validation_result_text.tag_config("error", foreground="#FF0000", font=('Microsoft YaHei', 10, 'bold'))
            self.validation_result_text.tag_config("warning", foreground="#FFA500", font=('Microsoft YaHei', 10))
            self.validation_result_text.tag_config("sensitive", foreground="#FF6347", font=('Microsoft YaHei', 10))
            self.validation_result_text.tag_config("success", foreground="#00B050", font=('Microsoft YaHei', 10, 'bold'))
            self.validation_result_text.configure(state="disabled")

        if hasattr(self, 'validation_summary') and self.validation_summary.winfo_exists():
            if result.has_errors:
                self.validation_summary.configure(text=f"校验结果：存在 {len(result.errors)} 个错误，请修正后继续", foreground="#FF0000")
            elif result.has_warnings:
                self.validation_summary.configure(text=f"校验结果：存在 {len(result.warnings)} 个警告，建议检查后继续", foreground="#FFA500")
            else:
                self.validation_summary.configure(text="校验结果：全部通过 ✓", foreground="#00B050")

    def _refresh_generated_files_list(self):
        if not hasattr(self, 'generated_files_tree') or not self.generated_files_tree.winfo_exists():
            return

        for item in self.generated_files_tree.get_children():
            self.generated_files_tree.delete(item)

        if self.generated_files:
            for code, path in self.generated_files.items():
                material = self.material_list.get_material_by_code(code)
                name = material.name if material else code
                status = "已生成"
                self.generated_files_tree.insert("", "end", values=(code, name, status, path))
        else:
            self.generated_files_tree.insert("", "end", values=("", "（暂无生成文件）", "", ""))

    def _delete_record(self):
        record = self._get_selected_record()
        if not record:
            return

        if not messagebox.askyesno("确认", f"确定要删除这条记录吗？\n\n"
                                          f"项目: {record.get('product_name')}\n"
                                          f"批次: {record.get('batch_name', 'N/A')}\n"
                                          f"时间: {record.get('created_at')}"):
            return

        try:
            self.record_manager.delete_record(
                project_id=record.get('project_id', ''),
                batch_id=record.get('batch_id', ''),
                created_at=record.get('created_at', '')
            )
            self._refresh_records_list()
            messagebox.showinfo("成功", "记录已删除")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")

    def _refresh_project_info_ui(self):
        self.project_name_var.set(self.project_info.product_name or "")
        self.project_code_var.set(self.project_info.product_code or "")
        self.project_id_var.set(self.project_info.project_id or "")
        self.source_var.set(self.project_info.data_source or "")
        self.freq_var.set(self.project_info.update_frequency or "")
        self.scene_var.set(self.project_info.scene or "")
        self.volume_var.set(self.project_info.data_volume or "")
        self.email_var.set(self.project_info.contact_email or "")
        self.contact_var.set(self.project_info.contact_person or "")
        self.phone_var.set(self.project_info.contact_phone or "")
        self.valid_from_var.set(self.project_info.valid_from or "")
        self.valid_to_var.set(self.project_info.valid_to or "")

        if hasattr(self, 'limits_text') and self.limits_text.winfo_exists():
            self.limits_text.delete("1.0", tk.END)
            self.limits_text.insert("1.0", self.project_info.usage_limits or "")

        if hasattr(self, 'desc_text') and self.desc_text.winfo_exists():
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", self.project_info.data_description or "")

    def _current_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _update_step_buttons(self):
        pass


def main():
    root = tk.Tk()
    app = DataTradingToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()