from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import requests
import urllib.parse
import os


def create_presentation(topic, content_text, lang="ru"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # ===== ТИТУЛЬНЫЙ СЛАЙД =====
    slide = prs.slides.add_slide(blank_layout)
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(20, 20, 45)

    # Фоновая картинка
    try:
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(topic)}%20presentation%20dark%20background%20minimal?width=1280&height=720&nologo=true"
        r = requests.get(img_url, timeout=25)
        if r.status_code == 200:
            path = "/tmp/title_bg.jpg"
            with open(path, "wb") as f:
                f.write(r.content)
            pic = slide.shapes.add_picture(path, Inches(0), Inches(0), width=prs.slide_width)
            spTree = slide.shapes._spTree
            sp = pic._element
            spTree.remove(sp)
            spTree.insert(2, sp)
    except Exception:
        pass

    # Заголовок
    box = slide.shapes.add_textbox(Inches(1), Inches(2.8), Inches(11.333), Inches(1.5))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = topic
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Подпись
    sub = slide.shapes.add_textbox(Inches(1), Inches(4.5), Inches(11.333), Inches(1))
    tf = sub.text_frame
    p = tf.paragraphs[0]
    p.text = "BilimBot"
    p.font.size = Pt(22)
    p.font.color.rgb = RGBColor(180, 180, 220)
    p.alignment = PP_ALIGN.CENTER

    # ===== ПАРСИНГ СЛАЙДОВ =====
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
        slides_data = [{"title": topic, "points": [content_text[:300]]}]

    # ===== КОНТЕНТНЫЕ СЛАЙДЫ =====
    for idx, sdata in enumerate(slides_data[:8]):
        slide = prs.slides.add_slide(blank_layout)

        # Фон
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(245, 247, 250)

        # Цветная шапка
        header = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
        header.fill.solid()
        header.fill.fore_color.rgb = RGBColor(35, 75, 170)
        header.line.fill.background()
        ht = header.text_frame
        hp = ht.paragraphs[0]
        hp.text = sdata["title"]
        hp.font.size = Pt(26)
        hp.font.bold = True
        hp.font.color.rgb = RGBColor(255, 255, 255)

        # Текст слева
        content = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(7.5), Inches(5.5))
        tf = content.text_frame
        tf.word_wrap = True
        for point in sdata["points"][:6]:
            p = tf.add_paragraph()
            p.text = f"• {point}"
            p.font.size = Pt(19)
            p.font.color.rgb = RGBColor(30, 30, 30)
            p.space_after = Pt(14)

        # Картинка справа (ИИ)
        try:
            prompt = f"{topic} {sdata['title']}"
            img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=512&height=512&nologo=true"
            r = requests.get(img_url, timeout=25)
            if r.status_code == 200:
                path = f"/tmp/slide_{idx}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                slide.shapes.add_picture(path, Inches(8.4), Inches(1.4), width=Inches(4.3))
        except Exception:
            pass

    # Сохраняем
    safe_topic = topic[:40].replace(" ", "_").replace("/", "_")
    output = f"/tmp/pres_{safe_topic}.pptx"
    prs.save(output)
    return output
