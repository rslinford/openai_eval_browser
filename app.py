import json
import os
from flask import Flask, render_template, request

app = Flask(__name__)

root_dir = '../evals/evals/registry/data'
samples_filename = 'samples.jsonl'


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
                           sample=first_sample)

def load_samples(sub_dir_filename):
    samples_full_filename = os.path.join(root_dir, sub_dir_filename, samples_filename)

    samples = []
    with open(samples_full_filename, 'r') as file:
        for line in file:
            samples.append(line)
    return samples

@app.route('/', methods=['POST'])
def home_post():
    # get the subdirectories in the root directory
    sub_dirs = next(os.walk(root_dir))[1]
    sub_dir = request.form['sub_dir']
    if 'sample' in request.form:
        x = request.form['sample']
        sample = json.loads(x)
    else:
        sample = json.loads('{}')

    samples = load_samples(sub_dir)

    return render_template('home.html',
                           sub_dirs=sub_dirs,
                           sub_dir=sub_dir,
                           samples=samples,
                           sample=sample)


if __name__ == '__main__':
    app.run(debug=True)