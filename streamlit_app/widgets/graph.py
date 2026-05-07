"""Graph rendering helpers. Pure functions — no Streamlit imports.

Returns DOT strings (for st.graphviz_chart) or Plotly Figures
(for st.plotly_chart). Pages call these and pass results to the right
st.* primitive.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import plotly.graph_objects as go  # type: ignore

# ---------------------------------------------------------------------------
# Node colour maps
# ---------------------------------------------------------------------------

_ADR_STATUS_COLOR: dict[str, str] = {
    "accepted": "lightgreen",
    "proposed": "lightyellow",
    "superseded": "lightgray",
    "rejected": "lightcoral",
}

_STEP_DONE_COLOR = "lightgreen"
_STEP_PENDING_COLOR = "white"


# ---------------------------------------------------------------------------
# DOT helpers
# ---------------------------------------------------------------------------


def _dot_node(node_id: str, label: str, **attrs: str) -> str:
    """Render a single DOT node statement."""
    attr_str = ", ".join(f'{k}="{v}"' for k, v in attrs.items())
    safe_id = node_id.replace("-", "_").replace(".", "_")
    return f'  "{safe_id}" [label="{label}", {attr_str}];'


def _dot_edge(src: str, dst: str, label: str = "") -> str:
    """Render a single DOT edge statement."""
    safe_src = src.replace("-", "_").replace(".", "_")
    safe_dst = dst.replace("-", "_").replace(".", "_")
    if label:
        return f'  "{safe_src}" -> "{safe_dst}" [label="{label}"];'
    return f'  "{safe_src}" -> "{safe_dst}";'


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def step_dag_dot(steps: list[dict]) -> str:
    """Build Graphviz DOT source for an IMPLEMENTATION_PLAN step DAG.

    Each step dict: {step_id: str, label: str, done: bool,
    dependencies: list[str]}.
    Done steps rendered with ``style=filled, fillcolor=lightgreen``;
    pending plain.
    """
    lines = ["digraph G {", '  rankdir="LR";']

    for step in steps:
        step_id = step.get("step_id", "")
        label = step.get("label", step_id)
        done = bool(step.get("done", False))
        color = _STEP_DONE_COLOR if done else _STEP_PENDING_COLOR
        style = "filled" if done else "solid"
        lines.append(_dot_node(step_id, label, style=style, fillcolor=color))

    for step in steps:
        step_id = step.get("step_id", "")
        for dep in step.get("dependencies", []):
            lines.append(_dot_edge(dep, step_id))

    lines.append("}")
    return "\n".join(lines)


def adr_lineage_dot(adrs: list[dict]) -> str:
    """Build Graphviz DOT source for an ADR supersession DAG.

    Each adr dict: {id: str, title: str, status: str,
    supersedes: str|None, superseded_by: str|None}.
    Edges go from successor to predecessor labeled "supersedes".
    Status drives node colour.
    """
    lines = ["digraph G {", '  rankdir="LR";']

    for adr in adrs:
        adr_id = adr.get("id", "")
        title = adr.get("title", adr_id)
        status = str(adr.get("status", "proposed")).lower()
        color = _ADR_STATUS_COLOR.get(status, "white")
        lines.append(
            _dot_node(adr_id, f"{adr_id}\\n{title}", style="filled", fillcolor=color)
        )

    for adr in adrs:
        adr_id = adr.get("id", "")
        supersedes = adr.get("supersedes")
        if supersedes:
            lines.append(_dot_edge(adr_id, supersedes, label="supersedes"))

    lines.append("}")
    return "\n".join(lines)


def metrics_aggregate_lines(df: pd.DataFrame):  # type: ignore[return]
    """Build a multi-line trend chart for the 15-field aggregate over time.

    Empty DataFrame returns an empty figure.
    """
    import plotly.graph_objects as go  # noqa: PLC0415

    if df.empty:
        return go.Figure()

    fig = go.Figure()
    # First column is assumed to be the time axis; remainder are metrics.
    columns = list(df.columns)
    if len(columns) < 2:
        return go.Figure()

    time_col = columns[0]
    for metric_col in columns[1:]:
        fig.add_trace(
            go.Scatter(
                x=df[time_col],
                y=df[metric_col],
                mode="lines+markers",
                name=metric_col,
            )
        )

    fig.update_layout(
        xaxis_title=time_col,
        yaxis_title="Value",
        margin={"l": 40, "r": 20, "t": 20, "b": 40},
    )
    return fig


def adr_supersession_dot(adrs: list[dict]) -> str:
    """Alias for adr_lineage_dot — retained for backwards compatibility."""
    return adr_lineage_dot(adrs)


def metrics_sparkline(df: pd.DataFrame, col: str):  # type: ignore[return]
    """Build a Plotly Figure for a single named column over time.

    ``df`` must have at least two columns: the first is treated as the time
    axis; ``col`` is the metric to plot.

    Raises ``KeyError`` if ``col`` is not present in ``df``.
    Returns an empty Figure for an empty DataFrame.
    """
    import plotly.graph_objects as go  # noqa: PLC0415

    if df.empty:
        return go.Figure()

    # Raise KeyError clearly when the column is missing.
    if col not in df.columns:
        raise KeyError(
            f"Column {col!r} not found in DataFrame. Available: {list(df.columns)}"
        )

    time_col = df.columns[0]
    fig = go.Figure(
        go.Scatter(
            x=df[time_col],
            y=df[col],
            mode="lines+markers",
            name=col,
        )
    )
    fig.update_layout(
        xaxis_title=time_col,
        yaxis_title=col,
        margin={"l": 40, "r": 20, "t": 10, "b": 40},
    )
    return fig


def sentinel_health_sparkline(df: pd.DataFrame):  # type: ignore[return]
    """Build a sparkline for SENTINEL_LOG.md health-grade history.

    Empty DataFrame returns an empty figure.
    """
    import plotly.graph_objects as go  # noqa: PLC0415

    if df.empty:
        return go.Figure()

    # Prefer columns named 'health_grade' or 'grade'; fall back to last column.
    grade_col: str | None = None
    for candidate in ("health_grade", "grade", "Health Grade"):
        if candidate in df.columns:
            grade_col = candidate
            break
    if grade_col is None:
        grade_col = df.columns[-1]

    time_col: str | None = None
    for candidate in ("timestamp", "Timestamp", "date", "Date"):
        if candidate in df.columns:
            time_col = candidate
            break

    x_data = df[time_col] if time_col else list(range(len(df)))

    fig = go.Figure(
        go.Scatter(
            x=x_data,
            y=df[grade_col],
            mode="lines+markers",
            line={"color": "steelblue"},
            name="Health Grade",
        )
    )
    fig.update_layout(
        xaxis_title="Run",
        yaxis_title="Grade",
        margin={"l": 40, "r": 20, "t": 10, "b": 40},
    )
    return fig
