from flask import Flask
from utils import router as router


def create_app():
    app = Flask(__name__)
    app.config.from_object("utils.settings")

    
    app.add_url_rule("/", view_func=router.base_page)
    app.add_url_rule("/players", view_func=router.players_page)
    app.add_url_rule("/transfers", view_func=router.transfers_page)
    app.add_url_rule("/games", view_func=router.games_page)
    app.add_url_rule(
        "/games/<int:game_id>/favorite",
        view_func=router.update_game_favorite,
        methods=["POST"],
    )
    app.add_url_rule("/clubs", view_func=router.clubs_page)
    app.add_url_rule("/competitions", view_func=router.competitions_page)

    return app


if __name__ == "__main__":
    app = create_app()
    port = app.config.get("PORT", 8080)
    app.run(host="0.0.0.0", port=port, debug=True)
