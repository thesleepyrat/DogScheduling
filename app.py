import os
import pandas as pd
from flask import Flask, request, render_template, send_file, flash
from scheduler import space_runs_min_gap_hard   # your existing function

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('No file selected.')
            return render_template('index.html')

        f = request.files['file']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
        f.save(filepath)

        output_filename = 'result_' + f.filename
        output_path = os.path.join(app.config['RESULT_FOLDER'], output_filename)

        # Run your processing function that writes the output file
        space_runs_min_gap_hard(input_path=filepath, output_path=output_path)

        # Return the output file for immediate download
        return send_file(
            output_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=output_filename
        )

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
