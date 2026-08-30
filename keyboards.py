from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data import MESSAGES, SUBJECTS, TEXTBOOKS

def lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
         InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kz")]
    ])

def class_keyboard(lang: str):
    buttons = []
    row = []
    for i in range(1, 12):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"class:{i}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(text=MESSAGES[lang]["other"], callback_data="class:other"),
        InlineKeyboardButton(text=MESSAGES[lang]["change_lang"], callback_data="menu:lang")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def other_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MESSAGES[lang]["make_presentation"], callback_data="other:presentation")],
        [InlineKeyboardButton(text=MESSAGES[lang]["solve_task"], callback_data="other:solve")],
        [InlineKeyboardButton(text=MESSAGES[lang]["bzb_photo"], callback_data="other:bzb")],
        [InlineKeyboardButton(text=MESSAGES[lang]["back"], callback_data="other:back")]
    ])

def subjects_keyboard(class_num: str, lang: str):
    subjects = SUBJECTS.get(class_num, {}).get(lang, [])
    buttons = []
    row = []
    for subj in subjects:
        row.append(InlineKeyboardButton(text=subj, callback_data=f"subject:{subj}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=MESSAGES[lang]["back"], callback_data="subject:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def textbooks_keyboard(class_num: str, subject: str, lang: str):
    textbooks = TEXTBOOKS.get(class_num, {}).get(subject, [])
    buttons = [[InlineKeyboardButton(text=tb, callback_data=f"textbook:{tb}")] for tb in textbooks]
    buttons.append([InlineKeyboardButton(text=MESSAGES[lang]["back"], callback_data="textbook:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def menu_keyboard(lang: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MESSAGES[lang]["find_gdz"], callback_data="action:gdz"),
         InlineKeyboardButton(text=MESSAGES[lang]["find_konspekt"], callback_data="action:konspekt")],
        [InlineKeyboardButton(text=MESSAGES[lang]["back"], callback_data="action:back")]
    ])

def back_only_keyboard(lang: str, callback: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MESSAGES[lang]["back"], callback_data=callback)]
    ])
