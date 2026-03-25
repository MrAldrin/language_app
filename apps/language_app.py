# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "polars",
# ]
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="full", layout_file="layouts/language_app.grid.json")

with app.setup:
    import marimo as mo
    import random
    from typing import Callable, Literal
    import json
    import polars as pl
    import string
    import sys


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # UI stuff
    """)
    return


@app.cell
def _(render_main_ui):
    render_main_ui()
    return


@app.cell
def _(
    current_sentence,
    render_footer,
    render_interaction_section,
    render_options_section,
    render_top_section,
):
    def render_main_ui() -> mo.Html:
        """Assembles the final application layout."""
        app_header = (
            mo.md("# Schipper mag ik overvaren?")
            .center()
            .style(
                {
                    "padding-top": "1rem",
                    "padding-bottom": "2rem",
                }
            )
        )

        if not current_sentence:
            not_correct_use_ui = mo.vstack(
                [app_header, render_options_section(), render_placeholder_element()],
                gap=0.0,
            )
            return not_correct_use_ui
        else:
            ui = mo.vstack(
                [
                    app_header,
                    render_options_section(),
                    render_top_section(),
                    render_interaction_section(),
                    render_footer(),
                ],
                gap=0.0,
            )
            return ui

    return (render_main_ui,)


@app.cell
def _(current_sentence, df, row_number):
    ui_difficulty = (
        render_difficulty_indicator(
            current_sentence["difficulty"], current_sentence["difficulty_str"]
        )
        if current_sentence
        else mo.md("")
    )
    progress = render_progress(row_number, len(df))
    question = (
        render_question_text(current_sentence["source"]) if current_sentence else mo.md("")
    )
    return progress, question, ui_difficulty


@app.cell
def _(current_sentence, get_answer_pool, move_word, pool_words):
    if not current_sentence:
        ui_answer = mo.md("")
        ui_word_alternatives = mo.md("")
    else:
        answer_indices = get_answer_pool()
        ui_answer = render_word_chips(
            pool_words, indices=answer_indices, on_click=move_word, is_pool=False
        )
        if not answer_indices:
            ui_answer = mo.vstack(
                [ui_answer, mo.md("*Click words from the pool below*").center()]
            )

        pool_chips_ui = render_word_chips(
            pool_words,
            on_click=move_word,
            is_pool=True,
            disabled_indices=answer_indices,
        )
        ui_word_alternatives = mo.vstack([mo.callout(pool_chips_ui, kind="neutral")])
    return ui_answer, ui_word_alternatives


@app.cell
def _(button_check_answer, get_score):
    feedback = render_feedback(button_check_answer.value)
    _stats = get_score()
    score = render_score(_stats["correct"], _stats["tries"])
    return feedback, score


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # constants and state initiation
    """)
    return


@app.cell
def _():
    LANG_MAP = {
        "en": "English",
        "nl": "Dutch",
        "es": "Spanish",
        "de": "German",
        "no": "Norwegian",
    }
    return (LANG_MAP,)


@app.cell
def _(dropdown_language_pairs):
    pair = dropdown_language_pairs.value

    if "pyodide" in sys.modules:
        from pyodide.http import open_url

        url = f"../public/{pair}/questions.json"
        data = json.loads(open_url(url).read())
    else:
        file_path = mo.notebook_location() / "public" / pair / "questions.json"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    df_raw = load_curriculum(data)
    return (df_raw,)


@app.cell
def _(current_sentence):
    pool_words = sort_words(current_sentence["words"]) if current_sentence else []
    return (pool_words,)


@app.cell
def _():
    get_answer_pool, set_answer_pool = mo.state([])
    return get_answer_pool, set_answer_pool


@app.cell
def _():
    get_score, set_score = mo.state({"tries": 0, "correct": 0})
    return get_score, set_score


@app.cell
def _(df_raw, dropdown_difficulty):
    df_temp = select_difficulty(df_raw, dropdown_difficulty.value)
    return (df_temp,)


@app.cell
def _(LANG_MAP, df_temp, dropdown_translation_direction, language_1):
    mo.stop(dropdown_translation_direction.value == "None")
    if "Both Directions" in dropdown_translation_direction.value:
        df = df_temp.with_columns(
            pl.Series(
                "is_l1_source",
                [random.choice([True, False]) for _ in range(len(df_temp))],
            )
        )
    else:
        is_l1_source = dropdown_translation_direction.value.startswith(
            LANG_MAP.get(language_1, language_1)
        )
        df = df_temp.with_columns(pl.lit(is_l1_source).alias("is_l1_source"))

    # Shuffle the rows
    df = df.sample(fraction=1.0, shuffle=True)
    return (df,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Drop down menus
    """)
    return


@app.cell
def _(LANG_MAP):
    raw_pairs = sorted(["de_en", "de_nl", "de_no", "en_nl", "en_no", "nl_no"])

    pair_options = {}
    for p in raw_pairs:
        p_l1, p_l2 = p.split("_")
        display_name = f"{LANG_MAP.get(p_l1, p_l1)} and {LANG_MAP.get(p_l2, p_l2)}"
        pair_options[display_name] = p

    dropdown_language_pairs = mo.ui.dropdown(
        options=pair_options,
        value="Dutch and Norwegian",
        allow_select_none=False,
        label="Language pair",
    )
    return (dropdown_language_pairs,)


@app.cell
def _(LANG_MAP, dropdown_language_pairs):
    if dropdown_language_pairs.value == None:
        directions = ["Not applicable"]
        language_1, language_2 = "", ""
    else:
        language_1, language_2 = dropdown_language_pairs.value.split("_")
        name1 = LANG_MAP.get(language_1, language_1)
        name2 = LANG_MAP.get(language_2, language_2)
        directions = [
            "Both Directions",
            f"{name1} -> {name2}",
            f"{name2} -> {name1}",
        ]
    dropdown_translation_direction = mo.ui.dropdown(
        options=directions, value=directions[0], label="Direction"
    )
    dropdown_translation_direction
    return dropdown_translation_direction, language_1, language_2


@app.cell
def _(df_raw, dropdown_language_pairs):
    if dropdown_language_pairs.value == None:
        dropdown_difficulty = mo.ui.multiselect(
            options=["Not applicable"], value=["Not applicable"], label="Difficulty"
        )
    else:
        dropdown_difficulty = mo.ui.multiselect.from_series(
            df_raw["difficulty_str"], value=["easy"], label="Difficulty"
        )
    dropdown_difficulty
    return (dropdown_difficulty,)


@app.cell
def _(dropdown_language_pairs, dropdown_translation_direction):
    mo.vstack([dropdown_language_pairs, dropdown_translation_direction])
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Buttons
    """)
    return


@app.cell
def _():
    button_prev = mo.ui.button(value=0, on_click=lambda c: c + 1, label="◀ Previous")
    button_next = mo.ui.button(value=0, on_click=lambda c: c + 1, label="Next ▶")
    return button_next, button_prev


@app.cell
def _(button_next, button_prev, df):
    netto_count = button_next.value - button_prev.value
    row_number = netto_count % len(df) if len(df) > 0 else 0
    return (row_number,)


@app.cell
def _(current_sentence, get_answer_pool, pool_words, set_score):
    button_check_answer = mo.ui.button(
        value=None,
        on_click=lambda _: (
            set_score(
                lambda s: {
                    "tries": s["tries"] + 1,
                    "correct": s["correct"]
                    + (
                        1
                        if check_answer(
                            [pool_words[i] for i in get_answer_pool()],
                            current_sentence["target"],
                            current_sentence.get("accepted", []),
                        )
                        else 0
                    ),
                }
            )
            or check_answer(
                [pool_words[i] for i in get_answer_pool()],
                current_sentence["target"],
                current_sentence.get("accepted", []),
            )
        ),
        label="Check answer",
    )
    return (button_check_answer,)


@app.cell
def _(df, language_1, language_2, row_number):
    current_sentence = get_sentence(df, row_number, language_1, language_2)
    button_reveal = mo.ui.button(
        label="👀 Reveal Answer", value=False, on_click=lambda _: True
    )
    return button_reveal, current_sentence


@app.cell
def _(df, language_1, language_2, row_number, set_answer_pool):
    new_sentence = get_sentence(df, row_number, language_1, language_2)
    set_answer_pool([])
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Testing cells for inspection
    """)
    return


@app.cell
def _(df, language_1, language_2, row_number):
    get_sentence(df, row_number, language_1, language_2)
    return


@app.cell
def _(df_raw):
    df_raw
    return


@app.cell
def _(df):
    df
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## testing cells for inspection ends here
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Functions
    """)
    return


@app.function
def load_curriculum(data: list[dict]) -> pl.DataFrame:
    """Loads the curriculum from parsed JSON data into a Polars DataFrame."""
    df = pl.DataFrame(data)

    # Map integer difficulties to string classes
    df = df.with_columns(
        pl.when(pl.col("difficulty") <= 3)
        .then(pl.lit("easy"))
        .when(pl.col("difficulty") <= 7)
        .then(pl.lit("medium"))
        .otherwise(pl.lit("hard"))
        .alias("difficulty_str")
    )

    return df


@app.function
def select_difficulty(df: pl.DataFrame, difficulty_list: list[str]):
    df = df.filter(pl.col("difficulty_str").is_in(difficulty_list))
    return df


@app.function
def get_sentence(df: pl.DataFrame, row_number: int, l1: str, l2: str) -> dict | None:
    if df.height == 0:
        return None
    valid_row = max(0, min(row_number, df.height - 1))
    row = df.row(valid_row, named=True)

    translations = row["translations"]

    def get_word_pool(lang_data):
        pool = lang_data.get("word_pool")
        if pool is not None:
            return pool
        words = lang_data.get("primary", "").split()
        for acc in lang_data.get("accepted", []):
            words.extend(acc.split())
        words.extend(lang_data.get("distraction_pool", []))
        return list(set(words))

    if row["is_l1_source"]:
        return {
            "difficulty": row["difficulty"],
            "difficulty_str": row["difficulty_str"],
            "source": translations[l1]["primary"],
            "target": translations[l2]["primary"],
            "accepted": translations[l2].get("accepted", []),
            "words": get_word_pool(translations[l2]),
        }
    else:
        return {
            "difficulty": row["difficulty"],
            "difficulty_str": row["difficulty_str"],
            "source": translations[l2]["primary"],
            "target": translations[l1]["primary"],
            "accepted": translations[l1].get("accepted", []),
            "words": get_word_pool(translations[l1]),
        }


@app.function
def normalize_text(text: str) -> str:
    """Removes punctuation and lowercase the text."""
    if not text:
        return ""

    return str(text).lower().translate(str.maketrans("", "", string.punctuation))


@app.function
def check_answer(user_answer: list[str], target: str, accepted: list[str]) -> bool:
    """Checks if the assembled words match the target sentence or accepted alternatives."""
    user_str = normalize_text(" ".join(user_answer))
    target_str = normalize_text(target)
    accepted_strs = [normalize_text(a) for a in (accepted or [])]

    return user_str == target_str or user_str in accepted_strs


@app.function
def sort_words(words: list[str]) -> list[str]:
    return sorted(words, key=lambda w: w.lower())


@app.function
def callout_custom(
    text: str, kind: Literal["neutral", "warn", "success", "info", "danger"] = "neutral"
) -> mo.Html:
    """A centralized callout that centers its markdown text."""
    return mo.callout(mo.md(text).center(), kind=kind)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Render ui functions
    """)
    return


@app.function
def render_placeholder_element():
    return mo.vstack(
        [
            mo.callout(
                mo.md(
                    "### 💡 Selection Required: "
                    "You must have selected something in all the above menus"
                ).center(),
                kind="info",
            ),
        ]
    )


@app.function
def render_difficulty_indicator(difficulty_int: int, difficulty_str: str) -> mo.Html:
    """Renders a color-coded difficulty indicator."""
    kind: Literal["info", "warn", "danger", "neutral"]
    match str(difficulty_str).lower():
        case "easy":
            kind = "info"
        case "medium":
            kind = "warn"
        case "hard":
            kind = "danger"
        case _:
            kind = "neutral"
    return callout_custom(
        f"Difficulty: {difficulty_int}/10 ({difficulty_str})", kind=kind
    )


@app.function
def render_question_text(source: str) -> mo.Html:
    """Renders the main question prompt."""
    return mo.vstack(
        [
            mo.md("Translate this sentence:").center(),
            mo.md(f"### {source}").center(),
            mo.md("---"),
            mo.md("**Your Answer:**").center(),
        ]
    )


@app.function
def render_word_chips(
    words: list[str],
    indices: list[int] | None = None,
    *,
    on_click: Callable[[int, bool], None],
    is_pool: bool,
    disabled_indices: list[int] | None = None,
) -> mo.Html:
    """Renders a collection of word chips as buttons."""
    if not words:
        return mo.md("No words available").center()

    chips = []
    display_indices = indices if indices is not None else range(len(words))
    disabled_indices = disabled_indices or []

    for idx in display_indices:
        word = words[idx]
        chips.append(
            mo.ui.button(
                label=word,
                on_change=lambda _, i=idx: on_click(i, is_pool),
                kind="neutral",
                tooltip="Click to add" if is_pool else "Click to remove",
                disabled=is_pool and idx in disabled_indices,
            )
        )

    return mo.hstack(chips, justify="center", gap=1, wrap=True)


@app.function
def render_feedback(check_value: bool | None) -> mo.Html:
    """Renders feedback based on the check result."""
    if check_value is None:
        return callout_custom("Press the button to check your answer")
    elif check_value:
        return callout_custom(
            "✅ Correct! Continue to the next question.", kind="success"
        )
    else:
        return callout_custom(
            "❌ False, continue or try again right away!", kind="warn"
        )


@app.function
def render_progress(current_idx: int, total_count: int) -> mo.Html:
    """Renders the question progress indicator."""
    return callout_custom(f"**Question:** {current_idx + 1}/{total_count}", kind="info")


@app.function
def render_score(correct: int, tries: int) -> mo.Html:
    """Renders the current session score."""
    score_text = f"**Score:** {correct} / {tries}" if tries > 0 else "*No attempts yet*"
    return callout_custom(score_text, kind="info")


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Render ui - non reusable
    """)
    return


@app.cell
def _(
    dropdown_difficulty,
    dropdown_language_pairs,
    dropdown_translation_direction,
):
    def render_options_section() -> mo.Html:
        """Renders the initial configuration UI."""
        instruction_text = mo.md(
            "Choose the language, difficulty level and translation direction to begin!"
        ).center()

        options_row = mo.hstack(
            [
                dropdown_language_pairs,
                dropdown_translation_direction,
                dropdown_difficulty,
            ],
            justify="space-between",
        )

        return mo.vstack([instruction_text, options_row, mo.md("---")], gap=1)

    return (render_options_section,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## State updaters
    """)
    return


@app.cell
def _(get_answer_pool, set_answer_pool):
    def move_word(idx: int, to_answer: bool):
        if to_answer:
            current = get_answer_pool()
            if idx not in current:
                set_answer_pool(lambda a: a + [idx])
        else:
            current = get_answer_pool()
            if idx in current:
                new = list(current)
                new.remove(idx)
                set_answer_pool(new)

    return (move_word,)


@app.cell
def _(
    button_check_answer,
    button_reveal,
    current_sentence,
    question,
    ui_answer,
    ui_word_alternatives,
):
    def render_interaction_section():
        # Core Exercise
        answer_text = (
            f"**Answer:** {current_sentence['target']}" if current_sentence else ""
        )
        if current_sentence and current_sentence.get("accepted"):
            answer_text += f"<br/>*Or:* {' / '.join(current_sentence['accepted'])}"

        reveal_text = (
            mo.md(answer_text).center()
            if button_reveal.value and current_sentence
            else mo.md("&nbsp;")
        )

        interaction_section = mo.vstack(
            [
                question,
                ui_answer,
                mo.md("---"),
                ui_word_alternatives,
                mo.hstack([button_check_answer, button_reveal], justify="center"),
                reveal_text,
            ],
            gap=0.0,
        )
        return interaction_section

    return (render_interaction_section,)


@app.cell
def _(progress, ui_difficulty):
    def render_top_section():
        return mo.hstack([ui_difficulty, progress], widths="equal")

    return (render_top_section,)


@app.cell
def _(button_next, button_prev, feedback, score):
    def render_footer():
        return mo.vstack(
            [
                mo.hstack([feedback, score], widths="equal"),
                mo.md("---"),
                mo.hstack([button_prev, button_next]),
            ]
        )

    return (render_footer,)


if __name__ == "__main__":
    app.run()
