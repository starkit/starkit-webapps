import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.graph_objs as go

from starkit.gridkit import load_grid


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


grid = load_grid('test_grid.h5')
teff_extent, logg_extent, mh_extent = grid.get_grid_extent()


def generate_slider(slider_header, slider_id, slider_step, param_extent):
    """Generates a well-formatted division (<div> element) for slider along
    with its header.
    
    Parameters
    ----------
    slider_header : str
        Heading/title of the slider
    slider_id : str
        id for slider element
    slider_step : int or float
        Value of step for the slider
    param_extent : tuple
        Extent/range of grid parameter described as a tuple (min_val, max_val)
    
    Returns
    -------
    dash.dash_html_components.Div
    """
    return html.Div(
        className='slider',
        children=[
            html.Div(
                slider_header,
                className='slider-header'
            ),
            dcc.Slider(
                id=slider_id,
                className='slider-control',
                min=param_extent[0],
                max=param_extent[1],
                value=param_extent[0],
                step=slider_step,
                tooltip={
                    'always_visible': True,
                    'placement': 'topLeft'
                },
                #marks={
                #    param_extent[0]: 'min',
                #    param_extent[1]: 'max'
                #}
            )     
        ]
    )


app.layout = html.Div([
    generate_slider('T eff', 'teff_slider', 1, teff_extent),
    generate_slider('log g', 'logg_slider', 0.1, logg_extent),
    generate_slider('[M/H]', 'mh_slider', 0.1, mh_extent),
    dcc.Graph(id='spectrum_graph')
])


@app.callback(
    Output('spectrum_graph', 'figure'),
    [Input('teff_slider', 'value'),
     Input('logg_slider', 'value'),
     Input('mh_slider', 'value')])
def plot_spectrum(selected_teff, selected_logg, selected_mh):
    grid.teff = selected_teff
    grid.logg = selected_logg
    grid.mh = selected_mh
    wave, flux = grid()

    return {
        'data': [go.Scatter(
            x=wave,
            y=flux,
            mode='lines'
            )],
        'layout': go.Layout(
            title={'text': 'Spectrum', 
                'font': {'size': 20}},
            xaxis={'title': 'Wavelength (Ang)'},
            yaxis={'title': 'Flux',
                'exponentformat': 'e'}
            )
        }


if __name__ == '__main__':
    app.run_server(debug=True)