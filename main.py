from flask import Flask, render_templates

app = Flask("__main__")

@app.route("/")
def main():
    return render_templates("paginainicial.html")

if __name__ == "__main__":
    app.run(debug=True)