from flask import Flask, jsonify, render_template
# import psycopg2  #PostgreSQL bağlantısı yapılınca aç
import os
import views

# def get_conn():
#     #PostgreSQL bağlantısını oluşturur.
#     DB_URL = os.getenv("DATABASE_URL")
#     return psycopg2.connect(DB_URL)      #PostgreSQL bağlantısı yapılınca aç


def create_app():
    app = Flask(__name__)
    app.config.from_object("settings")

    
    app.add_url_rule("/", view_func=views.base_page)
    app.add_url_rule("/players", view_func=views.players_page)
    app.add_url_rule("/transfers", view_func=views.transfers_page)
    app.add_url_rule("/games", view_func=views.games_page)
    app.add_url_rule("/clubs", view_func=views.clubs_page)
    app.add_url_rule("/competitions", view_func=views.competitions_page)


#    @app.route("/api/transfers")
#    def get_transfers():
#        try:
#            conn = get_conn()     
#            cur = conn.cursor()
#            cur.execute("SELECT * FROM transfers ORDER BY id ASC LIMIT 3;")
#            rows = cur.fetchall()
#            cur.close()
#            conn.close()
#            output = [list(map(str, row)) for row in rows]
#            return jsonify(output)
#        except Exception as e:
#            return jsonify({"error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = app.config.get("PORT", 8080)
    app.run(host="0.0.0.0", port=port, debug=True)
