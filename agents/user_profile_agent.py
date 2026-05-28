from datetime import datetime
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD


class UserProfileAgent:
    def __init__(self, rdf_path: str):
        self.rdf_path = str(rdf_path)
        self.graph = Graph()
        self.graph.parse(self.rdf_path, format="turtle")
        self.EDU = Namespace("http://www.semanticweb.org/edurecommend#")

    def update_user_interests(self, user_id: str, interests: list[str]) -> None:
        user_uri = URIRef(self.EDU[user_id])

        if not interests:
            return

        old_interests = list(self.graph.objects(user_uri, self.EDU.tieneInteres))
        for interest in old_interests:
            self.graph.remove((user_uri, self.EDU.tieneInteres, interest))

        for interest in interests:
            interest_uri = URIRef(self.EDU[interest])
            self.graph.add((user_uri, self.EDU.tieneInteres, interest_uri))

        self.save_graph()

    def register_content_view(self, user_id: str, content_id: str) -> None:
        user_uri = URIRef(self.EDU[user_id])
        content_uri = URIRef(self.EDU[content_id])

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        interaction_uri = URIRef(self.EDU[f"interaccion_{user_id}_{content_id}_{timestamp}"])

        self.graph.add((interaction_uri, RDF.type, self.EDU.Interaccion))
        self.graph.add((interaction_uri, self.EDU.realizadaPor, user_uri))
        self.graph.add((interaction_uri, self.EDU.sobreContenido, content_uri))
        self.graph.add((interaction_uri, self.EDU.fecha, Literal(datetime.now().isoformat(), datatype=XSD.string)))

        self.learn_user_trends(user_id)
        self.save_graph()

    def learn_user_trends(self, user_id: str) -> None:
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

        for row in results:
            self.graph.add((user_uri, self.EDU.tieneInteres, row.categoria))

    def save_graph(self) -> None:
        path = Path(self.rdf_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.graph.serialize(destination=self.rdf_path, format="turtle")