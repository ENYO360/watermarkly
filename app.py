"""Web version of the watermarker.

The watermark is drawn in the visitor's browser (see static/render.js), so the
preview updates instantly and photos are never uploaded. Flask only serves the page.
"""

from flask import Flask, render_template

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)