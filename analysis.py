import os
import requests
import gzip
from io import BytesIO
import pandas as pd
import pyvis


class Analysis:
    def __init__(self, params=None):
        self.genres = {}
        self.genres_combinations = {}
        self.network = pyvis.network.Network()

        if params is not None:
            self.params = params
        else:
            # default parameters
            self.params = {
                'minimal_rating': 0.0,
                'maximal_rating': 10.0,
                'minimal_year': 0,
                'maximal_year': 9999,
                'minimal_count': 0,
                'maximal_count': 9999999999,
                'top': 0,
                'last': 0,
                'sampling': 0.5
            }

        self._check_dataset_age()
        self._check_if_dataset_exists()
        self._read_data()
        start_time = pd.Timestamp.now()
        self._filter_data()
        self._count_genres()
        self._count_genre_combinations()
        print(f'Analysis took {(pd.Timestamp.now() - start_time)} and loaded {len(self.titles)} movies.')

    def _check_dataset_age(self):
        try:
            with open('dataset/timestamp.txt', 'r') as file:
                timestamp = file.read()
                if pd.Timestamp.now() - pd.Timestamp(timestamp) > pd.Timedelta(days=7):
                    print('Dataset is too old. Downloading a new one...')
                    self._check_if_dataset_exists(old=True)
        except FileNotFoundError:
            print('Dataset does not have a timestamp.')
            self._check_if_dataset_exists(old=True)

    def _check_if_dataset_exists(self, old=False):
        # if dataset folder does not exist, create it
        if not os.path.exists('dataset'):
            os.mkdir('dataset')
        # if at least one file in the folder does not exist or dataset is too old, download dataset
        if not os.path.exists('dataset/titles.tsv') or not os.path.exists('dataset/ratings.tsv') or not os.path.exists(
                'dataset/crew.tsv') or old:
            # movies data
            self._download_data('https://datasets.imdbws.com/title.basics.tsv.gz', 'dataset/titles.tsv')
            # ratings data
            self._download_data('https://datasets.imdbws.com/title.ratings.tsv.gz', 'dataset/ratings.tsv')

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

    @staticmethod
    def _download_data(url, destination):
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
            raise Exception(f"An error occurred while downloading the dataset. Error code: {response.status_code}")

    def _read_data(self):
        self.titles = pd.read_csv('dataset/titles.tsv', sep='\t')
        self.ratings = pd.read_csv('dataset/ratings.tsv', sep='\t')

        # merging the dataframes and sampling
        self.titles = self.titles.merge(self.ratings, on='tconst').sample(frac=float(self.params['sampling']))

    def _filter_data(self):
        indices_to_drop = []
        for index, row in self.titles.iterrows():
            if '\\N' in [str(row['startYear']), str(row['averageRating']), str(row['startYear']), str(row['genres'])]:
                indices_to_drop.append(index)
                continue
            elif int(row['startYear']) < self.params['minimal_year'] or int(row['startYear']) > self.params[
                'maximal_year']:
                indices_to_drop.append(index)
                continue
            elif float(row['averageRating']) < self.params['minimal_rating'] or float(row['averageRating']) > \
                    self.params['maximal_rating']:
                indices_to_drop.append(index)
                continue
        print(f'Dropped {len(indices_to_drop)} movies due to filtering.')
        self.titles = self.titles.drop(indices_to_drop)

    def _count_genres(self):
        for i in self.titles['genres']:
            i = str(i)
            if i != '\\N':
                for j in i.split(','):
                    if j not in self.genres:
                        self.genres[j] = 1
                    else:
                        self.genres[j] += 1
        if 'nan' in self.genres:
            del self.genres['nan']

    def _count_genre_combinations(self):
        # creating the combinations
        for i in range(0, len(self.genres.keys())):
            for j in range(i + 1, len(self.genres.keys())):
                self.genres_combinations[(list(self.genres.keys())[i], list(self.genres.keys())[j])] = 0
        # counting the combinations
        for i in self.titles['genres']:
            i = str(i).split(',')
            if len(i) > 1:
                # creating possible genre combinations from the dataset entries
                for j in range(0, len(i)):
                    for k in range(j + 1, len(i)):
                        if (i[j], i[k]) in self.genres_combinations:
                            self.genres_combinations[(i[j], i[k])] += 1
                        else:
                            self.genres_combinations[(i[k], i[j])] += 1

    def run(self):
        self._plot()

    def _plot(self):
        for genre, count in self.genres.items():
            self.network.add_node(genre, label=str(genre), value=count, title=str(count))

        # sorting the combinations by count for top/last genres combinations
        sorted_combinations = [x[0] for x in sorted(self.genres_combinations.items(), key=lambda x: x[1], reverse=True)]

        # calculating top/last genres combinations and plotting
        for (genre1, genre2), count in self.genres_combinations.items():
            if count == 0:
                continue
            elif count < self.params['minimal_count']:
                continue
            elif count > self.params['maximal_count']:
                continue

            if self.params['top'] == 0 and self.params['last'] == 0:
                self.network.add_edge(genre1, genre2, weight=count, title=str(count), label=str(count))
                continue

            if self.params['top'] != 0 and (genre1, genre2) in sorted_combinations[:self.params['top']]:
                self.network.add_edge(genre1, genre2, weight=count, title=str(count), label=str(count))
            if self.params['last'] != 0 and (genre1, genre2) in sorted_combinations[-self.params['last']:]:
                self.network.add_edge(genre1, genre2, weight=count, title=str(count), label=str(count))

        self.network.toggle_physics(True)
        self.network.force_atlas_2based(gravity=-20)
        self.network.show_buttons(filter_=['physics'])
        self.network.show('network.html', notebook=False)
