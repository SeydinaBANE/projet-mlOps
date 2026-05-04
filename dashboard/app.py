import logging
import os

import dash
import pandas as pd
import plotly.express as px
import psycopg2
from dash import dcc, html
from dash.dependencies import Input, Output
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard E-commerce", style={"textAlign": "center", "fontFamily": "Arial"}),
    html.Div(id="kpis", style={"display": "flex", "justifyContent": "center", "gap": "40px", "margin": "20px"}),
    html.Div([
        dcc.Graph(id="graph-ventes"),
        dcc.Graph(id="graph-clients"),
    ], style={"display": "flex", "gap": "20px", "padding": "0 20px"}),
    dcc.Interval(id="interval", interval=10000, n_intervals=0),
])


def get_data() -> pd.DataFrame:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    try:
        return pd.read_sql("""
            SELECT o.id, o.customer_id, c.nom AS client,
                   o.statut, o.montant_total,
                   DATE(o.created_at) AS date
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
        """, conn)
    finally:
        conn.close()


@app.callback(
    Output("kpis", "children"),
    Output("graph-ventes", "figure"),
    Output("graph-clients", "figure"),
    Input("interval", "n_intervals"),
)
def update(n):
    try:
        df = get_data()
    except Exception as e:
        logger.error("Erreur base de données : %s", e)
        msg = html.Div(
            f"Erreur de connexion à la base de données : {e}",
            style={"color": "red", "textAlign": "center"},
        )
        return [msg], {}, {}

    if df.empty:
        return [html.P("Aucune donnée disponible.")], {}, {}

    ca_total = df[df.statut == "completed"]["montant_total"].sum()
    nb_commandes = len(df)
    nb_clients = df["client"].nunique()

    kpis = [
        html.Div([html.H2(f"{ca_total:,.0f} FCFA"), html.P("CA Total")],
            style={"textAlign": "center", "background": "#e8f5e9", "padding": "20px",
                   "borderRadius": "10px", "minWidth": "180px"}),
        html.Div([html.H2(nb_commandes), html.P("Commandes")],
            style={"textAlign": "center", "background": "#e3f2fd", "padding": "20px",
                   "borderRadius": "10px", "minWidth": "180px"}),
        html.Div([html.H2(nb_clients), html.P("Clients actifs")],
            style={"textAlign": "center", "background": "#fff3e0", "padding": "20px",
                   "borderRadius": "10px", "minWidth": "180px"}),
    ]

    ventes_jour = df.groupby("date")["montant_total"].sum().reset_index()
    fig_ventes = px.bar(ventes_jour, x="date", y="montant_total",
        title="CA par jour", labels={"montant_total": "FCFA", "date": "Date"})

    ventes_client = df.groupby("client")["montant_total"].sum().reset_index()
    fig_clients = px.pie(ventes_client, names="client", values="montant_total",
        title="Répartition CA par client")

    return kpis, fig_ventes, fig_clients


if __name__ == "__main__":
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=8050)
