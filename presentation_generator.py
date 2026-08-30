from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
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

    # ===== ТИТУЛЬНЫЙ СЛАЙД =====
    slide = prs.slides.add_slide(blank_layout)

    # Фон — градиентная заливка (синий → фиолетовый)
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = RGBColor(30, 60, 150)
    bg_shape.line.fill.background()
    # Отправляем фон на задний план
    spTree = slide.shapes._spTree
    sp = bg_shape._element
    spTree.remove(sp)
    spTree.insert(2, sp)

    # Декоративная полоса
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(6.8), prs.slide_width, Inches(0.7)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = RGBColor(255, 200, 50)
    accent.line.fill.background()

    # Заголовок
    title_box = slide.shapes.add_textbox(
        Inches(0.8), Inches(2.5), Inches(11.7), Inches(1.5)
    )
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = topic
    p.font.size = Pt(54)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Подзаголовок
    sub_box = slide.shapes.add_textbox(
        Inches(0.8), Inches(4.2), Inches(11.7), Inches(0.8)
    )
    tf = sub_box.text_frame
    p = tf.paragraphs[0]
    p.text = "BilimBot — Школьный помощник"
    p.font.size = Pt(22)
    p.font.color.rgb = RGBColor(200, 210, 255)
    p.alignment = PP_ALIGN.CENTER

    # ===== КОНТЕНТНЫЕ СЛАЙДЫ =====
    for idx, sdata in enumerate(slides_data[:8]):
        slide = prs.slides.add_slide(blank_layout)

        # Белый фон
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(250, 251, 252)
        bg.line.fill.background()
        spTree = slide.shapes._spTree
        sp = bg._element
        spTree.remove(sp)
        spTree.insert(2, sp)

        # Синяя шапка
        header = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, Inches(1.0)
        )
        header.fill.solid()
        header.fill.fore_color.rgb = RGBColor(35, 75, 170)
        header.line.fill.background()

        # Заголовок слайда
        ht = header.text_frame
        ht.word_wrap = True
        hp = ht.paragraphs[0]
        hp.text = sdata["title"]
        hp.font.size = Pt(26)
        hp.font.bold = True
        hp.font.color.rgb = RGBColor(255, 255, 255)

        # Жёлтая полоска под шапкой
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.0), prs.slide_width, Inches(0.08)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(255, 200, 50)
        line.line.fill.background()

        # Текст слева
        content = slide.shapes.add_textbox(
            Inches(0.5), Inches(1.3), Inches(7.8), Inches(5.8)
        )
        tf = content.text_frame
        tf.word_wrap = True
        for point in sdata["points"][:6]:
            p = tf.add_paragraph()
            p.text = f"• {point}"
            p.font.size = Pt(20)
            p.font.color.rgb = RGBColor(40, 40, 40)
            p.space_after = Pt(16)
            p.level = 0

        # Пробуем загрузить картинку справа
        try:
            prompt = f"{topic} {sdata['title']}"
            img_url = (
                f"https://image.pollinations.ai/prompt/"
                f"{urllib.parse.quote(prompt)}?width=512&height=512&nologo=true"
            )
            r = requests.get(img_url, timeout=20)
            if r.status_code == 200:
                path = f"/tmp/slide_{idx}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                # Рамка для картинки
                frame = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(8.6), Inches(1.4), Inches(4.2), Inches(4.2)
                )
                frame.fill.solid()
                frame.fill.fore_color.rgb = RGBColor(230, 235, 245)
                frame.line.color.rgb = RGBColor(200, 210, 230)
                # Картинка
                pic = slide.shapes.add_picture(
                    path, Inches(8.7), Inches(1.5), width=Inches(4.0)
                )
                # Закругляем углы картинки (визуально через рамку поверх)
        except Exception:
            # Если картинка не загрузилась — добавляем иконку/декор
            decor = slide.shapes.add_shape(
                MSO_SHAPE.OVAL, Inches(9.5), Inches(2.5), Inches(2.5), Inches(2.5)
            )
            decor.fill.solid()
            decor.fill.fore_color.rgb = RGBColor(230, 235, 245)
            decor.line.color.rgb = RGBColor(200, 210, 230)

        # Номер слайда внизу
        footer = slide.shapes.add_textbox(
            Inches(11.5), Inches(7.0), Inches(1.5), Inches(0.4)
        )
        ft = footer.text_frame
        fp = ft.paragraphs[0]
        fp.text = f"{idx + 1} / {len(slides_data[:8])}"
        fp.font.size = Pt(12)
        fp.font.color.rgb = RGBColor(150, 150, 150)
        fp.alignment = PP_ALIGN.RIGHT

    # ===== ЗАКЛЮЧИТЕЛЬНЫЙ СЛАЙД =====
    slide = prs.slides.add_slide(blank_layout)
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(30, 60, 150)
    bg.line.fill.background()
    spTree = slide.shapes._spTree
    sp = bg._element
    spTree.remove(sp)
    spTree.insert(2, sp)

    end_box = slide.shapes.add_textbox(
        Inches(0.8), Inches(3.0), Inches(11.7), Inches(1.5)
    )
    tf = end_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Спасибо за внимание!"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    sub = slide.shapes.add_textbox(
        Inches(0.8), Inches(4.5), Inches(11.7), Inches(0.8)
    )
    tf = sub.text_frame
    p = tf.paragraphs[0]
    p.text = "Сгенерировано BilimBot"
    p.font.size = Pt(20)
    p.font.color.rgb = RGBColor(200, 210, 255)
    p.alignment = PP_ALIGN.CENTER

    # Сохраняем
    safe_topic = topic[:40].replace(" ", "_").replace("/", "_").replace("?", "")
    output = f"/tmp/pres_{safe_topic}.pptx"
    prs.save(output)
    return output
