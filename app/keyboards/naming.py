from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def variants_keyboard(variants: list[dict[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idx, variant in enumerate(variants):
        title = variant.get("title", f"Вариант {idx + 1}")[:32]
        builder.button(text=f"{idx + 1}. {title}", callback_data=f"pick:{idx}")
    builder.button(text="Еще варианты", callback_data="regen")
    builder.adjust(1)
    return builder.as_markup()


def image_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Сгенерировать картинку", callback_data="gen_image")
    builder.button(text="Еще варианты", callback_data="regen")
    builder.adjust(1)
    return builder.as_markup()
