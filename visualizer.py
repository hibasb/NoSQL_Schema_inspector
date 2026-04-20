import plotly.graph_objects as go

def build_tree_figure(schema, collection_name="collection"):
    labels = [collection_name]
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
            "string": "📝",
            "integer": "🔢",
            "float": "🔢",
            "boolean": "☑️",
            "object": "📁",
            "array": "📋",
            "null": "∅"
        }
        return icons.get(t, "•")

    # Ajouter les champs de premier niveau
    for field, info in sorted(top_fields.items()):
        presence = info["presence"]
        types = info["types"]
        icon = get_icon(types)
        types_str = ", ".join(types.keys())
        label = f"{icon} {field}"

        labels.append(label)
        parents.append(collection_name)
        values.append(max(presence, 10))
        colors.append(get_color(presence, types))
        texts.append(f"{types_str} | {presence}%")

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
        parent_info = schema.get(parent_field, {})
        parent_icon = get_icon(parent_info.get("types", {"object": 1}))
        parent_label = f"{parent_icon} {parent_field}" if parent_field in top_fields else f"📁 {parts[-2]}"

        label = f"{icon} {parts[-1]}"
        if label in labels:
            label = f"{icon} {field}"

        labels.append(label)
        parents.append(parent_label)
        values.append(max(presence, 10))
        colors.append(get_color(presence, types))
        texts.append(f"{types_str} | {presence}%")

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        text=texts,
        textinfo="label+text",
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
        font=dict(color="white", size=13),
        height=550
    )

    return fig