import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import flask
import plotly.graph_objs as go

import os
import io
import pandas as pd
import numpy as np
from starkit.gridkit import load_grid
from wsynphot import list_filters
from wsynphot.io.cache_filters import load_transmission_data

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Load the grid to be used for plotting spectrum
grid = load_grid('test_grid.h5')
teff_extent, logg_extent, mh_extent = grid.get_grid_extent()

# Generate filter id options for dropdown
filter_ids = np.sort(list_filters()['filterID'])
filter_id_options = [{'label': filter_id, 'value': filter_id}
                     for filter_id in filter_ids]


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
                # marks={
                #    param_extent[0]: 'min',
                #    param_extent[1]: 'max'
                # }
            )
        ]
    )


# Define layout (front-end components) of the app
app.layout = html.Div([
    html.Div(
        className='controls',
        children=[
            html.Div(
                className='parameter-sliders-container',
                children=[
                    generate_slider('T eff', 'teff_slider', 1, teff_extent),
                    generate_slider('log g', 'logg_slider', 0.1, logg_extent),
                    generate_slider('[M/H]', 'mh_slider', 0.1, mh_extent)
                ]
            ),
            html.Div(
                className='filter-selection-container',
                children=[
                    html.Label(
                        'Select Filter to overplot',
                        className='filter-dropdown-label',
                        htmlFor='filter-ids-dropdown'
                    ),
                    dcc.Dropdown(
                        id='filter-ids-dropdown',
                        options=filter_id_options,
                        multi=True,
                        placeholder='Start typing to find the filter ID'
                    ),
                    html.Button(
                        'Clear All',
                        id='clear-all-btn'
                    )
                ]
            )
        ]),
    dcc.Graph(id='spectrum_graph'),
    html.Div(
        html.A(
            id='download-btn',
            children=html.Button('Download This Spectrum')
        ),
        className='download-btn-container'
    )
])


# To plot the spectrum on every change in value of sliders
@app.callback(
    Output('spectrum_graph', 'figure'),
    [Input('teff_slider', 'value'),
     Input('logg_slider', 'value'),
     Input('mh_slider', 'value'),
     Input('filter-ids-dropdown', 'value')])
def plot_graph(selected_teff, selected_logg, selected_mh, selected_filters):
    grid.teff = selected_teff
    grid.logg = selected_logg
    grid.mh = selected_mh
    wave, flux = grid()

    graph_data = [go.Scatter(
        x=wave,
        y=flux,
        mode='lines',
        name='Spectrum'
    )]

    if selected_filters is not None:
        for filter_id in selected_filters:
            filter_data = load_transmission_data(filter_id)
            scaling_factor = max(flux)/max(filter_data['Transmission'])
            graph_data.append(go.Scatter(
                x=filter_data['Wavelength'],
                y=filter_data['Transmission']*scaling_factor,
                mode='lines',
                name=filter_id
            ))

    return {
        'data': graph_data,
        'layout': go.Layout(
            title={'text': 'Spectrum',
                   'font': {'size': 20}},
            xaxis={'title': 'Wavelength (Ang)',
                   'exponentformat': 'none'},
            yaxis={'title': 'Flux',
                   'exponentformat': 'e'}
        )
    }


# To update the url (where a download button click will lead to) on every
# change in value of sliders
@app.callback(
    Output('download-btn', 'href'),
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


# To clear all filter selections at once
@app.callback(
    Output('filter-ids-dropdown', 'value'),
    [Input('clear-all-btn', 'n_clicks')])
def clear_all_filters(n_clicks):
    return None


if __name__ == '__main__':
    app.run_server(debug=True)
