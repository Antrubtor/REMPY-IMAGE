import os

from dash import Dash, html

# URL du backend pour les appels API
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

app = Dash(__name__)

app.layout = html.Div([
    html.H1("REMPY-IMAGE"),
    html.P("Frontend Dash - En cours de développement"),
])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
