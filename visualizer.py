import plotly.graph_objects as go

def build_tree_figure(schema, collection_name="collection"):
    labels = [f"<b>{collection_name}</b>"]
    parents = [""]
    values = [100]
    colors = ["#1e3a5f"]
    texts = ["Racine"]

    # Regrouper les champs par niveau
    top_fields = {}
    nested = {}

    for field, info in schema.items():
        parts = field.split(".")
        if len(parts) == 1:
            top_fields[field] = info
        else:
            parent = ".".join(parts[:-1])
            if parent not in nested:
                nested[parent] = {}
            nested[parent][field] = info

    def get_color(presence, types):
        type_keys = list(types.keys())
        if len(type_keys) > 1:
            return "#f59e0b"   # orange = type mixte
        if presence == 100:
            return "#10b981"   # vert = obligatoire
        elif presence >= 50:
            return "#3b82f6"   # bleu = fréquent
        else:
            return "#6b7280"   # gris = rare

    def get_icon(types):
        t = list(types.keys())[0] if types else "unknown"
        icons = {
            "string": "[str]",
            "integer": "[int]",
            "float": "[float]",
            "boolean": "[bool]",
            "object": "[obj]",
            "array": "[arr]",
            "null": "[null]"
        }
        return icons.get(t, "")

    # Ajouter les champs de premier niveau
    for field, info in sorted(top_fields.items()):
        presence = info["presence"]
        types = info["types"]
        icon = get_icon(types)
        types_str = ", ".join(types.keys())
        label = f"<b>{field}</b>"

        labels.append(label)
        parents.append(f"<b>{collection_name}</b>")
        values.append(max(presence, 10))
        colors.append(get_color(presence, types))
        texts.append(f"{icon}  {types_str} | {presence}%")

    # Ajouter les champs imbriqués
    for field, info in sorted(schema.items()):
        parts = field.split(".")
        if len(parts) < 2:
            continue

        presence = info["presence"]
        types = info["types"]
        icon = get_icon(types)
        types_str = ", ".join(types.keys())

        parent_field = ".".join(parts[:-1])
        parent_label = f"<b>{parent_field}</b>" if parent_field in top_fields else f"<b>{parts[-2]}</b>"

        label = f"<b>{parts[-1]}</b>"
        if label in labels:
            label = f"<b>{field}</b>"

        labels.append(label)
        parents.append(parent_label)
        values.append(max(presence, 10))
        colors.append(get_color(presence, types))
        texts.append(f"{icon}  {types_str} | {presence}%")

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        text=texts,
        textinfo="label+text",
        textposition="middle center",
        hovertemplate="<b>%{label}</b><br>%{text}<extra></extra>",
        marker=dict(
            colors=colors,
            line=dict(width=2, color="#0b0f1a")
        ),
        pathbar=dict(visible=True),
        root_color="#0b0f1a"
    ))

    fig.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        paper_bgcolor="#111827",
        font=dict(color="white", size=15, family="monospace"),
        height=600
    )

    return fig


def build_security_gauge(score: int) -> go.Figure:
    """
    Jauge arc Plotly pour le score de sécurité (0–100).
    Rouge → Orange → Vert selon le score.
    """
    if score >= 70:
        bar_color = "#10b981"   # vert
        label     = "BON"
    elif score >= 40:
        bar_color = "#f59e0b"   # orange
        label     = "MOYEN"
    else:
        bar_color = "#ef4444"   # rouge
        label     = "DANGER"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={
            "text": (
                f"Score de Sécurité<br>"
                f"<span style='font-size:0.85em;color:{bar_color}'>{label}</span>"
            ),
            "font": {"size": 18, "color": "white"}
        },
        number={
            "suffix": " / 100",
            "font": {"size": 42, "color": bar_color}
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#9ca3af",
                "tickfont": {"color": "#9ca3af"}
            },
            "bar": {"color": bar_color, "thickness": 0.25},
            "bgcolor": "#1f2937",
            "borderwidth": 2,
            "bordercolor": "#374151",
            "steps": [
                {"range": [0,  40], "color": "#450a0a"},
                {"range": [40, 70], "color": "#431407"},
                {"range": [70, 100], "color": "#052e16"},
            ],
            "threshold": {
                "line": {"color": bar_color, "width": 4},
                "thickness": 0.75,
                "value": score
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor="#111827",
        font={"color": "white"},
        height=280,
        margin=dict(t=60, b=10, l=30, r=30)
    )

    return fig