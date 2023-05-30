import json
import os

import openai
import yaml
from flask import Flask, render_template, request, session

app = Flask(__name__)

with open("api_key.txt", "r") as file:
    openai.api_key = file.read().strip()

# Flask's secret key to make session available.
app.secret_key = openai.api_key

registry_dir = '../evals/evals/registry'
data_dir = os.path.join(registry_dir, 'data')
evals_dir = os.path.join(registry_dir, 'evals')
# Default file name for samples. If this file doesn't exist, a sample file will be picked at random.
default_samples_filename = 'samples.jsonl'
# Samples are silently ignored over this max
MAX_SAMPLES = 3000


def load_samples(samples_filename):
    samples = []
    samples_full_filename = os.path.join(data_dir, samples_filename)
    with open(samples_full_filename, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i > MAX_SAMPLES:
                break
            samples.append(line.strip())
    return samples


def read_sub_dirs():
    return next(os.walk(data_dir))[1]


class Eval:
    def __init__(self, name, the_id, metrics, the_class, samples_jsonl, eval_type, modelgraded_spec_file):
        self.name = name
        self.the_id = the_id
        self.metrics = metrics
        self.the_class = the_class
        self.samples_jsonl = samples_jsonl
        self.eval_type = eval_type
        self.modelgraded_spec_file = modelgraded_spec_file

    def __repr__(self):
        return f'name({self.name}) id({self.the_id}) metrics({self.metrics}) class({self.the_class}) samples_jsonl({self.samples_jsonl}) eval_type({self.eval_type}) modelgraded_spec_file({self.modelgraded_spec_file})'


def load_evals():
    registry = load_registry()
    evals = []
    for k, v in registry.items():
        if 'id' not in v:
            continue
        metrics = ''
        the_class = ''
        samples_jsonl = ''
        eval_type = ''
        modelgraded_spec_file = ''
        the_id = v['id']
        if 'metrics' in v:
            metrics = v['metrics']
        sub_item = registry[the_id]
        if 'class' in sub_item:
            the_class = sub_item['class']
        if 'args' not in sub_item:
            # Skip this one. No args means no samples file.
            print(f'No "args" found. Skipping Eval {k}')
            continue
        args = sub_item['args']
        if 'samples_jsonl' in args:
            samples_jsonl = args['samples_jsonl']
        if 'eval_type' in args:
            eval_type = args['eval_type']
        if 'modelgraded_spec_file' in args:
            modelgraded_spec_file = args['modelgraded_spec_file']
        # modelgraded_spec_file has been renamed recently to modelgraded_spec so both are still in use.
        if 'modelgraded_spec' in args:
            modelgraded_spec_file = args['modelgraded_spec']

        evals.append(Eval(k, the_id, metrics, the_class, samples_jsonl, eval_type, modelgraded_spec_file))
    return evals


def load_registry():
    registry = {}
    for d in os.listdir(evals_dir):
        with open(os.path.join(evals_dir, d), 'r', encoding='utf-8') as f:
            registry.update(yaml.load(f, Loader=yaml.FullLoader))

    return registry


@app.route('/registry', methods=['GET'])
def registry_get():
    registry = load_registry()
    return render_template('registry.html',
                           registry=registry)


@app.route('/', methods=['GET'])
def evals_get():
    evals = load_evals()
    samples = load_samples(evals[0].samples_jsonl)
    sample = json.loads(samples[0])
    return render_template('evals.html',
                           evals=evals,
                           samples=samples,
                           eval_name_index=0,
                           sample_index=0,
                           sample=sample,
                           selected_eval=evals[0])


@app.route('/', methods=['POST'])
def evals_post():
    eval_name_index = request.form['eval_name']
    if 'eval_name_index' in session:
        eval_name_unchanged = session['eval_name_index'] == eval_name_index
    else:
        eval_name_unchanged = False
    session['eval_name_index'] = eval_name_index
    session.modified = True

    if eval_name_unchanged:
        sample_index = request.form['sample']
    else:
        sample_index = 0
    evals = load_evals()
    if len(evals[int(eval_name_index)].samples_jsonl) > 0:
        try:
            samples = load_samples(evals[int(eval_name_index)].samples_jsonl)
            sample = json.loads(samples[int(sample_index)])
        except FileNotFoundError:
            samples = ''
            sample = json.loads(
                '{"input": [{"role": "error", "content": "Eval sample file not found"}], "ideal": ""}')
    else:
        samples = ''
        sample = json.loads('{"input": [{"role": "error", "content": "Eval sample file not specified."}], "ideal": ""}')

    # Validate sample structure
    try:
        dummy = sample['input'][0]['role']
        dummy = sample['ideal']
    except (TypeError, KeyError):
        sample = json.loads('{"input": [{"role": "error", "content": "Non-standard sample format"}], "ideal": ""}')

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

    return render_template('evals.html',
                           evals=evals,
                           samples=samples,
                           eval_name_index=eval_name_index,
                           sample_index=sample_index,
                           sample=sample,
                           selected_eval=evals[int(eval_name_index)],
                           assistant_response=assistant_response,
                           finish_reason=finish_reason)


if __name__ == '__main__':
    app.run(debug=True)
