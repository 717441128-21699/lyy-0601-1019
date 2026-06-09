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

        self._create_label_entry(basic_frame, "数据产品名称 *", 0, 0,
                                getattr(self.project_info, 'product_name', ''),
                                lambda v: setattr(self.project_info, 'product_name', v))
        self._create_label_entry(basic_frame, "产品编码", 0, 2,
                                getattr(self.project_info, 'product_code', ''),
                                lambda v: setattr(self.project_info, 'product_code', v))
        self._create_label_entry(basic_frame, "数据来源 *", 1, 0,
                                getattr(self.project_info, 'data_source', ''),
                                lambda v: setattr(self.project_info, 'data_source', v))
        self._create_label_combobox(basic_frame, "更新频率 *", 1, 2,
                                   UPDATE_FREQUENCIES,
                                   getattr(self.project_info, 'update_frequency', ''),
                                   lambda v: setattr(self.project_info, 'update_frequency', v))
        self._create_label_combobox(basic_frame, "交易场景 *", 2, 0,
                                   TRADING_SCENARIOS,
                                   getattr(self.project_info, 'trading_scene', ''),
                                   lambda v: setattr(self.project_info, 'trading_scene', v))
        self._create_label_entry(basic_frame, "数据量级", 2, 2,
                                getattr(self.project_info, 'data_volume', ''),
                                lambda v: setattr(self.project_info, 'data_volume', v))

        desc_frame = ttk.LabelFrame(scrollable_frame, text="产品描述", style="Section.TLabelframe", padding=15)
        desc_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(desc_frame, text="详细描述：").grid(row=0, column=0, sticky=tk.W, pady=5)
        desc_text = scrolledtext.ScrolledText(desc_frame, height=5, font=('Microsoft YaHei', 10))
        desc_text.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        if self.project_info.data_description:
            desc_text.insert(tk.END, self.project_info.data_description)
        desc_text.bind('<KeyRelease>', lambda e: setattr(self.project_info, 'data_description',
                                                        desc_text.get("1.0", tk.END).strip()))
        desc_frame.columnconfigure(1, weight=1)
        desc_frame.columnconfigure(2, weight=1)

        usage_frame = ttk.LabelFrame(scrollable_frame, text="使用限制", style="Section.TLabelframe", padding=15)
        usage_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(usage_frame, text="使用限制说明：").grid(row=0, column=0, sticky=tk.W, pady=5)
        usage_text = scrolledtext.ScrolledText(usage_frame, height=4, font=('Microsoft YaHei', 10))
        usage_text.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        if self.project_info.usage_restrictions:
            usage_text.insert(tk.END, self.project_info.usage_restrictions)
        usage_text.bind('<KeyRelease>', lambda e: setattr(self.project_info, 'usage_restrictions',
                                                         usage_text.get("1.0", tk.END).strip()))
        usage_frame.columnconfigure(1, weight=1)
        usage_frame.columnconfigure(2, weight=1)

        contact_frame = ttk.LabelFrame(scrollable_frame, text="联系信息", style="Section.TLabelframe", padding=15)
        contact_frame.pack(fill=tk.X, padx=10, pady=10)
        self._create_label_entry(contact_frame, "联系人 *", 0, 0,
                                getattr(self.project_info, 'contact_person', ''),
                                lambda v: setattr(self.project_info, 'contact_person', v))
        self._create_label_entry(contact_frame, "联系电话 *", 0, 2,
                                getattr(self.project_info, 'contact_phone', ''),
                                lambda v: setattr(self.project_info, 'contact_phone', v))
        self._create_label_entry(contact_frame, "电子邮箱", 1, 0,
                                getattr(self.project_info, 'contact_email', ''),
                                lambda v: setattr(self.project_info, 'contact_email', v))

        validity_frame = ttk.LabelFrame(scrollable_frame, text="授权有效期", style="Section.TLabelframe", padding=15)
        validity_frame.pack(fill=tk.X, padx=10, pady=10)
        self._create_label_entry(validity_frame, "有效期开始 * (YYYY-MM-DD)", 0, 0,
                                getattr(self.project_info, 'valid_from', ''),
                                lambda v: setattr(self.project_info, 'valid_from', v))
        self._create_label_entry(validity_frame, "有效期截止 * (YYYY-MM-DD)", 0, 2,
                                getattr(self.project_info, 'valid_to', ''),
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

        ttk.Label(main_frame, text="打包输出 - 提交预览",
                 font=('Microsoft YaHei', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(main_frame,
                 text="请先查看提交预览，确认内容无误后再生成压缩包。",
                 foreground="#666").pack(anchor=tk.W, pady=(0, 15))

        top_btn_frame = ttk.Frame(main_frame)
        top_btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(top_btn_frame, text="刷新预览", command=self._refresh_submission_preview,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(top_btn_frame, text="管理确认文件", command=self._manage_current_batch_files,
                   style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        preview_frame = ttk.LabelFrame(main_frame, text="提交预览", style="Section.TLabelframe", padding=15)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=16, font=('Microsoft YaHei', 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.insert(tk.END, "点击【刷新预览】按钮，查看即将打包的内容...\n")
        self.preview_text.configure(state="disabled")

        if self.validation_result and self.validation_result.has_errors:
            warning_frame = ttk.Frame(main_frame)
            warning_frame.pack(fill=tk.X, pady=10)
            ttk.Label(warning_frame, text="⚠ 校验存在错误，建议返回修正后再打包。",
                     foreground="#FF0000", font=('Microsoft YaHei', 11, 'bold')).pack(side=tk.LEFT)
            self.ignore_errors_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(warning_frame, text="忽略错误继续打包", variable=self.ignore_errors_var).pack(side=tk.LEFT, padx=20)

        bottom_btn_frame = ttk.Frame(main_frame)
        bottom_btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(bottom_btn_frame, text="确认并生成压缩包", command=self._build_package,
                   style="Success.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frame, text="查看提交清单", command=self._view_checklist,
                   style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frame, text="打开压缩包", command=self._open_zip,
                   style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frame, text="打开输出目录", command=self._open_output_dir,
                   style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="打包日志", style="Section.TLabelframe", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.package_log = scrolledtext.ScrolledText(log_frame, height=8, font=('Consolas', 10))
        self.package_log.pack(fill=tk.BOTH, expand=True)
        self.package_log.insert(tk.END, "确认预览内容无误后，点击【确认并生成压缩包】按钮...\n")
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
        packager = PackageOutput(self.project_info, self.material_list,
                                  self.generated_files, self.validation_result)
        preview = packager.get_submission_preview()
        self.submission_preview = preview

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)

        current_batch = self.material_list.get_current_batch()
        batch_info = f"当前批次：{current_batch.batch_name} ({current_batch.batch_id})" if current_batch else "当前批次：未设置"

        self.preview_text.insert(tk.END, f"提交预览报告\n{'='*60}\n\n")
        self.preview_text.insert(tk.END, f"生成时间：{self._current_time()}\n")
        self.preview_text.insert(tk.END, f"{batch_info}\n\n")

        self.preview_text.insert(tk.END, f"一、待打包文件 ({len(preview.files_to_include)} 个)\n")
        self.preview_text.insert(tk.END, f"{'-'*60}\n")
        if preview.files_to_include:
            for i, f in enumerate(preview.files_to_include, 1):
                status = "✓ 已确认" if f.get('confirmed') else "○ 未确认"
                self.preview_text.insert(tk.END, f"{i:2d}. [{status}] {f['name']}\n")
                self.preview_text.insert(tk.END, f"     来源: {f['source']}\n")
                if f.get('size'):
                    self.preview_text.insert(tk.END, f"     大小: {f['size']}\n")
        else:
            self.preview_text.insert(tk.END, "  (无待打包文件)\n")

        self.preview_text.insert(tk.END, f"\n二、缺失的必填材料 ({len(preview.missing_required)} 个)\n")
        self.preview_text.insert(tk.END, f"{'-'*60}\n")
        if preview.missing_required:
            for m in preview.missing_required:
                self.preview_text.insert(tk.END, f"  ✗ {m.code} - {m.name}\n")
        else:
            self.preview_text.insert(tk.END, "  ✓ 所有必填材料已齐全\n")

        self.preview_text.insert(tk.END, f"\n三、缺失的选填材料 ({len(preview.missing_optional)} 个)\n")
        self.preview_text.insert(tk.END, f"{'-'*60}\n")
        if preview.missing_optional:
            for m in preview.missing_optional:
                self.preview_text.insert(tk.END, f"  ○ {m.code} - {m.name}\n")
        else:
            self.preview_text.insert(tk.END, "  ✓ 所有选填材料已齐全\n")

        self.preview_text.insert(tk.END, f"\n四、敏感词警告 ({len(preview.sensitive_warnings)} 条)\n")
        self.preview_text.insert(tk.END, f"{'-'*60}\n")
        if preview.sensitive_warnings:
            for i, w in enumerate(preview.sensitive_warnings, 1):
                self.preview_text.insert(tk.END, f"{i:2d}. 文件: {w['file']}\n")
                self.preview_text.insert(tk.END, f"     敏感词: {', '.join(w['words'])}\n")
                self.preview_text.insert(tk.END, f"     位置: 第 {w['line']} 行\n")
        else:
            self.preview_text.insert(tk.END, "  ✓ 未检测到敏感词\n")

        self.preview_text.insert(tk.END, f"\n五、校验错误 ({len(preview.validation_errors)} 条)\n")
        self.preview_text.insert(tk.END, f"{'-'*60}\n")
        if preview.validation_errors:
            for e in preview.validation_errors:
                self.preview_text.insert(tk.END, f"  ✗ {e}\n")
        else:
            self.preview_text.insert(tk.END, "  ✓ 无校验错误\n")

        self.preview_text.insert(tk.END, f"\n六、校验警告 ({len(preview.validation_warnings)} 条)\n")
        self.preview_text.insert(tk.END, f"{'-'*60}\n")
        if preview.validation_warnings:
            for w in preview.validation_warnings:
                self.preview_text.insert(tk.END, f"  ⚠ {w}\n")
        else:
            self.preview_text.insert(tk.END, "  ✓ 无校验警告\n")

        self.preview_text.insert(tk.END, f"\n{'='*60}\n")
        if preview.can_submit:
            self.preview_text.insert(tk.END, "✓ 可以提交\n", "ok")
        else:
            self.preview_text.insert(tk.END, "✗ 存在问题，请先修正后再提交\n", "error")

        self.preview_text.tag_configure("ok", foreground="#2e7d32")
        self.preview_text.tag_configure("error", foreground="#c62828")
        self.preview_text.configure(state="disabled")

        self._update_validation_display(preview)
        self._update_package_summary(preview)

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
            messagebox.showwarning("提示", "请先刷新预览")
            return

        if not self.submission_preview.can_submit:
            if not messagebox.askyesno("确认", "存在必填材料缺失或校验错误，确定要继续打包吗？"):
                return

        try:
            self.package_log.configure(state="normal")
            self.package_log.delete("1.0", tk.END)
            self.package_log.insert(tk.END, f"开始打包...\n时间: {self._current_time()}\n\n")
            self.package_log.update()

            packager = PackageOutput(self.project_info, self.material_list,
                                      self.generated_files, self.validation_result)
            result = packager.build_package(ignore_errors=not self.submission_preview.can_submit)

            self.package_log.insert(tk.END, f"打包完成！\n")
            self.package_log.insert(tk.END, f"压缩包路径: {result['zip_path']}\n")
            self.package_log.insert(tk.END, f"包含文件: {result['file_count']} 个\n")
            self.package_log.insert(tk.END, f"清单文件: {result['checklist_path']}\n")

            self.last_zip_path = result['zip_path']
            self.last_checklist_path = result['checklist_path']

            self._save_generation_record(result)

            self.package_log.insert(tk.END, f"\n✓ 记录已保存到历史记录\n")
            self.package_log.configure(state="disabled")

            messagebox.showinfo("成功", f"打包完成！\n\n压缩包: {result['zip_path']}")

        except Exception as e:
            self.package_log.insert(tk.END, f"\n✗ 打包失败: {str(e)}\n")
            self.package_log.configure(state="disabled")
            messagebox.showerror("错误", f"打包失败: {str(e)}")

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
        self.search_scene = ttk.Combobox(row2, values=[""] + SCENES, width=25, state="readonly")
        self.search_scene.pack(side=tk.LEFT, padx=5)
        self.search_scene.current(0)

        ttk.Label(row2, text="开始日期:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.search_start_date = ttk.Entry(row2, width=15)
        self.search_start_date.pack(side=tk.LEFT, padx=5)
        self.search_start_date.insert(0, "")

        ttk.Label(row2, text="结束日期:", width=10).pack(side=tk.LEFT, padx=(10, 0))
        self.search_end_date = ttk.Entry(row2, width=15)
        self.search_end_date.pack(side=tk.LEFT, padx=5)
        self.search_end_date.insert(0, "")

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

        records = self.record_manager.search_records(
            project_id=project_id,
            product_code=product_code,
            product_name=product_name,
            contact_person=contact_person,
            start_date=start_date,
            end_date=end_date,
            scene=scene
        )

        self._populate_records_tree(records)

    def _clear_search_filters(self):
        self.search_project_id.delete(0, tk.END)
        self.search_product_code.delete(0, tk.END)
        self.search_product_name.delete(0, tk.END)
        self.search_contact.delete(0, tk.END)
        self.search_scene.current(0)
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
        created_at = values[7]

        records = self.record_manager.search_records(
            project_id=project_id,
            product_code=product_code
        )
        for rec in records:
            if rec.get('created_at') == created_at:
                return rec
        return None

    def _view_record_detail(self):
        record = self._get_selected_record()
        if not record:
            return

        win = tk.Toplevel(self.root)
        win.title(f"记录详情 - {record['product_name']}")
        win.geometry("900x650")
        win.grab_set()

        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        info_frame = ttk.Frame(notebook, padding=10)
        notebook.add(info_frame, text="项目信息")

        info_text = scrolledtext.ScrolledText(info_frame, font=('Consolas', 10))
        info_text.pack(fill=tk.BOTH, expand=True)

        info_text.insert(tk.END, "项目信息\n")
        info_text.insert(tk.END, f"{'='*60}\n\n")
        pi = record.get('project_info', {})
        for key, value in pi.items():
            info_text.insert(tk.END, f"{key}: {value}\n")

        materials_frame = ttk.Frame(notebook, padding=10)
        notebook.add(materials_frame, text="材料状态")

        mat_text = scrolledtext.ScrolledText(materials_frame, font=('Consolas', 10))
        mat_text.pack(fill=tk.BOTH, expand=True)

        mat_text.insert(tk.END, "材料清单\n")
        mat_text.insert(tk.END, f"{'='*60}\n\n")
        materials = record.get('materials', {}).get('materials', [])
        for m in materials:
            status = "已上传" if m.get('file_path') else "未上传"
            req = "必填" if m.get('required') else "选填"
            mat_text.insert(tk.END, f"[{req}] {m['code']} - {m['name']} ({status})\n")
            if m.get('file_path'):
                mat_text.insert(tk.END, f"     文件: {m['file_path']}\n")

        val_frame = ttk.Frame(notebook, padding=10)
        notebook.add(val_frame, text="校验报告")

        val_text = scrolledtext.ScrolledText(val_frame, font=('Consolas', 10))
        val_text.pack(fill=tk.BOTH, expand=True)

        vr = record.get('validation_result', {})
        val_text.insert(tk.END, "校验报告\n")
        val_text.insert(tk.END, f"{'='*60}\n\n")
        val_text.insert(tk.END, f"校验时间: {vr.get('timestamp', 'N/A')}\n")
        val_text.insert(tk.END, f"通过: {'是' if vr.get('passed') else '否'}\n\n")

        val_text.insert(tk.END, "错误:\n")
        for e in vr.get('errors', []):
            val_text.insert(tk.END, f"  ✗ {e}\n")

        val_text.insert(tk.END, "\n警告:\n")
        for w in vr.get('warnings', []):
            val_text.insert(tk.END, f"  ⚠ {w}\n")

        val_text.insert(tk.END, "\n敏感词警告:\n")
        for sw in vr.get('sensitive_warnings', []):
            val_text.insert(tk.END, f"  ⚠ 文件: {sw.get('file')}, 敏感词: {', '.join(sw.get('words', []))}\n")

        files_frame = ttk.Frame(notebook, padding=10)
        notebook.add(files_frame, text="生成文件")

        files_text = scrolledtext.ScrolledText(files_frame, font=('Consolas', 10))
        files_text.pack(fill=tk.BOTH, expand=True)

        files_text.insert(tk.END, "生成的文件\n")
        files_text.insert(tk.END, f"{'='*60}\n\n")
        files_text.insert(tk.END, f"压缩包: {record.get('zip_path', 'N/A')}\n")
        files_text.insert(tk.END, f"清单文件: {record.get('checklist_path', 'N/A')}\n")
        files_text.insert(tk.END, f"批次: {record.get('batch_name', 'N/A')} ({record.get('batch_id', 'N/A')})\n\n")

        gf = record.get('generated_files', {})
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
            self.record_manager.restore_record(
                record,
                self.project_info,
                self.material_list,
                self.generated_files,
                self.validation_result
            )

            self._refresh_project_info_ui()
            self._refresh_materials_tree()
            self._refresh_material_status()
            self._refresh_batch_list()
            self._update_step_buttons()

            if win:
                win.destroy()

            messagebox.showinfo("成功", "记录已恢复！\n\n"
                                      f"项目: {record.get('product_name')}\n"
                                      f"批次: {record.get('batch_name', 'N/A')}\n"
                                      f"时间: {record.get('created_at')}")

        except Exception as e:
            messagebox.showerror("错误", f"恢复失败: {str(e)}")

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
        self.limits_text.delete("1.0", tk.END)
        self.limits_text.insert("1.0", self.project_info.usage_limits or "")
        self.contact_var.set(self.project_info.contact_person or "")
        self.phone_var.set(self.project_info.contact_phone or "")
        self.valid_from_var.set(self.project_info.valid_from or "")
        self.valid_to_var.set(self.project_info.valid_to or "")

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