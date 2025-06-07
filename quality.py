import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context, no_update
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Initialize Dash app with a modern theme and exception suppression
# Ensure your custom styles.css is linked in the assets folder
app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
app.title = "Quality Dashboard"

# --- Global Styles and Configurations ---
# Refined Custom Light Theme Dictionary
custom_light_theme_dict = {
    "layout": {
        "paper_bgcolor": "#f8f9fa", # Lighter background for the entire plot area
        "plot_bgcolor": "#ffffff", # White background for the plotting region
        "font": {"color": "#495057", "family": "Arial, sans-serif"}, # Slightly softer text color, added font family
        "title": {"x": 0.5, "xanchor": "center", "font": {"color": "#343a40"}},
        "xaxis": {"gridcolor": "#e9ecef", "linecolor": "#ced4da"}, # Lighter grid lines
        "yaxis": {"gridcolor": "#e9ecef", "linecolor": "#ced4da"},
        "legend": {"bgcolor": "#ffffff", "bordercolor": "#e0e0e0", "borderwidth": 1, "font": {"color": "#495057"}},
        "margin": {"t": 60, "b": 40, "l": 50, "r": 30}, "annotations": [],
        # Refined Colorway for charts (Bootstrap-inspired but slightly adjusted)
        "colorway": ["#007bff", "#28a745", "#fd7e14", "#6f42c1", "#dc3545", "#17a2b8", "#e83e8c"] # Added orange and purple
    }
}
custom_light_theme = go.layout.Template(custom_light_theme_dict)

# Consistent inline styles (you can move these to CSS if preferred)
dropdown_inline_style = {"color": "#495057", "background-color": "#ffffff", "border": "1px solid #ced4da", "border-radius": "0.25rem"}
input_inline_style = {"background-color": "#ffffff", "border": "1px solid #ced4da", "color": "#495057", "width": "100%", "padding": "0.375rem 0.75rem", "borderRadius": "0.25rem"}


# --- Helper Functions ---
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

        essential_columns = ['Date', 'Run ID', 'Status', 'Roll ID', 'Avg Thickness',
                             'Theoretical Weight', 'Actual Weight', 'Density']

        if not all(col in df.columns for col in essential_columns):
            missing_cols = [col for col in essential_columns if col not in df.columns]
            return None, f"Missing essential columns in the CSV: {', '.join(missing_cols)}. Please ensure the CSV contains all required data."

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        if 'Startup Weight ' in df.columns:
            df['Startup Weight'] = df['Startup Weight ']
            df.drop(columns=['Startup Weight '], inplace=True)
        if 'Startup Weight' not in df.columns:
            df['Startup Weight'] = 0

        return df, None
    except Exception as e:
        return None, f"Error processing file: {e}"


def generate_kpi_cards(dff, custom_theme_dict):
    if dff.empty:
        return dbc.Row(dbc.Col(dbc.Alert("No data available for KPIs based on current filters.", color="warning", className="mt-4"), width=12))

    total_rolls = len(dff)
    acceptance_rate = (dff['Status'] == 'Accepted').mean() * 100 if not dff.empty else 0
    avg_thickness = dff['Avg Thickness'].mean() if not dff.empty else 0
    avg_density = dff['Density'].mean() if not dff.empty else 0

    total_actual_weight = dff['Actual Weight'].sum() if 'Actual Weight' in dff.columns and not dff.empty else 0
    total_startup_weight = dff['Startup Weight'].sum() if 'Startup Weight' in dff.columns and not dff.empty else 0
    accepted_actual_weight = dff[dff['Status'] == 'Accepted']['Actual Weight'].sum() if 'Actual Weight' in dff.columns and not dff.empty else 0

    total_weight_for_accepted_calc = total_actual_weight + total_startup_weight
    accepted_weight_percentage = (accepted_actual_weight / total_weight_for_accepted_calc) * 100 if total_weight_for_accepted_calc > 0 else 0
    startup_weight_percentage = (total_startup_weight / total_actual_weight) * 100 if total_actual_weight > 0 else 0


    return dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([html.H5("Total Rolls", className="text-secondary mb-0"),], className="d-flex justify-content-between align-items-center")),
            dbc.CardBody([html.H3(f"{total_rolls}", className="text-primary"),dbc.Progress(value=(total_rolls % 100) + 1, className="mb-1", style={"height": "5px"}, color="primary"),html.Small("Total products processed", className="text-secondary")])
        ], className="dbc-card"), md=6, lg=3),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([html.H5("Acceptance Rate", className="text-secondary mb-0"),], className="d-flex justify-content-between align-items-center")),
            dbc.CardBody([html.H3(f"{acceptance_rate:.2f}%", className="text-success"),dbc.Progress(value=acceptance_rate, className="mb-1", style={"height": "5px"}, color="success"),html.Small("Percentage of accepted rolls", className="text-secondary")])
        ], className="dbc-card"), md=6, lg=3),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([html.H5("Avg Thickness", className="text-secondary mb-0"),], className="d-flex justify-content-between align-items-center")),
            dbc.CardBody([html.H3(f"{avg_thickness:.2f}", className="text-info"),dbc.Progress(value=(avg_thickness % 100 if avg_thickness > 0 else 0) * 2, className="mb-1", style={"height": "5px"}, color="info"),html.Small("Average thickness of rolls", className="text-secondary")])
        ], className="dbc-card"), md=6, lg=3),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([html.H5("Avg Density", className="text-secondary mb-0"),], className="d-flex justify-content-between align-items-center")),
            dbc.CardBody([html.H3(f"{avg_density:.3f}", className="text-warning"),dbc.Progress(value=(avg_density % 100 if avg_density > 0 else 0) * 100, className="mb-1", style={"height": "5px"}, color="warning"),html.Small("Average density of rolls", className="text-secondary")])
        ], className="dbc-card"), md=6, lg=3),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([html.H5("Accepted Weight %", className="text-secondary mb-0"),], className="d-flex justify-content-between align-items-center")),
            dbc.CardBody([html.H3(f"{accepted_weight_percentage:.2f}%", className="text-success"),dbc.Progress(value=accepted_weight_percentage, className="mb-1", style={"height": "5px"}, color="success"),html.Small("Accepted / (Actual + Startup Weight)", className="text-secondary")])
        ], className="dbc-card"), md=6, lg=3),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([html.H5("Total Startup Weight", className="text-secondary mb-0"),], className="d-flex justify-content-between align-items-center")),
            dbc.CardBody([html.H3(f"{total_startup_weight:.2f}", className="text-info"),dbc.Progress(value=(total_startup_weight % 100 if total_startup_weight > 0 else 0) + 1, className="mb-1", style={"height": "5px"}, color="info"),html.Small("Total weight from startup operations", className="text-secondary")])
        ], className="dbc-card"), md=6, lg=3),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.Div([html.H5("Startup Weight % of Total", className="text-secondary mb-0"),], className="d-flex justify-content-between align-items-center")),
            dbc.CardBody([html.H3(f"{startup_weight_percentage:.2f}%", className="text-warning"),dbc.Progress(value=startup_weight_percentage, className="mb-1", style={"height": "5px"}, color="warning"),html.Small("Startup Weight / Total Actual Weight", className="text-secondary")])
        ], className="dbc-card"), md=6, lg=3),
    ])

def generate_statistical_summary_table(dff):
    if dff.empty:
        return dbc.Alert("No data available for statistical summary based on current filters.", color="warning", className="mt-4")

    statistical_summary_data = []
    numerical_cols_for_summary = ['Avg Thickness', 'Theoretical Weight', 'Actual Weight', 'Density', 'Startup Weight']
    for col in numerical_cols_for_summary:
        if col in dff.columns and dff[col].dtype in ['float64', 'int64']:
            stats = dff[col].describe().to_dict()
            statistical_summary_data.append({
                'Metric': col,
                'Count': f"{stats.get('count', 0):.0f}",
                'Mean': f"{stats.get('mean', 0):.2f}",
                'Std Dev': f"{stats.get('std', 0):.2f}",
                'Min': f"{stats.get('min', 0):.2f}",
                '25%': f"{stats.get('25%', 0):.2f}",
                '50% (Median)': f"{stats.get('50%', 0):.2f}",
                '75%': f"{stats.get('75%', 0):.2f}",
                'Max': f"{stats.get('max', 0):.2f}"
            })
    return dash_table.DataTable(
        id='summary-table',
        columns=[{"name": i, "id": i} for i in statistical_summary_data[0].keys()] if statistical_summary_data else [],
        data=statistical_summary_data,
        style_table={'overflowX': 'auto', 'backgroundColor': '#ffffff', 'border': 'none'},
        style_header={
            'backgroundColor': '#e9ecef', 'color': '#343a40', 'fontWeight': 'bold',
            'borderBottom': '1px solid #dee2e6', 'borderTop': 'none'
        },
        style_data={
            'backgroundColor': '#ffffff', 'color': '#495057',
            'borderBottom': '1px solid #e0e0e0'
        },
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f0f2f5'}],
        css=[{'selector': 'table', 'rule': 'width: 100%;'}],
    )

def create_dynamic_chart_figure(dff, x_axis, y_axis, chart_type, custom_theme):
    dynamic_fig = go.Figure(layout=go.Layout(
        title_text=f"No data to display or selected columns not available for {y_axis} over {x_axis}",
        xaxis_title=x_axis,
        yaxis_title=y_axis,
        template=custom_theme
    ))

    if not dff.empty and x_axis in dff.columns and y_axis in dff.columns:
        if chart_type == 'line':
            dynamic_fig = px.line(dff, x=x_axis, y=y_axis, color='Run ID' if 'Run ID' in dff.columns else None, title=f'{y_axis} over {x_axis}', template=custom_theme)
            dynamic_fig.update_layout(hovermode="x unified")
        elif chart_type == 'bar':
            dynamic_fig = px.bar(dff, x=x_axis, y=y_axis, color='Run ID' if 'Run ID' in dff.columns else None, title=f'{y_axis} by {x_axis}', template=custom_theme)
        elif chart_type == 'scatter':
            dynamic_fig = px.scatter(dff, x=x_axis, y=y_axis, color='Status' if 'Status' in dff.columns else None, size='Avg Thickness' if 'Avg Thickness' in dff.columns else None, hover_data=dff.columns, title=f'{y_axis} vs. {x_axis}', template=custom_theme)
        elif chart_type == 'histogram':
            dynamic_fig = px.histogram(dff, x=y_axis, nbins=20, title=f'Distribution of {y_axis}', template=custom_theme)
    dynamic_fig.update_layout(title_x=0.5)
    return dynamic_fig

def create_control_chart_figure(dff, ucl_value, lcl_value, min_y_axis, max_y_axis, custom_theme, custom_theme_dict):
    actual_weight_control_chart_fig = go.Figure()
    actual_weight_control_chart_fig.update_layout(template=custom_theme)

    if not dff.empty and 'Roll ID' in dff.columns and 'Actual Weight' in dff.columns:
        actual_weight_control_chart_fig.add_trace(
            go.Scatter(
                x=dff['Roll ID'],
                y=dff['Actual Weight'],
                mode='lines+markers',
                name='Actual Weight',
                marker=dict(color=custom_theme_dict["layout"]["colorway"][0])
            )
        )
        mean_actual_weight = dff['Actual Weight'].mean()
        actual_weight_control_chart_fig.add_hline(
            y=mean_actual_weight,
            line_dash="dash",
            line_color="grey",
            annotation_text=f"Mean: {mean_actual_weight:.2f}",
            annotation_position="bottom right"
        )

        if ucl_value is not None and pd.isna(ucl_value) == False and pd.api.types.is_number(ucl_value):
            actual_weight_control_chart_fig.add_hline(
                y=ucl_value,
                line_dash="dot",
                line_color="red",
                annotation_text=f"UCL: {ucl_value:.2f}",
                annotation_position="top right"
            )

        if lcl_value is not None and pd.isna(lcl_value) == False and pd.api.types.is_number(lcl_value):
            actual_weight_control_chart_fig.add_hline(
                y=lcl_value,
                line_dash="dot",
                line_color="red",
                annotation_text=f"LCL: {lcl_value:.2f}",
                annotation_position="bottom left"
            )

        if min_y_axis is not None and max_y_axis is not None and min_y_axis < max_y_axis:
            actual_weight_control_chart_fig.update_yaxes(range=[min_y_axis, max_y_axis])
        elif min_y_axis is not None:
            actual_weight_control_chart_fig.update_yaxes(range=[min_y_axis, None])
        elif max_y_axis is not None:
            actual_weight_control_chart_fig.update_yaxes(range=[None, max_y_axis])

        if ucl_value is not None and lcl_value is not None and ucl_value < lcl_value:
             actual_weight_control_chart_fig.layout.shapes = [s for s in actual_weight_control_chart_fig.layout.shapes if s.y0 != ucl_value and s.y0 != lcl_value]
             actual_weight_control_chart_fig.layout.annotations = [a for a in actual_weight_control_chart_fig.layout.annotations if 'UCL' not in a.text and 'LCL' not in a.text]


        actual_weight_control_chart_fig.update_layout(
            title_text='Actual Weight Control Chart (Roll ID)',
            xaxis_title='Roll ID',
            yaxis_title='Actual Weight',
            title_x=0.5
        )
    else:
        actual_weight_control_chart_fig.update_layout(
            title_text='Actual Weight Control Chart (Roll ID) - No Data or Missing Columns',
            xaxis_title='Roll ID',
            yaxis_title='Actual Weight',
            title_x=0.5
        )
    return actual_weight_control_chart_fig

def create_pie_chart_figure(dff, custom_theme):
    pie_fig = go.Figure(layout=go.Layout(
        title_text="No data for Status Distribution or 'Status' column missing",
        template=custom_theme
    ))
    if not dff.empty and 'Status' in dff.columns:
        pie_fig = px.pie(dff, names='Status', title='Status Distribution', template=custom_theme, hole=0.3)
    pie_fig.update_layout(title_x=0.5)
    return pie_fig

def create_density_histogram_figure(dff, custom_theme):
    density_histogram = go.Figure(layout=go.Layout(
        title_text="No data for Avg Thickness Distribution or 'Avg Thickness' column missing",
        template=custom_theme
    ))
    if not dff.empty and 'Avg Thickness' in dff.columns:
        density_histogram = px.histogram(dff, x='Avg Thickness', nbins=20, title='Avg Thickness Distribution', template=custom_theme)
    density_histogram.update_layout(title_x=0.5)
    return density_histogram

def create_run_id_trend_chart_figure(dff, custom_theme):
    run_id_trend_chart = go.Figure(layout=go.Layout(
        title_text="No data for Mean Avg Thickness per Run ID Trend or required columns missing",
        template=custom_theme
    ))
    if not dff.empty and 'Run ID' in dff.columns and 'Avg Thickness' in dff.columns and 'Date' in dff.columns:
        mean_thickness_per_run = dff.groupby('Run ID')['Avg Thickness'].mean().reset_index()
        run_dates = dff.groupby('Run ID')['Date'].agg(['min', 'max']).reset_index()
        run_dates['Date Range Label'] = run_dates.apply(
            lambda row: f"{row['Run ID']} ({row['min'].strftime('%d/%m/%Y')} to {row['max'].strftime('%d/%m/%Y')})",
            axis=1
        )
        merged_run_data = pd.merge(mean_thickness_per_run, run_dates[['Run ID', 'Date Range Label']], on='Run ID')
        run_id_trend_chart = px.line(merged_run_data, x='Date Range Label', y='Avg Thickness', title='Mean Avg Thickness per Run ID Trend', template=custom_theme)
    run_id_trend_chart.update_layout(title_x=0.5)
    return run_id_trend_chart


# --- Dash App Layout ---
app.layout = dbc.Container([
    dcc.Download(id="download-dataframe-csv"),
    dcc.Download(id="download-chart-image"),

    dbc.Row(dbc.Col(
        html.P("Created By Eng / Bahaa Abdelfattah",
               className="text-start mb-0 text-secondary fw-bold",
               style={'fontSize': '0.9em', 'paddingLeft': '15px', 'paddingTop': '15px'}),
        width=12
    ), className="mt-0"),

    dbc.Row(dbc.Col(
        html.Img(
            src=app.get_asset_url('Hyma Logo.png'),
            style={'height': '370px', 'width': 'auto', 'display': 'block', 'margin': '0 auto 20px auto'}
        ),
        width=12, className="text-center mt-0"
    )),
    dbc.Row(dbc.Col(html.H1("Quality Control Dashboard", className="text-center my-4 text-primary"))),


    html.Div(id='upload-section-container', children=[
        dbc.Row(dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Upload Your Quality Data", className="card-title text-center mb-3 text-secondary"),
                    html.P("Drag and drop your CSV file here, or click to select a file from your computer.", className="text-center text-secondary mb-4"),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.I(className="bi bi-cloud-arrow-up-fill"),
                            html.Div('Drag and Drop your file here', style={'marginTop': '10px', 'fontWeight': 'bold'}),
                            html.A('or Click to Browse', className="text-primary fw-bold d-block mt-2")
                        ]),
                        style={
                            'width': '100%',
                            'height': '180px',
                            'lineHeight': 'normal',
                            'borderWidth': '3px',
                            'borderStyle': 'dashed',
                            'borderRadius': '12px',
                            'textAlign': 'center',
                            'padding': '30px',
                            'margin': '10px auto',
                            'borderColor': '#007bff',
                            'backgroundColor': '#f8f9fa',
                            'color': '#495057',
                            'cursor': 'pointer',
                            'transition': 'all 0.3s ease-in-out',
                            'display': 'flex',
                            'flexDirection': 'column',
                            'justifyContent': 'center',
                            'alignItems': 'center'
                        },
                        className="upload-component"
                        ,multiple=False
                    ),
                    html.Div(id='upload-status-message', className="text-center mt-3")
                ])
            ], className="dbc-card upload-card mb-5"),
            width=8, lg=6, md=8, className="mx-auto"
        ))
    ]),

    dbc.Row(dbc.Col(html.Div(id='dashboard-content'), width=12))
], fluid=True, className="dbc-container-fluid")

app.layout.children.append(dcc.Store(id='collapse-store', data={'summary_open': True, 'viz_open': True}))
app.layout.children.append(dcc.Store(id='stored-data'))


# --- Callbacks ---

@app.callback(
    [Output('dashboard-content', 'children'),
     Output('upload-section-container', 'style'),
     Output('upload-status-message', 'children'),
     Output('stored-data', 'data')],
    Input('upload-data', 'contents')
)
def handle_upload_and_initial_dashboard_load(contents):
    if contents is None:
        return (dbc.Alert("Please upload a CSV file to view the dashboard.", color="info", className="mt-4"),
                {'display': 'block'},
                "",
                None)

    df, error_message = parse_contents(contents)

    if error_message:
        return (no_update,
                {'display': 'block'},
                dbc.Alert(error_message, color="danger", className="mt-3"),
                None)

    if df.empty:
        return (dbc.Alert("The uploaded CSV file is empty or could not be parsed correctly.", color="danger", className="mt-4"),
                {'display': 'block'},
                "",
                None)

    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'datetime']).columns.tolist()
    if 'Date' in categorical_cols:
        categorical_cols.remove('Date')

    if 'Startup Weight' in df.columns and 'Startup Weight' not in numerical_cols:
        numerical_cols.append('Startup Weight')

    initial_dashboard_layout = html.Div([
        dbc.Button(
            "Toggle Production & Statistical Summary",
            id="toggle-summary-button",
            className="mb-3 mt-4 section-toggle-button",
            color="primary",
            n_clicks=0
        ),
        dbc.Collapse(
            html.Div([
                html.H3("Production & Statistical Summary", className="text-center my-4 text-secondary"),
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardHeader(html.H5("Filter Options", className="card-title text-secondary")),
                        dbc.CardBody([
                            html.Label("Filter by Status", className="text-secondary"),
                            dcc.Dropdown(
                                id='status-filter',
                                options=[{"label": s, "value": s} for s in df['Status'].unique()],
                                multi=True,
                                value=df['Status'].unique().tolist(),
                                className="mb-3 dash-dropdown",
                                style=dropdown_inline_style
                            ),
                            html.Label("Select Run ID", className="text-secondary"),
                            dcc.Dropdown(
                                id='run-filter',
                                options=[{"label": r, "value": r} for r in df['Run ID'].unique()],
                                multi=True,
                                value=df['Run ID'].unique().tolist(),
                                className="mb-3 dash-dropdown",
                                style=dropdown_inline_style
                            ),
                            html.Label("Select Date Range", className="text-secondary"),
                            dcc.DatePickerRange(
                                id='date-range',
                                start_date=df['Date'].min(),
                                end_date=df['Date'].max(),
                                display_format='YYYY-MM-DD',
                                className="mb-3",
                                style={"width": "100%", "color": "#495057", "background-color": "#f8f9fa", "border": "1px solid #ced4da"}
                            )
                        ])
                    ], className="dbc-card"), md=4),

                    dbc.Col(html.Div(id='kpi-cards', className="mb-4"), md=8),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardHeader(html.H5("Statistical Summary", className="card-title text-secondary")),
                        dbc.CardBody(html.Div(id='statistical-summary-table'))
                    ], className="dbc-card"), md=12)
                ]),
            ]),
            id="summary-collapse",
            is_open=True,
        ),

        dbc.Button(
            "Toggle Visualizations",
            id="toggle-viz-button",
            className="mb-3 mt-4 section-toggle-button",
            color="primary",
            n_clicks=0
        ),
        dbc.Collapse(
            html.Div([
                html.H3("Visualizations", className="text-center my-4 text-secondary"),
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardHeader(html.H5("Dynamic Chart Options", className="card-title text-secondary")),
                        dbc.CardBody([
                            html.Label("Select X-axis (Numerical/Date)", className="text-secondary mt-2"),
                            dcc.Dropdown(
                                id='x-axis-selector',
                                options=[{'label': col, 'value': col} for col in numerical_cols + ['Date']],
                                value='Date',
                                className="mb-3 dash-dropdown",
                                style=dropdown_inline_style
                            ),
                            html.Label("Select Y-axis (Numerical)", className="text-secondary"),
                            dcc.Dropdown(
                                id='y-axis-selector',
                                options=[{'label': col, 'value': col} for col in numerical_cols],
                                value='Avg Thickness',
                                className="mb-3 dash-dropdown",
                                style=dropdown_inline_style
                            ),
                            html.Label("Select Chart Type", className="text-secondary"),
                            dcc.Dropdown(
                                id='chart-type-selector',
                                options=[
                                    {'label': 'Line Plot', 'value': 'line'},
                                    {'label': 'Bar Plot', 'value': 'bar'},
                                    {'label': 'Scatter Plot', 'value': 'scatter'},
                                    {'label': 'Histogram', 'value': 'histogram'}
                                ],
                                value='line',
                                className="mb-3 dash-dropdown",
                                style=dropdown_inline_style
                            ),
                            html.H5("Control Chart Limits (for Actual Weight)", className="card-title text-secondary mt-4"),
                            dcc.Input(
                                id='ucl-input',
                                type='number',
                                placeholder='Enter UCL',
                                className="mb-3 form-control",
                                style=input_inline_style
                            ),
                            html.Label("Lower Control Limit (LCL)", className="text-secondary"),
                            dcc.Input(
                                id='lcl-input',
                                type='number',
                                placeholder='Enter LCL',
                                className="mb-3 form-control",
                                style=input_inline_style
                            ),
                            html.H5("Y-axis Range (Actual Weight Control Chart)", className="card-title text-secondary mt-4"),
                            html.Label("Minimum Y-axis Value", className="text-secondary mt-2"),
                            dcc.Input(
                                id='min-y-axis-input',
                                type='number',
                                placeholder='Enter Min Y',
                                className="mb-3 form-control",
                                style=input_inline_style
                            ),
                            html.Label("Maximum Y-axis Value", className="text-secondary"),
                            dcc.Input(
                                id='max-y-axis-input',
                                type='number',
                                placeholder='Enter Max Y',
                                className="mb-3 form-control",
                                style=input_inline_style
                            ),
                            dbc.Button([html.I(className="bi bi-download me-2"), "Export Dynamic Chart as PNG"], id="btn-export-dynamic-chart", color="info", className="mb-2 mt-4"),
                        ])
                    ], className="dbc-card"), md=4),
                    dbc.Col(dbc.Card(dcc.Loading(dcc.Graph(id='dynamic-chart'), type="circle"), className="dbc-card"), md=8),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col(dbc.Card(dcc.Loading(dcc.Graph(id='actual-weight-control-chart'), type="circle"), className="dbc-card"), md=6),
                    dbc.Col(dbc.Card(dcc.Loading(dcc.Graph(id='status-pie'), type="circle"), className="dbc-card"), md=6),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Card(dcc.Loading(dcc.Graph(id='density-histogram'), type="circle"), className="dbc-card"), md=6),
                    dbc.Col(dbc.Card([
                        dbc.CardHeader(html.H5("Mean Avg Thickness per Run ID Trend", className="card-title text-secondary")),
                        dbc.CardBody(dcc.Loading(dcc.Graph(id='box-plot-thickness'), type="circle"))
                    ], className="dbc-card"), md=6),
                ]),
                dbc.Row(dbc.Col(
                    dbc.Button([html.I(className="bi bi-download me-2"), "Export Filtered Data as CSV"], id="btn-export-filtered-data", color="success", className="mb-3 mt-4"),
                    width=12, className="text-center"
                ))
            ]),
            id="viz-collapse",
            is_open=True,
        ),
    ])

    return (initial_dashboard_layout, {'display': 'none'}, "", df.to_dict('records'))

@app.callback(
    Output("summary-collapse", "is_open"),
    Output("collapse-store", "data", allow_duplicate=True),
    Input("toggle-summary-button", "n_clicks"),
    State("summary-collapse", "is_open"),
    State("collapse-store", "data"),
    prevent_initial_call=True
)
def toggle_summary_collapse(n_clicks, is_open, store_data):
    if n_clicks:
        new_state = not is_open
        store_data['summary_open'] = new_state
        return new_state, store_data
    return no_update, no_update


@app.callback(
    Output("viz-collapse", "is_open"),
    Output("collapse-store", "data", allow_duplicate=True),
    Input("toggle-viz-button", "n_clicks"),
    State("viz-collapse", "is_open"),
    State("collapse-store", "data"),
    prevent_initial_call=True
)
def toggle_viz_collapse(n_clicks, is_open, store_data):
    if n_clicks:
        new_state = not is_open
        store_data['viz_open'] = new_state
        return new_state, store_data
    return no_update, no_update


@app.callback(
    [
        Output('kpi-cards', 'children'),
        Output('dynamic-chart', 'figure'),
        Output('actual-weight-control-chart', 'figure'),
        Output('status-pie', 'figure'),
        Output('density-histogram', 'figure'),
        Output('box-plot-thickness', 'figure'),
        Output('statistical-summary-table', 'children')
    ],
    [
        Input('status-filter', 'value'),
        Input('run-filter', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
        Input('x-axis-selector', 'value'),
        Input('y-axis-selector', 'value'),
        Input('chart-type-selector', 'value'),
        Input('ucl-input', 'value'),
        Input('lcl-input', 'value'),
        Input('min-y-axis-input', 'value'),
        Input('max-y-axis-input', 'value')
    ],
    State('stored-data', 'data')
)
def update_dashboard_content(status, run_ids, start_date, end_date, x_axis, y_axis, chart_type, ucl_value, lcl_value, min_y_axis, max_y_axis, data):
    if data is None:
        raise PreventUpdate

    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    dff = df[
        df['Status'].isin(status) &
        df['Run ID'].isin(run_ids) &
        (df['Date'] >= pd.to_datetime(start_date)) &
        (df['Date'] <= pd.to_datetime(end_date))
    ].copy()

    kpis = generate_kpi_cards(dff, custom_light_theme_dict)
    dynamic_fig = create_dynamic_chart_figure(dff, x_axis, y_axis, chart_type, custom_light_theme)
    actual_weight_control_chart_fig = create_control_chart_figure(dff, ucl_value, lcl_value, min_y_axis, max_y_axis, custom_light_theme, custom_light_theme_dict)
    pie_fig = create_pie_chart_figure(dff, custom_light_theme)
    density_histogram = create_density_histogram_figure(dff, custom_light_theme)
    run_id_trend_chart = create_run_id_trend_chart_figure(dff, custom_light_theme)
    statistical_summary_table = generate_statistical_summary_table(dff)

    return kpis, dynamic_fig, actual_weight_control_chart_fig, pie_fig, density_histogram, run_id_trend_chart, statistical_summary_table

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-export-filtered-data", "n_clicks"),
    State('status-filter', 'value'),
    State('run-filter', 'value'),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    State('stored-data', 'data'),
    prevent_initial_call=True
)
def export_filtered_data(n_clicks, status, run_ids, start_date, end_date, data):
    if not n_clicks or data is None:
        raise PreventUpdate

    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    dff = df[
        df['Status'].isin(status) &
        df['Run ID'].isin(run_ids) &
        (df['Date'] >= pd.to_datetime(start_date)) &
        (df['Date'] <= pd.to_datetime(end_date))
    ].copy()

    if 'Date' in dff.columns:
        dff['Date'] = dff['Date'].dt.strftime('%Y-%m-%d')

    return dcc.send_data_frame(dff.to_csv, "filtered_quality_data.csv", index=False)

@app.callback(
    Output("download-chart-image", "data"),
    Input("btn-export-dynamic-chart", "n_clicks"),
    State('dynamic-chart', 'figure'),
    State('x-axis-selector', 'value'),
    State('y-axis-selector', 'value'),
    prevent_initial_call=True
)
def export_dynamic_chart(n_clicks, figure_data, x_axis, y_axis):
    if not n_clicks or figure_data is None:
        raise PreventUpdate

    fig = go.Figure(figure_data)
    
    filename = f"dynamic_chart_{y_axis}_vs_{x_axis}.png".replace(" ", "_").replace("/", "-")

    return dcc.send_image(fig.to_image(format="png"), filename=filename)


if __name__ == '__main__':
    app.run(debug=True)