# app.py
from flask import Flask, render_template, request, send_file
from io import BytesIO
from barcode_generator import generate_barcode_range_pdf

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        start = request.form.get("start_code")
        end = request.form.get("end_code")

        if not start or not end:
            return render_template("index.html", error="Both start and end codes are required.")

        try:
            pdf_file = generate_barcode_range_pdf(start, end)
            return send_file(
                pdf_file,
                download_name="barcode_sheet.pdf",
                as_attachment=True,
                mimetype="application/pdf"
            )

        except Exception as e:
            return render_template("index.html", error=f"Error generating PDF: {e}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
