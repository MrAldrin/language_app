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

__generated_with = "0.22.0"
app = marimo.App(width="full", layout_file="layouts/language_app.grid.json")

with app.setup:
    import marimo as mo
    import json
    import polars as pl
    import random
    import sys
    import anywidget
    import traitlets
    from typing import Any


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # testing out anywidget
    """)
    return


@app.class_definition
class QuestionWidget(anywidget.AnyWidget):
    _esm = r"""
        import Sortable from "https://esm.sh/sortablejs@1.15.7";

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
                let feedbackPhase = "idle";
                // ADDED: reveal is independent of phase - user can toggle it any time
                let revealed = false;

                function setIdleAndRedraw() {
                    phase = "idle";
                    redraw();
                }

                function redraw() {
                    const words = model.get("words");
                    const target = model.get("target");
                    const accepted = model.get("accepted");
                    const questionType = model.get("question_type");
                    const prompt = model.get("prompt") || "";
                    const sourceHint = model.get("source_hint") || "";
                    const hiddenIndex = model.get("hidden_index");

                    function on(selector, event, handler) {
                        const node = el.querySelector(selector);
                        if (node) node.addEventListener(event, handler);
                    }

                    let questionHeaderHtml = "";
                    if (questionType === "cloze_word_choice") {
                        questionHeaderHtml = `<strong>Fill in the blank:</strong>`;
                    } else {
                        questionHeaderHtml = `<strong>Translate this sentence:</strong>`;
                    }

                    const promptHtml = questionType !== "cloze_word_choice" 
                        ? `<div class="question-text">${prompt}</div>` 
                        : "";

                    const hintHtml = sourceHint 
                        ? `<div class="question-hint"><em>Hint: ${sourceHint}</em></div>` 
                        : "";

                    const questionAreaHtml = `
                        <div class="question-container">
                            <div class="question-header">${questionHeaderHtml}</div>
                            ${promptHtml}
                            ${hintHtml}
                        </div>
                    `;

                    let answerHtml = "";
                    if (questionType === "cloze_word_choice" && hiddenIndex !== -1) {
                        // CLOZE RENDERING: Render prompt with a blank space
                        const promptWords = prompt.split(/\s+/);
                        answerHtml = `<div class="question-text">`;
                        promptWords.forEach((pw, i) => {
                            if (i === hiddenIndex) {
                                const val = answerIndices.length > 0 ? words[answerIndices[0]] : "";
                                const cls = val ? "cloze-filled" : "cloze-blank";
                                answerHtml += `<span class="cloze-slot ${cls}">${val || "&nbsp;&nbsp;&nbsp;&nbsp;"}</span> `;
                            } else {
                                answerHtml += `<span>${pw}</span> `;
                            }
                        });
                        answerHtml += `</div>`;
                    } else {
                        // SENTENCE BUILDER RENDERING: Standard chip area
                        answerHtml = answerIndices.map(i =>
                            `<button class="control chip answer-chip" data-idx="${i}">${words[i]}</button>`
                        ).join("");
                        if (!answerHtml) {
                            answerHtml = "<span class='hint'>Click words below to build your answer</span>";
                        }
                    }

                    const poolHtml = words.map((word, i) => {
                        const isSelected = answerIndices.includes(i);
                        const isLocked = phase === "correct";
                        return `<button
                            class="control chip pool-chip ${isSelected || isLocked ? "chip-disabled" : ""}"
                            data-idx="${i}"
                            ${isSelected || isLocked ? "disabled" : ""}
                        >${word}</button>`;
                    }).join("");

                    const feedbackByPhase = {
                        idle:    { cls: "feedback-neutral", text: "Press Check to validate your answer" },
                        wrong:   { cls: "feedback-wrong", text: "Not quite, continue or try again" },
                        correct: { cls: "feedback-correct", text: "Correct! Continue" },
                    };
                    const feedback = feedbackByPhase[feedbackPhase] || feedbackByPhase.idle;
                    const feedbackHtml = `<div class="feedback ${feedback.cls}">${feedback.text}</div>`;

                    const checkDisabled = answerIndices.length === 0 ? "disabled" : "";
                    const checkLabel = "Check";
                    const clearDisabled = (answerIndices.length === 0 && phase === "idle") ? "disabled" : "";

                    el.innerHTML = `
                        ${questionAreaHtml}
                        <div class="surface answer-area ${questionType === "cloze_word_choice" ? "answer-area-cloze" : ""}">
                            ${answerHtml}
                        </div>
                        <div class="surface pool-area">
                            ${poolHtml}
                        </div>
                        <div class="button-row">
                            <button class="control action-btn clear-btn" id="clear-btn" ${clearDisabled}>Clear</button>
                            <button class="control action-btn check-btn" id="check-btn" ${checkDisabled}>${checkLabel}</button>
                        </div>
                        ${feedbackHtml}
                        <div class="reveal-container">
                            <button class="reveal-toggle-btn" id="reveal-btn">
                                ${revealed 
                                    ? `<div class="reveal-content">
                                         <div class="reveal-main">${target}</div>
                                         ${accepted.length > 0 ? `<div class="reveal-sub">Also: ${accepted.join(", ")}</div>` : ""}
                                       </div>` 
                                    : "Reveal answer"
                                }
                            </button>
                        </div>
                    `;

                    // chip handlers - only when not locked
                    if (phase !== "correct") {
                        if (questionType !== "cloze_word_choice") {
                            const answerAreaEl = el.querySelector(".answer-area");

                            const updateIndicesFromDOM = () => {
                                const newAnswerIndices = [];
                                answerAreaEl.querySelectorAll('.chip:not(.sortable-ghost)').forEach(btn => {
                                    const idx = parseInt(btn.dataset.idx);
                                    if (!isNaN(idx)) {
                                        newAnswerIndices.push(idx);
                                    }
                                });
                                answerIndices = newAnswerIndices;
                                setIdleAndRedraw();
                            };

                            if (answerAreaEl) {
                                Sortable.create(answerAreaEl, {
                                    animation: 150,
                                    filter: '.hint',
                                    ghostClass: 'sortable-ghost',
                                    onEnd: updateIndicesFromDOM
                                });
                            }
                        }

                        el.querySelectorAll(".answer-chip").forEach(btn => {
                            btn.addEventListener("click", () => {
                                const pos = answerIndices.indexOf(parseInt(btn.dataset.idx));
                                if (pos !== -1) answerIndices.splice(pos, 1);
                                setIdleAndRedraw();
                            });
                        });
                        // Also allow clicking the cloze slot to clear it
                        el.querySelectorAll(".cloze-slot").forEach(slot => {
                            slot.addEventListener("click", () => {
                                answerIndices = [];
                                setIdleAndRedraw();
                            });
                        });

                        el.querySelectorAll(".pool-chip").forEach(btn => {
                            btn.addEventListener("click", () => {
                                if (btn.classList.contains("chip-disabled")) return;
                                if (questionType === "cloze_word_choice") {
                                    // Single selection for cloze
                                    answerIndices = [parseInt(btn.dataset.idx)];
                                } else {
                                    // Multiple for sentence builder
                                    answerIndices.push(parseInt(btn.dataset.idx));
                                }
                                setIdleAndRedraw();
                            });
                        });
                    }

                    on("#clear-btn", "click", () => {
                        answerIndices = [];
                        setIdleAndRedraw();
                    });

                    on("#reveal-btn", "click", () => {
                        revealed = !revealed;
                        redraw();
                    });

                    on("#check-btn", "click", () => {
                        const isCorrect = checkAnswer(answerIndices, words, target, accepted);

                        model.set("correct", isCorrect);
                        model.save_changes();

                        phase = isCorrect ? "correct" : "wrong";
                        feedbackPhase = phase;
                        if (isCorrect) {
                            revealed = true;
                        }
                        redraw();
                    });
                }

            model.on("change:words", () => {
                answerIndices = [];
                phase = "idle";
                feedbackPhase = "idle";
                // ADDED: hide reveal when Python pushes a new question
                revealed = false;
                redraw();
            });

            redraw();
        }
        export default { render };
    """

    _css = """
        .question-container {
            text-align: center;
            margin-bottom: 1rem;
            margin-top: 0.5rem;
        }
        .question-header {
            font-size: 0.9rem;
            color: #475569;
            margin-bottom: 0.25rem;
        }
        .question-text {
            font-size: 1.1rem;
            line-height: 1.6;
            color: #1e293b;
            text-align: center;
            margin: 0.5rem 0;
        }
        .question-hint {
            font-size: 0.95rem;
            color: #64748b;
            margin-top: 0.25rem;
        }
        .surface {
            border-radius: 0.75rem;
            padding: 0.75rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            justify-content: center;
        }
        .answer-area {
            min-height: 4rem;
            margin-bottom: 0.5rem;
            border: 1px dashed #8ea3b8;
            align-items: center;
            padding-left: 0;
            padding-right: 0;
        }
        .answer-area-cloze {
            border: none;
            background: #f8fafc;
            border-radius: 0.75rem;
            padding: 1rem;
        }
        .cloze-slot {
            display: inline-block;
            min-width: 4rem;
            height: 2rem;
            border-bottom: 2px solid #8ea3b8;
            margin: 0 0.25rem;
            vertical-align: middle;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            line-height: 2rem;
        }
        .cloze-filled {
            border-bottom-color: #2e8b57;
            font-weight: 600;
        }
        .cloze-blank {
            background: #f1f5f9;
        }
        .pool-area {
            background: #e8f6f4;
        }
        .control {
            height: 2.25rem;
            padding: 0 0.8rem;
            border: 1px solid #8ea3b8;
            border-radius: 10px;
            font-size: 1rem;
            cursor: pointer;
            box-sizing: border-box;
        }
        .sortable-ghost {
            opacity: 0.4;
            background-color: #e2e8f0 !important;
        }
        .chip {
            background: #ffffff;
        }
        .answer-chip {
            cursor: grab;
        }
        .answer-chip:active {
            cursor: grabbing;
        }
        .chip:hover:not(.chip-disabled) {
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
            min-height: 2rem;
            box-sizing: border-box;
            width: 100%;
            max-width: 22rem;
            margin-left: auto;
            margin-right: auto;
        }
        .feedback-neutral {
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            color: #334155;
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
        .reveal-container {
            margin: 0.5rem auto 0;
            width: 100%;
            max-width: 22rem;
            display: flex;
            justify-content: center;
        }
        .reveal-toggle-btn {
            width: 100%;
            height: 3.5rem;
            padding: 0.4rem 1rem;
            border-radius: 0.75rem;
            border: 1px solid #cbd5e1;
            background: #f8fafc;
            color: #475569;
            cursor: pointer;
            font-size: 0.95rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
            overflow: hidden;
            box-sizing: border-box;
        }
        .reveal-toggle-btn:hover {
            background: #f1f5f9;
        }
        .reveal-main {
            font-weight: 600;
            color: #1e293b;
            text-align: center;
        }
        .reveal-sub {
            font-size: 0.8rem;
            opacity: 0.8;
            margin-top: 0.1rem;
            text-align: center;
        }
        .button-row {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 0.75rem;
        }
        .action-btn {
            min-width: 5rem;
            background: #f3f7fc;
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
    question_type = traitlets.Unicode("").tag(sync=True)
    prompt = traitlets.Unicode("").tag(sync=True)
    source_hint = traitlets.Unicode("").tag(sync=True)
    hidden_index = traitlets.Int(-1).tag(sync=True)

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
            question_type=current_sentence.get("question_type", ""),
            prompt=current_sentence.get("source", ""),
            source_hint=current_sentence.get("source_hint") or "",
            hidden_index=current_sentence.get("hidden_word_index", -1),
        )
        widget = mo.ui.anywidget(_widget)
    return (widget,)


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
    pyodide_question_files_by_pair = {
        pair: ["sentence_builder_questions.json"] for pair in raw_pairs
    }
    pyodide_question_files_by_pair["de_no"] = [
        "sentence_builder_questions.json",
        "word_translation_questions.json",
    ]
    pyodide_question_files_by_pair["nl_no"] = [
        "sentence_builder_questions.json",
        "word_translation_questions.json",
    ]
    return (pyodide_question_files_by_pair,)


@app.cell
def _():
    # Mirror language-level files available in deployment (pyodide mode).
    pyodide_question_files_by_language = {
        "de": ["cloze_word_choice_questions.json"],
        "nl": ["cloze_word_choice_questions.json"],
    }
    return (pyodide_question_files_by_language,)


@app.cell
def _(raw_pairs):
    available_languages = sorted(
        {lang for pair in raw_pairs for lang in pair.split("_")}
    )
    return (available_languages,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Read and process data
    """)
    return


@app.cell
def _(dropdown_question_file, selected_pair, source_language, target_language):
    _read_json_data = load_json_data(
        pair=selected_pair,
        filename=dropdown_question_file.value,
        target_language=target_language,
    )
    df_raw = load_curriculum(data=_read_json_data)
    df_canonical = transform_to_canonical(
        df=df_raw, language_1=source_language, language_2=target_language
    )
    return df_canonical, df_raw


@app.cell
def _(
    LANG_MAP,
    df_canonical,
    dropdown_difficulty,
    dropdown_translation_direction,
    source_language,
    start_session_id,
    target_language,
):
    direction_mode = resolve_direction_mode(
        selected_direction=dropdown_translation_direction.value,
        language_1=source_language,
        language_2=target_language,
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
    return


@app.cell
def _(button_next, df, in_question_view, row_number):
    total_questions = len(df)
    last_question_index = max(0, total_questions - 1)
    is_last_question = total_questions > 0 and row_number >= last_question_index
    show_summary_page = (
        in_question_view
        and total_questions > 0
        and button_next.value > last_question_index
    )
    return show_summary_page, total_questions


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Drop down menus
    """)
    return


@app.cell
def _(LANG_MAP, available_languages):
    source_options = {LANG_MAP.get(code, code): code for code in available_languages}
    default_source = (
        "no"
        if "no" in available_languages
        else (available_languages[0] if available_languages else "")
    )
    default_source_label = LANG_MAP.get(default_source, default_source)

    dropdown_source_language = mo.ui.dropdown(
        options=source_options,
        value=default_source_label,
        allow_select_none=False,
        label="Source language",
    )
    dropdown_source_language
    return (dropdown_source_language,)


@app.cell
def _(LANG_MAP, dropdown_source_language, raw_pairs):
    _source_language = dropdown_source_language.value or ""
    connected_targets = sorted(
        {
            b if a == _source_language else a
            for pair in raw_pairs
            for a, b in [pair.split("_")]
            if _source_language in {a, b}
        }
    )
    target_options = {LANG_MAP.get(code, code): code for code in connected_targets}
    if connected_targets:
        default_target = "nl" if "nl" in connected_targets else connected_targets[0]
        default_target_label = LANG_MAP.get(default_target, default_target)
    else:
        default_target_label = ""

    dropdown_target_language = mo.ui.dropdown(
        options=target_options,
        value=default_target_label,
        allow_select_none=False,
        label="Target language",
    )
    dropdown_target_language
    return (dropdown_target_language,)


@app.cell
def _(dropdown_source_language, dropdown_target_language):
    source_language = dropdown_source_language.value or ""
    target_language = dropdown_target_language.value or ""

    if not source_language or not target_language or source_language == target_language:
        selected_pair = None
    else:
        selected_pair = "_".join(sorted([source_language, target_language]))
    return selected_pair, source_language, target_language


@app.cell
def _(
    pyodide_question_files_by_language,
    pyodide_question_files_by_pair,
    selected_pair,
    target_language,
):
    pair = selected_pair
    file_names = list_question_files(
        pair=pair, pyodide_files_by_pair=pyodide_question_files_by_pair
    )
    cloze_files = list_language_question_files(
        language=target_language,
        pyodide_files_by_language=pyodide_question_files_by_language,
    )
    file_names = sorted(set(file_names + cloze_files))

    default_file = (
        "sentence_builder_questions.json"
        if "sentence_builder_questions.json" in file_names
        else file_names[0]
    )
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
def _(LANG_MAP, source_language, target_language):
    if not source_language or not target_language:
        directions = ["Not applicable"]
    else:
        name1 = LANG_MAP.get(source_language, source_language)
        name2 = LANG_MAP.get(target_language, target_language)
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
    return (dropdown_translation_direction,)


@app.cell
def _(df_raw, selected_pair):
    if selected_pair is None:
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
        return ["sentence_builder_questions.json"]

    if "pyodide" in sys.modules:
        files = pyodide_files_by_pair.get(pair, ["sentence_builder_questions.json"])
        unique_files = sorted(set(files))
        return unique_files or ["sentence_builder_questions.json"]

    pair_dir = mo.notebook_location() / "public" / pair
    if pair_dir.exists():
        file_names = sorted(
            path.name for path in pair_dir.glob("*.json") if path.is_file()
        )
        if file_names:
            return file_names

    return ["sentence_builder_questions.json"]


@app.function
def list_language_question_files(
    language: str | None, pyodide_files_by_language: dict[str, list[str]]
) -> list[str]:
    """Lists selectable JSON files for a language-level folder (e.g. cloze)."""
    if not language:
        return []

    if "pyodide" in sys.modules:
        files = pyodide_files_by_language.get(language, [])
        return sorted(set(files))

    lang_dir = mo.notebook_location() / "public" / language
    if lang_dir.exists():
        file_names = sorted(
            path.name for path in lang_dir.glob("*.json") if path.is_file()
        )
        return file_names

    return []


@app.function
def humanize_question_file_name(filename: str) -> str:
    stem = filename.removesuffix(".json")
    return stem.replace("_", " ")


@app.function
def load_json_data(
    pair: str | None, filename: str, target_language: str | None = None
) -> list[dict[str, Any]]:
    """Loads curriculum JSON data from Pyodide or local filesystem."""
    use_language_path = (
        filename == "cloze_word_choice_questions.json" and target_language
    )

    if "pyodide" in sys.modules:
        from pyodide.http import open_url

        if use_language_path:
            url = f"../public/{target_language}/{filename}"
        else:
            url = f"../public/{pair}/{filename}"
        return json.loads(open_url(url).read())
    else:
        if use_language_path:
            file_path = mo.notebook_location() / "public" / target_language / filename
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
                    "question_type": row.get("question_type", ""),
                    "response_mode": row.get("response_mode"),
                    "difficulty": row["difficulty"],
                    "difficulty_str": row["difficulty_str"],
                    "direction": direction,
                    "source": row.get("prompt_l1", row["text_l1"]),
                    "source_hint": row.get("hint_l1"),
                    "target": row["text_l2"],
                    "accepted": row["accepted_l2"],
                    "words": row["word_pool_l2"],
                    "hidden_word_index": row.get("hidden_word_index", -1),
                }
            )
        else:
            prepared_rows.append(
                {
                    "question_id": row["question_id"],
                    "question_type": row.get("question_type", ""),
                    "response_mode": row.get("response_mode"),
                    "difficulty": row["difficulty"],
                    "difficulty_str": row["difficulty_str"],
                    "direction": direction,
                    "source": row.get("prompt_l2", row["text_l2"]),
                    "source_hint": row.get("hint_l2"),
                    "target": row["text_l1"],
                    "accepted": row["accepted_l1"],
                    "words": row["word_pool_l1"],
                    "hidden_word_index": row.get("hidden_word_index", -1),
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
def extract_translation_fields(lang_data: dict[str, Any]) -> dict[str, Any]:
    """Normalizes translation fields across schema versions."""
    primary = lang_data.get("primary", "")
    prompt = lang_data.get("prompt", primary)
    answer = lang_data.get("answer", primary)
    hint = lang_data.get("hint")

    if not isinstance(prompt, str):
        prompt = str(prompt) if prompt is not None else ""
    if not isinstance(answer, str):
        answer = str(answer) if answer is not None else ""
    if not isinstance(hint, str) or not hint.strip():
        hint = None

    return {"prompt": prompt, "answer": answer, "hint": hint}


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
        question_type = row.get("question_type", "")
        content = row.get("content") if isinstance(row.get("content"), dict) else {}

        if question_type == "cloze_word_choice":
            practice_language = content.get("practice_language") or language_2
            practice_data = translations.get(practice_language)
            if not practice_data and len(translations) == 1:
                practice_data = next(iter(translations.values()))

            if not practice_data:
                continue

            practice_fields = extract_translation_fields(practice_data)
            rows.append(
                {
                    "question_id": row.get("id", index),
                    "question_type": question_type,
                    "schema_version": row.get("schema_version"),
                    "response_mode": content.get("response_mode"),
                    "difficulty": row["difficulty"],
                    "difficulty_str": row["difficulty_str"],
                    "language_1": language_1,
                    "language_2": language_2,
                    # Keep both sides aligned for cloze so direction does not drop rows.
                    "prompt_l1": practice_fields["prompt"],
                    "prompt_l2": practice_fields["prompt"],
                    "text_l1": practice_fields["answer"],
                    "text_l2": practice_fields["answer"],
                    "hint_l1": extract_translation_fields(
                        translations.get(language_1, {})
                    ).get("prompt")
                    or practice_fields["hint"],
                    "hint_l2": extract_translation_fields(
                        translations.get(language_1, {})
                    ).get("prompt")
                    or practice_fields["hint"],
                    "accepted_l1": practice_data.get("accepted", []),
                    "accepted_l2": practice_data.get("accepted", []),
                    "word_pool_l1": make_word_pool(lang_data=practice_data),
                    "word_pool_l2": make_word_pool(lang_data=practice_data),
                    "hidden_word_index": practice_data.get("hidden_word_index", -1),
                }
            )
            continue

        lang_1_data = translations.get(language_1)
        lang_2_data = translations.get(language_2)

        if not lang_1_data or not lang_2_data:
            continue

        lang_1_fields = extract_translation_fields(lang_1_data)
        lang_2_fields = extract_translation_fields(lang_2_data)

        rows.append(
            {
                "question_id": row.get("id", index),
                "question_type": question_type,
                "schema_version": row.get("schema_version"),
                "response_mode": content.get("response_mode"),
                "difficulty": row["difficulty"],
                "difficulty_str": row["difficulty_str"],
                "language_1": language_1,
                "language_2": language_2,
                "prompt_l1": lang_1_fields["prompt"],
                "prompt_l2": lang_2_fields["prompt"],
                "text_l1": lang_1_fields["answer"],
                "text_l2": lang_2_fields["answer"],
                "hint_l1": lang_1_fields["hint"],
                "hint_l2": lang_2_fields["hint"],
                "accepted_l1": lang_1_data.get("accepted", []),
                "accepted_l2": lang_2_data.get("accepted", []),
                "word_pool_l1": make_word_pool(lang_data=lang_1_data),
                "word_pool_l2": make_word_pool(lang_data=lang_2_data),
                "hidden_word_index": -1,
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


@app.cell
def _(feedback_chip):
    def success_chip(text: str) -> mo.Html:
        return feedback_chip(
            text=text,
            border="var(--la-success-border)",
            background="var(--la-success-bg)",
            foreground="var(--la-success-fg)",
        )

    return


@app.cell
def _(feedback_chip):
    def warn_chip(text: str) -> mo.Html:
        return feedback_chip(
            text=text,
            border="var(--la-warning-border)",
            background="var(--la-warning-bg)",
            foreground="var(--la-warning-fg)",
        )

    return


@app.cell
def _(feedback_chip):
    def neutral_chip(text: str) -> mo.Html:
        return feedback_chip(
            text=text,
            border="var(--la-neutral-border)",
            background="var(--la-neutral-bg)",
            foreground="var(--la-neutral-fg)",
        )

    return


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
    dropdown_question_file,
    dropdown_source_language,
    dropdown_target_language,
    dropdown_translation_direction,
):
    def render_options_section() -> mo.Html:
        """Renders the initial configuration UI."""
        instruction_text = mo.md(
            "Choose source and target language, question set, and difficulty, then press start. You can also lock practice to one direction."
        ).center()

        options_row = mo.hstack(
            [
                dropdown_source_language,
                dropdown_target_language,
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
def _(button_next, button_prev):
    def render_navigation_buttons():
        return mo.hstack([button_prev, button_next]).style({"margin-top": "1rem"})

    return (render_navigation_buttons,)


@app.cell
def _(render_navigation_buttons, render_stats, widget):
    def render_interaction_section() -> mo.Html:
        interaction_section = mo.vstack(
            [
                render_stats(),
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
def _(button_back_to_settings, button_restart_session, total_questions):
    def render_summary_section() -> mo.Html:
        # stats = button_check_answer.value
        # attempts = stats["tries"]
        # correct = stats["correct"]
        # incorrect = max(0, attempts - correct)
        # accuracy = f"{(correct / attempts * 100):.0f}%" if attempts > 0 else "0%"

        summary_stats = mo.hstack(
            [
                render_stat_box(
                    value=str(total_questions),
                    label="Total questions",
                    caption="Session size",
                ),
                # render_stat_box(
                #     value=str(attempts),
                #     label="Attempts",
                #     caption="Answers checked",
                # ),
                # render_stat_box(
                #     value=str(correct),
                #     label="Correct",
                #     caption="Correct answers",
                # ),
                # render_stat_box(
                #     value=str(incorrect),
                #     label="Incorrect",
                #     caption="Needs review",
                # ),
                # render_stat_box(
                #     value=accuracy,
                #     label="Accuracy",
                #     caption="Session result",
                # ),
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


if __name__ == "__main__":
    app.run()
