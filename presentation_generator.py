from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
import requests
import urllib.parse
import os


def create_presentation(topic, content_text, lang="ru"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # ===== ПАРСИНГ =====
    lines = content_text.strip().split("\n")
    slides_data = []
    current = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("##") or line.startswith("###") or line.startswith("####"):
            if current:
                slides_data.append(current)
            current = {"title": line.replace("#", "").strip(), "points": []}
        elif line.startswith("- ") or line.startswith("• ") or line.startswith("* "):
            if current:
                current["points"].append(line[2:].strip())
        elif line and current is None:
            current = {"title": line, "points": []}

    if current:
        slides_data.append(current)

    if not slides_data:
        slides_data = [{"title": topic, "points": [content_text[:500]]}]

    # ===== ТИТУЛЬНИК =====
    slide = prs.slides.add_slide(blank_layout)
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(25, 55, 140)
    bg.line.fill.background()
    spTree = slide.shapes._spTree
    sp = bg._element
    spTree.remove(sp)
    spTree.insert(2, sp)

    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(6.8), prs.slide_width, Inches(0.7)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = RGBColor(255, 190, 40)
    accent.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.5), Inches(2.4), Inches(12.3), Inches(1.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = topic
    p.font.size = Pt(52)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    sub = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(12.3), Inches(0.8))
    tf = sub.text_frame
    p = tf.paragraphs[0]
    p.text = "BilimBot — Школьный помощник"
    p.font.size = Pt(22)
    p.font.color.rgb = RGBColor(180, 200, 255)
    p.alignment = PP_ALIGN.CENTER

    # ===== СЛАЙДЫ С КОНТЕНТОМ =====
    total = len(slides_data[:10])
    for idx, sdata in enumerate(slides_data[:10]):
        slide = prs.slides.add_slide(blank_layout)

        # Фон
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(248, 249, 252)
        bg.line.fill.background()
        spTree = slide.shapes._spTree
        sp = bg._element
        spTree.remove(sp)
        spTree.insert(2, sp)

        # Шапка
        header = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, Inches(1.0)
        )
        header.fill.solid()
        header.fill.fore_color.rgb = RGBColor(35, 75, 170)
        header.line.fill.background()
        ht = header.text_frame
        ht.word_wrap = True
        hp = ht.paragraphs[0]
        hp.text = sdata["title"]
        hp.font.size = Pt(24)
        hp.font.bold = True
        hp.font.color.rgb = RGBColor(255, 255, 255)

        # Жёлтая полоска
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.0), prs.slide_width, Inches(0.06)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(255, 190, 40)
        line.line.fill.background()

        # ТЕКСТ слева (широкий блок)
        content = slide.shapes.add_textbox(
            Inches(0.4), Inches(1.25), Inches(8.6), Inches(5.9)
        )
        tf = content.text_frame
        tf.word_wrap = True
        for point in sdata["points"][:8]:
            p = tf.add_paragraph()
            p.text = f"• {point}"
            p.font.size = Pt(17)
            p.font.color.rgb = RGBColor(35, 35, 35)
            p.space_after = Pt(12)
            p.level = 0

        # КАРТИНКА справа — Unsplash (реальные фото)
        img_loaded = False
        try:
            # Формируем поисковый запрос на английском (просто topic)
            query = urllib.parse.quote(topic.replace(" ", ","))
            img_url = f"https://source.unsplash.com/600x500/?{query}"
            r = requests.get(img_url, timeout=20, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 1000:
                path = f"/tmp/slide_{idx}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                # Рамка
                frame = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(9.2), Inches(1.3), Inches(3.7), Inches(4.8)
                )
                frame.fill.solid()
                frame.fill.fore_color.rgb = RGBColor(230, 235, 245)
                frame.line.color.rgb = RGBColor(200, 210, 230)
                # Картинка внутри рамки
                pic = slide.shapes.add_picture(
                    path, Inches(9.3), Inches(1.4), width=Inches(3.5)
                )
                img_loaded = True
        except Exception:
            pass

        # Если картинка не загрузилась — цветной декор с иконкой-текстом
        if not img_loaded:
            decor = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(9.5), Inches(2.0), Inches(3.0), Inches(3.0)
            )
            decor.fill.solid()
            decor.fill.fore_color.rgb = RGBColor(230, 235, 245)
            decor.line.color.rgb = RGBColor(200, 210, 230)
            dt = decor.text_frame
            dt.word_wrap = True
            dp = dt.paragraphs[0]
            dp.text = "📷"
            dp.font.size = Pt(48)
            dp.alignment = PP_ALIGN.CENTER

        # Номер слайда
        num = slide.shapes.add_textbox(
            Inches(11.8), Inches(7.05), Inches(1.2), Inches(0.35)
        )
        nt = num.text_frame
        np = nt.paragraphs[0]
        np.text = f"{idx + 1} / {total}"
        np.font.size = Pt(11)
        np.font.color.rgb = RGBColor(150, 150, 150)
        np.alignment = PP_ALIGN.RIGHT

    # ===== ЗАКЛЮЧЕНИЕ =====
    slide = prs.slides.add_slide(blank_layout)
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(25, 55, 140)
    bg.line.fill.background()
    spTree = slide.shapes._spTree
    sp = bg._element
    spTree.remove(sp)
    spTree.insert(2, sp)

    end = slide.shapes.add_textbox(Inches(0.5), Inches(2.8), Inches(12.3), Inches(1.5))
    tf = end.text_frame
    p = tf.paragraphs[0]
    p.text = "Спасибо за внимание!"
    p.font.size = Pt(46)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    sub = slide.shapes.add_textbox(Inches(0.5), Inches(4.3), Inches(12.3), Inches(0.8))
    tf = sub.text_frame
    p = tf.paragraphs[0]
    p.text = "Сгенерировано BilimBot"
    p.font.size = Pt(20)
    p.font.color.rgb = RGBColor(180, 200, 255)
    p.alignment = PP_ALIGN.CENTER

    # Сохраняем
    safe = topic[:35].replace(" ", "_").replace("/", "").replace("?", "")
    output = f"/tmp/pres_{safe}.pptx"
    prs.save(output)
    return output
