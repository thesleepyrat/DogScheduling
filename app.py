from flask import Flask, request
import logging

app = Flask(__name__)

# Enable debug logging to console
logging.basicConfig(level=logging.DEBUG)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        app.logger.debug(f"Request content length: {request.content_length}")
        app.logger.debug(f"Request form keys: {list(request.form.keys())}")
        app.logger.debug(f"Request files keys: {list(request.files.keys())}")

        uploaded_file = request.files.get("file")
        if uploaded_file:
            app.logger.debug(f"Received file: {uploaded_file.filename}")
            return f"Received file: {uploaded_file.filename}"
        else:
            return "No file received", 400

    # Simple upload form with proper enctype
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Upload Test</title></head>
    <body>
        <h1>File Upload Test</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit">Upload</button>
        </form>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
