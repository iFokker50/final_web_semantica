from rdflib import Graph


class RecommendationAgent:
    def __init__(self, rdf_path: str):
        self.rdf_path = str(rdf_path)
        self.graph = Graph()
        self.graph.parse(self.rdf_path, format="turtle")

    def get_recommendations(self, user_id: str) -> list[dict]:
        query = f"""
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT DISTINCT ?contenido ?nombre ?descripcion ?nivel ?url ?categoriaNombre
        WHERE {{
            edu:{user_id} edu:tieneInteres ?categoria .
            ?contenido a edu:Contenido .
            ?contenido edu:perteneceACategoria ?categoria .
            ?contenido edu:nombre ?nombre .
            ?contenido edu:descripcion ?descripcion .
            ?contenido edu:nivel ?nivel .
            ?contenido edu:url ?url .
            ?categoria edu:nombre ?categoriaNombre .
        }}
        ORDER BY ?categoriaNombre ?nombre
        """

        results = self.graph.query(query)
        return self.rows_to_content_list(results)

    def get_all_content(self) -> list[dict]:
        query = """
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT DISTINCT ?contenido ?nombre ?descripcion ?nivel ?url ?categoriaNombre
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
        return self.rows_to_content_list(results)

    def get_content_by_id(self, content_id: str) -> dict | None:
        query = f"""
        PREFIX edu: <http://www.semanticweb.org/edurecommend#>

        SELECT DISTINCT ?contenido ?nombre ?descripcion ?nivel ?url ?categoriaNombre
        WHERE {{
            edu:{content_id} a edu:Contenido .
            edu:{content_id} edu:nombre ?nombre .
            edu:{content_id} edu:descripcion ?descripcion .
            edu:{content_id} edu:nivel ?nivel .
            edu:{content_id} edu:url ?url .
            edu:{content_id} edu:perteneceACategoria ?categoria .
            ?categoria edu:nombre ?categoriaNombre .
            BIND(edu:{content_id} AS ?contenido)
        }}
        """

        results = self.graph.query(query)
        contents = self.rows_to_content_list(results)

        if not contents:
            return None

        first = contents[0]
        first["categorias"] = sorted(list({item["categoria"] for item in contents}))
        return first

    def get_user_trends(self, user_id: str) -> list[dict]:
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
            trends.append({
                "categoria": str(row.categoriaNombre),
                "total": int(row.total.toPython())
            })

        return trends

    def get_user_interests(self, user_id: str) -> list[str]:
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
        return [str(row.categoriaNombre) for row in results]

    def rows_to_content_list(self, results) -> list[dict]:
        contents = []

        for row in results:
            contents.append({
                "contenido_uri": str(row.contenido),
                "contenido_id": str(row.contenido).split("#")[-1],
                "nombre": str(row.nombre),
                "descripcion": str(row.descripcion),
                "nivel": str(row.nivel),
                "url": str(row.url),
                "categoria": str(row.categoriaNombre),
            })

        return contents