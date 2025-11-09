from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

DB_URL = os.getenv("DATABASE_URL")
def get_conn():
    return psycopg2.connect(DB_URL)


@app.route("/")
def home_page():
    return "Hello World"


@app.route("/transfers")
def get_transfers():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM transfers ORDER BY id ASC LIMIT 3;")
    rows = cur.fetchall()

    conn.close()

    output = []
    for row in rows:
        output.append([str(x) for x in row])
    return jsonify(output)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
