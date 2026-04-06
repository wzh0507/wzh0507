"""
meal_planner.py - 每周膳食规划桌面应用程序
使用 Python 标准库 tkinter / ttk 构建，无需第三方依赖。
"""

import json
import os
import random
import tkinter as tk
from tkinter import ttk, messagebox

# ──────────────────────────────────────────────
#  常量定义
# ──────────────────────────────────────────────

DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
MEALS = ["早餐", "午餐", "晚餐"]

# 持久化文件路径（与脚本同目录）
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meal_records.json")

# ──────────────────────────────────────────────
#  内置食谱数据
#  每个食谱：name, calories(kcal), protein(g), fat(g), carbs(g)
# ──────────────────────────────────────────────

RECIPES = {
    "早餐": [
        {"name": "燕麦粥", "calories": 150, "protein": 5, "fat": 3, "carbs": 27},
        {"name": "鸡蛋三明治", "calories": 320, "protein": 15, "fat": 12, "carbs": 38},
        {"name": "豆浆油条", "calories": 420, "protein": 14, "fat": 18, "carbs": 52},
        {"name": "全麦面包+牛奶", "calories": 280, "protein": 12, "fat": 6, "carbs": 42},
        {"name": "皮蛋瘦肉粥", "calories": 200, "protein": 10, "fat": 5, "carbs": 30},
        {"name": "煎饼果子", "calories": 380, "protein": 12, "fat": 14, "carbs": 50},
        {"name": "紫薯银耳羹", "calories": 130, "protein": 2, "fat": 1, "carbs": 30},
        {"name": "希腊酸奶+蓝莓", "calories": 180, "protein": 12, "fat": 4, "carbs": 22},
    ],
    "午餐": [
        {"name": "红烧肉米饭", "calories": 680, "protein": 28, "fat": 32, "carbs": 72},
        {"name": "番茄鸡蛋面", "calories": 520, "protein": 18, "fat": 12, "carbs": 85},
        {"name": "清炒蔬菜+米饭", "calories": 420, "protein": 10, "fat": 8, "carbs": 78},
        {"name": "鸡胸肉沙拉", "calories": 350, "protein": 32, "fat": 10, "carbs": 28},
        {"name": "麻婆豆腐米饭", "calories": 580, "protein": 22, "fat": 20, "carbs": 76},
        {"name": "扬州炒饭", "calories": 610, "protein": 20, "fat": 18, "carbs": 88},
        {"name": "牛肉拉面", "calories": 650, "protein": 30, "fat": 20, "carbs": 80},
        {"name": "糖醋排骨米饭", "calories": 720, "protein": 30, "fat": 35, "carbs": 76},
    ],
    "晚餐": [
        {"name": "清蒸鱼+米饭", "calories": 480, "protein": 30, "fat": 8, "carbs": 65},
        {"name": "蔬菜汤+杂粮饭", "calories": 320, "protein": 12, "fat": 5, "carbs": 58},
        {"name": "蒜蓉虾仁炒饭", "calories": 560, "protein": 28, "fat": 14, "carbs": 74},
        {"name": "西红柿牛腩汤饭", "calories": 620, "protein": 32, "fat": 22, "carbs": 68},
        {"name": "清炒时蔬+玉米饼", "calories": 380, "protein": 8, "fat": 6, "carbs": 70},
        {"name": "鸡肉蘑菇焖饭", "calories": 540, "protein": 28, "fat": 12, "carbs": 72},
        {"name": "三文鱼沙拉", "calories": 440, "protein": 35, "fat": 20, "carbs": 18},
        {"name": "排骨莲藕汤+米饭", "calories": 590, "protein": 26, "fat": 18, "carbs": 75},
    ],
}


# ──────────────────────────────────────────────
#  数据持久化工具函数
# ──────────────────────────────────────────────

def load_records() -> dict:
    """从 JSON 文件加载历史记录，返回嵌套字典 records[day][meal] = recipe_dict"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[警告] 无法加载历史记录文件，将使用空记录：{e}")
    # 初始化空记录
    return {day: {meal: None for meal in MEALS} for day in DAYS}


def save_records(records: dict) -> None:
    """将当前记录保存到 JSON 文件"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except OSError as e:
        messagebox.showerror("保存失败", f"无法保存数据：{e}")


# ──────────────────────────────────────────────
#  弹出推荐选择对话框
# ──────────────────────────────────────────────

class RecommendDialog(tk.Toplevel):
    """随机推荐 3~5 个食谱，让用户从中选择一个"""

    def __init__(self, parent, meal: str, candidates: list):
        super().__init__(parent)
        self.title(f"推荐食谱 - {meal}")
        self.resizable(False, False)
        self.grab_set()          # 模态对话框
        self.result = None       # 用户选中的食谱字典

        tk.Label(self, text=f"为【{meal}】推荐以下食谱，请选择一个：",
                 font=("微软雅黑", 11), pady=8).pack()

        # 使用单选按钮列表
        self._var = tk.StringVar(value="")
        frame = tk.Frame(self)
        frame.pack(padx=20, pady=4)
        self._candidates = {r["name"]: r for r in candidates}
        for recipe in candidates:
            row = tk.Frame(frame)
            row.pack(anchor="w", pady=2)
            rb = tk.Radiobutton(
                row, text=recipe["name"],
                variable=self._var, value=recipe["name"],
                font=("微软雅黑", 10),
            )
            rb.pack(side="left")
            info = (f"  {recipe['calories']} kcal  |  "
                    f"蛋白质 {recipe['protein']}g  |  "
                    f"脂肪 {recipe['fat']}g  |  "
                    f"碳水 {recipe['carbs']}g")
            tk.Label(row, text=info, fg="gray", font=("微软雅黑", 9)).pack(side="left")

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="确认选择", command=self._confirm,
                  bg="#4CAF50", fg="white", width=10).pack(side="left", padx=6)
        tk.Button(btn_frame, text="取消", command=self.destroy,
                  width=10).pack(side="left", padx=6)

        # 居中显示
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _confirm(self):
        name = self._var.get()
        if not name:
            messagebox.showwarning("提示", "请先选择一个食谱", parent=self)
            return
        self.result = self._candidates[name]
        self.destroy()


# ──────────────────────────────────────────────
#  主应用程序类
# ──────────────────────────────────────────────

class MealPlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("每周膳食规划助手")
        self.geometry("1000x640")
        self.minsize(900, 580)
        self.configure(bg="#F5F5F5")

        # 加载历史数据
        self.records = load_records()
        # 确保所有 key 存在（兼容旧格式）
        for day in DAYS:
            self.records.setdefault(day, {})
            for meal in MEALS:
                self.records[day].setdefault(meal, None)

        # 当前选择的星期（StringVar，绑定到下拉框）
        self._selected_day = tk.StringVar(value=DAYS[0])
        self._selected_day.trace_add("write", self._on_day_change)

        self._build_ui()
        self._refresh_table()
        self._refresh_nutrition()

        # 关闭窗口时自动保存
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI 构建 ──────────────────────────────

    def _build_ui(self):
        """构建三区域布局"""
        # ── 顶部控制区 ──
        top = tk.Frame(self, bg="#2196F3", pady=6)
        top.pack(fill="x", side="top")
        self._build_top(top)

        # ── 中部主体（选餐 + 表格） ──
        body = tk.Frame(self, bg="#F5F5F5")
        body.pack(fill="both", expand=True, padx=10, pady=6)

        # 左侧：每餐选择面板
        left = tk.LabelFrame(body, text="选择食谱", bg="#F5F5F5",
                              font=("微软雅黑", 10, "bold"), padx=8, pady=6)
        left.pack(side="left", fill="y", padx=(0, 8))
        self._build_meal_selectors(left)

        # 右侧：Treeview 表格
        right = tk.LabelFrame(body, text="本周记录表", bg="#F5F5F5",
                               font=("微软雅黑", 10, "bold"))
        right.pack(side="left", fill="both", expand=True)
        self._build_table(right)

        # ── 底部营养摘要区 ──
        bottom = tk.Frame(self, bg="#E8F5E9", relief="groove", bd=1)
        bottom.pack(fill="x", side="bottom", padx=10, pady=(0, 8))
        self._build_nutrition_summary(bottom)

    def _build_top(self, parent):
        """顶部：星期选择 + 分析按钮"""
        tk.Label(parent, text="每周膳食规划助手", bg="#2196F3", fg="white",
                 font=("微软雅黑", 14, "bold")).pack(side="left", padx=16)

        tk.Label(parent, text="查看星期：", bg="#2196F3", fg="white",
                 font=("微软雅黑", 11)).pack(side="left", padx=(20, 4))
        cb = ttk.Combobox(parent, textvariable=self._selected_day,
                          values=DAYS, state="readonly", width=6,
                          font=("微软雅黑", 11))
        cb.pack(side="left")

        tk.Button(parent, text="📊 分析当日营养", command=self._show_nutrition_popup,
                  bg="#FF9800", fg="white", font=("微软雅黑", 10, "bold"),
                  relief="flat", padx=10).pack(side="right", padx=16)

        tk.Button(parent, text="🗑 清除当日记录", command=self._clear_day,
                  bg="#F44336", fg="white", font=("微软雅黑", 10),
                  relief="flat", padx=10).pack(side="right", padx=4)

    def _build_meal_selectors(self, parent):
        """左侧面板：每餐的推荐按钮 + 手动下拉菜单"""
        self._meal_vars = {}      # meal -> StringVar（下拉菜单当前值）
        self._meal_combos = {}    # meal -> Combobox widget

        for meal in MEALS:
            frame = tk.LabelFrame(parent, text=meal, bg="#F5F5F5",
                                  font=("微软雅黑", 10), padx=6, pady=4)
            frame.pack(fill="x", pady=4)

            # 推荐按钮
            btn = tk.Button(
                frame, text="✨ 推荐",
                command=lambda m=meal: self._recommend(m),
                bg="#2196F3", fg="white", font=("微软雅黑", 9),
                relief="flat", padx=6,
            )
            btn.pack(side="left", padx=(0, 6))

            # 手动下拉
            names = [r["name"] for r in RECIPES[meal]]
            var = tk.StringVar(value="-- 手动选择 --")
            combo = ttk.Combobox(frame, textvariable=var,
                                 values=["-- 手动选择 --"] + names,
                                 state="readonly", width=16,
                                 font=("微软雅黑", 9))
            combo.pack(side="left")
            combo.bind("<<ComboboxSelected>>",
                       lambda e, m=meal: self._on_manual_select(m))

            self._meal_vars[meal] = var
            self._meal_combos[meal] = combo

    def _build_table(self, parent):
        """右侧 Treeview 表格"""
        columns = ("day", "meal", "name", "calories", "protein", "fat", "carbs")
        col_labels = {
            "day": "星期", "meal": "餐别", "name": "食谱名称",
            "calories": "卡路里(kcal)", "protein": "蛋白质(g)",
            "fat": "脂肪(g)", "carbs": "碳水化合物(g)",
        }
        col_widths = {
            "day": 60, "meal": 55, "name": 130,
            "calories": 100, "protein": 85, "fat": 70, "carbs": 100,
        }

        self.tree = ttk.Treeview(parent, columns=columns, show="headings",
                                 height=10, selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col_labels[col])
            self.tree.column(col, width=col_widths[col], anchor="center")

        # 滚动条
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # 标签样式：奇偶行不同背景色
        self.tree.tag_configure("odd", background="#FFFFFF")
        self.tree.tag_configure("even", background="#E3F2FD")

    def _build_nutrition_summary(self, parent):
        """底部营养摘要标签"""
        tk.Label(parent, text="当日营养摘要：", bg="#E8F5E9",
                 font=("微软雅黑", 10, "bold")).pack(side="left", padx=10, pady=6)
        self._nutrition_label = tk.Label(
            parent, text="--", bg="#E8F5E9",
            font=("微软雅黑", 10), fg="#333333",
        )
        self._nutrition_label.pack(side="left", pady=6)

    # ── 事件处理 ──────────────────────────────

    def _on_day_change(self, *_):
        """切换星期时刷新表格和营养摘要"""
        self._refresh_table()
        self._refresh_nutrition()
        # 同步左侧下拉菜单显示
        day = self._selected_day.get()
        for meal in MEALS:
            rec = self.records[day][meal]
            if rec:
                self._meal_vars[meal].set(rec["name"])
            else:
                self._meal_vars[meal].set("-- 手动选择 --")

    def _recommend(self, meal: str):
        """弹出随机推荐对话框"""
        pool = RECIPES[meal]
        count = min(random.randint(3, 5), len(pool))
        candidates = random.sample(pool, count)
        dlg = RecommendDialog(self, meal, candidates)
        self.wait_window(dlg)
        if dlg.result:
            self._save_selection(meal, dlg.result)

    def _on_manual_select(self, meal: str):
        """手动下拉菜单选择"""
        name = self._meal_vars[meal].get()
        if name == "-- 手动选择 --":
            return
        recipe = next((r for r in RECIPES[meal] if r["name"] == name), None)
        if recipe:
            self._save_selection(meal, recipe)

    def _save_selection(self, meal: str, recipe: dict):
        """保存选择并刷新 UI"""
        day = self._selected_day.get()
        self.records[day][meal] = recipe
        self._meal_vars[meal].set(recipe["name"])
        self._refresh_table()
        self._refresh_nutrition()

    def _clear_day(self):
        """清除当前日期的所有记录"""
        day = self._selected_day.get()
        if not messagebox.askyesno("确认", f"确定要清除【{day}】的所有食谱记录吗？"):
            return
        for meal in MEALS:
            self.records[day][meal] = None
            self._meal_vars[meal].set("-- 手动选择 --")
        self._refresh_table()
        self._refresh_nutrition()

    # ── 刷新显示 ─────────────────────────────

    def _refresh_table(self):
        """刷新 Treeview，只显示当前选定日期的三餐"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        day = self._selected_day.get()
        for i, meal in enumerate(MEALS):
            rec = self.records[day][meal]
            tag = "odd" if i % 2 == 0 else "even"
            if rec:
                self.tree.insert("", "end", tags=(tag,), values=(
                    day, meal, rec["name"],
                    rec["calories"], rec["protein"], rec["fat"], rec["carbs"],
                ))
            else:
                self.tree.insert("", "end", tags=(tag,),
                                 values=(day, meal, "（未选择）", "--", "--", "--", "--"))

    def _calc_nutrition(self, day: str) -> dict:
        """汇总某天三餐的营养数据"""
        total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
        for meal in MEALS:
            rec = self.records[day][meal]
            if rec:
                for k in total:
                    total[k] += rec[k]
        return total

    def _refresh_nutrition(self):
        """更新底部营养摘要标签"""
        day = self._selected_day.get()
        total = self._calc_nutrition(day)
        has_data = any(self.records[day][m] for m in MEALS)
        if not has_data:
            self._nutrition_label.config(text="当日尚未选择任何食谱")
        else:
            self._nutrition_label.config(
                text=(
                    f"总卡路里：{total['calories']} kcal  |  "
                    f"蛋白质：{total['protein']} g  |  "
                    f"脂肪：{total['fat']} g  |  "
                    f"碳水化合物：{total['carbs']} g"
                )
            )

    def _show_nutrition_popup(self):
        """弹窗详细展示当日营养分析"""
        day = self._selected_day.get()
        total = self._calc_nutrition(day)
        lines = [f"【{day}】营养分析报告\n"]
        for meal in MEALS:
            rec = self.records[day][meal]
            if rec:
                lines.append(
                    f"  {meal}：{rec['name']}\n"
                    f"    卡路里 {rec['calories']} kcal | 蛋白质 {rec['protein']}g | "
                    f"脂肪 {rec['fat']}g | 碳水 {rec['carbs']}g"
                )
            else:
                lines.append(f"  {meal}：（未选择）")
        lines.append(
            f"\n─────────────────────────────\n"
            f"  全天合计\n"
            f"  总卡路里：{total['calories']} kcal\n"
            f"  总蛋白质：{total['protein']} g\n"
            f"  总脂肪：{total['fat']} g\n"
            f"  总碳水化合物：{total['carbs']} g"
        )
        messagebox.showinfo(f"{day} 营养分析", "\n".join(lines))

    def _on_close(self):
        """关闭窗口前保存数据"""
        save_records(self.records)
        self.destroy()


# ──────────────────────────────────────────────
#  程序入口
# ──────────────────────────────────────────────

if __name__ == "__main__":
    app = MealPlannerApp()
    app.mainloop()
