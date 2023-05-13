import json
import os
from flask import Flask, render_template, request

app = Flask(__name__)

root_dir = '../evals/evals/registry/data'
samples_filename = 'samples.jsonl'


def load_samples(sub_dir_filename):
    samples_full_filename = os.path.join(root_dir, sub_dir_filename, samples_filename)

    samples = []
    with open(samples_full_filename, 'r') as file:
        for line in file:
            samples.append(line.strip())
    return samples


def read_sub_dirs():
    return next(os.walk(root_dir))[1]


@app.route('/', methods=['GET'])
def home():
    # get the subdirectories in the root directory
    sub_dirs = next(os.walk(root_dir))[1]
    first_sub_dir_name = sub_dirs[1]
    samples = load_samples(first_sub_dir_name)
    first_sample = json.loads(samples[0])
    return render_template('home.html',
                           sub_dirs=sub_dirs,
                           sub_dir=first_sub_dir_name,
                           samples=samples,
                           sample_index=0,
                           sample=first_sample)


@app.route('/', methods=['POST'])
def home_post():
    # get the subdirectories in the root directory
    sub_dirs = read_sub_dirs()
    sub_dir = request.form['sub_dir']
    samples = load_samples(sub_dir)

    sample_index = int(request.form['sample'])
    sample = json.loads(samples[sample_index])

    return render_template('home.html',
                           sub_dirs=sub_dirs,
                           sub_dir=sub_dir,
                           samples=samples,
                           sample_index=sample_index,
                           sample=sample)


if __name__ == '__main__':
    app.run(debug=True)