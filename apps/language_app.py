# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "polars",
#     "anywidget",
#     "traitlets",
# ]
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="full", layout_file="layouts/language_app.grid.json")

with app.setup:
    import marimo as mo
    import json
    import polars as pl
    import random
    import re
    import string
    import sys
    import anywidget
    import traitlets
    from typing import Any, Callable


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # testing out anywidget
    """)
    return


@app.class_definition
class QuestionWidget(anywidget.AnyWidget):
    _esm = """
        function normalize(str) {
            return str.toLowerCase()
                .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "")
                .replace(/\s+/g, " ")
                .trim();
        }
    
        function checkAnswer(answerIndices, words, target, accepted) {
            const userStr = normalize(answerIndices.map(i => words[i]).join(" "));
            const targetStr = normalize(target);
            const acceptedStrs = accepted.map(a => normalize(a));
            return userStr === targetStr || acceptedStrs.includes(userStr);
        }
    
        function render({ model, el }) {
            let answerIndices = [];
            let phase = "idle";
            // ADDED: reveal is independent of phase - user can toggle it any time
            let revealed = false;
    
            function redraw() {
                const words = model.get("words");
    
                const answerHtml = answerIndices.map(i =>
                    `<button class="chip answer-chip" data-idx="${i}">${words[i]}</button>`
                ).join("");
    
                const poolHtml = words.map((word, i) => {
                    const isSelected = answerIndices.includes(i);
                    const isLocked = phase === "correct";
                    return `<button
                        class="chip pool-chip ${isSelected || isLocked ? "chip-disabled" : ""}"
                        data-idx="${i}"
                        ${isSelected || isLocked ? "disabled" : ""}
                    >${word}</button>`;
                }).join("");
    
                const feedbackHtml = {
                    idle:    "",
                    wrong:   `<div class="feedback feedback-wrong">✗ Not quite — try again</div>`,
                    correct: `<div class="feedback feedback-correct">✓ Correct!</div>`,
                }[phase];
    
                // ADDED: reveal area shown when revealed=true, always same height to avoid jumping
                const target = model.get("target");
                const accepted = model.get("accepted");
                const acceptedHtml = accepted.length > 0
                    ? `<div class="reveal-accepted">Also accepted: ${accepted.join(" / ")}</div>`
                    : "";
                const revealHtml = `
                    <div class="reveal-area ${revealed ? "reveal-visible" : "reveal-hidden"}">
                        <div class="reveal-target">${target}</div>
                        ${acceptedHtml}
                    </div>
                `;
    
                // CHANGED: three buttons, each with fixed width so the row never changes size
                // check/next label changes but button stays same width via CSS
                const checkDisabled = answerIndices.length === 0 ? "disabled" : "";
                const checkLabel = phase === "correct"
                // ADDED: clear disabled when answer is empty and phase is idle - nothing to clear
                const clearDisabled = (answerIndices.length === 0 && phase === "idle") ? "disabled" : "";
    
                el.innerHTML = `
                    <div class="answer-area">
                        ${answerHtml || "<span class='hint'>Click words below to build your answer</span>"}
                    </div>
                    <div class="pool-area">
                        ${poolHtml}
                    </div>
                    ${revealHtml}
                    ${feedbackHtml}
                    <div class="button-row">
                        <button class="action-btn clear-btn" id="clear-btn" ${clearDisabled}>↺ Clear</button>
                        <button class="action-btn check-btn" id="check-btn" ${checkDisabled}>${checkLabel}</button>
                        <button class="action-btn reveal-btn" id="reveal-btn">
                            ${revealed ? "Hide answer" : "Reveal answer"}
                        </button>
                    </div>
                `;
    
                // chip handlers - only when not locked
                if (phase !== "correct") {
                    el.querySelectorAll(".answer-chip").forEach(btn => {
                        btn.addEventListener("click", () => {
                            const pos = answerIndices.indexOf(parseInt(btn.dataset.idx));
                            if (pos !== -1) answerIndices.splice(pos, 1);
                            phase = "idle";
                            redraw();
                        });
                    });
                    el.querySelectorAll(".pool-chip:not([disabled])").forEach(btn => {
                        btn.addEventListener("click", () => {
                            answerIndices.push(parseInt(btn.dataset.idx));
                            phase = "idle";
                            redraw();
                        });
                    });
                }
    
                // ADDED: clear resets answer area and phase back to idle
                const clearBtn = el.querySelector("#clear-btn");
                if (clearBtn) {
                    clearBtn.addEventListener("click", () => {
                        answerIndices = [];
                        phase = "idle";
                        redraw();
                    });
                }
    
                // ADDED: reveal toggles independently - does not affect phase or answer
                const revealBtn = el.querySelector("#reveal-btn");
                if (revealBtn) {
                    revealBtn.addEventListener("click", () => {
                        revealed = !revealed;
                        redraw();
                    });
                }
    
                const checkBtn = el.querySelector("#check-btn");
                if (checkBtn) {
                    checkBtn.addEventListener("click", () => {
    
                        const words = model.get("words");
                        const target = model.get("target");
                        const accepted = model.get("accepted");
                        const isCorrect = checkAnswer(answerIndices, words, target, accepted);
    
                        model.set("correct", isCorrect);
                        model.save_changes();
    
                        phase = isCorrect ? "correct" : "wrong";
                        redraw();
                    });
                }
            }
    
            model.on("change:words", () => {
                answerIndices = [];
                phase = "idle";
                // ADDED: hide reveal when Python pushes a new question
                revealed = false;
                redraw();
            });
    
            redraw();
        }
        export default { render };
    """

    _css = """
        .answer-area {
            min-height: 3rem;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border: 1px dashed #8ea3b8;
            border-radius: 0.75rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
            justify-content: center;
        }
        .pool-area {
            padding: 0.75rem;
            background: #e8f6f4;
            border-radius: 0.75rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            justify-content: center;
        }
        .chip {
            padding: 0.3rem 0.8rem;
            border: 1px solid #8ea3b8;
            border-radius: 9999px;
            background: white;
            cursor: pointer;
            font-size: 1rem;
        }
        .chip:hover:not([disabled]) {
            background: #e8f6f4;
        }
        .chip-disabled {
            opacity: 0.35;
            cursor: default;
        }
        .hint {
            color: #8ea3b8;
            font-style: italic;
            font-size: 0.9rem;
        }
        .feedback {
            margin: 0.75rem 0 0.25rem;
            padding: 0.4rem 1rem;
            border-radius: 9999px;
            text-align: center;
            font-weight: 500;
            font-size: 0.95rem;
        }
        .feedback-wrong {
            background: #fff0d8;
            border: 1px solid #c97b0e;
            color: #704010;
        }
        .feedback-correct {
            background: #e5f7ee;
            border: 1px solid #2e8b57;
            color: #145339;
        }
        /* ADDED: reveal area always rendered but visibility toggled
           using visibility+height instead of display:none so layout stays stable */
        .reveal-area {
            margin: 0.5rem 0 0.25rem;
            text-align: center;
            min-height: 2.5rem;
        }
        .reveal-hidden {
            visibility: hidden;
        }
        .reveal-visible {
            visibility: visible;
        }
        .reveal-target {
            font-weight: 600;
            font-size: 1rem;
            color: #243548;
        }
        .reveal-accepted {
            font-size: 0.85rem;
            font-style: italic;
            color: #243548;
            margin-top: 0.2rem;
        }
        .button-row {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 0.75rem;
        }
        /* ADDED: all action buttons share the same base style and fixed min-width
           so the row never changes size when labels change */
        .action-btn {
            min-width: 8rem;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            border: 1px solid #8ea3b8;
            background: white;
            font-size: 1rem;
            cursor: pointer;
            text-align: center;
        }
        .action-btn:hover:not([disabled]) {
            background: #e8f6f4;
        }
        .action-btn[disabled] {
            opacity: 0.35;
            cursor: default;
        }
    """

    # Python → JS (inputs)
    words = traitlets.List([]).tag(sync=True)
    target = traitlets.Unicode("").tag(sync=True)
    accepted = traitlets.List([]).tag(sync=True)

    # JS → Python (outputs)
    correct = traitlets.Bool(False).tag(sync=True)


@app.cell
def _(current_sentence, pool_words):
    if current_sentence is None:
        widget = None
    else:
        _widget = QuestionWidget(
            words=pool_words,
            target=current_sentence["target"],
            accepted=current_sentence.get("accepted", []),
        )
        widget = mo.ui.anywidget(_widget)
    return (widget,)


@app.cell
def _(widget):
    correct = widget.value["correct"]
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # UI
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
    in_question_view,
    render_footer,
    render_interaction_section,
    render_options_section,
    render_summary_section,
    show_summary_page,
):
    def render_main_ui() -> mo.Html:
        """Assembles the final application layout."""

        app_header = (
            mo.md("# Schipper mag ik overvaren?")
            .center()
            .style(
                {
                    "padding-top": "1rem",
                    "padding-bottom": "1rem",
                }
            )
        )

        mo_elems = [app_theme_styles, app_header]
        if not in_question_view:
            mo_elems.append(render_options_section())
        elif show_summary_page:
            mo_elems.append(render_summary_section())
        else:
            if current_sentence:
                mo_elems.append(render_interaction_section())
            else:
                mo_elems.append(render_no_questions_element())
            mo_elems.append(render_footer())
        return mo.vstack(mo_elems, gap=0)

    return (render_main_ui,)


@app.cell
def _(active_question_key, get_answer_pool_by_question, move_word, pool_words):
    answer_indices = get_answer_pool_by_question().get(active_question_key, [])
    ui_answer = render_answer_chips(
        words=pool_words, indices=answer_indices, on_click=move_word
    )
    pool_chips_ui = render_word_pool(
        words=pool_words, on_click=move_word, disabled_indices=answer_indices
    )
    return


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
            /* Active design tokens used by current UI styles/components. */
            --la-bg-surface: #ffffff;
            --la-border-subtle: #d8e0ea;
            --la-accent-primary-soft: #e8f6f4;
            --la-accent-secondary-soft: #eef4ff;
            --la-success-border: #2e8b57;
            --la-success-bg: #e5f7ee;
            --la-success-fg: #145339;
            --la-warning-border: #c97b0e;
            --la-warning-bg: #fff0d8;
            --la-warning-fg: #704010;
            --la-neutral-border: #8ea3b8;
            --la-neutral-bg: #eaf0f6;
            --la-neutral-fg: #243548;
            --la-radius-md: 0.75rem;
            --la-radius-lg: 1rem;
            --la-radius-pool: 0.85rem;
            --la-space-section: 1rem;
            --la-space-card-margin: 0.5rem;
          }
          /* Keep all menu controls visually consistent across widget types. */
          [data-testid="mo-output"] marimo-dropdown,
          [data-testid="mo-output"] marimo-multiselect {
            --background: var(--la-bg-surface);
          }
          [data-testid="mo-output"] select,
          [data-testid="mo-output"] select:focus,
          [data-testid="mo-output"] [role="combobox"],
          [data-testid="mo-output"] [aria-haspopup="listbox"] {
            background: var(--la-bg-surface) !important;
            background-color: var(--la-bg-surface) !important;
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
def _(raw_pairs):
    pyodide_question_files_by_pair = {pair: ["questions.json"] for pair in raw_pairs}
    pyodide_question_files_by_pair["de_no"] = [
        "questions.json",
        "targeted_questions.json",
    ]
    pyodide_question_files_by_pair["nl_no"] = [
        "questions.json",
        "targeted_questions.json",
    ]
    return (pyodide_question_files_by_pair,)


@app.cell
def _():
    get_answer_pool_by_question, set_answer_pool_by_question = mo.state({})


    def set_answer_pool(
        question_key: str, update: list[int] | Callable[[list[int]], list[int]]
    ) -> None:
        def _update_answer_pool(state: dict[str, list[int]]) -> dict[str, list[int]]:
            current_pool = state.get(question_key, [])
            new_pool = update(current_pool) if callable(update) else update

            if new_pool == current_pool:
                return state

            if not new_pool:
                if question_key not in state:
                    return state
                return {k: v for k, v in state.items() if k != question_key}

            return {**state, question_key: new_pool}

        set_answer_pool_by_question(_update_answer_pool)

    return get_answer_pool_by_question, set_answer_pool


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Read and process data
    """)
    return


@app.cell
def _(dropdown_language_pairs, dropdown_question_file, language_1, language_2):
    _read_json_data = load_json_data(
        pair=dropdown_language_pairs.value, filename=dropdown_question_file.value
    )
    df_raw = load_curriculum(data=_read_json_data)
    df_canonical = transform_to_canonical(
        df=df_raw, language_1=language_1, language_2=language_2
    )
    return df_canonical, df_raw


@app.cell
def _(
    LANG_MAP,
    df_canonical,
    dropdown_difficulty,
    dropdown_translation_direction,
    language_1,
    language_2,
    start_session_id,
):
    direction_mode = resolve_direction_mode(
        selected_direction=dropdown_translation_direction.value,
        language_1=language_1,
        language_2=language_2,
        lang_map=LANG_MAP,
    )
    df = prepare_curriculum(
        df=df_canonical,
        difficulty_list=dropdown_difficulty.value,
        direction_mode=direction_mode,
        session_id=start_session_id,
    )
    return (df,)


@app.cell
def _(df, row_number, start_session_id):
    _ = start_session_id
    current_sentence = get_sentence(df=df, row_number=row_number)


    def toggle_reveal(current: bool) -> bool:
        return not current


    # button_reveal = mo.ui.button(label="Reveal Answer", value=False, on_click=toggle_reveal)
    return (current_sentence,)


@app.cell
def _(current_sentence):
    pool_words = sort_words(words=current_sentence["words"]) if current_sentence else []
    return (pool_words,)


@app.cell
def _(button_next, button_prev, df):
    netto_count = button_next.value - button_prev.value
    if len(df) == 0:
        row_number = 0
    else:
        row_number = max(0, min(netto_count, len(df) - 1))
    return (row_number,)


@app.cell
def _(button_next, button_prev, row_number, start_session_id):
    question_step = button_next.value + button_prev.value
    active_question_key = f"{start_session_id}:{question_step}:{row_number}"
    return (active_question_key,)


@app.cell
def _(button_next, df, in_question_view, row_number):
    total_questions = len(df)
    last_question_index = max(0, total_questions - 1)
    is_last_question = total_questions > 0 and row_number >= last_question_index
    show_summary_page = (
        in_question_view and total_questions > 0 and button_next.value > last_question_index
    )
    return show_summary_page, total_questions


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Drop down menus
    """)
    return


@app.cell
def _(LANG_MAP, raw_pairs):
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
    dropdown_language_pairs
    return (dropdown_language_pairs,)


@app.cell
def _(dropdown_language_pairs, pyodide_question_files_by_pair):
    pair = dropdown_language_pairs.value
    file_names = list_question_files(
        pair=pair, pyodide_files_by_pair=pyodide_question_files_by_pair
    )

    default_file = "questions.json" if "questions.json" in file_names else file_names[0]
    default_file_option = humanize_question_file_name(default_file)
    file_options = {humanize_question_file_name(name): name for name in file_names}

    dropdown_question_file = mo.ui.dropdown(
        options=file_options,
        value=default_file_option,
        allow_select_none=False,
        label="Question set",
    )
    dropdown_question_file
    return (dropdown_question_file,)


@app.cell
def _(LANG_MAP, dropdown_language_pairs):
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
    )
    dropdown_translation_direction
    return dropdown_translation_direction, language_1, language_2


@app.cell
def _(df_raw, dropdown_language_pairs):
    if dropdown_language_pairs.value is None:
        dropdown_difficulty = mo.ui.multiselect(
            options=["Not applicable"], value=["Not applicable"], label="Difficulty"
        )
    else:
        dropdown_difficulty = mo.ui.multiselect.from_series(
            df_raw["difficulty_str"],
            value=["easy"],
            label="Difficulty",
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
def _():
    def bump(counter: int) -> int:
        return counter + 1


    button_start_questions = mo.ui.button(
        value=0,
        on_click=bump,
        label="Start questions",
    )
    button_back_to_settings = mo.ui.button(
        value=0,
        on_click=bump,
        label="↩ Back to settings",
    )
    button_restart_session = mo.ui.button(
        value=0,
        on_click=bump,
        label="Start new session",
    )
    mo.hstack([button_start_questions, button_restart_session, button_back_to_settings])
    return (
        button_back_to_settings,
        button_restart_session,
        button_start_questions,
    )


@app.cell
def _(button_back_to_settings, button_restart_session, button_start_questions):
    start_session_id = button_start_questions.value + button_restart_session.value
    in_question_view = start_session_id > button_back_to_settings.value
    return in_question_view, start_session_id


@app.cell
def _(start_session_id):
    _ = start_session_id


    def handle_navigation(c: int) -> int:
        return c + 1


    button_prev = mo.ui.button(value=0, on_click=handle_navigation, label="◀ Previous")
    button_next = mo.ui.button(value=0, on_click=handle_navigation, label="Next ▶")
    return button_next, button_prev


@app.cell
def _():
    # def handle_check_answer(score: dict[str, Any] | None) -> dict[str, Any]:
    #     prev_score = score or {"tries": 0, "correct": 0, "last_result": None}
    #     if len(df) == 0:
    #         return prev_score

    #     row_number = max(0, min(button_next.value - button_prev.value, len(df) - 1))
    #     question_step = button_next.value + button_prev.value
    #     active_question_key = f"{start_session_id}:{question_step}:{row_number}"
    #     current_sentence = get_sentence(df=df, row_number=row_number)
    #     if not current_sentence:
    #         return prev_score

    #     pool_words = sort_words(words=current_sentence["words"])
    #     answer_pool = get_answer_pool_by_question().get(active_question_key, [])

    #     is_correct = check_answer(
    #         user_answer=[pool_words[i] for i in answer_pool],
    #         target=current_sentence["target"],
    #         accepted=current_sentence.get("accepted", []),
    #     )
    #     return {
    #         "tries": prev_score["tries"] + 1,
    #         "correct": prev_score["correct"] + (1 if is_correct else 0),
    #         "last_result": is_correct,
    #     }
    return


@app.cell
def _():
    # def handle_reset_answer(click_count: int) -> int:
    #     if len(df) == 0:
    #         return click_count
    #     row_number = max(0, min(button_next.value - button_prev.value, len(df) - 1))
    #     question_step = button_next.value + button_prev.value
    #     active_question_key = f"{start_session_id}:{question_step}:{row_number}"
    #     set_answer_pool(active_question_key, [])
    #     return click_count
    return


@app.cell
def _(start_session_id):
    _ = start_session_id

    # button_check_answer = mo.ui.button(
    #     value={"tries": 0, "correct": 0, "last_result": None},
    #     on_click=handle_check_answer,
    #     label="Check answer",
    # )
    # button_reset = mo.ui.button(
    #     value=0,
    #     on_click=handle_reset_answer,
    #     label="↺ Reset",
    # )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Testing cells for inspection
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
    custom_word_pool_box = render_word_pool_container(content=pool_preview)

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


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Data load and transform
    """)
    return


@app.function
def list_question_files(
    pair: str | None, pyodide_files_by_pair: dict[str, list[str]]
) -> list[str]:
    """Lists selectable JSON files for a language pair with safe fallbacks."""
    if not pair:
        return ["questions.json"]

    if "pyodide" in sys.modules:
        files = pyodide_files_by_pair.get(pair, ["questions.json"])
        unique_files = sorted(set(files))
        return unique_files or ["questions.json"]

    pair_dir = mo.notebook_location() / "public" / pair
    if pair_dir.exists():
        file_names = sorted(
            path.name for path in pair_dir.glob("*.json") if path.is_file()
        )
        if file_names:
            return file_names

    return ["questions.json"]


@app.function
def humanize_question_file_name(filename: str) -> str:
    stem = filename.removesuffix(".json")
    return stem.replace("_", " ")


@app.function
def load_json_data(pair: str, filename: str) -> list[dict[str, Any]]:
    """Loads curriculum JSON data from Pyodide or local filesystem."""
    if "pyodide" in sys.modules:
        from pyodide.http import open_url

        url = f"../public/{pair}/{filename}"
        return json.loads(open_url(url).read())
    else:
        file_path = mo.notebook_location() / "public" / pair / filename
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


@app.function
def load_curriculum(data: list[dict[str, Any]]) -> pl.DataFrame:
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
    session_size: int = 10,
    session_id: int | None = None,
) -> pl.DataFrame:
    """Filters and materializes a shuffled session of UI-ready rows."""
    _ = session_id  # kept as a reactive trigger for new sessions
    if df.height == 0:
        return df

    filtered_df = df.filter(pl.col("difficulty_str").is_in(difficulty_list))

    if filtered_df.height == 0:
        return filtered_df

    rng = random.Random()

    if direction_mode == "l1_to_l2":
        directions = ["l1_to_l2"] * filtered_df.height
    elif direction_mode == "l2_to_l1":
        directions = ["l2_to_l1"] * filtered_df.height
    else:
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

    rng.shuffle(prepared_rows)
    if len(prepared_rows) <= session_size:
        return pl.DataFrame(prepared_rows)
    return pl.DataFrame(prepared_rows[:session_size])


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Other functions
    """)
    return


@app.function
def make_word_pool(lang_data: dict[str, Any]) -> list[str]:
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
                "word_pool_l1": make_word_pool(lang_data=lang_1_data),
                "word_pool_l2": make_word_pool(lang_data=lang_2_data),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame([])


@app.function
def get_sentence(df: pl.DataFrame, row_number: int) -> dict[str, Any] | None:
    if df.height == 0:
        return None

    valid_row = max(0, min(row_number, df.height - 1))
    return df.row(valid_row, named=True)


@app.function
def normalize_text(text: str) -> str:
    """Removes punctuation and lowercase the text."""
    if not text:
        return ""

    # Drop parenthetical clarifiers (e.g. "deze (enkelvoud)" -> "deze")
    # so one-word answers compare correctly against word forms.
    no_parentheses = re.sub(r"\s*\([^)]*\)", "", str(text))
    normalized = no_parentheses.lower().translate(
        str.maketrans("", "", string.punctuation)
    )
    return " ".join(normalized.split())


@app.function
def check_answer(user_answer: list[str], target: str, accepted: list[str]) -> bool:
    """Checks if the assembled words match the target sentence or accepted alternatives."""
    user_str = normalize_text(text=" ".join(user_answer))
    target_str = normalize_text(text=target)
    accepted_strs = [normalize_text(text=a) for a in (accepted or [])]

    return user_str == target_str or user_str in accepted_strs


@app.function
def sort_words(words: list[str]) -> list[str]:
    return sorted(words, key=lambda w: w.lower())


@app.function
def style_card(
    *,
    accent_edge: str | None = None,
) -> dict[str, str]:
    style = {
        "padding": "var(--la-space-section)",
        "margin": "var(--la-space-card-margin)",
        "border-radius": "var(--la-radius-lg)",
        "background": "var(--la-bg-surface)",
        "border": "1px solid var(--la-border-subtle)",
        "box-sizing": "border-box",
    }
    if accent_edge:
        style["border-right"] = f"5px solid {accent_edge}"
        style["border-bottom"] = f"5px solid {accent_edge}"
    return style


@app.function
def style_stat_box() -> dict[str, str]:
    return {
        "width": "100%",
        "padding": ".5rem",
        "border-radius": "var(--la-radius-md)",
        "background": "var(--la-bg-surface)",
        "border": "1px solid var(--la-border-subtle)",
        "box-sizing": "border-box",
        "text-align": "center",
    }


@app.function
def style_feedback_chip(
    *, border: str, background: str, foreground: str
) -> dict[str, str]:
    return {
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


@app.function
def style_word_pool_box() -> dict[str, str]:
    return {
        # "margin": "0.5rem 0",
        "padding": "1rem",
        "border": "1px solid var(--la-border-subtle)",
        "border-radius": "var(--la-radius-pool)",
        "background": "var(--la-accent-primary-soft)",
        "overflow-y": "hidden",
        "box-sizing": "border-box",
        "width": "100%",
        "display": "flex",
        "justify-content": "center",
    }


@app.function
def feedback_chip(
    text: str, *, border: str, background: str, foreground: str
) -> mo.Html:
    """Creates a compact pill-like feedback chip."""
    return (
        mo.md(text)
        .center()
        .style(
            style_feedback_chip(
                border=border,
                background=background,
                foreground=foreground,
            )
        )
    )


@app.function
def success_chip(text: str) -> mo.Html:
    return feedback_chip(
        text=text,
        border="var(--la-success-border)",
        background="var(--la-success-bg)",
        foreground="var(--la-success-fg)",
    )


@app.function
def warn_chip(text: str) -> mo.Html:
    return feedback_chip(
        text=text,
        border="var(--la-warning-border)",
        background="var(--la-warning-bg)",
        foreground="var(--la-warning-fg)",
    )


@app.function
def neutral_chip(text: str) -> mo.Html:
    return feedback_chip(
        text=text,
        border="var(--la-neutral-border)",
        background="var(--la-neutral-bg)",
        foreground="var(--la-neutral-fg)",
    )


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Render ui functions
    """)
    return


@app.function
def render_no_questions_element() -> mo.Html:
    return mo.callout(
        mo.md(
            "### No questions found\n"
            "Go back to settings and adjust language pair, direction, or difficulty."
        ).center(),
        kind="warn",
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
    ).style(style_stat_box())


@app.function
def render_difficulty_indicator(difficulty_int: int, difficulty_str: str) -> mo.Html:
    """Renders difficulty as a full-width centered stat card."""
    return render_stat_box(
        value=f"{difficulty_int}/10",
        label="Difficulty",
        caption=str(difficulty_str).capitalize(),
    )


@app.function
def render_score(correct: int, tries: int) -> mo.Html:
    """Renders the current session score as a full-width centered stat card."""
    return render_stat_box(
        value=f"{correct}/{tries}", label="Correct", caption="Attempts"
    )


@app.function
def render_progress(current_idx: int, total_count: int) -> mo.Html:
    """Renders question progress as a full-width centered stat card."""
    return render_stat_box(
        value=f"{current_idx + 1}/{total_count}",
        label="Question",
        caption="Progress",
    )


@app.function
def render_question_area(source: str) -> mo.Html:
    """Renders the main question prompt."""
    return mo.vstack(
        [
            mo.md("**Translate this sentence:**").center(),
            mo.md(f"### {source}").center(),
        ]
    ).style({"margin-top": "1rem"})


@app.function
def render_answer_area(ui_answer: mo.Html) -> mo.Html:
    return mo.vstack(
        [mo.md("**Your answer:**").center(), ui_answer, mo.md("---")]
    ).style({"margin-top": "1rem"})


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

    def handle_chip_click(click_count: int, i: int = idx) -> int:
        on_click(i, is_pool)
        return click_count + 1

    return mo.ui.button(
        label=word,
        value=0,
        on_click=handle_chip_click,
        kind="neutral",
        tooltip="Click to add" if is_pool else "Click to remove",
        disabled=disabled,
    )


@app.function
def render_answer_chips(
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
        make_word_chip(word=words[idx], idx=idx, on_click=on_click, is_pool=False)
        for idx in indices
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
            word=words[idx],
            idx=idx,
            on_click=on_click,
            is_pool=True,
            disabled=idx in disabled,
        )
        for idx in range(len(words))
    ]
    return mo.hstack(chips, justify="center", gap=1, wrap=True)


@app.function
def render_word_pool_container(content: mo.Html) -> mo.Html:
    """Renders the word pool inside a compact bordered container."""
    return mo.vstack([content], gap=0).style(style_word_pool_box())


@app.cell
def _():
    # def render_feedback(check_value: bool | None) -> mo.Html:
    #     """Renders feedback based on the check result."""
    #     if check_value is None:
    #         return neutral_chip(text="Press the button to check your answer")
    #     elif check_value:
    #         return success_chip(text="Correct! Continue to the next question.")
    #     else:
    #         return warn_chip(text="False, continue or try again")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Render ui - non reusable
    """)
    return


@app.cell
def _(
    button_start_questions,
    dropdown_difficulty,
    dropdown_language_pairs,
    dropdown_question_file,
    dropdown_translation_direction,
):
    def render_options_section() -> mo.Html:
        """Renders the initial configuration UI."""
        instruction_text = mo.md(
            "Choose the language and difficulty level, then press start to begin! If you only want to practice sentences in one dirrection, choose the direction too."
        ).center()

        options_row = mo.hstack(
            [
                dropdown_language_pairs,
                dropdown_question_file,
                dropdown_translation_direction,
                dropdown_difficulty,
            ],
            justify="space-between",
            wrap=True,
        )

        return mo.vstack(
            [instruction_text, options_row, button_start_questions.center()], gap=1
        ).style(
            style_card(
                accent_edge="var(--la-accent-secondary-soft)",
            )
        )

    return (render_options_section,)


@app.cell
def _(current_sentence, df, row_number):
    # stats = button_check_answer.value


    def render_stats() -> mo.Html:
        return mo.hstack(
            [
                render_difficulty_indicator(
                    difficulty_int=current_sentence["difficulty"],
                    difficulty_str=current_sentence["difficulty_str"],
                ),
                # render_score(correct=stats["correct"], tries=stats["tries"]),
                render_progress(current_idx=row_number, total_count=len(df)),
            ],
            widths="equal",
        )

    return (render_stats,)


@app.cell
def _():
    # def render_answer_button_set() -> mo.Html:
    #     return mo.hstack(
    #         [
    #             # button_check_answer,
    #             button_reset,
    #             button_reveal,
    #         ],
    #         justify="center",
    #     ).style({"margin-top": "1rem"})
    return


@app.cell
def _(button_next, button_prev):
    def render_navigation_buttons():
        return mo.hstack([button_prev, button_next]).style({"margin-top": "1rem"})

    return (render_navigation_buttons,)


@app.cell
def _(current_sentence, render_navigation_buttons, render_stats, widget):
    def render_interaction_section() -> mo.Html:
        # session_score = button_check_answer.value
        # answer_indices = get_answer_pool_by_question().get(active_question_key, [])
        # feedback_value = session_score["last_result"] if answer_indices else None
        # # Core Exercise
        # answer_text = (
        #     f"**Answer:** {current_sentence['target']}" if current_sentence else ""
        # )
        # if current_sentence and current_sentence.get("accepted"):
        #     answer_text += f"<br/>*Or:* {' / '.join(current_sentence['accepted'])}"

        # reveal_text = (
        #     mo.md(answer_text).center()
        #     if button_reveal.value and current_sentence
        #     else mo.md("&nbsp;")
        # )

        interaction_section = mo.vstack(
            [
                render_stats(),
                render_question_area(source=current_sentence["source"]),
                # render_answer_area(ui_answer=ui_answer),
                # render_word_pool_container(content=pool_chips_ui),
                # render_answer_button_set(),
                # reveal_text,
                # mo.hstack(
                #     [
                #         render_feedback(check_value=feedback_value),
                #     ],
                #     justify="center",
                # ),
                widget,
                render_navigation_buttons(),
            ],
            gap=0.0,
        ).style(
            style_card(
                accent_edge="var(--la-accent-primary-soft)",
            )
        )
        return interaction_section

    return (render_interaction_section,)


@app.cell
def _(button_back_to_settings):
    def render_footer() -> mo.Html:
        return mo.vstack([button_back_to_settings.center()]).style(
            style_card(
                accent_edge="var(--la-accent-secondary-soft)",
            )
        )

    return (render_footer,)


@app.cell
def _(button_back_to_settings, button_restart_session, stats, total_questions):
    def render_summary_section() -> mo.Html:
        # stats = button_check_answer.value
        attempts = stats["tries"]
        correct = stats["correct"]
        incorrect = max(0, attempts - correct)
        accuracy = f"{(correct / attempts * 100):.0f}%" if attempts > 0 else "0%"

        summary_stats = mo.hstack(
            [
                render_stat_box(
                    value=str(total_questions),
                    label="Total questions",
                    caption="Session size",
                ),
                render_stat_box(
                    value=str(attempts),
                    label="Attempts",
                    caption="Answers checked",
                ),
                render_stat_box(
                    value=str(correct),
                    label="Correct",
                    caption="Correct answers",
                ),
                render_stat_box(
                    value=str(incorrect),
                    label="Incorrect",
                    caption="Needs review",
                ),
                render_stat_box(
                    value=accuracy,
                    label="Accuracy",
                    caption="Session result",
                ),
            ],
            widths="equal",
        )

        actions = mo.hstack(
            [button_restart_session, button_back_to_settings],
            justify="center",
        )

        return mo.vstack(
            [
                mo.md("## Session complete").center(),
                summary_stats,
                actions,
            ],
            gap=0.8,
        ).style(style_card(accent_edge="var(--la-accent-secondary-soft)"))

    return (render_summary_section,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## State updaters
    """)
    return


@app.cell
def _(active_question_key, get_answer_pool_by_question, set_answer_pool):
    def move_word(index: int, to_answer: bool) -> None:
        # Read current answer pool to keep callback reactivity wired in marimo.
        _ = get_answer_pool_by_question()
        # Adds or removes the clicked word index from the active answer pool.
        if to_answer:
            set_answer_pool(
                active_question_key, lambda a: a + [index] if index not in a else a
            )
        else:
            set_answer_pool(active_question_key, lambda a: [i for i in a if i != index])

    return (move_word,)


if __name__ == "__main__":
    app.run()
