from rdflib import Graph

from utils.logger_config import setup_logger

logger = setup_logger()


class RecommendationAgent:
    def __init__(self, rdf_path: str):
        self.rdf_path = str(rdf_path)
        self.graph = Graph()
        self.graph.parse(self.rdf_path, format="turtle")

        logger.info("Agente de Recomendación inicializado con RDF: %s", self.rdf_path)

    def get_recommendations(self, user_id: str) -> list[dict]:
        logger.info("Generando recomendaciones para usuario: %s", user_id)

        contents = self.get_all_content(user_id)
        recommendations = [item for item in contents if item["score"] > 0]

        if not recommendations:
            recommendations = contents

        logger.info(
            "Recomendaciones generadas para %s: %s resultados",
            user_id,
            len(recommendations),
        )

        return recommendations

    def get_all_content(self, user_id: str | None = None) -> list[dict]:
        logger.info("Consultando todos los contenidos disponibles")

        query = """
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT DISTINCT ?contenido ?nombre ?descripcion ?nivel ?url ?categoria ?categoriaNombre
        WHERE {
            ?contenido a edu:Contenido .
            ?contenido edu:nombre ?nombre .
            ?contenido edu:descripcion ?descripcion .
            ?contenido edu:nivel ?nivel .
            ?contenido edu:url ?url .
            ?contenido edu:perteneceACategoria ?categoria .
            ?categoria edu:nombre ?categoriaNombre .
        }
        ORDER BY ?nombre
        """

        results = self.graph.query(query)

        user_interest_uris = set()
        trend_scores = {}
        rating_scores = self.get_content_rating_scores()

        if user_id:
            user_interest_uris = self.get_user_interest_uris(user_id)
            trend_scores = self.get_user_trend_scores(user_id)

        contents_map = {}

        for row in results:
            content_id = str(row.contenido).split("#")[-1]
            category_uri = str(row.categoria)
            category_name = str(row.categoriaNombre)

            if content_id not in contents_map:
                rating_info = rating_scores.get(content_id, {"average": 0, "count": 0})

                contents_map[content_id] = {
                    "contenido_uri": str(row.contenido),
                    "contenido_id": content_id,
                    "nombre": str(row.nombre),
                    "descripcion": str(row.descripcion),
                    "nivel": str(row.nivel),
                    "url": str(row.url),
                    "categorias": [],
                    "categoria": "",
                    "score": 0,
                    "match_interes": False,
                    "match_tendencia": False,
                    "average_rating": rating_info["average"],
                    "rating_count": rating_info["count"],
                    "highly_rated": rating_info["average"] >= 4
                    and rating_info["count"] > 0,
                }

                if rating_info["count"] > 0:
                    contents_map[content_id]["score"] += (
                        int(rating_info["average"] * 20) + rating_info["count"]
                    )

            contents_map[content_id]["categorias"].append(category_name)

            if category_uri in user_interest_uris:
                contents_map[content_id]["score"] += 100
                contents_map[content_id]["match_interes"] = True

            if category_uri in trend_scores:
                contents_map[content_id]["score"] += trend_scores[category_uri] * 10
                contents_map[content_id]["match_tendencia"] = True

        contents = []

        for item in contents_map.values():
            item["categorias"] = sorted(list(set(item["categorias"])))
            item["categoria"] = ", ".join(item["categorias"])
            contents.append(item)

        contents = sorted(
            contents,
            key=lambda item: (
                -item["score"],
                -item["average_rating"],
                -item["rating_count"],
                item["nombre"],
            ),
        )

        logger.info("Total de contenidos encontrados: %s", len(contents))

        return contents

    def get_content_by_id(self, content_id: str) -> dict | None:
        logger.info("Consultando detalle del contenido: %s", content_id)

        contents = self.get_all_content()

        for content in contents:
            if content["contenido_id"] == content_id:
                return content

        logger.warning("No se encontró contenido con ID: %s", content_id)
        return None

    def get_user_trends(self, user_id: str) -> list[dict]:
        logger.info("Consultando tendencias del usuario: %s", user_id)

        query = f"""
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT ?categoriaNombre (COUNT(?interaccion) AS ?total)
        WHERE {{
            ?interaccion a edu:Interaccion .
            ?interaccion edu:realizadaPor edu:{user_id} .
            ?interaccion edu:sobreContenido ?contenido .
            ?contenido edu:perteneceACategoria ?categoria .
            ?categoria edu:nombre ?categoriaNombre .
        }}
        GROUP BY ?categoriaNombre
        ORDER BY DESC(?total) ?categoriaNombre
        """

        results = self.graph.query(query)

        trends = []
        for row in results:
            trends.append(
                {
                    "categoria": str(row.categoriaNombre),
                    "total": int(row.total.toPython()),
                }
            )

        logger.info("Tendencias encontradas para %s: %s", user_id, trends)

        return trends

    def get_user_interests(self, user_id: str) -> list[str]:
        logger.info("Consultando intereses actuales del usuario: %s", user_id)

        query = f"""
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT DISTINCT ?categoriaNombre
        WHERE {{
            edu:{user_id} edu:tieneInteres ?categoria .
            ?categoria edu:nombre ?categoriaNombre .
        }}
        ORDER BY ?categoriaNombre
        """

        results = self.graph.query(query)
        interests = [str(row.categoriaNombre) for row in results]

        logger.info("Intereses actuales de %s: %s", user_id, interests)

        return interests

    def get_user_interest_uris(self, user_id: str) -> set[str]:
        query = f"""
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT DISTINCT ?categoria
        WHERE {{
            edu:{user_id} edu:tieneInteres ?categoria .
        }}
        """

        results = self.graph.query(query)
        return {str(row.categoria) for row in results}

    def get_user_trend_scores(self, user_id: str) -> dict[str, int]:
        query = f"""
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT ?categoria (COUNT(?interaccion) AS ?total)
        WHERE {{
            ?interaccion a edu:Interaccion .
            ?interaccion edu:realizadaPor edu:{user_id} .
            ?interaccion edu:sobreContenido ?contenido .
            ?contenido edu:perteneceACategoria ?categoria .
        }}
        GROUP BY ?categoria
        """

        results = self.graph.query(query)

        scores = {}
        for row in results:
            scores[str(row.categoria)] = int(row.total.toPython())

        return scores

    def get_content_rating_scores(self) -> dict[str, dict]:
        query = """
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT ?contenido (AVG(?puntaje) AS ?promedio) (COUNT(?calificacion) AS ?total)
        WHERE {
            ?calificacion a edu:Calificacion .
            ?calificacion edu:sobreContenido ?contenido .
            ?calificacion edu:puntaje ?puntaje .
        }
        GROUP BY ?contenido
        """

        results = self.graph.query(query)

        scores = {}

        for row in results:
            content_id = str(row.contenido).split("#")[-1]
            scores[content_id] = {
                "average": round(float(row.promedio.toPython()), 2),
                "count": int(row.total.toPython()),
            }

        return scores
