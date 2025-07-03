import os
import tempfile
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
from io import BytesIO

def parse_code(code):
    parts = code.split("\\")
    return parts[0].upper(), int(parts[1])

def generate_code_range(start_code, end_code):
    start_alpha, start_num = parse_code(start_code)
    end_alpha, end_num = parse_code(end_code)

    def next_code(alpha, num):
        if num < 12:
            return alpha, num + 1
        else:
            alpha = list(alpha)
            idx = len(alpha) - 1
            while idx >= 0:
                if alpha[idx] != 'Z':
                    alpha[idx] = chr(ord(alpha[idx]) + 1)
                    break
                else:
                    alpha[idx] = 'A'
                    idx -= 1
            if idx < 0:
                alpha.insert(0, 'A')
            return ''.join(alpha), 1

    codes = []
    curr_alpha, curr_num = start_alpha, start_num
    while True:
        codes.append(f"{curr_alpha}\\{curr_num}")
        if curr_alpha == end_alpha and curr_num == end_num:
            break
        curr_alpha, curr_num = next_code(curr_alpha, curr_num)
    return codes

def generate_barcode_range_pdf(start_code, end_code):
    # Constants
    dpi = 300
    cm_to_px = lambda cm: int((cm / 2.54) * dpi)
    barcode_width_cm = 4.1
    barcode_height_cm = 1.6
    barcode_width_px = cm_to_px(barcode_width_cm)
    barcode_height_px = cm_to_px(barcode_height_cm)

    barcode_width_mm = 41.0  # 4.1 cm
    barcode_height_mm = 16.0  # 1.6 cm
    spacing_mm = 0.0  # No spacing between barcodes

    col_count = 5  # Force 5 barcodes per row
    x_start = 2.5  # 2.5 mm left margin
    y_start = 5.0  # 5 mm top margin

    max_height_mm = 297 - (2 * y_start)
    row_count = int((max_height_mm + spacing_mm) // (barcode_height_mm + spacing_mm))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_path):
        font_path = "arial.ttf"
    try:
        font = ImageFont.truetype(font_path, 40)
    except:
        font = ImageFont.load_default()

    codes = generate_code_range(start_code, end_code)

    pdf = FPDF("P", "mm", "A4")
    x = x_start
    y = y_start
    col = 0
    row = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, code in enumerate(codes):
            # Generate barcode
            barcode = Code128(code, writer=ImageWriter())
            barcode_img = barcode.render(writer_options={'module_height': 45, 'font_size': 0, 'write_text': False})
            barcode_img = barcode_img.resize((barcode_width_px, int(barcode_height_px * 0.75)), Image.LANCZOS)

            canvas = Image.new("RGB", (barcode_width_px, barcode_height_px), "white")
            draw = ImageDraw.Draw(canvas)
            canvas.paste(barcode_img, (0, 0))

            bbox = draw.textbbox((0, 0), code, font=font)
            x_text = (barcode_width_px - (bbox[2] - bbox[0])) // 2
            y_text = barcode_height_px - (bbox[3] - bbox[1]) - 15
            draw.text((x_text, y_text), code, font=font, fill="black")
            draw.rectangle([0, 0, barcode_width_px - 1, barcode_height_px - 1], outline="black", width=2)

            safe_code = code.replace("\\", "_")
            img_path = os.path.join(tmpdir, f"{safe_code}.png")
            canvas.save(img_path)

            if i % (col_count * row_count) == 0:
                pdf.add_page()
                x = x_start
                y = y_start
                col = 0
                row = 0

            pdf.image(img_path, x=x, y=y, w=barcode_width_mm, h=barcode_height_mm)

            col += 1
            if col >= col_count:
                col = 0
                row += 1
                x = x_start
                y += barcode_height_mm + spacing_mm
            else:
                x += barcode_width_mm + spacing_mm

        # Finalize PDF in memory
        pdf_output = BytesIO()
        pdf_bytes = pdf.output(dest="S").encode("latin1")
        pdf_output.write(pdf_bytes)
        pdf_output.seek(0)
        return pdf_output
