from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for

from agents.user_profile_agent import UserProfileAgent
from agents.recommendation_agent import RecommendationAgent
from utils.logger_config import setup_logger

logger = setup_logger()

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

RDF_PATH = BASE_DIR / "semantic" / "data.ttl"

AVAILABLE_INTERESTS = {
    "InteligenciaArtificial": "Inteligencia Artificial",
    "Programacion": "Programación",
    "WebSemantica": "Web Semántica",
    "BasesDeDatos": "Bases de Datos",
    "Automatizacion": "Automatización",
    "Ciberseguridad": "Ciberseguridad",
    "AnaliticaDatos": "Analítica de Datos",
}

USER_ID = "usuario1"


@app.route("/", methods=["GET"])
def index():
    logger.info("Acceso a página principal")

    recommendation_agent = RecommendationAgent(str(RDF_PATH))

    contents = recommendation_agent.get_all_content(USER_ID)
    trends = recommendation_agent.get_user_trends(USER_ID)
    user_interests = recommendation_agent.get_user_interests(USER_ID)

    return render_template(
        "index.html",
        interests=AVAILABLE_INTERESTS,
        contents=contents,
        trends=trends,
        user_interests=user_interests,
    )


@app.route("/recommendations", methods=["POST"])
def recommendations():
    selected_interests = request.form.getlist("interests")

    logger.info("Solicitud de recomendaciones recibida")
    logger.info("Intereses seleccionados desde la interfaz: %s", selected_interests)

    if selected_interests:
        profile_agent = UserProfileAgent(str(RDF_PATH))
        profile_agent.update_user_interests(USER_ID, selected_interests)
    else:
        logger.info(
            "No se seleccionaron intereses nuevos. Se usarán intereses existentes/aprendidos"
        )

    recommendation_agent = RecommendationAgent(str(RDF_PATH))
    recommendations_result = recommendation_agent.get_recommendations(USER_ID)
    trends = recommendation_agent.get_user_trends(USER_ID)
    user_interests = recommendation_agent.get_user_interests(USER_ID)

    return render_template(
        "recommendations.html",
        recommendations=recommendations_result,
        selected_interests=[AVAILABLE_INTERESTS[item] for item in selected_interests],
        trends=trends,
        user_interests=user_interests,
    )


@app.route("/content/<content_id>", methods=["GET"])
def content_detail(content_id):
    logger.info("Usuario abrió contenido desde la interfaz: %s", content_id)

    profile_agent = UserProfileAgent(str(RDF_PATH))
    profile_agent.register_content_view(USER_ID, content_id)

    recommendation_agent = RecommendationAgent(str(RDF_PATH))
    content = recommendation_agent.get_content_by_id(content_id)
    trends = recommendation_agent.get_user_trends(USER_ID)
    user_interests = recommendation_agent.get_user_interests(USER_ID)

    if content is None:
        logger.warning(
            "Contenido no encontrado. Redireccionando al inicio: %s", content_id
        )
        return redirect(url_for("index"))

    return render_template(
        "content_detail.html",
        content=content,
        trends=trends,
        user_interests=user_interests,
    )


@app.route("/rate", methods=["POST"])
def rate_content():
    content_id = request.form.get("content_id")
    rating = request.form.get("rating")

    logger.info(
        "Solicitud de calificación recibida: content_id=%s rating=%s",
        content_id,
        rating,
    )

    if not content_id or not rating:
        logger.warning("Datos incompletos para calificación")
        return redirect(url_for("index"))

    profile_agent = UserProfileAgent(str(RDF_PATH))
    profile_agent.register_rating(USER_ID, content_id, int(rating))

    logger.info("Calificación procesada correctamente")

    return redirect(url_for("content_detail", content_id=content_id))


@app.route("/reset-profile", methods=["POST"])
def reset_profile():
    logger.info("Solicitud para reiniciar perfil del usuario: %s", USER_ID)

    profile_agent = UserProfileAgent(str(RDF_PATH))
    profile_agent.reset_user_profile(USER_ID)

    logger.info("Perfil reiniciado correctamente para usuario: %s", USER_ID)

    return redirect(url_for("index"))


if __name__ == "__main__":
    logger.info("Iniciando aplicación EduRecommend AI")
    logger.info("Ruta RDF configurada: %s", RDF_PATH)
    app.run(debug=True)
