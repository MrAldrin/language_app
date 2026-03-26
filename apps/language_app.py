# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "polars",
# ]
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="full", layout_file="layouts/language_app.grid.json")

with app.setup:
    import marimo as mo
    from typing import Callable, Literal
    import json
    import polars as pl
    import random
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
    app_theme_styles,
    current_sentence,
    render_footer,
    render_interaction_section,
    render_options_section,
    render_top_section,
):
    def render_main_ui() -> mo.Html:
        """Assembles the final application layout."""

        app_header = (
            mo.md(
                """
                <h1 style="margin:0; font-size:clamp(1.8rem, 3vw, 2.6rem);">
                  <span style="color: var(--la-title);">Schipper mag ik overvaren?</span>
                </h1>
                """
            )
            .center()
            .style(
                {
                    "padding-top": "1.25rem",
                    "padding-bottom": "1.25rem",
                }
            )
        )

        mo_elems = [app_theme_styles, app_header, render_options_section()]
        if not current_sentence:
            mo_elems.append(render_placeholder_element())
        else:
            mo_elems.append(render_top_section())
            mo_elems.append(render_interaction_section())
            mo_elems.append(render_footer())
        return mo.vstack(mo_elems, gap=0).style(
            {
                "margin": "0 auto",
                "padding": "0.5rem 0.75rem 1rem 0.75rem",
                "border-radius": "1rem",
                "background": "var(--la-page-bg)",
                "color": "var(--la-text)",
            }
        )

    return (render_main_ui,)


@app.cell
def _(get_answer_pool, move_word, pool_words):
    answer_indices = get_answer_pool()
    ui_answer = render_answer_area(pool_words, answer_indices, on_click=move_word)
    pool_chips_ui = render_word_pool(
        pool_words, on_click=move_word, disabled_indices=answer_indices
    )
    return pool_chips_ui, ui_answer


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # constants and state initiation
    """)
    return


@app.cell
def _():
    app_theme_styles = mo.md(
        """
        <style>
          :root {
            --la-page-bg: #f4f6f8;
            --la-card-bg: #ffffff;
            --la-card-border: #dbe1e8;
            --la-card-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
            --la-text: #1f2937;
            --la-title: #1f2937;
            --la-button-border: #cbd5e1;
          }
          button {
            border-radius: 9999px !important;
            border-color: var(--la-button-border) !important;
            transition: transform 0.12s ease, box-shadow 0.12s ease;
          }
          button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.14);
          }
        </style>
        """
    )
    return (app_theme_styles,)


@app.cell
def _():
    LANG_MAP = {
        "en": "English",
        "nl": "Dutch",
        "es": "Spanish",
        "de": "German",
        "no": "Norwegian",
    }

    raw_pairs = sorted(["de_en", "de_nl", "de_no", "en_nl", "en_no", "nl_no"])
    return LANG_MAP, raw_pairs


@app.cell
def _():
    get_answer_pool, set_answer_pool = mo.state([])
    return get_answer_pool, set_answer_pool


@app.cell
def _():
    get_score, set_score = mo.state({"tries": 0, "correct": 0})
    return get_score, set_score


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # temp
    """)
    return


@app.cell
def _(dropdown_language_pairs, language_1, language_2):
    _read_json_data = load_json_data(pair=dropdown_language_pairs.value)
    df_raw = load_curriculum(_read_json_data)
    df_canonical = transform_to_canonical(df_raw, language_1, language_2)
    return df_canonical, df_raw


@app.cell
def _(
    LANG_MAP,
    df_canonical,
    dropdown_difficulty,
    dropdown_translation_direction,
    language_1,
    language_2,
):
    direction_mode = resolve_direction_mode(
        dropdown_translation_direction.value,
        language_1,
        language_2,
        LANG_MAP,
    )
    df = prepare_curriculum(
        df_canonical,
        dropdown_difficulty.value,
        direction_mode,
    )
    return (df,)


@app.cell
def _(df, row_number):
    current_sentence = get_sentence(df, row_number)
    button_reveal = mo.ui.button(
        label="Reveal Answer", value=False, on_click=lambda _: True
    )
    return button_reveal, current_sentence


@app.cell
def _(current_sentence, set_answer_pool):
    # Reset answer selection whenever sentence identity updates.
    pool_words = sort_words(current_sentence["words"]) if current_sentence else []
    set_answer_pool([])
    return (pool_words,)


@app.cell
def _(button_next, button_prev, df):
    netto_count = button_next.value - button_prev.value
    row_number = netto_count % len(df) if len(df) > 0 else 0
    return (row_number,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Drop down menus
    """)
    return


@app.cell
def _(LANG_MAP, raw_pairs, set_answer_pool):
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
        on_change=lambda _: set_answer_pool([]),
    )
    dropdown_language_pairs
    return (dropdown_language_pairs,)


@app.cell
def _(LANG_MAP, dropdown_language_pairs, set_answer_pool):
    if dropdown_language_pairs.value is None:
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
        options=directions,
        value=directions[0],
        label="Direction",
        on_change=lambda _: set_answer_pool([]),
    )
    dropdown_translation_direction
    return dropdown_translation_direction, language_1, language_2


@app.cell
def _(df_raw, dropdown_language_pairs, set_answer_pool):
    if dropdown_language_pairs.value is None:
        dropdown_difficulty = mo.ui.multiselect(
            options=["Not applicable"], value=["Not applicable"], label="Difficulty"
        )
    else:
        dropdown_difficulty = mo.ui.multiselect.from_series(
            df_raw["difficulty_str"],
            value=["easy"],
            label="Difficulty",
            on_change=lambda _: set_answer_pool([]),
        )
    dropdown_difficulty
    return (dropdown_difficulty,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Buttons
    """)
    return


@app.cell
def _(set_answer_pool):
    def handle_navigation(c):
        set_answer_pool([])  # Clear the pool synchronously!
        return c + 1


    button_prev = mo.ui.button(value=0, on_click=handle_navigation, label="◀ Previous")
    button_next = mo.ui.button(value=0, on_click=handle_navigation, label="Next ▶")
    return button_next, button_prev


@app.cell
def _(
    current_sentence,
    get_answer_pool,
    pool_words,
    set_answer_pool,
    set_score,
):
    def handle_check(_):
        is_correct = check_answer(
            [pool_words[i] for i in get_answer_pool()],
            current_sentence["target"],
            current_sentence.get("accepted", []),
        )
        set_score(
            lambda s: {
                "tries": s["tries"] + 1,
                "correct": s["correct"] + (1 if is_correct else 0),
            }
        )
        return is_correct


    button_check_answer = mo.ui.button(
        value=None,
        on_click=handle_check,
        label="Check answer",
    )
    button_reset = mo.ui.button(
        value=None,
        on_click=lambda _: set_answer_pool([]),
        label="↺ Reset",
    )
    return button_check_answer, button_reset


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Testing cells for inspection
    """)
    return


@app.cell
def _():
    test_words = [
        "jeg",
        "vil",
        "gjerne",
        "bestille",
        "to",
        "store",
        "kaffer",
        "uten",
        "sukker",
        "takk",
    ]
    pool_preview = mo.hstack(
        [mo.ui.button(label=w, kind="neutral") for w in test_words],
        justify="center",
        gap=0.4,
        wrap=True,
    )
    default_word_pool_box = mo.callout(pool_preview, kind="neutral")
    custom_word_pool_box = render_word_pool_container(pool_preview)

    mo.vstack(
        [
            mo.vstack(
                [
                    mo.md("Word pool container comparison"),
                    mo.hstack(
                        [default_word_pool_box, custom_word_pool_box], widths="equal"
                    ),
                ],
                gap=0.15,
            ),
        ],
        gap=0.5,
    )
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
def load_json_data(pair: str) -> dict:
    """Loads curriculum JSON data from Pyodide or local filesystem."""
    if "pyodide" in sys.modules:
        from pyodide.http import open_url

        url = f"../public/{pair}/questions.json"
        return json.loads(open_url(url).read())
    else:
        file_path = mo.notebook_location() / "public" / pair / "questions.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


@app.function
def load_curriculum(data: list[dict]) -> pl.DataFrame:
    """Loads the curriculum from parsed JSON data into a Polars DataFrame."""
    return pl.DataFrame(data).with_columns(
        pl.when(pl.col("difficulty") <= 3)
        .then(pl.lit("easy"))
        .when(pl.col("difficulty") <= 7)
        .then(pl.lit("medium"))
        .otherwise(pl.lit("hard"))
        .alias("difficulty_str")
    )


@app.function
def resolve_direction_mode(
    selected_direction: str,
    language_1: str,
    language_2: str,
    lang_map: dict[str, str],
) -> str:
    if selected_direction == "Both Directions":
        return "both"

    if not language_1 or not language_2:
        return "not_applicable"

    name_1 = lang_map.get(language_1, language_1)
    name_2 = lang_map.get(language_2, language_2)

    if selected_direction == f"{name_1} -> {name_2}":
        return "l1_to_l2"
    if selected_direction == f"{name_2} -> {name_1}":
        return "l2_to_l1"
    return "both"


@app.function
def prepare_curriculum(
    df: pl.DataFrame,
    difficulty_list: list[str],
    direction_mode: str,
) -> pl.DataFrame:
    """Filters, precomputes direction, and materializes UI-ready rows."""
    if df.height == 0:
        return df

    filtered_df = df.filter(pl.col("difficulty_str").is_in(difficulty_list))

    if filtered_df.height == 0:
        return filtered_df

    if direction_mode == "l1_to_l2":
        directions = ["l1_to_l2"] * filtered_df.height
    elif direction_mode == "l2_to_l1":
        directions = ["l2_to_l1"] * filtered_df.height
    else:
        rng = random.Random()
        directions = [
            rng.choice(["l1_to_l2", "l2_to_l1"]) for _ in range(filtered_df.height)
        ]

    prepared_rows = []
    for row, direction in zip(filtered_df.iter_rows(named=True), directions):
        if direction == "l1_to_l2":
            prepared_rows.append(
                {
                    "question_id": row["question_id"],
                    "difficulty": row["difficulty"],
                    "difficulty_str": row["difficulty_str"],
                    "direction": direction,
                    "source": row["text_l1"],
                    "target": row["text_l2"],
                    "accepted": row["accepted_l2"],
                    "words": row["word_pool_l2"],
                }
            )
        else:
            prepared_rows.append(
                {
                    "question_id": row["question_id"],
                    "difficulty": row["difficulty"],
                    "difficulty_str": row["difficulty_str"],
                    "direction": direction,
                    "source": row["text_l2"],
                    "target": row["text_l1"],
                    "accepted": row["accepted_l1"],
                    "words": row["word_pool_l1"],
                }
            )

    if not prepared_rows:
        return pl.DataFrame([])

    prepared_df = pl.DataFrame(prepared_rows)
    return prepared_df.sample(fraction=1.0, shuffle=True)


@app.function
def make_word_pool(lang_data: dict) -> list[str]:
    pool = lang_data.get("word_pool")
    if pool is not None:
        return pool

    words = lang_data.get("primary", "").split()
    for accepted in lang_data.get("accepted", []):
        words.extend(accepted.split())
    words.extend(lang_data.get("distraction_pool", []))
    return list(dict.fromkeys(words))


@app.function
def transform_to_canonical(
    df: pl.DataFrame,
    language_1: str,
    language_2: str,
) -> pl.DataFrame:
    """
    Transforms source rows into a canonical bilingual schema.
    This is the adapter layer for future data-source formats.
    """
    if df.height == 0 or not language_1 or not language_2:
        return pl.DataFrame([])

    rows = []
    for index, row in enumerate(df.iter_rows(named=True)):
        translations = row.get("translations", {})
        lang_1_data = translations.get(language_1)
        lang_2_data = translations.get(language_2)

        if not lang_1_data or not lang_2_data:
            continue

        rows.append(
            {
                "question_id": row.get("id", index),
                "difficulty": row["difficulty"],
                "difficulty_str": row["difficulty_str"],
                "language_1": language_1,
                "language_2": language_2,
                "text_l1": lang_1_data.get("primary", ""),
                "text_l2": lang_2_data.get("primary", ""),
                "accepted_l1": lang_1_data.get("accepted", []),
                "accepted_l2": lang_2_data.get("accepted", []),
                "word_pool_l1": make_word_pool(lang_1_data),
                "word_pool_l2": make_word_pool(lang_2_data),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame([])


@app.function
def get_sentence(df: pl.DataFrame, row_number: int) -> dict | None:
    if df.height == 0:
        return None

    valid_row = max(0, min(row_number, df.height - 1))
    return df.row(valid_row, named=True)


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
def feedback_chip(
    text: str, *, border: str, background: str, foreground: str
) -> mo.Html:
    """Creates a compact pill-like feedback chip."""
    return (
        mo.md(text)
        .center()
        .style(
            {
                "display": "inline-flex",
                "justify-content": "center",
                "align-items": "center",
                "margin": "0",
                "padding": "0.2rem 0.6rem",
                "border": f"1px solid {border}",
                "border-radius": "9999px",
                "background": background,
                "color": foreground,
                "font-weight": "500",
                "line-height": "1.15",
                "box-sizing": "border-box",
                "width": "min(100%, 32rem)",
                "text-align": "center",
            }
        )
    )


@app.function
def success_chip(text: str) -> mo.Html:
    return feedback_chip(
        text,
        border="#22c55e",
        background="#dcfce7",
        foreground="#14532d",
    )


@app.function
def warn_chip(text: str) -> mo.Html:
    return feedback_chip(
        text,
        border="#f59e0b",
        background="#fef3c7",
        foreground="#78350f",
    )


@app.function
def neutral_chip(text: str) -> mo.Html:
    return feedback_chip(
        text,
        border="#9ca3af",
        background="#f3f4f6",
        foreground="#1f2937",
    )


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
                    "### Selection Required: "
                    "You must have selected something in all the above menus"
                ).center(),
                kind="info",
            ),
        ]
    )


@app.function
def render_stat_box(value: str, label: str, caption: str) -> mo.Html:
    """Renders a full-width stat card with centered text."""
    return mo.vstack(
        [
            mo.md(f"**{label}**").center(),
            mo.md(f"### {value}").center(),
            mo.md(f"*{caption}*").center(),
        ],
        gap=0.15,
    ).style(
        {
            "width": "100%",
            "padding": "0.85rem 0.7rem",
            "border-radius": "0.75rem",
            "background": "var(--la-card-bg)",
            "border": "1px solid var(--la-card-border)",
            "box-sizing": "border-box",
            "text-align": "center",
        }
    )


@app.function
def render_difficulty_indicator(difficulty_int: int, difficulty_str: str) -> mo.Html:
    """Renders difficulty as a full-width centered stat card."""
    return render_stat_box(
        f"{difficulty_int}/10",
        "Difficulty",
        str(difficulty_str).capitalize(),
    )


@app.function
def render_score(correct: int, tries: int) -> mo.Html:
    """Renders the current session score as a full-width centered stat card."""
    return render_stat_box(f"{correct}/{tries}", "Correct", "Attempts")


@app.function
def render_progress(current_idx: int, total_count: int) -> mo.Html:
    """Renders question progress as a full-width centered stat card."""
    return render_stat_box(f"{current_idx + 1}/{total_count}", "Question", "Progress")


@app.function
def render_question_text(source: str) -> mo.Html:
    """Renders the main question prompt."""
    return mo.vstack(
        [
            mo.md("**Translate this sentence:**").center(),
            mo.md(f"### {source}").center(),
            mo.md("---"),
            mo.md("**Your Answer:**").center(),
        ]
    )


@app.function
def make_word_chip(
    word: str,
    idx: int,
    on_click: Callable[[int, bool], None],
    *,
    is_pool: bool,
    disabled: bool = False,
) -> mo.Html:
    """Creates a single word chip button."""
    return mo.ui.button(
        label=word,
        on_change=lambda _, i=idx: on_click(i, is_pool),
        kind="neutral",
        tooltip="Click to add" if is_pool else "Click to remove",
        disabled=disabled,
    )


@app.function
def render_answer_area(
    words: list[str],
    indices: list[int],
    *,
    on_click: Callable[[int, bool], None],
) -> mo.Html:
    """Renders selected word chips as the answer area, or a hint when empty."""
    if not indices:
        return (
            mo.md("*Click words from the pool below*").center()
            if words
            else mo.md("No words available").center()
        )

    chips = [
        make_word_chip(words[idx], idx, on_click, is_pool=False) for idx in indices
    ]
    return mo.hstack(chips, justify="center", gap=1, wrap=True)


@app.function
def render_word_pool(
    words: list[str],
    *,
    on_click: Callable[[int, bool], None],
    disabled_indices: list[int] | None = None,
) -> mo.Html:
    """Renders all word chips for the pool, disabling already-selected words."""
    if not words:
        return mo.md("No words available").center()

    disabled = disabled_indices or []
    chips = [
        make_word_chip(
            words[idx], idx, on_click, is_pool=True, disabled=idx in disabled
        )
        for idx in range(len(words))
    ]
    return mo.hstack(chips, justify="center", gap=1, wrap=True)


@app.function
def render_word_pool_container(content: mo.Html) -> mo.Html:
    """Renders the word pool inside a compact bordered container."""
    return mo.vstack([content], gap=0).style(
        {
            "margin": "0.5rem 0",
            "padding": "1.25rem 0.75rem",
            "border": "1px solid var(--la-card-border)",
            "border-radius": "0.85rem",
            "background": "var(--la-card-bg)",
            "overflow-y": "hidden",
            "box-sizing": "border-box",
            "width": "100%",
            "display": "flex",
            "justify-content": "center",
            "box-shadow": "var(--la-card-shadow)",
        }
    )


@app.function
def render_feedback(check_value: bool | None) -> mo.Html:
    """Renders feedback based on the check result."""
    if check_value is None:
        return neutral_chip("Press the button to check your answer")
    elif check_value:
        return success_chip("Correct! Continue to the next question.")
    else:
        return warn_chip("False, continue or try again right away!")


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
            wrap=True,
        )

        return mo.vstack([instruction_text, options_row], gap=1).style(
            {
                "padding": "1rem",
                "border-radius": "1rem",
                "background": "var(--la-card-bg)",
                "border": "1px solid var(--la-card-border)",
                "box-shadow": "var(--la-card-shadow)",
            }
        )

    return (render_options_section,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## State updaters
    """)
    return


@app.cell
def _(get_answer_pool, set_answer_pool):
    def move_word(index: int, to_answer: bool):
        # needs to call get_answer_pool for reactivity reasons
        get_answer_pool()
        # adds or removes the element from the answer pool
        if to_answer:
            set_answer_pool(lambda a: a + [index] if index not in a else a)
        else:
            set_answer_pool(lambda a: [i for i in a if i != index])

    return (move_word,)


@app.cell
def _(current_sentence, df, get_score, row_number):
    def render_top_section():
        stats = get_score()
        return mo.hstack(
            [
                render_difficulty_indicator(
                    current_sentence["difficulty"], current_sentence["difficulty_str"]
                ),
                render_score(stats["correct"], stats["tries"]),
                render_progress(row_number, len(df)),
            ],
            widths="equal",
        ).style(
            {
                "padding": "1rem",
                "border-radius": "1rem",
                "background": "var(--la-card-bg)",
                "border": "1px solid var(--la-card-border)",
                "box-shadow": "var(--la-card-shadow)",
            }
        )

    return (render_top_section,)


@app.cell
def _(
    button_check_answer,
    button_reset,
    button_reveal,
    current_sentence,
    pool_chips_ui,
    ui_answer,
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
                render_question_text(current_sentence["source"]),
                ui_answer,
                mo.md("---"),
                render_word_pool_container(pool_chips_ui),
                mo.hstack(
                    [button_check_answer, button_reset, button_reveal],
                    justify="center",
                ),
                reveal_text,
                mo.hstack(
                    [
                        render_feedback(button_check_answer.value),
                    ],
                    justify="center",
                ),
            ],
            gap=0.0,
        ).style(
            {
                "padding": "1rem",
                "margin-top": "0.75rem",
                "border-radius": "1rem",
                "background": "var(--la-card-bg)",
                "border": "1px solid var(--la-card-border)",
                "box-shadow": "var(--la-card-shadow)",
            }
        )
        return interaction_section

    return (render_interaction_section,)


@app.cell
def _(button_next, button_prev):
    def render_footer():
        return mo.vstack(
            [
                mo.hstack([button_prev, button_next]),
            ]
        ).style(
            {
                "padding": "1rem",
                "margin-top": "0.75rem",
                "border-radius": "1rem",
                "background": "var(--la-card-bg)",
                "border": "1px solid var(--la-card-border)",
                "box-shadow": "var(--la-card-shadow)",
            }
        )

    return (render_footer,)


if __name__ == "__main__":
    app.run()
