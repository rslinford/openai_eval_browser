import json
import os

import openai
from flask import Flask, render_template, request, session

app = Flask(__name__)


with open("api_key.txt", "r") as file:
    openai.api_key = file.read().strip()

# Flask's secret key to make session available.
app.secret_key = openai.api_key


root_dir = '../evals/evals/registry/data'
# Default file name for samples. If this file doesn't exist, a sample file will be picked at random.
samples_filename = 'samples.jsonl'
# Samples are silently ignored over this max
MAX_SAMPLES = 3000


def load_samples(sub_dir_filename):
    samples_full_filename = os.path.join(root_dir, sub_dir_filename, samples_filename)

    samples = []
    try:
        with open(samples_full_filename, 'r', encoding='utf-8') as samples_file:
            for i, line in enumerate(samples_file):
                if i > MAX_SAMPLES:
                    break
                samples.append(line.strip())
    except FileNotFoundError as e:
        # Assume non-standard samples filename
        dir_listing = os.listdir(os.path.join(root_dir, sub_dir_filename))
        if len(dir_listing) == 0:
            raise ValueError(f'Samples not found in {os.path.join(root_dir, sub_dir_filename)}')
        if len(dir_listing) > 1:
            print(f'Multiple sample files. Using the first one of: {dir_listing}')
        samples_full_filename = os.path.join(root_dir, sub_dir_filename, dir_listing[0])
        with open(samples_full_filename, 'r', encoding='utf-8') as samples_file:
            for line in samples_file:
                samples.append(line.strip())

    return samples


def read_sub_dirs():
    return next(os.walk(root_dir))[1]


@app.route('/', methods=['GET'])
def home():
    # get the subdirectories in the root directory
    sub_dirs = next(os.walk(root_dir))[1]
    first_sub_dir_name = sub_dirs[0]
    try:
        samples = load_samples(first_sub_dir_name)
    except PermissionError:
        samples = [json.loads('{"input": [{"role": "error", "content": "Failed to load samples"}], "ideal": ""}')]
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
    if 'sub_dir' in session:
        sub_dir_unchanged = session['sub_dir'] == sub_dir
    else:
        sub_dir_unchanged = False
    session['sub_dir'] = sub_dir
    session.modified = True

    try:
        samples = load_samples(sub_dir)
    except PermissionError:
        samples = ['{"input": [{"role": "error", "content": "Failed to load samples"}], "ideal": ""}']

    if sub_dir_unchanged:
        sample_index = int(request.form['sample'])
    else:
        sample_index = 0

    sample = json.loads(samples[sample_index])

    # Validate sample structure
    try:
        dummy = sample['input'][0]['role']
        dummy = sample['ideal']
    except (TypeError, KeyError):
        sample = json.loads('{"input": [{"role": "error", "content": "Invalid sample format"}], "ideal": ""}')

    if 'Prompt' in request.form:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=sample['input'],
                temperature=0,
                top_p=1,
                max_tokens=2048)

            assistant_response = response['choices'][0]['message']['content']
            finish_reason = response['choices'][0]['finish_reason']
            session.modified = True
        except openai.error.OpenAIError as e:
            assistant_response = ''
            finish_reason = str(e)
    else:
        assistant_response = ''
        finish_reason = ''

    return render_template('home.html',
                           sub_dirs=sub_dirs,
                           sub_dir=sub_dir,
                           samples=samples,
                           sample_index=sample_index,
                           sample=sample,
                           assistant_response=assistant_response,
                           finish_reason=finish_reason)


if __name__ == '__main__':
    app.run(debug=True)