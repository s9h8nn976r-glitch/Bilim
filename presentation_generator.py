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

    total = len(slides_data[:10])

    # ===== ТИТУЛЬНИК =====
    slide = prs.slides.add_slide(blank_layout)

    # Фоновая картинка через Pollinations
    try:
        bg_prompt = f"{topic} presentation dark blue background abstract minimal"
        bg_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(bg_prompt)}?width=1280&height=720&nologo=true&seed=999"
        r = requests.get(bg_url, timeout=25)
        if r.status_code == 200 and len(r.content) > 5000:
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

    # Тёмная подложка поверх картинки для читаемости
    overlay = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
    )
    overlay.fill.solid()
    overlay.fill.fore_color.rgb = RGBColor(25, 55, 140)
    overlay.fill.fore_color.brightness = 0.2
    overlay.line.fill.background()
    spTree = slide.shapes._spTree
    sp = overlay._element
    spTree.remove(sp)
    spTree.insert(2, sp)

    # Жёлтая полоса
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(6.8), prs.slide_width, Inches(0.7)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = RGBColor(255, 190, 40)
    accent.line.fill.background()

    # Заголовок
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(2.4), Inches(12.3), Inches(1.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = topic
    p.font.size = Pt(52)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Подзаголовок
    sub = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(12.3), Inches(0.8))
    tf = sub.text_frame
    p = tf.paragraphs[0]
    p.text = "BilimBot — Школьный помощник"
    p.font.size = Pt(22)
    p.font.color.rgb = RGBColor(200, 220, 255)
    p.alignment = PP_ALIGN.CENTER

    # ===== КОНТЕНТНЫЕ СЛАЙДЫ =====
    for idx, sdata in enumerate(slides_data[:10]):
        slide = prs.slides.add_slide(blank_layout)

        # Белый фон
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
            Inches(0.4), Inches(1.25), Inches(8.5), Inches(5.9)
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

        # КАРТИНКА справа — Pollinations.ai (бесплатно, без ключа)
        img_loaded = False
        try:
            img_prompt = f"{topic} {sdata['title']}, illustration, clean, educational"
            img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_prompt)}?width=512&height=512&nologo=true&seed={idx}"
            r = requests.get(img_url, timeout=25)
            if r.status_code == 200 and len(r.content) > 5000:
                path = f"/tmp/slide_{idx}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                # Рамка
                frame = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(9.1), Inches(1.3), Inches(3.8), Inches(4.9)
                )
                frame.fill.solid()
                frame.fill.fore_color.rgb = RGBColor(230, 235, 245)
                frame.line.color.rgb = RGBColor(200, 210, 230)
                # Картинка внутри
                pic = slide.shapes.add_picture(
                    path, Inches(9.2), Inches(1.4), width=Inches(3.6)
                )
                img_loaded = True
        except Exception:
            pass

        # Если картинка не загрузилась — цветной декор
        if not img_loaded:
            decor = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(9.5), Inches(2.2), Inches(3.0), Inches(3.0)
            )
            decor.fill.solid()
            decor.fill.fore_color.rgb = RGBColor(230, 235, 245)
            decor.line.color.rgb = RGBColor(200, 210, 230)
            dt = decor.text_frame
            dt.word_wrap = True
            dp = dt.paragraphs[0]
            dp.text = "🖼️"
            dp.font.size = Pt(48)
            dp.alignment = PP_ALIGN.CENTER

        # Номер слайда
        num = slide.shapes.add_textbox(
            Inches(11.5), Inches(7.0), Inches(1.5), Inches(0.4)
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
