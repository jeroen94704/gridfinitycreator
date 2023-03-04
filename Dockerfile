FROM continuumio/miniconda3
RUN apt-get update -y && \
	apt install -y libgl1-mesa-glx && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN conda install -c conda-forge -c cadquery cadquery=master && \
	conda clean -a -y

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /app

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]

CMD ["view.py" ]
