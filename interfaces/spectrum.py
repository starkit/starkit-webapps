import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import flask
import plotly.graph_objs as go

import os
import io
import pandas as pd
from starkit.gridkit import load_grid


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


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


# Define layout (front-end components) of the app
app.layout = html.Div([
    generate_slider('T eff', 'teff_slider', 1, teff_extent),
    generate_slider('log g', 'logg_slider', 0.1, logg_extent),
    generate_slider('[M/H]', 'mh_slider', 0.1, mh_extent),
    dcc.Graph(id='spectrum_graph'),
    html.A(
        id='download_btn',
        children=html.Button('Download This Spectrum')
    )
])


# To plot the spectrum on every change in value of sliders
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


# To update the url (where a download button click will lead to) on every 
# change in value of sliders
@app.callback(
    Output('download_btn', 'href'),
    [Input('teff_slider', 'value'),
     Input('logg_slider', 'value'),
     Input('mh_slider', 'value')])
def update_href(selected_teff, selected_logg, selected_mh):
    return '/downloadSpectrum?teff={0}&logg={1}&mh={2}'.format(
        selected_teff, selected_logg, selected_mh)


# To download spectrum as csv file on clicking the download button
# (This function is actually triggered by the route where clicking takes us) 
@app.server.route('/downloadSpectrum')
def download_spectrum():
    # Get data from the HTTP request (in url)
    selected_teff = flask.request.args.get('teff')
    selected_logg = flask.request.args.get('logg')
    selected_mh = flask.request.args.get('mh')
    fname = 'pheonix_teff{0}_logg{1}_mh{2}.csv'.format(
        selected_teff, selected_logg, selected_mh)
    
    grid.teff = selected_teff
    grid.logg = selected_logg
    grid.mh = selected_mh
    wave, flux = grid()

    # Write csv file dynamically (in text stream) instead of saving it on disk
    str_io = io.StringIO()
    data = pd.DataFrame({'Wavelength': wave, 'Flux': flux})
    data.to_csv(str_io, index=False)

    # Convert to binary stream since flask.send_file() permits only that
    mem = io.BytesIO()
    mem.write(str_io.getvalue().encode('utf-8'))
    mem.seek(0)
    str_io.close()
    return flask.send_file(mem,
                       mimetype='text/csv',
                       attachment_filename=fname,
                       as_attachment=True)


if __name__ == '__main__':
    app.run_server(debug=True)