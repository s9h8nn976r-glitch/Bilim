from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from urllib.parse import quote

from google import genai
from google.genai import types

from openai import AsyncOpenAI
import os

from data import MESSAGES, SUBJECTS, TEXTBOOKS
from keyboards import *
from states import MenuState
from config import (
    BOT_TOKEN,
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    BING_SEARCH_KEY,
)
import searcher


# ============================================================
# GEMINI
# ============================================================

gemini_client = None

if GEMINI_API_KEY and GEMINI_API_KEY != "placeholder":
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# OPENROUTER
# ============================================================

openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=(
        OPENROUTER_API_KEY
        if OPENROUTER_API_KEY
        and OPENROUTER_API_KEY != "placeholder"
        else "sk-fake"
    ),
)


router = Router()


# ============================================================
# START
# ============================================================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        MESSAGES["ru"]["welcome"],
        reply_markup=lang_keyboard()
    )


# ============================================================
# LANGUAGE
# ============================================================

@router.callback_query(F.data.startswith("lang:"))
async def set_lang(
    call: CallbackQuery,
    state: FSMContext
):
    await call.answer()

    lang = call.data.split(":")[1]

    await state.update_data(
        lang=lang
    )

    await call.message.edit_text(
        MESSAGES[lang]["class_choice"],
        reply_markup=class_keyboard(lang)
    )


@router.callback_query(F.data == "menu:lang")
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
# CLASS
# ============================================================

@router.callback_query(F.data.startswith("class:"))
async def set_class(
    call: CallbackQuery,
    state: FSMContext
):
    await call.answer()

    class_num = call.data.split(":")[1]

    data = await state.get_data()
    lang = data.get("lang", "ru")

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

    subjects = SUBJECTS.get(
        class_num,
        {}
    ).get(
        lang,
        []
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
# OTHER MENU
# ============================================================

@router.callback_query(F.data == "other:back")
async def other_back(
    call: CallbackQuery,
    state: FSMContext
):
    await call.answer()

    data = await state.get_data()
    lang = data.get("lang", "ru")

    await state.set_state(
        MenuState.class_choice
    )

    await call.message.edit_text(
        MESSAGES[lang]["class_choice"],
        reply_markup=class_keyboard(lang)
    )


@router.callback_query(F.data.startswith("other:"))
async def other_actions(
    call: CallbackQuery,
    state: FSMContext
):
    await call.answer()

    action = call.data.split(":")[1]

    data = await state.get_data()
    lang = data.get("lang", "ru")

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
# SUBJECT
# ============================================================

@router.callback_query(F.data == "subject:back")
async def subject_back(
    call: CallbackQuery,
    state: FSMContext
):
    await call.answer()

    data = await state.get_data()
    lang = data.get("lang", "ru")

    await state.set_state(
        MenuState.class_choice
    )

    await call.message.edit_text(
        MESSAGES[lang]["class_choice"],
        reply_markup=class_keyboard(lang)
    )


@router.callback_query(F.data.startswith("subject:"))
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

    lang = data.get("lang", "ru")
    class_num = data.get("class_num")

    await state.update_data(
        subject=subject
    )

    textbooks = TEXTBOOKS.get(
        class_num,
        {}
    ).get(
        subject,
        []
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
# TEXTBOOK
# ============================================================

@router.callback_query(F.data == "textbook:back")
async def textbook_back(
    call: CallbackQuery,
    state: FSMContext
):
    await call.answer()

    data = await state.get_data()

    lang = data.get("lang", "ru")
    class_num = data.get("class_num")

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


@router.callback_query(F.data.startswith("textbook:"))
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

    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    subject = data.get("subject")

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
# MENU
# ============================================================

@router.callback_query(F.data == "action:back")
async def menu_back(
    call: CallbackQuery,
    state: FSMContext
):
    await call.answer()

    data = await state.get_data()

    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    subject = data.get("subject")

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


@router.callback_query(F.data.startswith("action:"))
async def menu_actions(
    call: CallbackQuery,
    state: FSMContext
):
    await call.answer()

    action = call.data.split(":")[1]

    data = await state.get_data()
    lang = data.get("lang", "ru")

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
# GDZ
# ============================================================

@router.message(MenuState.gdz)
async def process_gdz(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    subject = data.get("subject")
    textbook = data.get("textbook")

    query = message.text

    if not query:
        await message.answer(
            "❌ Напиши номер или условие задания."
        )
        return

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
# KONSPEKT
# ============================================================

@router.message(MenuState.konspekt)
async def process_konspekt(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    subject = data.get("subject")

    query = message.text

    if not query:
        await message.answer(
            "❌ Напиши тему."
        )
        return

    clean_subject = (
        subject.split(" ", 1)[1]
        if " " in subject
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
# PRESENTATION
# ============================================================

@router.message(MenuState.presentation)
async def process_presentation(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    lang = data.get("lang", "ru")
    topic = message.text

    if not topic:
        await message.answer(
            "❌ Напиши тему презентации."
        )
        return

    prompt = (
        f"Сделай подробный план презентации "
        f"(8-10 слайдов) на тему: {topic}. "
        f"Каждый слайд: заголовок через ###, "
        f"5-7 пунктов. "
        f"Каждый пункт — 1-2 полных предложения "
        f"с развёрнутым объяснением. "
        f"Используй markdown: "
        f"заголовки через ###, пункты через -. "
        f"Без вступления и заключения."
    )

    if lang == "kz":
        prompt = (
            f"Келесі тақырыпқа толық презентация "
            f"жоспарын (8-10 слайд) жаса: {topic}. "
            f"Әр слайд: ### тақырып, 5-7 пункт. "
            f"Әр пункт — 1-2 толық сөйлем. "
            f"Markdown қолдан: ### тақырыптар, - пункттер. "
            f"Тек презентация құрылымы."
        )

    await message.answer(
        "⏳ Генерирую презентацию..."
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
                "HTTP-Referer": "https://t.me/bilim_bot",
                "X-Title": "BilimBot"
            }
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "OpenRouter не вернул текст."
            )

        from presentation_generator import create_presentation

        file_path = create_presentation(
            topic,
            content,
            lang
        )

        document = FSInputFile(
            file_path,
            filename=f"{topic[:40]}.pptx"
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

        try:
            os.remove(file_path)
        except Exception:
            pass

    except Exception as e:

        await message.answer(
            "❌ Ошибка при создании презентации:\n\n"
            + str(e),

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


# ============================================================
# GEMINI — PHOTO SOLVER
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

    if gemini_client is None:

        await message.answer(
            "❌ Gemini API ключ не настроен.\n\n"
            "Добавь GEMINI_API_KEY в Railway Variables.",

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return

    try:

        await message.answer(
            "⏳ Анализирую фотографию..."
        )

        photo = message.photo[-1]

        file_obj = await message.bot.get_file(
            photo.file_id
        )

        image_file = await message.bot.download_file(
            file_obj.file_path
        )

        image_data = image_file.read()

        if lang == "kz":

            prompt = (
                "Суреттегі мектеп тапсырмасын шеш. "
                "Мәтінді мұқият оқы. "
                "Шешу жолын қадам-қадамымен көрсет. "
                "Формулалар мен есептеулерді түсіндір. "
                "Соңында нақты жауапты көрсет. "
                "Қазақ тілінде жауап бер."
            )

        else:

            prompt = (
                "На фотографии находится школьная задача. "
                "Внимательно прочитай её. "
                "Реши задачу полностью. "
                "Покажи решение пошагово. "
                "Объясни формулы и вычисления. "
                "В конце обязательно напиши итоговый ответ."
            )

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",

            contents=[
                prompt,

                types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/jpeg"
                )
            ]
        )

        answer = response.text

        if not answer:
            answer = (
                "❌ Не удалось получить решение."
            )

        await message.answer(
            "📚 *Решение:*\n\n" + answer,

            parse_mode="Markdown",

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

    except Exception as e:

        await message.answer(
            "❌ Ошибка при обработке фотографии:\n\n"
            + str(e),

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


# ============================================================
# GEMINI — TEXT SOLVER
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

    if gemini_client is None:

        await message.answer(
            "❌ Gemini API ключ не настроен.\n\n"
            "Добавь GEMINI_API_KEY в Railway Variables.",

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return

    query = message.text

    if not query:
        return

    if lang == "kz":

        prompt = (
            "Мектеп тапсырмасын толық шеш.\n\n"
            f"Тапсырма:\n{query}\n\n"
            "Шешу жолын қадам-қадамымен түсіндір. "
            "Формулаларды көрсет. "
            "Соңында нақты жауапты жаз. "
            "Қазақ тілінде жауап бер."
        )

    else:

        prompt = (
            "Реши школьную задачу полностью.\n\n"
            f"Задача:\n{query}\n\n"
            "Покажи решение пошагово. "
            "Объясни формулы и вычисления. "
            "В конце обязательно укажи итоговый ответ."
        )

    try:

        await message.answer(
            "⏳ Решаю задачу..."
        )

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        answer = response.text

        if not answer:
            answer = "❌ Gemini не вернул решение."

        await message.answer(
            "📚 *Решение:*\n\n" + answer,

            parse_mode="Markdown",

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

    except Exception as e:

        await message.answer(
            "❌ Ошибка Gemini:\n\n"
            + str(e),

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


# ============================================================
# BZB — PHOTO
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

    if gemini_client is None:

        await message.answer(
            "❌ Gemini API ключ не настроен.\n\n"
            "Добавь GEMINI_API_KEY в Railway Variables.",

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return

    try:

        await message.answer(
            "⏳ Анализирую БЖБ..."
        )

        photo = message.photo[-1]

        file_obj = await message.bot.get_file(
            photo.file_id
        )

        image_file = await message.bot.download_file(
            file_obj.file_path
        )

        image_data = image_file.read()

        if lang == "kz":

            prompt = (
                "Бұл суретте мектептің БЖБ тапсырмасы бар. "
                "Барлық тапсырмаларды мұқият оқы. "
                "Әр тапсырманы нөмірімен көрсетіп, "
                "толық әрі дұрыс жауап бер. "
                "Қажет болса шешу жолын көрсет. "
                "Жауапты қазақ тілінде бер."
            )

        else:

            prompt = (
                "На фотографии находится БЖБ "
                "(школьная проверочная работа). "
                "Внимательно прочитай ВСЕ задания. "
                "Ответь на каждое задание по порядку. "
                "Пиши номер задания и полный ответ. "
                "Для задач покажи решение. "
                "Не пропускай задания."
            )

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",

            contents=[
                prompt,

                types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/jpeg"
                )
            ]
        )

        answer = response.text

        if not answer:
            answer = (
                "❌ Не удалось распознать БЖБ."
            )

        await message.answer(
            "📝 *Ответы на БЖБ:*\n\n" + answer,

            parse_mode="Markdown",

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

    except Exception as e:

        await message.answer(
            "❌ Ошибка при обработке БЖБ:\n\n"
            + str(e),

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )


# ============================================================
# BZB — TEXT
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

    if gemini_client is None:

        await message.answer(
            "❌ Gemini API ключ не настроен.",

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

        return

    query = message.text

    if lang == "kz":

        prompt = (
            "Төмендегі БЖБ тапсырмаларына жауап бер. "
            "Әр тапсырманы нөмірімен көрсет. "
            "Қажет болса шешу жолын түсіндір. "
            "Қазақ тілінде жауап бер.\n\n"
            f"{query}"
        )

    else:

        prompt = (
            "Реши следующие задания БЖБ. "
            "Ответь на каждое задание по порядку. "
            "Показывай решение там, где оно необходимо.\n\n"
            f"{query}"
        )

    try:

        await message.answer(
            "⏳ Решаю БЖБ..."
        )

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        answer = response.text

        if not answer:
            answer = "❌ Gemini не вернул ответы."

        await message.answer(
            "📝 *Ответы на БЖБ:*\n\n" + answer,

            parse_mode="Markdown",

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )

    except Exception as e:

        await message.answer(
            "❌ Ошибка Gemini:\n\n"
            + str(e),

            reply_markup=back_only_keyboard(
                lang,
                "other:back"
            )
        )
