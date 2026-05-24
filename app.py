from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

# Identify the absolute path for the database file to ensure reliability on cloud servers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bakery.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cake_id INTEGER,
        name TEXT,
        base_qty REAL,
        unit TEXT,
        FOREIGN KEY(cake_id) REFERENCES cakes(id)
    )""")
    
    # Check if empty, then seed initial default 1kg datasets
    cursor.execute("SELECT COUNT(*) FROM cakes")
    if cursor.fetchone()[0] == 0:
        default_cakes = ["Butter Cake", "Chocolate Cake", "Date Cake", "Coffee Cake"]
        for cake in default_cakes:
            cursor.execute("INSERT INTO cakes (name) VALUES (?)", (cake,))
        
        # 1kg Butter Cake Baseline
        cursor.execute("SELECT id FROM cakes WHERE name='Butter Cake'")
        b_id = cursor.fetchone()[0]
        cursor.executemany("INSERT INTO ingredients (cake_id, name, base_qty, unit) VALUES (?, ?, ?, ?)", [
            (b_id, "Flour", 500, "g"), (b_id, "Sugar", 500, "g"), (b_id, "Butter", 500, "g"), (b_id, "Eggs", 8, "pcs")
        ])
        
        # 1kg Chocolate Cake Baseline
        cursor.execute("SELECT id FROM cakes WHERE name='Chocolate Cake'")
        c_id = cursor.fetchone()[0]
        cursor.executemany("INSERT INTO ingredients (cake_id, name, base_qty, unit) VALUES (?, ?, ?, ?)", [
            (c_id, "Flour", 400, "g"), (c_id, "Cocoa Powder", 100, "g"), (c_id, "Sugar", 500, "g"), (c_id, "Butter", 450, "g"), (c_id, "Eggs", 8, "pcs")
        ])
        
        # 1kg Date Cake Baseline
        cursor.execute("SELECT id FROM cakes WHERE name='Date Cake'")
        d_id = cursor.fetchone()[0]
        cursor.executemany("INSERT INTO ingredients (cake_id, name, base_qty, unit) VALUES (?, ?, ?, ?)", [
            (d_id, "Flour", 400, "g"), (d_id, "Dates", 300, "g"), (d_id, "Sugar", 300, "g"), (d_id, "Butter", 400, "g"), (d_id, "Eggs", 6, "pcs")
        ])
        
        # 1kg Coffee Cake Baseline
        cursor.execute("SELECT id FROM cakes WHERE name='Coffee Cake'")
        co_id = cursor.fetchone()[0]
        cursor.executemany("INSERT INTO ingredients (cake_id, name, base_qty, unit) VALUES (?, ?, ?, ?)", [
            (co_id, "Flour", 500, "g"), (co_id, "Sugar", 500, "g"), (co_id, "Butter", 500, "g"), (co_id, "Coffee Powder", 25, "g"), (co_id, "Eggs", 8, "pcs")
        ])
        
    conn.commit()
    conn.close()

def format_unit(qty, unit):
    if unit == "g" and qty >= 1000:
        return f"{qty/1000:.2f} kg"
    return f"{int(qty) if qty.is_integer() else qty:.1f} {unit}"

@app.route("/", methods=["GET"])
def home():
    selected_cake = request.args.get("cake_type", "Butter Cake")
    try:
        weight = float(request.args.get("weight", 1.0))
    except ValueError:
        weight = 1.0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Fetch list of available cakes
    cursor.execute("SELECT name FROM cakes")
    cakes = [row[0] for row in cursor.fetchall()]
    
    # Fetch base elements for selected cake
    cursor.execute("""
        SELECT i.name, i.base_qty, i.unit 
        FROM ingredients i
        JOIN cakes c ON i.cake_id = c.id 
        WHERE c.name = ?
    """, (selected_cake,))
    raw_ingredients = cursor.fetchall()
    conn.close()
    
    # Run scaling logic
    processed_ingredients = []
    for name, base_qty, unit in raw_ingredients:
        scaled_qty = base_qty * weight
        processed_ingredients.append({
            "name": name,
            "qty": format_unit(scaled_qty, unit)
        })
        
    return render_template("index.html", 
                           cakes=cakes, 
                           selected_cake=selected_cake, 
                           weight=weight, 
                           ingredients=processed_ingredients)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)