from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from urllib.parse import quote
import os
import re
import asyncio

import google.generativeai as genai
from openai import AsyncOpenAI

from data import MESSAGES, SUBJECTS, TEXTBOOKS
from keyboards import *
from states import MenuState
from config import (
    BOT_TOKEN,
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    BING_SEARCH_KEY
)

import searcher


# ============================================================
# НАСТРОЙКА GEMINI
# ============================================================

if GEMINI_API_KEY and GEMINI_API_KEY != "placeholder":
    genai.configure(api_key=GEMINI_API_KEY)


# ============================================================
# OPENROUTER
# ============================================================

if (
    OPENROUTER_API_KEY
    and OPENROUTER_API_KEY != "placeholder"
):

    openrouter_client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )

else:

    openrouter_client = None


# ============================================================
# ROUTER
# ============================================================

router = Router()


# ============================================================
# START
# ============================================================

@router.message(Command("start"))
async def cmd_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        MESSAGES["ru"]["welcome"],
        reply_markup=lang_keyboard()
    )


# ============================================================
# ЯЗЫК
# ============================================================

@router.callback_query(
    F.data.startswith("lang:")
)
async def set_lang(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    lang = call.data.split(":")[1]

    if lang not in ("ru", "kz"):
        lang = "ru"

    await state.update_data(
        lang=lang
    )

    await call.message.edit_text(
        MESSAGES[lang]["class_choice"],
        reply_markup=class_keyboard(lang)
    )


# ============================================================
# СМЕНА ЯЗЫКА
# ============================================================

@router.callback_query(
    F.data == "menu:lang"
)
async def change_lang(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    await state.clear()

    await call.message.edit_text(
        MESSAGES["ru"]["welcome"],
        reply_markup=lang_keyboard()
    )


# ============================================================
# ВЫБОР КЛАССА
# ============================================================

@router.callback_query(
    F.data.startswith("class:")
)
async def set_class(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    class_num = call.data.split(":")[1]

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )


    if class_num == "other":

        await state.set_state(
            MenuState.other
        )

        await call.message.edit_text(
            MESSAGES[lang]["other_menu"],
            reply_markup=other_keyboard(lang)
        )

        return


    await state.update_data(
        class_num=class_num
    )


    subjects = (
        SUBJECTS
        .get(class_num, {})
        .get(lang, [])
    )


    if not subjects:

        await call.message.edit_text(
            MESSAGES[lang]["no_data"],
            reply_markup=class_keyboard(lang)
        )

        return


    await state.set_state(
        MenuState.subject
    )


    await call.message.edit_text(
        MESSAGES[lang]["subject_choice"].format(
            class_num=class_num
        ),
        reply_markup=subjects_keyboard(
            class_num,
            lang
        )
    )


# ============================================================
# OTHER BACK
# ============================================================

@router.callback_query(
    F.data == "other:back"
)
async def other_back(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    await state.set_state(
        MenuState.class_choice
    )

    await call.message.edit_text(
        MESSAGES[lang]["class_choice"],
        reply_markup=class_keyboard(lang)
    )


# ============================================================
# OTHER ACTIONS
# ============================================================

@router.callback_query(
    F.data.startswith("other:")
)
async def other_actions(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    action = call.data.split(":")[1]

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )


    if action == "presentation":

        await state.set_state(
            MenuState.presentation
        )

        await call.message.edit_text(
            MESSAGES[lang]["presentation_prompt"],
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


    elif action == "solve":

        await state.set_state(
            MenuState.solve
        )

        await call.message.edit_text(
            MESSAGES[lang]["solve_prompt"],
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


    elif action == "bzb":

        await state.set_state(
            MenuState.bzb
        )

        await call.message.edit_text(
            MESSAGES[lang]["bzb_prompt"],
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


# ============================================================
# SUBJECT BACK
# ============================================================

@router.callback_query(
    F.data == "subject:back"
)
async def subject_back(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    await state.set_state(
        MenuState.class_choice
    )

    await call.message.edit_text(
        MESSAGES[lang]["class_choice"],
        reply_markup=class_keyboard(lang)
    )


# ============================================================
# SUBJECT
# ============================================================

@router.callback_query(
    F.data.startswith("subject:")
)
async def set_subject(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    subject = call.data.split(
        ":",
        1
    )[1]


    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    class_num = data.get(
        "class_num"
    )


    await state.update_data(
        subject=subject
    )


    textbooks = (
        TEXTBOOKS
        .get(class_num, {})
        .get(subject, [])
    )


    if not textbooks:

        await call.message.edit_text(
            "Пока нет учебников",
            reply_markup=subjects_keyboard(
                class_num,
                lang
            )
        )

        return


    await state.set_state(
        MenuState.textbook
    )


    await call.message.edit_text(
        MESSAGES[lang]["textbook_choice"].format(
            subject=subject
        ),
        reply_markup=textbooks_keyboard(
            class_num,
            subject,
            lang
        )
    )


# ============================================================
# TEXTBOOK BACK
# ============================================================

@router.callback_query(
    F.data == "textbook:back"
)
async def textbook_back(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    class_num = data.get(
        "class_num"
    )


    await state.set_state(
        MenuState.subject
    )


    await call.message.edit_text(
        MESSAGES[lang]["subject_choice"].format(
            class_num=class_num
        ),
        reply_markup=subjects_keyboard(
            class_num,
            lang
        )
    )


# ============================================================
# TEXTBOOK
# ============================================================

@router.callback_query(
    F.data.startswith("textbook:")
)
async def set_textbook(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    textbook = call.data.split(
        ":",
        1
    )[1]


    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    class_num = data.get(
        "class_num"
    )

    subject = data.get(
        "subject"
    )


    await state.update_data(
        textbook=textbook
    )


    await state.set_state(
        MenuState.menu
    )


    await call.message.edit_text(
        MESSAGES[lang]["menu"].format(
            subject=subject,
            class_num=class_num,
            textbook=textbook
        ),
        reply_markup=menu_keyboard(lang)
    )


# ============================================================
# ACTION BACK
# ============================================================

@router.callback_query(
    F.data == "action:back"
)
async def menu_back(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    class_num = data.get(
        "class_num"
    )

    subject = data.get(
        "subject"
    )


    await state.set_state(
        MenuState.textbook
    )


    await call.message.edit_text(
        MESSAGES[lang]["textbook_choice"].format(
            subject=subject
        ),
        reply_markup=textbooks_keyboard(
            class_num,
            subject,
            lang
        )
    )


# ============================================================
# ACTIONS
# ============================================================

@router.callback_query(
    F.data.startswith("action:")
)
async def menu_actions(
    call: CallbackQuery,
    state: FSMContext
):

    await call.answer()

    action = call.data.split(":")[1]

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )


    if action == "gdz":

        await state.set_state(
            MenuState.gdz
        )

        await call.message.edit_text(
            MESSAGES[lang]["gdz_prompt"],
            reply_markup=back_only_keyboard(
                lang,
                "action:back"
            )
        )


    elif action == "konspekt":

        await state.set_state(
            MenuState.konspekt
        )

        await call.message.edit_text(
            MESSAGES[lang]["konspekt_prompt"],
            reply_markup=back_only_keyboard(
                lang,
                "action:back"
            )
        )


# ============================================================
# ГДЗ
# ============================================================

@router.message(
    MenuState.gdz
)
async def process_gdz(
    message: Message,
    state: FSMContext
):

    if not message.text:
        return


    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    class_num = data.get(
        "class_num"
    )

    subject = data.get(
        "subject"
    )

    textbook = data.get(
        "textbook",
        ""
    )

    query = message.text.strip()


    clean_textbook = textbook.replace(
        "📗 ",
        ""
    )


    search_query = (
        f"{subject} "
        f"{class_num} класс "
        f"{clean_textbook} "
        f"{query} гдз"
    )


    url = (
        "https://www.google.com/search?q="
        + quote(search_query)
    )


    await message.answer(
        MESSAGES[lang]["gdz_result"].format(
            class_num=class_num,
            subject=subject,
            textbook=textbook,
            query=query,
            url=url
        ),
        parse_mode="Markdown",
        reply_markup=back_only_keyboard(
            lang,
            "action:back"
        )
    )


# ============================================================
# КОНСПЕКТ
# ============================================================

@router.message(
    MenuState.konspekt
)
async def process_konspekt(
    message: Message,
    state: FSMContext
):

    if not message.text:
        return


    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    class_num = data.get(
        "class_num"
    )

    subject = data.get(
        "subject"
    )

    query = message.text.strip()


    clean_subject = (
        subject.split(" ", 1)[1]
        if subject and " " in subject
        else subject
    )


    search_query = (
        f"{clean_subject} "
        f"{class_num} класс "
        f"{query} конспект"
    )


    url = (
        "https://www.google.com/search?q="
        + quote(search_query)
    )


    await message.answer(
        MESSAGES[lang]["konspekt_result"].format(
            class_num=class_num,
            subject=subject,
            query=query,
            url=url
        ),
        parse_mode="Markdown",
        reply_markup=back_only_keyboard(
            lang,
            "action:back"
        )
    )


# ============================================================
# ПРЕЗЕНТАЦИЯ
# ============================================================

@router.message(
    MenuState.presentation
)
async def process_presentation(
    message: Message,
    state: FSMContext
):

    if not message.text:
        return


    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    topic = message.text.strip()


    if not openrouter_client:

        await message.answer(
            "❌ OPENROUTER_API_KEY не настроен.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return


    if not topic:

        await message.answer(
            "❌ Напиши тему презентации."
        )

        return


    # ========================================================
    # PROMPT
    # ========================================================

    if lang == "kz":

        prompt = f"""
Келесі тақырып бойынша мектепке арналған
сапалы презентация жаса:

{topic}

8-10 слайд болсын.

Әр слайд мына форматта:

### Слайд тақырыбы
- Бірінші толық түсіндірме сөйлем.
- Екінші толық түсіндірме сөйлем.
- Үшінші толық түсіндірме сөйлем.
- Төртінші толық түсіндірме сөйлем.
- Бесінші толық түсіндірме сөйлем.

Әр пункт 1-2 толық сөйлемнен тұрсын.

Тек презентация құрылымын бер.
Кіріспе немесе артық түсініктеме қоспа.
"""

    else:

        prompt = f"""
Сделай качественную школьную презентацию
на тему:

{topic}

Нужно 8-10 слайдов.

Каждый слайд строго в формате:

### Заголовок слайда
- Полное объяснение первого пункта в 1-2 предложениях.
- Полное объяснение второго пункта в 1-2 предложениях.
- Полное объяснение третьего пункта в 1-2 предложениях.
- Полное объяснение четвертого пункта в 1-2 предложениях.
- Полное объяснение пятого пункта в 1-2 предложениях.

Пункты должны быть информативными,
а не состоять из 2-3 слов.

Только структура презентации.
Без лишнего вступления и заключения.
"""


    await message.answer(
        "⏳ Создаю презентацию с изображениями..."
    )


    try:

        response = await openrouter_client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            extra_headers={
                "HTTP-Referer":
                    "https://t.me/bilim_bot",

                "X-Title":
                    "BilimBot"
            }
        )


        content = (
            response
            .choices[0]
            .message
            .content
        )


        if not content:

            raise Exception(
                "ИИ не вернул текст презентации."
            )


        # ====================================================
        # СОЗДАЁМ PPTX
        # ====================================================

        from presentation_generator import (
            create_presentation
        )


        file_path = await asyncio.to_thread(
            create_presentation,
            topic,
            content,
            lang
        )


        if not os.path.exists(
            file_path
        ):

            raise Exception(
                "Файл презентации не создан."
            )


        filename = (
            re.sub(
                r'[\\/*?:"<>|]',
                "",
                topic
            )[:40]
            + ".pptx"
        )


        document = FSInputFile(
            file_path,
            filename=filename
        )


        await message.answer_document(
            document=document,
            caption=(
                f"📊 Презентация: {topic}\n\n"
                "Сгенерировано BilimBot"
            ),
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


        # ====================================================
        # УДАЛЯЕМ ВРЕМЕННЫЕ ФАЙЛЫ
        # ====================================================

        try:

            if os.path.exists(
                file_path
            ):

                os.remove(
                    file_path
                )

        except Exception:
            pass


        try:

            for filename in os.listdir(
                "/tmp"
            ):

                if (
                    filename.startswith(
                        "bilim_slide_"
                    )
                    or filename.startswith(
                        "slide_"
                    )
                    or filename == "title_bg.jpg"
                ):

                    path = os.path.join(
                        "/tmp",
                        filename
                    )

                    try:
                        os.remove(path)
                    except Exception:
                        pass

        except Exception:
            pass


    except Exception as error:

        print(
            "Presentation error:",
            repr(error)
        )


        await message.answer(
            "❌ Ошибка при создании презентации:\n\n"
            + str(error)[:1500],
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


# ============================================================
# GEMINI MODEL
# ============================================================

def get_gemini_model():

    if (
        not GEMINI_API_KEY
        or GEMINI_API_KEY == "placeholder"
    ):
        return None


    # Используем актуальную модель,
    # доступную через google-generativeai.
    #
    # Если Google изменит название модели,
    # можно поменять только эту строку.

    return genai.GenerativeModel(
        "gemini-2.5-flash"
    )


# ============================================================
# ПОЛУЧЕНИЕ ФОТО ИЗ TELEGRAM
# ============================================================

async def download_telegram_photo(
    message: Message
):

    if not message.photo:
        return None


    photo = message.photo[-1]


    bot = message.bot


    file = await bot.get_file(
        photo.file_id
    )


    path = (
        f"/tmp/"
        f"bilim_input_"
        f"{message.from_user.id}_"
        f"{message.message_id}.jpg"
    )


    await bot.download_file(
        file.file_path,
        destination=path
    )


    return path


# ============================================================
# РЕШЕНИЕ ЗАДАЧИ ПО ФОТО
# ============================================================

@router.message(
    MenuState.solve,
    F.photo
)
async def process_solve_photo(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )


    if (
        not GEMINI_API_KEY
        or GEMINI_API_KEY == "placeholder"
    ):

        await message.answer(
            "❌ GEMINI_API_KEY не настроен "
            "в Railway Variables.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return


    await message.answer(
        "🔎 Читаю фотографию и решаю задачу..."
    )


    image_path = None


    try:

        image_path = await download_telegram_photo(
            message
        )


        if not image_path:

            raise Exception(
                "Не удалось скачать фотографию."
            )


        model = get_gemini_model()


        if model is None:

            raise Exception(
                "Gemini API ключ не настроен."
            )


        # ====================================================
        # GEMINI ЧИТАЕТ И РЕШАЕТ ЗАДАЧУ
        # ====================================================

        upload_file = await asyncio.to_thread(
            genai.upload_file,
            path=image_path
        )


        if lang == "kz":

            prompt = """
Суреттегі тапсырманы мұқият оқы.

Тапсырманың нақты шартын анықта.
Содан кейін шешу жолын кезең-кезеңімен көрсет.

Формулаларды және есептеулерді түсіндір.

Соңында нақты жауап бер.

Егер суретте бірнеше тапсырма болса,
олардың барлығын ретімен шеш.

Жауап қазақ тілінде болсын.
"""

        else:

            prompt = """
Внимательно прочитай задачу на фотографии.

Сначала определи точное условие задачи.
Затем реши её пошагово.

Покажи необходимые формулы,
вычисления и объяснения.

В конце обязательно укажи
чёткий ответ.

Если на фотографии несколько заданий,
реши их все по порядку.

Ответ на русском языке.
"""


        result = await asyncio.to_thread(
            model.generate_content,
            [
                upload_file,
                prompt
            ]
        )


        answer = getattr(
            result,
            "text",
            None
        )


        if not answer:

            raise Exception(
                "Gemini не вернул ответ."
            )


        # Telegram ограничивает размер одного сообщения
        max_length = 4000


        for i in range(
            0,
            len(answer),
            max_length
        ):

            await message.answer(
                answer[i:i + max_length]
            )


        await message.answer(
            "✅ Готово.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


    except Exception as error:

        print(
            "Solve photo error:",
            repr(error)
        )


        await message.answer(
            "❌ Ошибка при обработке фотографии:\n\n"
            + str(error)[:1500],
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


    finally:

        if (
            image_path
            and os.path.exists(
                image_path
            )
        ):

            try:
                os.remove(
                    image_path
                )
            except Exception:
                pass


# ============================================================
# БЖБ ПО ФОТО
# ============================================================

@router.message(
    MenuState.bzb,
    F.photo
)
async def process_bzb_photo(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    class_num = data.get(
        "class_num",
        ""
    )

    subject = data.get(
        "subject",
        ""
    )


    if (
        not GEMINI_API_KEY
        or GEMINI_API_KEY == "placeholder"
    ):

        await message.answer(
            "❌ GEMINI_API_KEY не настроен "
            "в Railway Variables.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return


    await message.answer(
        "📚 Анализирую БЖБ..."
    )


    image_path = None


    try:

        image_path = await download_telegram_photo(
            message
        )


        if not image_path:

            raise Exception(
                "Не удалось скачать фотографию."
            )


        model = get_gemini_model()


        if model is None:

            raise Exception(
                "Gemini API ключ не настроен."
            )


        upload_file = await asyncio.to_thread(
            genai.upload_file,
            path=image_path
        )


        if lang == "kz":

            prompt = f"""
Суретте БЖБ тапсырмасы берілген.

Сынып: {class_num}
Пән: {subject}

Тапсырмалардың барлығын мұқият оқы.

Әр тапсырманы ретімен түсіндір.
Қажет болса шешу жолын көрсет.
Жауаптарды анық және түсінікті жаз.

Қазақ тілінде жауап бер.
"""

        else:

            prompt = f"""
На фотографии находится БЖБ.

Класс: {class_num}
Предмет: {subject}

Внимательно прочитай все задания.

Разбери задания по порядку.
Для каждого задания покажи решение
или объяснение, если оно требуется.

Ответы должны быть понятными
и соответствовать школьному уровню.

Пиши на русском языке.
"""


        result = await asyncio.to_thread(
            model.generate_content,
            [
                upload_file,
                prompt
            ]
        )


        answer = getattr(
            result,
            "text",
            None
        )


        if not answer:

            raise Exception(
                "Gemini не вернул ответ."
            )


        max_length = 4000


        for i in range(
            0,
            len(answer),
            max_length
        ):

            await message.answer(
                answer[i:i + max_length]
            )


        await message.answer(
            "✅ БЖБ обработано.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


    except Exception as error:

        print(
            "BZB photo error:",
            repr(error)
        )


        await message.answer(
            "❌ Ошибка при обработке БЖБ:\n\n"
            + str(error)[:1500],
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


    finally:

        if (
            image_path
            and os.path.exists(
                image_path
            )
        ):

            try:
                os.remove(
                    image_path
                )
            except Exception:
                pass


# ============================================================
# ЕСЛИ В SOLVE ПРИШЛИ ТЕКСТОМ
# ============================================================

@router.message(
    MenuState.solve,
    F.text
)
async def process_solve_text(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )


    if (
        not GEMINI_API_KEY
        or GEMINI_API_KEY == "placeholder"
    ):

        await message.answer(
            "❌ GEMINI_API_KEY не настроен.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return


    await message.answer(
        "🧠 Решаю задачу..."
    )


    try:

        model = get_gemini_model()


        if lang == "kz":

            prompt = f"""
Төмендегі тапсырманы толық шеш:

{message.text}

Шешу жолын кезең-кезеңімен түсіндір.
Соңында нақты жауап бер.
"""

        else:

            prompt = f"""
Реши следующую школьную задачу:

{message.text}

Покажи решение пошагово,
объясни формулы и вычисления,
а в конце дай точный ответ.
"""


        result = await asyncio.to_thread(
            model.generate_content,
            prompt
        )


        answer = getattr(
            result,
            "text",
            None
        )


        if not answer:

            raise Exception(
                "Gemini не вернул ответ."
            )


        for i in range(
            0,
            len(answer),
            4000
        ):

            await message.answer(
                answer[i:i + 4000]
            )


        await message.answer(
            "✅ Готово.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


    except Exception as error:

        await message.answer(
            "❌ Ошибка:\n\n"
            + str(error)[:1500],
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


# ============================================================
# БЖБ — ЕСЛИ ПРИШЁЛ ТЕКСТ
# ============================================================

@router.message(
    MenuState.bzb,
    F.text
)
async def process_bzb_text(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    lang = data.get(
        "lang",
        "ru"
    )

    class_num = data.get(
        "class_num",
        ""
    )

    subject = data.get(
        "subject",
        ""
    )


    if (
        not GEMINI_API_KEY
        or GEMINI_API_KEY == "placeholder"
    ):

        await message.answer(
            "❌ GEMINI_API_KEY не настроен.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return


    await message.answer(
        "🧠 Решаю БЖБ..."
    )


    try:

        model = get_gemini_model()


        prompt = f"""
Помоги решить школьное БЖБ.

Класс: {class_num}
Предмет: {subject}

Задания:

{message.text}

Реши задания по порядку.
Покажи объяснения и ответы.
"""


        result = await asyncio.to_thread(
            model.generate_content,
            prompt
        )


        answer = getattr(
            result,
            "text",
            None
        )


        if not answer:

            raise Exception(
                "Gemini не вернул ответ."
            )


        for i in range(
            0,
            len(answer),
            4000
        ):

            await message.answer(
                answer[i:i + 4000]
            )


        await message.answer(
            "✅ Готово.",
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


    except Exception as error:

        await message.answer(
            "❌ Ошибка:\n\n"
            + str(error)[:1500],
            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )
