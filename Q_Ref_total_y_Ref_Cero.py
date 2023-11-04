import dash
from dash.dependencies import Input, Output
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go



# Carga del archivo Excel en un DataFrame
df = pd.read_excel('183Garantia.xlsx')

# Código ya existente 
or_garantia = ['2AC', '2BC']
df = df[df['Tipo O.R'].isin(or_garantia)]
df['Mes'] = pd.to_datetime(df['O.R_F.cierre'], dayfirst=True).dt.month_name(locale='es_ES')
resultado_1 = df.groupby('Mes').agg({
    'Refer.': 'count',
    'Total factura': 'sum'
}).reset_index()
meses_ordenados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
resultado_1['Mes'] = pd.Categorical(resultado_1['Mes'], categories=meses_ordenados, ordered=True)
resultado_1 = resultado_1.sort_values('Mes')

#Filtramos el dataframe original para quedarnos solo con las filas que tengan un valor 'Tipo O.R'
#  que esté en la lista or_garantia:
df_original = pd.read_excel('183Garantia.xlsx')
df = df_original.copy()
df_garantia = df[df['Tipo O.R'].isin(or_garantia)]

# Tu código nuevo
df_garantia = df_original[df_original['Tipo O.R'].isin(or_garantia)].copy()
df_garantia['Mes'] = pd.to_datetime(df_garantia['O.R_F.cierre'], dayfirst=True).dt.month_name(locale='es_ES')
df_garantia['Mes'] = pd.Categorical(df_garantia['Mes'], categories=meses_ordenados, ordered=True)
#Agrupamos por mes y contamos las referencias. Esta operación nos dará el número total de 
# referencias que se hicieron en el mes:
ref_garantia = df_garantia.groupby('Mes').agg({'Refer.': 'count'}).rename(columns={'Refer.': 'Ref Cerradas en Garantia'})
#De las referencias filtradas, buscamos aquellas que cerraron con un 'Total factura' en cero 
# y las agrupamos por mes:
ref_cero = df_garantia[df_garantia['Total factura'] == 0].groupby('Mes').agg({'Refer.': 'count'}).rename(columns={'Refer.': 'Ref cerradas en Cero'})
#Fusionamos los dataframes para tener ambos conteos en una misma tabla y rellenamos 
# #con ceros donde no haya datos:
resultado_2 = pd.merge(ref_garantia, ref_cero, left_index=True, right_index=True, how='outer').fillna(0).reset_index()
#agregar el 'Mes' como una columna 
# Carga del archivo Excel en un DataFrame

meses_ordenados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
df_garantia['Mes'] = pd.Categorical(df_garantia['Mes'], categories=meses_ordenados, ordered=True)

resultado_2 = resultado_2.reset_index()

#Calculamos el porcentaje de referencias que cerraron en cero:
resultado_2['% de ref en cero'] = ((resultado_2['Ref cerradas en Cero'] / resultado_2['Ref Cerradas en Garantia']) * 100).round(2).astype(str) + '%'
#Calculamos las referencias tramitadas en garantía, que serían las referencias 
# totales menos las que cerraron en cero:
resultado_2['Tramitadas en Garantia'] = resultado_2['Ref Cerradas en Garantia'] - resultado_2['Ref cerradas en Cero']
#calculamos las referencias cerradas tramitadas por día asumiendo que hay 22 días laborables por mes:
resultado_2['Ref cerradas, tramitadas por dia'] = (resultado_2['Tramitadas en Garantia'] / 22).round(2)


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("OR En Garantía"),
    html.H3("Resumen por mes"),
    dash_table.DataTable(
        id='table-summary-1',
        columns=[{"name": i, "id": i} for i in resultado_1.columns],
        data=resultado_1.to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'}
    ),
    dcc.Graph(
    
    id='bar-chart',
    figure={
        'data': [
            {
                'x': resultado_1['Mes'],
                'y': resultado_1['Refer.'],
                'type': 'bar',
                'name': 'Referencias cerradas',
                'marker': {'color': '#2980B9',
                           'line': {
                               'color': '#154360 ',  # Color del borde
                                'width': 2  # Grosor del borde
                           }

                           } 
            },
            {
                'x': resultado_1['Mes'],
                'y': resultado_1['Total factura'],
                'type': 'line',
                'name': 'Total factura',
                'line': {'color': '#E74C3C'}  # Color rojo para la línea
            },
        ],
        'layout': {
            'title': 'Referencias cerradas y facturación total por mes',
            'xaxis': {
                'title': 'Mes',
            },
            'yaxis': {
                'title': 'Valor'
            }
        }
    }
),

    html.H3("Detalle de Referencias Trabajadas en Garantia"),
    dash_table.DataTable(
        id='table-summary-2',
        columns=[{"name": i, "id": i} for i in resultado_2.columns],
        data=resultado_2.reset_index().to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'}
    ),
    
    html.H3("Gráfico Por Mes "),
    dcc.Dropdown(
        id='month-selector',
        options=[{'label': month, 'value': month} for month in meses_ordenados],
        value='Enero'  # valor inicial
    ),
    dcc.Graph(id='pie-chart')
])

@app.callback(
    Output('pie-chart', 'figure'),
    [Input('month-selector', 'value')]
)
def update_pie_chart(selected_month):

    filtered_df = resultado_2[resultado_2['Mes'] == selected_month]

    total_ref_garantia = filtered_df['Ref Cerradas en Garantia'].values[0]
    ref_cero = filtered_df['Ref cerradas en Cero'].values[0]

    labels = ['Ref Cerradas en Garantia - Restantes', 'Ref cerradas en Cero']
    values = [
        total_ref_garantia - ref_cero,
        ref_cero
    ]

   # Actualizar colores
    colors = ['#85C1E9', '#138D75']

    return {
        'data': [go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        textinfo='label+percent',
        marker=dict(
            colors=colors,  # Nueva definición de colores
            line=dict(color='#1B4F72 ', width=2)  # Definición del borde
        )
    )],
        'layout': {
            'title': f'Distribución para {selected_month}'
        }
    }


if __name__ == '__main__':
    app.run_server(debug=True)

