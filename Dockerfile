FROM continuumio/miniconda3:25.1.1-2

RUN apt-get update -y && \
	apt install -y libgl1-mesa-glx && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN conda update conda && \
    conda install conda-forge::cadquery

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install --no-cache-dir -r requirements.txt 

# copy all local content to the image
COPY . /app

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]

CMD ["gfg_main.py" ]
