# EduRecommend AI

<p align="center">
  <strong>Sistema de recomendación semántico basado en agentes inteligentes</strong>
</p>

<p align="center">
  Aplicación web desarrollada con Python, Flask, RDF, OWL y SPARQL para recomendar contenidos educativos personalizados y aprender de las interacciones del usuario.
</p>

---

## Descripción del proyecto

**EduRecommend AI** es una aplicación web que recomienda contenidos educativos personalizados mediante la integración de **agentes inteligentes** y tecnologías de **Web Semántica**.

El sistema permite que un usuario seleccione intereses iniciales, consulte contenidos educativos y reciba recomendaciones relacionadas con su perfil. Además, el sistema aprende de forma implícita a partir de las interacciones del usuario, es decir, no necesita que el usuario califique los contenidos.

Cada vez que el usuario abre un contenido, el sistema registra esa acción como una interacción dentro del modelo RDF. Luego, el **Agente de Perfil de Usuario** analiza esas interacciones y aprende tendencias según las categorías más consultadas.

---

## Objetivo general

Desarrollar una aplicación web funcional que integre agentes inteligentes con tecnologías del Web Semántico para generar recomendaciones personalizadas de contenidos educativos, utilizando RDF, OWL y consultas SPARQL.

---

## Objetivos específicos

- Diseñar una ontología OWL para representar usuarios, contenidos, categorías, recomendaciones e interacciones.
- Crear un modelo RDF con datos de muestra sobre usuarios y contenidos educativos.
- Implementar un Agente de Perfil de Usuario que actualice preferencias y aprenda tendencias.
- Implementar un Agente de Recomendación que consulte RDF mediante SPARQL.
- Desarrollar una interfaz web simple con Flask.
- Desplegar la aplicación en una plataforma web gratuita para su demostración.

---

## Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python | Lenguaje principal del proyecto |
| Flask | Framework para la aplicación web |
| RDFLib | Manejo de RDF y consultas SPARQL |
| RDF | Representación semántica de datos |
| OWL | Definición de la ontología |
| SPARQL | Consulta de información semántica |
| HTML | Estructura de las vistas |
| CSS | Estilos visuales |
| Gunicorn | Servidor WSGI para despliegue |
| GitHub | Control de versiones y repositorio |
| Render | Despliegue web gratuito |

---

## Arquitectura general

```text
Usuario
   |
   v
Interfaz Web Flask
   |
   v
Agente de Perfil de Usuario
   |
   v
Modelo RDF / Ontología OWL
   |
   v
Agente de Recomendación
   |
   v
Consultas SPARQL
   |
   v
Recomendaciones personalizadas
