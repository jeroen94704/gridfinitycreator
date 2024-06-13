# Gridfinity Creator

This application generates STL or STEP files of configurable Gridfinity compatible components. For example, for the standard divider bin you can specify width, length, height, number of compartments (in both directions) and whether or not you want a stacking lip, magnet holes, screw holes, curved scoop surface and/or one or more label tabs. The total number of possible combinations with those options is beyond one million, which is why the 3D models are dynamically created and not pre-calculated.

## Available components

There are currently a few components available, listed below. Other components are in the works.

- Baseplate: Basic baseplate without screws, magnets or weighting.
- Divider bin: Standard divider bin very similar to Zack's original design. 
- Light bin: A light version of the normal Gridfinity bin that saves plastic and offers more room. This means there is no room for magnets and/or screws
- Solid bin: A completely filled solid Gridfinity bin which can be used as a starting point for custom bins

## Online generator

If you don't know how to run your own server (or simply don't want to), there should be an instance of the generator running at https://gridfinity.bouwens.co. No uptime guarantees, but it has been running since early 2023 and seems stable enough, even with the occasional spike in load.

## Installation and deployment

The generator runs as a web-application in a docker container. To run your own instance, perform the following steps from the command line:

- [Download and unzip the code](https://github.com/jeroen94704/gridfinitycreator/releases/latest) or clone the repository: `git clone https://github.com/jeroen94704/gridfinitycreator`
- cd into the source directory
- Build the Docker Image: `./build.sh`
- Start the server: `./deploy.sh`

You may have to run the above commands as root (e.g. using "sudo")

## Debug mode

The deploy script results in the server running in production mode using the [Waitress WSGI server](https://flask.palletsprojects.com/en/2.2.x/deploying/waitress/). This is good for performance, but if you want to debug the code, start the server using the "./debug.sh" script instead of "./deploy.sh". This will make the server start itself using the built-in Flask server, which has convenient debugging features.

## Reverse proxy

Because I use Traefik myself I included the Traefik labels I use in the docker-compose file. If you want to use Traefik, uncomment them and comment out the "ports" section. You will also need to fill in your domain in the .env.container file. 

I have no experience with other reverse proxy methods (Apache, nginx, Helm, etc), so if anyone creates instructions for setting up GridfinityCreator with any of those I'd happily accept the pull-request.

## Donate

If you find this project useful a small donation is much appreciated (but by no means required or expected): https://ko-fi.com/jeroen94704

## License

GridfinityCreator © 2023 by Jeroen Bouwens is licensed under CC BY-NC-SA 4.0. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/
