from analysis import Analysis
import json

if __name__ == '__main__':
    try:
        with open('params.json', 'r') as file:
            params = dict(json.load(file)['params'])
    except:
        raise FileNotFoundError('params.json not found')
    analysis = Analysis(params=params)
    analysis.run()
