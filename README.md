# IMDb movies analysis
This project analyzes a select set of movies in regard to their genres treating it as a complex network.

# Dataset
The data is directly acquired from the IMDb database (https://developer.imdb.com/non-commercial-datasets/).

# Parameters for the analysis
The parameters for the analysis can be edited in the 'params.json' file."
'top' and 'last' parameters are used to select the movies to be analyzed. 'top' selects the top 'n' movies, 
while 'last' selects the last 'n' movies. If both are set to 0, all the movies are selected. The parameter 'sampling'
determines the fraction of movies to be selected from the set of movies.

# Output
The output of the analysis is a .html file, which contains the network graph created using pyvis.

# Required libraries
The required libraries to run the code are as follows: os, json, pandas, pyvis, gzip and io.ByteISO.
