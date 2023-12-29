import os
import requests
import gzip
from io import BytesIO
import pandas as pd


class Analysis:
    def __init__(self):
        self.titles = None
        self.ratings = None
        self.crew = None
        self.genres = None
        self.genres_combinations = None

        self._check_dataset_age()
        self._check_if_dataset_exists()
        self._read_data()
        self._recalculate()

    def _check_dataset_age(self):
        try:
            with open('dataset/timestamp.txt', 'r') as file:
                timestamp = file.read()
                if pd.Timestamp.now() - pd.Timestamp(timestamp) > pd.Timedelta(days=1):
                    print('Dataset is too old. Downloading a new one...')
                    self._check_if_dataset_exists(old=True)
        except FileNotFoundError:
            print('Dataset does not have a timestamp.')
            self._check_if_dataset_exists(old=True)
    def _check_if_dataset_exists(self, old=False):
        # if at least one file in the folder does not exist or dataset is too old, download dataset
        if not os.path.exists('dataset/titles.tsv') or not os.path.exists('dataset/ratings.tsv') or not os.path.exists('dataset/crew.tsv') or old:
            # movies data
            self._download_data('https://datasets.imdbws.com/title.basics.tsv.gz', 'dataset/titles.tsv')
            # ratings data
            self._download_data('https://datasets.imdbws.com/title.ratings.tsv.gz', 'dataset/ratings.tsv')
            # crew data
            self._download_data('https://datasets.imdbws.com/title.crew.tsv.gz', 'dataset/crew.tsv')

            # write the current timestamp to a file
            with open('dataset/timestamp.txt', 'w') as file:
                file.write(str(pd.Timestamp.now()))

    def delete_dataset(self):
        if os.path.exists('dataset/titles.tsv'):
            os.remove('dataset/titles.tsv')
        if os.path.exists('dataset/ratings.tsv'):
            os.remove('dataset/ratings.tsv')
        if os.path.exists('dataset/crew.tsv'):
            os.remove('dataset/crew.tsv')

        print('Deleted existing dataset.')

        self._check_if_dataset_exists()

    def _download_data(self, url, destination):
        print(f"Downloading {url.split('/')[-1]}...")
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Decompress the gzip content
            compressed_data = BytesIO(response.content)
            with gzip.GzipFile(fileobj=compressed_data, mode='rb') as decompressed_data:
                # Save the decompressed content to a local file
                with open(destination, 'wb') as file:
                    file.write(decompressed_data.read())
            print(f"Downloaded successfully.")
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")

    def _read_data(self):
        # read the data
        self.titles = pd.read_csv('dataset/titles.tsv', sep='\t')
        self.ratings = pd.read_csv('dataset/ratings.tsv', sep='\t')
        self.crew = pd.read_csv('dataset/crew.tsv', sep='\t')

    def _recalculate(self):
        self._count_genres()
        self._count_genre_combinations()

    def _count_genres(self):
        # calculate the number of movies in each genre (one movie can have multiple genres)
        self.genres = {}
        for i in self.titles['genres']:
            i = str(i)
            if i != '\\N':
                for j in i.split(','):
                    if j in self.genres:
                        self.genres[j] += 1
                    else:
                        self.genres[j] = 1

    def _count_genre_combinations(self):
        self.genres_combinations = {}
        # creating the combinations
        for i in range(0, len(self.genres.keys())):
            for j in range(i + 1, len(self.genres.keys())):
                self.genres_combinations[(list(self.genres.keys())[i], list(self.genres.keys())[j])] = 0
        # counting the combinations
        for i in self.titles['genres']:
            i = str(i).split(',')
            if len(i) > 1:
                # creating possible genre combinations
                for j in range(0, len(i)):
                    for k in range(j + 1, len(i)):
                        if (i[j], i[k]) in self.genres_combinations:
                            self.genres_combinations[(i[j], i[k])] += 1
                        else:
                            self.genres_combinations[(i[k], i[j])] += 1