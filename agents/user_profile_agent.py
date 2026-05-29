from datetime import datetime
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

from utils.logger_config import setup_logger

logger = setup_logger()


class UserProfileAgent:
    def __init__(self, rdf_path: str):
        self.rdf_path = str(rdf_path)
        self.graph = Graph()
        self.graph.parse(self.rdf_path, format="turtle")
        self.EDU = Namespace("http://www.semanticweb.org/edurecommend#")

        logger.info("Agente de Perfil inicializado con RDF: %s", self.rdf_path)

    def update_user_interests(self, user_id: str, interests: list[str]) -> None:
        user_uri = URIRef(self.EDU[user_id])

        if not interests:
            logger.info(
                "No se recibieron intereses manuales para el usuario: %s", user_id
            )
            return

        logger.info("Actualizando intereses del usuario %s: %s", user_id, interests)

        old_interests = list(self.graph.objects(user_uri, self.EDU.tieneInteres))

        for interest in old_interests:
            self.graph.remove((user_uri, self.EDU.tieneInteres, interest))

        for interest in interests:
            interest_uri = URIRef(self.EDU[interest])
            self.graph.add((user_uri, self.EDU.tieneInteres, interest_uri))
            logger.info("Interés agregado al perfil RDF: %s -> %s", user_id, interest)

        self.save_graph()
        logger.info("Perfil RDF actualizado correctamente para el usuario: %s", user_id)

    def register_content_view(self, user_id: str, content_id: str) -> None:
        user_uri = URIRef(self.EDU[user_id])
        content_uri = URIRef(self.EDU[content_id])

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        interaction_uri = URIRef(
            self.EDU[f"interaccion_{user_id}_{content_id}_{timestamp}"]
        )

        logger.info(
            "Registrando interacción del usuario %s con contenido %s",
            user_id,
            content_id,
        )

        self.graph.add((interaction_uri, RDF.type, self.EDU.Interaccion))
        self.graph.add((interaction_uri, self.EDU.realizadaPor, user_uri))
        self.graph.add((interaction_uri, self.EDU.sobreContenido, content_uri))
        self.graph.add(
            (
                interaction_uri,
                self.EDU.fecha,
                Literal(datetime.now().isoformat(), datatype=XSD.string),
            )
        )

        logger.info("Interacción RDF creada: %s", str(interaction_uri).split("#")[-1])

        self.learn_user_trends(user_id)
        self.save_graph()

        logger.info(
            "Interacción guardada y aprendizaje ejecutado para usuario: %s", user_id
        )

    def register_rating(self, user_id: str, content_id: str, rating: int) -> None:
        user_uri = URIRef(self.EDU[user_id])
        content_uri = URIRef(self.EDU[content_id])

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        rating_uri = URIRef(
            self.EDU[f"calificacion_{user_id}_{content_id}_{timestamp}"]
        )

        logger.info(
            "Registrando calificación: usuario=%s contenido=%s puntaje=%s",
            user_id,
            content_id,
            rating,
        )

        self.graph.add((rating_uri, RDF.type, self.EDU.Calificacion))
        self.graph.add((rating_uri, self.EDU.realizadaPor, user_uri))
        self.graph.add((rating_uri, self.EDU.sobreContenido, content_uri))
        self.graph.add(
            (rating_uri, self.EDU.puntaje, Literal(rating, datatype=XSD.integer))
        )
        self.graph.add(
            (
                rating_uri,
                self.EDU.fecha,
                Literal(datetime.now().isoformat(), datatype=XSD.string),
            )
        )

        if rating >= 4:
            categories = list(
                self.graph.objects(content_uri, self.EDU.perteneceACategoria)
            )
            for category in categories:
                self.graph.add((user_uri, self.EDU.tieneInteres, category))
                logger.info(
                    "Interés aprendido por alta calificación: usuario=%s categoria=%s",
                    user_id,
                    str(category).split("#")[-1],
                )

        self.learn_user_trends(user_id)
        self.save_graph()

        logger.info(
            "Calificación guardada correctamente para usuario=%s contenido=%s",
            user_id,
            content_id,
        )

    def learn_user_trends(self, user_id: str) -> None:
        logger.info("Analizando tendencias del usuario: %s", user_id)

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
        HAVING (COUNT(?interaccion) >= 2)
        """

        results = self.graph.query(query)
        user_uri = URIRef(self.EDU[user_id])
        learned_count = 0

        for row in results:
            category_name = str(row.categoria).split("#")[-1]
            total = int(row.total.toPython())

            self.graph.add((user_uri, self.EDU.tieneInteres, row.categoria))
            learned_count += 1

            logger.info(
                "Tendencia aprendida por interacción: usuario=%s categoria=%s interacciones=%s",
                user_id,
                category_name,
                total,
            )

        if learned_count == 0:
            logger.info(
                "No se encontraron nuevas tendencias con suficientes interacciones para %s",
                user_id,
            )

    def reset_user_profile(self, user_id: str) -> None:
        user_uri = URIRef(self.EDU[user_id])

        old_interests = list(self.graph.objects(user_uri, self.EDU.tieneInteres))
        for interest in old_interests:
            self.graph.remove((user_uri, self.EDU.tieneInteres, interest))

        user_interactions = list(self.graph.subjects(self.EDU.realizadaPor, user_uri))

        for item in user_interactions:
            for predicate, obj in list(self.graph.predicate_objects(item)):
                self.graph.remove((item, predicate, obj))

        self.save_graph()
        logger.info(
            "Perfil reiniciado para usuario=%s. Intereses, interacciones y calificaciones propias eliminadas.",
            user_id,
        )

    def save_graph(self) -> None:
        path = Path(self.rdf_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.graph.serialize(destination=self.rdf_path, format="turtle")

        logger.info("Grafo RDF guardado en: %s", self.rdf_path)
