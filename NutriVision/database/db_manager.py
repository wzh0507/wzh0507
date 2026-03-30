import sqlite3
from pathlib import Path


SEED_RECIPES = [
    ("燕麦粥", "oats, milk, honey", 300, 10, 6, 54, "breakfast,healthy"),
    ("全麦吐司", "whole wheat bread", 250, 9, 3, 46, "breakfast"),
    ("鸡胸肉沙拉", "chicken breast, lettuce, tomato, olive oil", 350, 30, 12, 20, "lunch,protein"),
    ("糙米饭+蒸蔬菜", "brown rice, broccoli, carrots, soy sauce", 400, 8, 2, 82, "lunch,dinner,healthy"),
    ("三文鱼", "salmon fillet, lemon, dill", 450, 35, 25, 0, "dinner,protein"),
    ("牛油果", "avocado", 240, 3, 22, 12, "snack,healthy"),
    ("希腊酸奶", "greek yogurt, honey", 150, 15, 3, 10, "snack,breakfast"),
    ("水煮蛋", "eggs", 155, 13, 11, 1, "breakfast,snack,protein"),
    ("坚果混合", "almonds, walnuts, cashews, peanuts", 600, 18, 52, 20, "snack"),
    ("番茄汤", "tomatoes, onion, garlic, vegetable stock", 180, 4, 5, 28, "lunch,dinner"),
]


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_if_empty()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ingredients TEXT,
                calories REAL DEFAULT 0,
                protein REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                carbs REAL DEFAULT 0,
                tags TEXT
            );
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                recipe_id INTEGER,
                actual_intake_grams REAL DEFAULT 0,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id)
            );
        """)
        self.conn.commit()

    def _seed_if_empty(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM recipes")
        if cur.fetchone()[0] == 0:
            for recipe in SEED_RECIPES:
                cur.execute(
                    "INSERT INTO recipes (name, ingredients, calories, protein, fat, carbs, tags) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    recipe,
                )
            self.conn.commit()

    def add_recipe(self, name, ingredients, calories, protein, fat, carbs, tags):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO recipes (name, ingredients, calories, protein, fat, carbs, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, ingredients, calories, protein, fat, carbs, tags),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_all_recipes(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM recipes ORDER BY name")
        return [dict(row) for row in cur.fetchall()]

    def get_recipes_by_tags(self, tags_list):
        all_recipes = self.get_all_recipes()
        if not tags_list:
            return all_recipes
        result = []
        for recipe in all_recipes:
            recipe_tags = [t.strip() for t in (recipe.get("tags") or "").split(",")]
            if any(tag in recipe_tags for tag in tags_list):
                result.append(recipe)
        return result

    def add_log(self, date, meal_type, recipe_id, grams):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO daily_logs (date, meal_type, recipe_id, actual_intake_grams) "
            "VALUES (?, ?, ?, ?)",
            (date, meal_type, recipe_id, grams),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_logs_by_date(self, date):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT dl.id, dl.date, dl.meal_type, dl.actual_intake_grams,
                   r.id as recipe_id, r.name, r.calories, r.protein, r.fat, r.carbs, r.tags
            FROM daily_logs dl
            JOIN recipes r ON dl.recipe_id = r.id
            WHERE dl.date = ?
            ORDER BY dl.meal_type, dl.id
            """,
            (date,),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_logs_by_month(self, year, month):
        month_str = f"{year}-{month:02d}"
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT dl.id, dl.date, dl.meal_type, dl.actual_intake_grams,
                   r.calories, r.protein, r.fat, r.carbs
            FROM daily_logs dl
            JOIN recipes r ON dl.recipe_id = r.id
            WHERE dl.date LIKE ?
            ORDER BY dl.date
            """,
            (f"{month_str}-%",),
        )
        return [dict(row) for row in cur.fetchall()]

    def delete_log(self, log_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM daily_logs WHERE id = ?", (log_id,))
        self.conn.commit()

    def get_daily_nutrition(self, date):
        logs = self.get_logs_by_date(date)
        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        for log in logs:
            factor = log["actual_intake_grams"] / 100.0
            totals["calories"] += log["calories"] * factor
            totals["protein"] += log["protein"] * factor
            totals["fat"] += log["fat"] * factor
            totals["carbs"] += log["carbs"] * factor
        return totals
