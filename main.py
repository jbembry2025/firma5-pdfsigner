from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import base64
import requests

app = Flask(__name__)

@app.route("/sign-pdf", methods=["POST"])
def sign_pdf():
    try:
        # Get inputs
        pdf_file = request.files['pdf']
        signature_data = request.form['signature']  # base64 string OR image URL
        page_number = int(request.form.get('page', 0))
        x = int(request.form.get('x', 100))
        y = int(request.form.get('y', 100))

        # Handle signature: base64 string OR image URL
        if signature_data.startswith("http"):
            # Fetch image from URL
            response = requests.get(signature_data)
            signature_img = Image.open(io.BytesIO(response.content))
        else:
            # Assume base64 data string
            signature_img = Image.open(io.BytesIO(base64.b64decode(signature_data.split(",")[-1])))

        # Load PDF and get page
        pdf_reader = PdfReader(pdf_file)
        page = pdf_reader.pages[page_number]

        # Create overlay PDF with signature
        packet = io.BytesIO()
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        c = canvas.Canvas(packet, pagesize=(width, height))

        # Convert PIL image for reportlab
        sig_bytes = io.BytesIO()
        signature_img.save(sig_bytes, format="PNG")
        sig_bytes.seek(0)
        c.drawImage(ImageReader(sig_bytes), x, y, width=150, height=50, mask='auto')  # Adjust as needed
        c.save()
        packet.seek(0)

        # Merge overlay with original PDF
        overlay_pdf = PdfReader(packet)
        writer = PdfWriter()
        base_page = page
        base_page.merge_page(overlay_pdf.pages[0])
        writer.add_page(base_page)

        # Write result PDF to output
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        return send_file(output_stream, download_name="signed.pdf", as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0")
