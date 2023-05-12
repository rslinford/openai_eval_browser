import os
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    # the directory to list
    root_dir = '../evals/evals/registry/data'

    # get the subdirectories in the root directory
    sub_dirs = next(os.walk(root_dir))[1]

    return render_template('home.html', sub_dirs=sub_dirs)


@app.route('/list_files')
def list_files():
    # the root directory
    root_dir = './static/files'

    # get the selected subdirectory from the HTML form
    selected_dir = request.args.get('selected_dir')

    # if no subdirectory is selected, use the root directory
    if not selected_dir:
        selected_dir = root_dir

    # get the files and subdirectories in the selected directory
    files = os.listdir(selected_dir)
    sub_dirs = [os.path.join(selected_dir, f) for f in files if os.path.isdir(os.path.join(selected_dir, f))]

    return render_template('list_files.html', files=files, sub_dirs=sub_dirs)


if __name__ == '__main__':
    app.run(debug=True)