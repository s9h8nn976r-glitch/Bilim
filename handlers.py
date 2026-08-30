from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from urllib.parse import quote
from data import MESSAGES, SUBJECTS, TEXTBOOKS
from keyboards import *
from states import MenuState

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(MESSAGES["ru"]["welcome"], reply_markup=lang_keyboard())

@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery, state: FSMContext):
    await call.answer()
    lang = call.data.split(":")[1]
    await state.update_data(lang=lang)
    await call.message.edit_text(MESSAGES[lang]["class_choice"], reply_markup=class_keyboard(lang))

@router.callback_query(F.data == "menu:lang")
async def change_lang(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.edit_text(MESSAGES["ru"]["welcome"], reply_markup=lang_keyboard())

@router.callback_query(F.data.startswith("class:"))
async def set_class(call: CallbackQuery, state: FSMContext):
    await call.answer()
    class_num = call.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    if class_num == "other":
        await state.set_state(MenuState.other)
        await call.message.edit_text(MESSAGES[lang]["other_menu"], reply_markup=other_keyboard(lang))
        return
    
    await state.update_data(class_num=class_num)
    subjects = SUBJECTS.get(class_num, {}).get(lang, [])
    
    if not subjects:
        await call.message.edit_text(MESSAGES[lang]["no_data"], reply_markup=class_keyboard(lang))
        return
    
    await state.set_state(MenuState.subject)
    await call.message.edit_text(
        MESSAGES[lang]["subject_choice"].format(class_num=class_num),
        reply_markup=subjects_keyboard(class_num, lang)
    )

@router.callback_query(F.data == "other:back")
async def other_back(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.set_state(MenuState.class_choice)
    await call.message.edit_text(MESSAGES[lang]["class_choice"], reply_markup=class_keyboard(lang))

@router.callback_query(F.data.startswith("other:"))
async def other_actions(call: CallbackQuery, state: FSMContext):
    await call.answer()
    action = call.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    if action == "presentation":
        await state.set_state(MenuState.presentation)
        await call.message.edit_text(MESSAGES[lang]["presentation_prompt"], 
                                     reply_markup=back_only_keyboard(lang, "other:back"))
    elif action == "solve":
        await state.set_state(MenuState.solve)
        await call.message.edit_text(MESSAGES[lang]["solve_prompt"], 
                                     reply_markup=back_only_keyboard(lang, "other:back"))
    elif action == "bzb":
        await state.set_state(MenuState.bzb)
        await call.message.edit_text(MESSAGES[lang]["bzb_prompt"], 
                                     reply_markup=back_only_keyboard(lang, "other:back"))

@router.callback_query(F.data == "subject:back")
async def subject_back(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.set_state(MenuState.class_choice)
    await call.message.edit_text(MESSAGES[lang]["class_choice"], reply_markup=class_keyboard(lang))

@router.callback_query(F.data.startswith("subject:"))
async def set_subject(call: CallbackQuery, state: FSMContext):
    await call.answer()
    subject = call.data.split(":", 1)[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    await state.update_data(subject=subject)
    
    textbooks = TEXTBOOKS.get(class_num, {}).get(subject, [])
    if not textbooks:
        await call.message.edit_text("Пока нет учебников", 
                                     reply_markup=subjects_keyboard(class_num, lang))
        return
    
    await state.set_state(MenuState.textbook)
    await call.message.edit_text(
        MESSAGES[lang]["textbook_choice"].format(subject=subject),
        reply_markup=textbooks_keyboard(class_num, subject, lang)
    )

@router.callback_query(F.data == "textbook:back")
async def textbook_back(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    await state.set_state(MenuState.subject)
    await call.message.edit_text(
        MESSAGES[lang]["subject_choice"].format(class_num=class_num),
        reply_markup=subjects_keyboard(class_num, lang)
    )

@router.callback_query(F.data.startswith("textbook:"))
async def set_textbook(call: CallbackQuery, state: FSMContext):
    await call.answer()
    textbook = call.data.split(":", 1)[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    subject = data.get("subject")
    await state.update_data(textbook=textbook)
    await state.set_state(MenuState.menu)
    
    await call.message.edit_text(
        MESSAGES[lang]["menu"].format(subject=subject, class_num=class_num, textbook=textbook),
        reply_markup=menu_keyboard(lang)
    )

@router.callback_query(F.data == "action:back")
async def menu_back(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    subject = data.get("subject")
    await state.set_state(MenuState.textbook)
    await call.message.edit_text(
        MESSAGES[lang]["textbook_choice"].format(subject=subject),
        reply_markup=textbooks_keyboard(class_num, subject, lang)
    )

@router.callback_query(F.data.startswith("action:"))
async def menu_actions(call: CallbackQuery, state: FSMContext):
    await call.answer()
    action = call.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    
    if action == "gdz":
        await state.set_state(MenuState.gdz)
        await call.message.edit_text(MESSAGES[lang]["gdz_prompt"], 
                                     reply_markup=back_only_keyboard(lang, "action:back"))
    elif action == "konspekt":
        await state.set_state(MenuState.konspekt)
        await call.message.edit_text(MESSAGES[lang]["konspekt_prompt"], 
                                     reply_markup=back_only_keyboard(lang, "action:back"))

@router.message(MenuState.gdz)
async def process_gdz(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    subject = data.get("subject")
    textbook = data.get("textbook")
    query = message.text
    
    clean_textbook = textbook.replace("📗 ", "")
    search_query = f"{subject} {class_num} класс {clean_textbook} {query} гдз"
    url = f"https://www.google.com/search?q={quote(search_query)}"
    
    await message.answer(
        MESSAGES[lang]["gdz_result"].format(class_num=class_num, subject=subject, 
                                            textbook=textbook, query=query, url=url),
        parse_mode="Markdown",
        reply_markup=back_only_keyboard(lang, "action:back")
    )

@router.message(MenuState.konspekt)
async def process_konspekt(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    class_num = data.get("class_num")
    subject = data.get("subject")
    query = message.text
    
    clean_subject = subject.split(" ", 1)[1] if " " in subject else subject
    search_query = f"{clean_subject} {class_num} класс {query} конспект"
    url = f"https://www.google.com/search?q={quote(search_query)}"
    
    await message.answer(
        MESSAGES[lang]["konspekt_result"].format(class_num=class_num, subject=subject,
                                                 query=query, url=url),
        parse_mode="Markdown",
        reply_markup=back_only_keyboard(lang, "action:back")
    )

@router.message(MenuState.presentation)
async def process_presentation(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.answer(MESSAGES[lang]["soon"], reply_markup=back_only_keyboard(lang, "other:back"))

@router.message(MenuState.solve)
async def process_solve(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.answer(MESSAGES[lang]["soon"], reply_markup=back_only_keyboard(lang, "other:back"))

@router.message(MenuState.bzb)
async def process_bzb(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.answer(MESSAGES[lang]["soon"], reply_markup=back_only_keyboard(lang, "other:back"))
