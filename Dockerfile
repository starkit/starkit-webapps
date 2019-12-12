FROM continuumio/miniconda

# Update conda
RUN conda update -y conda

# Remove (large file sizes) MKL optimizations.
RUN conda install nomkl

# Install gcc required to pip install astropy
RUN apt-get update && apt-get -y install gcc

# Grab environment file for starkit
RUN wget https://raw.githubusercontent.com/starkit/starkit/master/starkit_env3.yml -q

# Create conda environment for starkit
RUN conda env create -n starkit --file ./starkit_env3.yml

# Grab requirements.txt
# TODO: Remove commit tag from starkit when fixed & might need to install it in release phase
ADD ./interfaces/requirements.txt /tmp/requirements.txt

# Activate starkit env & install dependencies in it
RUN /bin/bash -c 'source activate starkit && pip install -r /tmp/requirements.txt'



# Add the code of interfaces to /opt
ADD ./interfaces /opt/interfaces/
WORKDIR /opt/interfaces

# Download test grid in working dir (TODO: Put in release phase)
RUN wget https://zenodo.org/record/2557923/files/phoenix_t4000_10000_w3000_9000_r3000.h5?download=1 -O test_grid.h5 -q



# Activate starkit env & run the spectrum.py as dash app
# TODO: Tie all single page apps in interfaces/ in a multi-page dash app
CMD /bin/bash -c 'source activate starkit && gunicorn spectrum:server'