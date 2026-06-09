import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import (
    ProjectInfo,
    MaterialList,
    TemplateGenerator,
    ContentValidator,
    PackageOutput,
    RecordManager
)
from config import TRADING_SCENARIOS, UPDATE_FREQUENCIES, REQUIRED_MATERIALS, OUTPUT_DIR


class DataTradingToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("数据要素交易材料生成自动化工具")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 700)

        self.project_info = ProjectInfo()
        self.material_list = MaterialList()
        self.record_manager = RecordManager()
        self.generated_files = {}
        self.validation_result = None
        self.package_result = None
        self.current_step = 0

        self.steps = [
            ("项目信息", self._create_step1),
            ("材料清单", self._create_step2),
            ("模板生成", self._create_step3),
            ("内容校验", self._create_step4),
            ("打包输出", self._create_step5)
        ]

        self._setup_styles()
        self._create_main_layout()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Step.TFrame", background="#f5f7fa")
        style.configure("Nav.TButton", padding=10, font=('Microsoft YaHei', 10))
        style.configure("Primary.TButton", padding=10, font=('Microsoft YaHei', 10, 'bold'),
                        background="#4472C4", foreground="white")
        style.map("Primary.TButton",
                  background=[('active', '#335EA8'), ('disabled', '#B0B0B0')])
        style.configure("StepIndicator.TLabel", font=('Microsoft YaHei', 10),
                        background="#f5f7fa", padding=10)
        style.configure("StepIndicator.Active.TLabel", font=('Microsoft YaHei', 10, 'bold'),
                        background="#4472C4", foreground="white", padding=10)
        style.configure("StepIndicator.Completed.TLabel", font=('Microsoft YaHei', 10),
                        background="#00B050", foreground="white", padding=10)
        style.configure("Section.TLabelframe", font=('Microsoft YaHei', 11, 'bold'))
        style.configure("Section.TLabelframe.Label", font=('Microsoft YaHei', 11, 'bold'))

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
        elif self.current_step == 2:
            if not self._validate_step3():
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
                    self.package_result.get("zip_path", "")
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

        columns = ("code", "name", "required", "status", "source", "file")
        self.materials_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=12)
        self.materials_tree.heading("code", text="编码")
        self.materials_tree.heading("name", text="材料名称")
        self.materials_tree.heading("required", text="必填")
        self.materials_tree.heading("status", text="状态")
        self.materials_tree.heading("source", text="来源")
        self.materials_tree.heading("file", text="文件路径")
        self.materials_tree.column("code", width=80, anchor=tk.CENTER)
        self.materials_tree.column("name", width=180)
        self.materials_tree.column("required", width=60, anchor=tk.CENTER)
        self.materials_tree.column("status", width=100, anchor=tk.CENTER)
        self.materials_tree.column("source", width=100, anchor=tk.CENTER)
        self.materials_tree.column("file", width=300)
        self.materials_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        self._refresh_materials_tree()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="上传材料", command=self._upload_material, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="移除材料", command=self._remove_material, style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="打开文件", command=self._open_material_file, style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        summary = self.material_list.get_summary()
        status_frame = ttk.LabelFrame(main_frame, text="材料统计", style="Section.TLabelframe", padding=15)
        status_frame.pack(fill=tk.X, pady=15)

        status_text = (
            f"材料总数：{summary['total']}   |   "
            f"必填材料：{summary['required']}   |   "
            f"已提供：{summary['provided']}   |   "
            f"自动生成：{summary['generated']}   |   "
            f"缺失必填：{summary['missing_required']}"
        )
        status_color = "#00B050" if summary["complete"] else "#FF0000"
        status_label = ttk.Label(status_frame, text=status_text, foreground=status_color,
                                font=('Microsoft YaHei', 11, 'bold'))
        status_label.pack(anchor=tk.W)

        if not summary["complete"]:
            missing = self.material_list.get_missing_required()
            missing_names = "、".join([f"{m.name}({m.code})" for m in missing])
            ttk.Label(status_frame, text=f"缺失必填材料：{missing_names}", foreground="#FF0000").pack(anchor=tk.W, pady=5)
            ttk.Label(status_frame, text="说明：CPMS(产品说明)、SQMS(授权说明)、YLDQ(样例字段清单) 将在下一步自动生成，"
                     "其他必填材料需在此处上传。", foreground="#666").pack(anchor=tk.W, pady=5)

    def _refresh_materials_tree(self):
        for i in self.materials_tree.get_children():
            self.materials_tree.delete(i)
        for item in self.material_list.items:
            status = "已准备" if item.provided or item.generated else "未准备"
            source = "自动生成" if item.generated else ("用户上传" if item.provided else "-")
            required = "是" if item.required else "否"
            file_path = item.file_path if item.file_path else "-"
            tags = ()
            if item.required and not item.provided and not item.generated:
                tags = ("missing",)
            self.materials_tree.insert("", tk.END, values=(
                item.code, item.name, required, status, source, file_path
            ), tags=tags)
        self.materials_tree.tag_configure("missing", background="#FFEBEB")

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
            self._refresh_materials_tree()

    def _remove_material(self):
        selected = self.materials_tree.selection()
        if not selected:
            return
        item = self.materials_tree.item(selected[0])
        code = item['values'][0]
        mat_item = self.material_list.get_item(code)
        if mat_item and mat_item.generated:
            messagebox.showinfo("提示", "自动生成的材料无法移除")
            return
        if mat_item:
            mat_item.provided = False
            mat_item.file_path = ""
            self._refresh_materials_tree()

    def _open_material_file(self):
        selected = self.materials_tree.selection()
        if not selected:
            return
        item = self.materials_tree.item(selected[0])
        file_path = item['values'][5]
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

        ttk.Label(main_frame, text="模板生成",
                 font=('Microsoft YaHei', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(main_frame,
                 text="系统将根据您填写的项目信息，自动生成产品说明文档、授权说明文档和样例字段清单。",
                 foreground="#666").pack(anchor=tk.W, pady=(0, 15))

        options_frame = ttk.LabelFrame(main_frame, text="生成选项", style="Section.TLabelframe", padding=15)
        options_frame.pack(fill=tk.X, pady=10)

        self.gen_cpms = tk.BooleanVar(value=True)
        self.gen_sqms = tk.BooleanVar(value=True)
        self.gen_yldq = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="生成产品说明文档 (CPMS)", variable=self.gen_cpms).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Checkbutton(options_frame, text="生成授权说明文档 (SQMS)", variable=self.gen_sqms).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Checkbutton(options_frame, text="生成样例字段清单 (YLDQ)", variable=self.gen_yldq).grid(row=2, column=0, sticky=tk.W, pady=5)

        preview_frame = ttk.LabelFrame(main_frame, text="生成结果预览", style="Section.TLabelframe", padding=15)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.gen_log = scrolledtext.ScrolledText(preview_frame, height=12, font=('Consolas', 10))
        self.gen_log.pack(fill=tk.BOTH, expand=True)
        self.gen_log.insert(tk.END, "点击【开始生成】按钮，系统将自动生成文档...\n")
        self.gen_log.configure(state="disabled")

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="开始生成", command=self._generate_templates, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="打开输出目录", command=self._open_output_dir, style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重新生成", command=self._regenerate_templates, style="Nav.TButton").pack(side=tk.LEFT, padx=5)

    def _generate_templates(self):
        self.gen_log.configure(state="normal")
        self.gen_log.delete("1.0", tk.END)
        self.gen_log.insert(tk.END, f"开始生成文档...\n项目：{self.project_info.product_name}\n{'='*50}\n\n")

        generator = TemplateGenerator(self.project_info)
        generated_count = 0

        try:
            if self.gen_cpms.get():
                self.gen_log.insert(tk.END, "[1/3] 正在生成产品说明文档... ")
                path = generator.generate_product_description()
                self.generated_files["product_desc"] = path
                self.material_list.mark_generated("CPMS", True)
                self.gen_log.insert(tk.END, f"✓ 完成\n   路径：{path}\n\n")
                generated_count += 1
            if self.gen_sqms.get():
                self.gen_log.insert(tk.END, "[2/3] 正在生成授权说明文档... ")
                path = generator.generate_authorization_description()
                self.generated_files["auth_desc"] = path
                self.material_list.mark_generated("SQMS", True)
                self.gen_log.insert(tk.END, f"✓ 完成\n   路径：{path}\n\n")
                generated_count += 1
            if self.gen_yldq.get():
                self.gen_log.insert(tk.END, "[3/3] 正在生成样例字段清单... ")
                path = generator.generate_sample_fields_list()
                self.generated_files["sample_fields"] = path
                self.material_list.mark_generated("YLDQ", True)
                self.gen_log.insert(tk.END, f"✓ 完成\n   路径：{path}\n\n")
                generated_count += 1

            self.gen_log.insert(tk.END, f"{'='*50}\n生成完成！共生成 {generated_count} 个文档。\n")
            self.gen_log.see(tk.END)
        except Exception as e:
            self.gen_log.insert(tk.END, f"✗ 出错：{str(e)}\n")
            messagebox.showerror("生成失败", f"文档生成时出错：{str(e)}")
        finally:
            self.gen_log.configure(state="disabled")

    def _regenerate_templates(self):
        self.generated_files = {}
        self._generate_templates()

    def _validate_step3(self):
        if not self.generated_files:
            if messagebox.askyesno("提示", "尚未生成任何文档，确定要继续吗？"):
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
        self.validation_result_text.insert(tk.END, f"产品名称：{self.project_info.product_name}\n\n")

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
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _create_step5(self):
        main_frame = ttk.Frame(self.content_container, style="Step.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(main_frame, text="打包输出",
                 font=('Microsoft YaHei', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(main_frame,
                 text="系统将按平台目录命名规则重命名文件，生成提交清单，并打包为压缩包。",
                 foreground="#666").pack(anchor=tk.W, pady=(0, 15))

        if self.validation_result and self.validation_result.has_errors:
            warning_frame = ttk.Frame(main_frame)
            warning_frame.pack(fill=tk.X, pady=10)
            ttk.Label(warning_frame, text="⚠ 校验存在错误，建议返回修正后再打包。",
                     foreground="#FF0000", font=('Microsoft YaHei', 11, 'bold')).pack(side=tk.LEFT)
            self.ignore_errors_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(warning_frame, text="忽略错误继续打包", variable=self.ignore_errors_var).pack(side=tk.LEFT, padx=20)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="开始打包", command=self._build_package, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="查看提交清单", command=self._view_checklist, style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="打开压缩包", command=self._open_zip, style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="打开输出目录", command=self._open_output_dir, style="Nav.TButton").pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="打包日志", style="Section.TLabelframe", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.package_log = scrolledtext.ScrolledText(log_frame, height=15, font=('Consolas', 10))
        self.package_log.pack(fill=tk.BOTH, expand=True)
        self.package_log.insert(tk.END, "点击【开始打包】按钮，系统将整理所有材料并生成压缩包...\n")
        self.package_log.configure(state="disabled")

        self.package_summary = ttk.Label(main_frame, text="", font=('Microsoft YaHei', 11, 'bold'))
        self.package_summary.pack(anchor=tk.W, pady=10)

    def _build_package(self):
        if self.validation_result and self.validation_result.has_errors:
            if not hasattr(self, 'ignore_errors_var') or not self.ignore_errors_var.get():
                messagebox.showwarning("校验错误", "请先修正校验错误，或勾选【忽略错误继续打包】")
                return

        self.package_log.configure(state="normal")
        self.package_log.delete("1.0", tk.END)
        self.package_log.insert(tk.END, f"开始打包...\n{'='*50}\n\n")

        try:
            packager = PackageOutput(self.project_info, self.material_list, self.generated_files)
            self.package_result = packager.build_package(
                ignore_errors=getattr(self, 'ignore_errors_var', tk.BooleanVar(value=False)).get()
            )

            if self.package_result.get("success"):
                self.package_log.insert(tk.END, "✓ 文件收集完成\n")
                self.package_log.insert(tk.END, "✓ 按平台规则重命名文件\n")
                self.package_log.insert(tk.END, "✓ 生成提交清单\n")
                self.package_log.insert(tk.END, "✓ 创建压缩包\n\n")
                self.package_log.insert(tk.END, f"{'='*50}\n打包完成！\n\n")
                self.package_log.insert(tk.END, f"生成文件：\n")
                for f in self.package_result.get("output_files", []):
                    self.package_log.insert(tk.END, f"  - {Path(f).name}\n")
                self.package_log.insert(tk.END, f"\n压缩包路径：\n  {self.package_result.get('zip_path')}\n")

                self.package_summary.configure(
                    text=f"打包完成！共包含 {len(self.package_result.get('output_files', []))} 个文件",
                    foreground="#00B050"
                )
            else:
                errors = "\n".join(self.package_result.get("errors", []))
                self.package_log.insert(tk.END, f"✗ 打包失败：{errors}\n", "error")
                self.package_summary.configure(text="打包失败", foreground="#FF0000")
        except Exception as e:
            self.package_log.insert(tk.END, f"✗ 打包出错：{str(e)}\n", "error")
            messagebox.showerror("打包失败", f"打包时出错：{str(e)}")
        finally:
            self.package_log.tag_config("error", foreground="#FF0000")
            self.package_log.configure(state="disabled")

    def _view_checklist(self):
        if self.package_result and self.package_result.get("checklist_path"):
            path = self.package_result["checklist_path"]
            if Path(path).exists():
                try:
                    if sys.platform.startswith('win'):
                        os.startfile(path)
                    elif sys.platform == 'darwin':
                        os.system(f'open "{path}"')
                    else:
                        os.system(f'xdg-open "{path}"')
                except Exception as e:
                    messagebox.showerror("错误", f"无法打开文件：{str(e)}")
            else:
                messagebox.showwarning("提示", "提交清单尚未生成")
        else:
            messagebox.showwarning("提示", "请先完成打包")

    def _open_zip(self):
        if self.package_result and self.package_result.get("zip_path"):
            path = self.package_result["zip_path"]
            if Path(path).exists():
                try:
                    if sys.platform.startswith('win'):
                        os.startfile(Path(path).parent)
                    elif sys.platform == 'darwin':
                        os.system(f'open "{Path(path).parent}"')
                    else:
                        os.system(f'xdg-open "{Path(path).parent}"')
                except Exception as e:
                    messagebox.showerror("错误", f"无法打开目录：{str(e)}")
            else:
                messagebox.showwarning("提示", "压缩包尚未生成")
        else:
            messagebox.showwarning("提示", "请先完成打包")

    def _show_records(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("历史记录")
        dialog.geometry("1000x600")
        dialog.transient(self.root)

        search_frame = ttk.Frame(dialog, padding=10)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="关键词：").pack(side=tk.LEFT, padx=5)
        keyword_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=keyword_var, width=20).pack(side=tk.LEFT, padx=5)

        ttk.Label(search_frame, text="场景：").pack(side=tk.LEFT, padx=5)
        scene_var = tk.StringVar(value="")
        scene_cb = ttk.Combobox(search_frame, values=[""] + TRADING_SCENARIOS,
                               textvariable=scene_var, state="readonly", width=12)
        scene_cb.pack(side=tk.LEFT, padx=5)

        def search():
            records = self.record_manager.search_records(
                keyword=keyword_var.get(),
                scene=scene_var.get()
            )
            _refresh_records(records)

        ttk.Button(search_frame, text="搜索", command=search, style="Primary.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(search_frame, text="重置", command=lambda: _refresh_records(self.record_manager.get_all_records())).pack(side=tk.LEFT)

        stats = self.record_manager.get_statistics()
        stats_text = f"总记录：{stats['total']}  |  近30天：{stats['last_30_days']}  |  有错误：{stats['with_errors']}  |  有警告：{stats['with_warnings']}"
        ttk.Label(search_frame, text=stats_text, foreground="#666").pack(side=tk.RIGHT)

        columns = ("generated_at", "product_name", "product_code", "trading_scene",
                  "contact_person", "material_count", "has_errors", "has_warnings")
        tree = ttk.Treeview(dialog, columns=columns, show="headings", height=20)
        tree.heading("generated_at", text="生成时间")
        tree.heading("product_name", text="产品名称")
        tree.heading("product_code", text="产品编码")
        tree.heading("trading_scene", text="交易场景")
        tree.heading("contact_person", text="联系人")
        tree.heading("material_count", text="材料数")
        tree.heading("has_errors", text="错误")
        tree.heading("has_warnings", text="警告")
        tree.column("generated_at", width=150)
        tree.column("product_name", width=200)
        tree.column("product_code", width=120)
        tree.column("trading_scene", width=100)
        tree.column("contact_person", width=80)
        tree.column("material_count", width=70, anchor=tk.CENTER)
        tree.column("has_errors", width=60, anchor=tk.CENTER)
        tree.column("has_warnings", width=60, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def _refresh_records(records):
            for i in tree.get_children():
                tree.delete(i)
            for record in records:
                val_result = record.get("validation_result", {})
                mat_summary = record.get("material_summary", {})
                has_err = "是" if val_result.get("has_errors", False) else "否"
                has_warn = "是" if val_result.get("has_warnings", False) else "否"
                tags = ("error",) if val_result.get("has_errors", False) else ()
                tree.insert("", tk.END, values=(
                    record.get("generated_at", "")[:19],
                    record.get("product_name", ""),
                    record.get("product_code", ""),
                    record.get("trading_scene", ""),
                    record.get("contact_person", ""),
                    mat_summary.get("provided", 0),
                    has_err,
                    has_warn
                ), tags=tags)
            tree.tag_configure("error", background="#FFEBEB")

        _refresh_records(self.record_manager.get_all_records())

        def load_record():
            selected = tree.selection()
            if not selected:
                return
            item = tree.item(selected[0])
            product_code = item['values'][2]
            record = self.record_manager.get_record(product_code)
            if not record:
                records = self.record_manager.get_all_records()
                for r in records:
                    if r.get("product_name") == item['values'][1]:
                        record = r
                        break
            if record:
                self.project_info.from_dict(record.get("project_info", {}))
                self.material_list.from_dict(record.get("materials", []))
                self.generated_files = record.get("generated_files", {})
                self.current_step = 0
                self._show_current_step()
                dialog.destroy()
                messagebox.showinfo("成功", "记录已加载，可继续编辑")

        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="加载此记录", command=load_record, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="查看详情", command=lambda: self._view_record_detail(tree, dialog), style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除记录", command=lambda: self._delete_record(tree), style="Nav.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=dialog.destroy).pack(side=tk.RIGHT)

    def _view_record_detail(self, tree, parent_dialog):
        selected = tree.selection()
        if not selected:
            return
        item = tree.item(selected[0])
        product_name = item['values'][1]
        records = self.record_manager.get_all_records()
        record = None
        for r in records:
            if r.get("product_name") == product_name:
                record = r
                break
        if not record:
            return

        detail_dialog = tk.Toplevel(parent_dialog)
        detail_dialog.title("记录详情")
        detail_dialog.geometry("700x500")

        detail_text = scrolledtext.ScrolledText(detail_dialog, font=('Consolas', 9))
        detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        import json
        detail_text.insert(tk.END, json.dumps(record, ensure_ascii=False, indent=2))
        detail_text.configure(state="disabled")

        ttk.Button(detail_dialog, text="关闭", command=detail_dialog.destroy).pack(pady=10)

    def _delete_record(self, tree):
        selected = tree.selection()
        if not selected:
            return
        if not messagebox.askyesno("确认", "确定要删除这条记录吗？"):
            return
        item = tree.item(selected[0])
        product_name = item['values'][1]
        records = self.record_manager.get_all_records()
        for r in records:
            if r.get("product_name") == product_name:
                self.record_manager.delete_record(r.get("project_id", ""))
                break
        for i in tree.get_children():
            tree.delete(i)
        for record in self.record_manager.get_all_records():
            val_result = record.get("validation_result", {})
            mat_summary = record.get("material_summary", {})
            has_err = "是" if val_result.get("has_errors", False) else "否"
            has_warn = "是" if val_result.get("has_warnings", False) else "否"
            tags = ("error",) if val_result.get("has_errors", False) else ()
            tree.insert("", tk.END, values=(
                record.get("generated_at", "")[:19],
                record.get("product_name", ""),
                record.get("product_code", ""),
                record.get("trading_scene", ""),
                record.get("contact_person", ""),
                mat_summary.get("provided", 0),
                has_err,
                has_warn
            ), tags=tags)
        tree.tag_configure("error", background="#FFEBEB")
        messagebox.showinfo("成功", "记录已删除")


def main():
    root = tk.Tk()
    app = DataTradingToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
