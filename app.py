from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for

from agents.user_profile_agent import UserProfileAgent
from agents.recommendation_agent import RecommendationAgent

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

RDF_PATH = BASE_DIR / "semantic" / "data.ttl"

AVAILABLE_INTERESTS = {
    "InteligenciaArtificial": "Inteligencia Artificial",
    "Programacion": "Programación",
    "WebSemantica": "Web Semántica",
    "BasesDeDatos": "Bases de Datos",
    "Automatizacion": "Automatización",
}

USER_ID = "usuario1"


@app.route("/", methods=["GET"])
def index():
    recommendation_agent = RecommendationAgent(str(RDF_PATH))

    contents = recommendation_agent.get_all_content()
    trends = recommendation_agent.get_user_trends(USER_ID)
    user_interests = recommendation_agent.get_user_interests(USER_ID)

    return render_template(
        "index.html",
        interests=AVAILABLE_INTERESTS,
        contents=contents,
        trends=trends,
        user_interests=user_interests
    )


@app.route("/recommendations", methods=["POST"])
def recommendations():
    selected_interests = request.form.getlist("interests")

    if selected_interests:
        profile_agent = UserProfileAgent(str(RDF_PATH))
        profile_agent.update_user_interests(USER_ID, selected_interests)

    recommendation_agent = RecommendationAgent(str(RDF_PATH))
    recommendations_result = recommendation_agent.get_recommendations(USER_ID)
    trends = recommendation_agent.get_user_trends(USER_ID)
    user_interests = recommendation_agent.get_user_interests(USER_ID)

    return render_template(
        "recommendations.html",
        recommendations=recommendations_result,
        selected_interests=[
            AVAILABLE_INTERESTS[item] for item in selected_interests
        ],
        trends=trends,
        user_interests=user_interests
    )


@app.route("/content/<content_id>", methods=["GET"])
def content_detail(content_id):
    profile_agent = UserProfileAgent(str(RDF_PATH))
    profile_agent.register_content_view(USER_ID, content_id)

    recommendation_agent = RecommendationAgent(str(RDF_PATH))
    content = recommendation_agent.get_content_by_id(content_id)
    trends = recommendation_agent.get_user_trends(USER_ID)
    user_interests = recommendation_agent.get_user_interests(USER_ID)

    if content is None:
        return redirect(url_for("index"))

    return render_template(
        "content_detail.html",
        content=content,
        trends=trends,
        user_interests=user_interests
    )


if __name__ == "__main__":
    app.run(debug=True)
