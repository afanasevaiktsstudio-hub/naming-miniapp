from app.keyboards.naming import image_keyboard, variants_keyboard


def test_variants_keyboard_contains_buttons() -> None:
    keyboard = variants_keyboard(
        [
            {"title": "A", "style": "s1", "comment": "c1"},
            {"title": "B", "style": "s2", "comment": "c2"},
        ]
    )
    flat = [btn for row in keyboard.inline_keyboard for btn in row]
    callback_data = {btn.callback_data for btn in flat}
    assert "pick:0" in callback_data
    assert "pick:1" in callback_data
    assert "regen" in callback_data


def test_image_keyboard_contains_expected_actions() -> None:
    keyboard = image_keyboard()
    flat = [btn for row in keyboard.inline_keyboard for btn in row]
    callback_data = {btn.callback_data for btn in flat}
    assert callback_data == {"gen_image", "regen"}
