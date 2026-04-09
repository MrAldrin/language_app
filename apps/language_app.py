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

__generated_with = "0.23.0"
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

    # Session-scoped score cache keyed by start_session_id.
    SESSION_SCORE_STORE: dict[int, dict[str, Any]] = {}
    SESSION_PENDING_LIFETIME_STORE: dict[int, dict[str, Any]] = {}
    LIFETIME_STATS_DEFAULT = {
        "total_attempts": 0,
        "total_correct": 0,
        "by_target_language": {},
        "available": False,
        "loaded": False,
        "error": "",
    }
    LIFETIME_STATS_CACHE: dict[str, Any] = LIFETIME_STATS_DEFAULT.copy()


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # UI
    """)
    return


@app.cell
def _(
    app_theme_styles,
    current_sentence,
    in_question_view,
    render_interaction_section,
    render_lifetime_stats_section,
    render_options_section,
    render_summary_section,
    show_summary_page,
):
    def render_main_ui() -> mo.Html:
        """Assembles the final application layout."""

        app_header = mo.Html(
            """
            <div class="app-title">
              <h1>Schipper mag ik overvaren?</h1>
            </div>
            """
        )
        question_active_marker = (
            [mo.Html('<div class="question-active-marker" aria-hidden="true"></div>')]
            if in_question_view and not show_summary_page
            else []
        )

        mo_elems = [app_theme_styles, *question_active_marker, app_header]
        if not in_question_view:
            mo_elems.append(render_options_section())
            mo_elems.append(render_lifetime_stats_section())
        elif show_summary_page:
            mo_elems.append(render_summary_section())
            mo_elems.append(render_lifetime_stats_section())
        else:
            if current_sentence:
                mo_elems.append(render_interaction_section())
            else:
                mo_elems.append(render_no_questions_element())
        return mo.vstack(mo_elems, gap=0)

    return (render_main_ui,)


@app.cell
def _(render_main_ui):
    render_main_ui()
    return


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
                let checkNonce = Number(model.get("check_nonce") || 0);

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

                    const promptHtml = questionType !== "cloze_word_choice" 
                        ? `<div class="question-text">${prompt}</div>` 
                        : "";

                    const hintHtml = (sourceHint && questionType !== "cloze_word_choice") 
                        ? `<div class="question-hint"><em>${sourceHint}</em></div>` 
                        : "";

                    const questionAreaHtml = `
                        <div class="question-container ${questionType === "cloze_word_choice" ? "question-container-cloze" : "question-container-translation"}">
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
                                const content = val 
                                    ? `<button class="control chip cloze-filled" style="display: inline-flex; pointer-events: none;">${val}</button>`
                                    : "&nbsp;&nbsp;&nbsp;&nbsp;";
                                answerHtml += `<span class="cloze-slot cloze-blank">${content}</span> `;
                            } else {
                                answerHtml += `<span>${pw}</span> `;
                            }
                        });
                        answerHtml += `</div>`;
                        if (sourceHint) {
                            answerHtml += `<div class="question-hint" "><em>${sourceHint}</em></div>`;
                        }
                    } else {
                        // SENTENCE BUILDER RENDERING: Standard chip area
                        const isLocked = phase === "correct";
                        answerHtml = answerIndices.map(i =>
                            `<button
                                class="control chip answer-chip ${isLocked ? "chip-disabled" : ""}"
                                data-idx="${i}"
                                ${isLocked ? "disabled" : ""}
                            >${words[i]}</button>`
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

                    const isLocked = phase === "correct";
                    const checkDisabled = (answerIndices.length === 0 || isLocked) ? "disabled" : "";
                    const checkLabel = "Check";
                    const clearDisabled = ((answerIndices.length === 0 && phase === "idle") || isLocked) ? "disabled" : "";
                    const revealDisabled = isLocked ? "disabled" : "";

                    el.innerHTML = `
                        <div class="question-shell">
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
                                <button class="reveal-toggle-btn" id="reveal-btn" ${revealDisabled}>
                                    ${revealed 
                                        ? `<div class="reveal-content">
                                             <div class="reveal-main">${target}</div>
                                             ${accepted.length > 0 ? `<div class="reveal-sub">Also: ${accepted.join(", ")}</div>` : ""}
                                           </div>` 
                                        : "Reveal answer"
                                    }
                                </button>
                            </div>
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
                        // Also allow clicking the cloze slot or filled pill to clear it
                        el.querySelectorAll(".cloze-slot, .cloze-filled").forEach(slot => {
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
                        if (phase === "correct") return;
                        answerIndices = [];
                        setIdleAndRedraw();
                    });

                    on("#reveal-btn", "click", () => {
                        if (phase === "correct") return;
                        revealed = !revealed;
                        redraw();
                    });

                    on("#check-btn", "click", () => {
                        if (phase === "correct") return;
                        if (answerIndices.length === 0) return;
                        const isCorrect = checkAnswer(answerIndices, words, target, accepted);
                        checkNonce += 1;

                        model.set("check_nonce", checkNonce);
                        model.set("last_check_correct", isCorrect);
                        model.set("last_check_question_id", String(model.get("question_id") || ""));
                        model.save_changes();

                        phase = isCorrect ? "correct" : "wrong";
                        feedbackPhase = phase;
                        if (isCorrect) {
                            revealed = true;
                        }
                        redraw();
                    });
                }

            function resetForNewQuestion() {
                answerIndices = [];
                phase = "idle";
                feedbackPhase = "idle";
                // ADDED: hide reveal when Python pushes a new question
                revealed = false;
                checkNonce = 0;
                redraw();
            }

            model.on("change:words", resetForNewQuestion);
            model.on("change:question_id", resetForNewQuestion);

            redraw();
        }
        export default { render };
    """

    _css = """
        .question-container {
            text-align: center;
            width: 100%;
            margin: 1rem auto 0;
            box-sizing: border-box;
        }
        .question-container-translation {
            margin-bottom: 0.2rem;
        }
        .question-shell {
            width: 100%;
            max-width: var(--la-max-width-interaction, 100%);
            margin-left: auto;
            margin-right: auto;
            box-sizing: border-box;
        }
        .question-shell > * {
            box-sizing: border-box;
        }
        .question-text {
            font-size: 1.25rem;
            line-height: 1.6;
            color: var(--la-text-main, #1e293b);
            text-align: center;
            margin: 0;
        }
        .question-hint {
            font-size: 0.95rem;
            color: var(--la-text-muted, #64748b);
            margin-top: 0;
        }
        .question-shell .question-text,
        .question-shell .question-hint,
        .question-shell .surface,
        .question-shell .button-row {
            width: 100%;
            max-width: var(--la-max-width-controls, 100%);
            margin-left: auto;
            margin-right: auto;
        }
        .question-shell .question-text {
            max-width: 34rem;
        }
        .question-shell .question-hint {
            max-width: 30rem;
        }
        .surface {
            border-radius: 0.75rem;
            padding: 0.55rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            justify-content: center;
        }
        .answer-area {
            min-height: 4rem;
            margin-bottom: 0.2rem;
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .question-shell .answer-area {
            max-width: min(var(--la-max-width-controls, 100%), 38rem);
        }
        .answer-area-cloze {
            flex-direction: column;
            padding: 0.75rem;
        }
        .cloze-slot {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 5rem;
            height: 2.5rem;
            border-bottom: 2px solid var(--la-neutral-border, #8ea3b8);
            margin: 0 0.25rem;
            vertical-align: middle;
            cursor: pointer;
        }
        .cloze-blank {
            border-radius: 0.25rem 0.25rem 0 0;
        }
        .pool-area {
            background: var(--la-accent-primary-soft, #e8f6f4);
        }
        .question-shell .pool-area {
            max-width: min(var(--la-max-width-controls, 100%), 44rem);
        }
        .control {
            height: 2.25rem;
            padding: 0 0.8rem;
            border: 1px solid var(--la-border-subtle, #d8e0ea);
            border-radius: 0.75rem;
            font-size: 1.25rem;
            cursor: pointer;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .sortable-ghost {
            opacity: 0.4;
            background-color: var(--la-border-subtle, #e2e8f0) !important;
        }
        .chip {
            background: var(--la-bg-surface, #ffffff);
            color: var(--la-text-main, #1e293b);
        }
        .answer-chip {
            cursor: grab;
        }
        .answer-chip:active {
            cursor: grabbing;
        }
        .answer-chip[disabled],
        .answer-chip.chip-disabled,
        .answer-chip.chip-disabled:active {
            cursor: default;
        }
        .chip:hover:not(.chip-disabled) {
            background: var(--la-accent-primary-soft, #e8f6f4);
        }
        .chip-disabled {
            opacity: 0.35;
            cursor: default;
        }
        .hint {
            color: var(--la-text-muted, #8ea3b8);
            font-style: italic;
            font-size: 0.9rem;
        }
        .feedback {
            margin: 0.5rem 0 0.15rem;
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            text-align: center;
            font-weight: 500;
            font-size: 0.95rem;
            min-height: 2rem;
            box-sizing: border-box;
            width: 100%;
            max-width: min(var(--la-max-width-controls, 100%), 28rem);
            margin-left: auto;
            margin-right: auto;
        }
        .feedback-neutral {
            background: var(--la-neutral-bg, #f1f5f9);
            border: 1px solid var(--la-neutral-border, #cbd5e1);
            color: var(--la-neutral-fg, #334155);
        }
        .feedback-wrong {
            background: var(--la-warning-bg, #fff0d8);
            border: 1px solid var(--la-warning-border, #c97b0e);
            color: var(--la-warning-fg, #704010);
        }
        .feedback-correct {
            background: var(--la-success-bg, #e5f7ee);
            border: 1px solid var(--la-success-border, #2e8b57);
            color: var(--la-success-fg, #145339);
        }
        .reveal-container {
            margin: 0.35rem auto 0;
            width: 100%;
            display: flex;
            max-width: min(var(--la-max-width-controls, 100%), 28rem);
            justify-content: center;
        }
        .action-btn, .reveal-toggle-btn {
            background: var(--la-bg-surface, #f8fafc);
            border: 1px solid var(--la-border-subtle, #cbd5e1);
            color: var(--la-text-main, #475569);
            font-size: 0.95rem;
            cursor: pointer;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .action-btn:hover:not([disabled]), .reveal-toggle-btn:hover:not([disabled]) {
            background: var(--la-accent-secondary-soft, #f1f5f9);
        }
        .reveal-toggle-btn {
            width: 100%;
            height: 3.5rem;
            padding: 0.35rem 0.8rem;
            border-radius: 0.75rem;
            flex-direction: column;
            overflow: hidden;
        }
        .reveal-main {
            font-weight: 600;
            color: var(--la-text-main, #1e293b);
            text-align: center;
        }
        .reveal-sub {
            font-size: 0.8rem;
            opacity: 0.8;
            margin-top: 0.1rem;
            text-align: center;
            color: var(--la-text-muted, #64748b);
        }
        .button-row {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.55rem;
        }
        .action-btn {
            min-width: 5rem;
        }
        .action-btn[disabled] {
            opacity: 0.35;
            cursor: default;
        }
        .reveal-toggle-btn[disabled] {
            opacity: 0.55;
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
    question_id = traitlets.Unicode("").tag(sync=True)

    # JS → Python (outputs)
    check_nonce = traitlets.Int(0).tag(sync=True)
    last_check_correct = traitlets.Bool(False).tag(sync=True)
    last_check_question_id = traitlets.Unicode("").tag(sync=True)


@app.class_definition
class LifetimeStatsStore(anywidget.AnyWidget):
    _esm = r"""
        const DB_NAME = "language-app-stats";
        const DB_VERSION = 1;
        const STORE_NAME = "kv";
        const STATS_KEY = "lifetime_stats";
        const DEFAULT_STATS = {
            total_attempts: 0,
            total_correct: 0,
            by_target_language: {},
        };

        function cloneStats(stats) {
            const rawByTargetLanguage =
                stats?.by_target_language && typeof stats.by_target_language === "object"
                    ? stats.by_target_language
                    : {};
            const byTargetLanguage = {};
            for (const [language, counts] of Object.entries(rawByTargetLanguage)) {
                byTargetLanguage[String(language)] = {
                    attempts: Number(counts?.attempts || 0),
                    correct: Number(counts?.correct || 0),
                };
            }
            return {
                total_attempts: Number(stats?.total_attempts || 0),
                total_correct: Number(stats?.total_correct || 0),
                by_target_language: byTargetLanguage,
            };
        }

        function setState(model, patch) {
            const current = model.get("state") || {};
            model.set("state", { ...current, ...patch });
            model.save_changes();
        }

        async function openDb() {
            if (!("indexedDB" in globalThis)) {
                throw new Error("IndexedDB is not available in this browser.");
            }

            return await new Promise((resolve, reject) => {
                const request = indexedDB.open(DB_NAME, DB_VERSION);
                request.onupgradeneeded = () => {
                    const db = request.result;
                    if (!db.objectStoreNames.contains(STORE_NAME)) {
                        db.createObjectStore(STORE_NAME);
                    }
                };
                request.onsuccess = () => resolve(request.result);
                request.onerror = () =>
                    reject(request.error || new Error("Failed to open IndexedDB."));
            });
        }

        async function readStats(db) {
            return await new Promise((resolve, reject) => {
                const tx = db.transaction(STORE_NAME, "readonly");
                const store = tx.objectStore(STORE_NAME);
                const request = store.get(STATS_KEY);
                request.onsuccess = () => {
                    resolve(cloneStats(request.result || DEFAULT_STATS));
                };
                request.onerror = () =>
                    reject(request.error || new Error("Failed to read lifetime stats."));
            });
        }

        async function writeStats(db, stats) {
            return await new Promise((resolve, reject) => {
                const tx = db.transaction(STORE_NAME, "readwrite");
                const store = tx.objectStore(STORE_NAME);
                const nextStats = cloneStats(stats);
                const request = store.put(nextStats, STATS_KEY);
                request.onsuccess = () => resolve(nextStats);
                request.onerror = () =>
                    reject(request.error || new Error("Failed to write lifetime stats."));
            });
        }

        function render({ model, el }) {
            el.style.display = "none";
            let dbPromise = null;
            let applying = false;
            let pending = false;

            async function getDb() {
                if (!dbPromise) {
                    dbPromise = openDb();
                }
                return await dbPromise;
            }

            async function loadInitialState() {
                try {
                    const db = await getDb();
                    const stats = await readStats(db);
                    setState(model, {
                        ...stats,
                        available: true,
                        loaded: true,
                        error: "",
                    });
                } catch (error) {
                    setState(model, {
                        ...DEFAULT_STATS,
                        available: false,
                        loaded: true,
                        error: error?.message || "Unable to use IndexedDB.",
                    });
                }
            }

            async function applyCommand() {
                if (applying) {
                    pending = true;
                    return;
                }
                applying = true;
                try {
                    const command = model.get("command") || {};
                    const commandType = String(command.type || "noop");
                    const commandNonce = Number(command.nonce || 0);
                    const lastAppliedNonce = Number(model.get("last_applied_nonce") || 0);

                    if (commandNonce <= 0 || commandNonce === lastAppliedNonce) {
                        return;
                    }

                    try {
                        const db = await getDb();
                        let nextStats = await readStats(db);

                        if (commandType === "flush_session_stats") {
                            const deltaTotalAttempts = Number(command.delta_total_attempts || 0);
                            const deltaTotalCorrect = Number(command.delta_total_correct || 0);
                            const deltaByTargetLanguage =
                                command.delta_by_target_language &&
                                typeof command.delta_by_target_language === "object"
                                    ? command.delta_by_target_language
                                    : {};

                            nextStats.total_attempts += deltaTotalAttempts;
                            nextStats.total_correct += deltaTotalCorrect;

                            for (const [targetLanguage, counts] of Object.entries(deltaByTargetLanguage)) {
                                const languageKey = String(targetLanguage || "").trim();
                                if (!languageKey) continue;
                                const currentLanguageStats =
                                    nextStats.by_target_language[languageKey] || {
                                        attempts: 0,
                                        correct: 0,
                                    };
                                currentLanguageStats.attempts += Number(counts?.attempts || 0);
                                currentLanguageStats.correct += Number(counts?.correct || 0);
                                nextStats.by_target_language[languageKey] =
                                    currentLanguageStats;
                            }
                        } else if (commandType === "reset") {
                            nextStats = { ...DEFAULT_STATS };
                        } else {
                            model.set("last_applied_nonce", commandNonce);
                            model.save_changes();
                            return;
                        }

                        const savedStats = await writeStats(db, nextStats);
                        model.set("last_applied_nonce", commandNonce);
                        setState(model, {
                            ...savedStats,
                            available: true,
                            loaded: true,
                            error: "",
                        });
                    } catch (error) {
                        model.set("last_applied_nonce", commandNonce);
                        setState(model, {
                            ...(model.get("state") || DEFAULT_STATS),
                            loaded: true,
                            available: false,
                            error: error?.message || "IndexedDB update failed.",
                        });
                    }
                } finally {
                    applying = false;
                    if (pending) {
                        pending = false;
                        void applyCommand();
                    }
                }
            }

            model.on("change:command", () => {
                void applyCommand();
            });

            void loadInitialState();
        }

        export default { render };
    """

    state = traitlets.Dict(LIFETIME_STATS_DEFAULT.copy()).tag(sync=True)
    command = traitlets.Dict({"type": "noop", "nonce": 0}).tag(sync=True)
    last_applied_nonce = traitlets.Int(0).tag(sync=True)


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
            question_id=str(current_sentence.get("question_id", "")),
        )
        widget = mo.ui.anywidget(_widget)
    return (widget,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # constants and state initiation
    """)
    return


@app.cell
def _():
    app_theme_styles = mo.Html('<link rel="stylesheet" href="public/styles.css">')
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
    available_languages = sorted({lang for pair in raw_pairs for lang in pair.split("_")})
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
    selected_focus_attributes,
    selected_focus_family,
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
        focus_attributes=selected_focus_attributes,
        focus_family=selected_focus_family,
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
def _(active_question_key, start_session_id, target_language, widget):
    session_state = SESSION_SCORE_STORE.setdefault(
        start_session_id,
        {
            "attempts": 0,
            "correct": 0,
            "last_processed_check_nonce": 0,
            "question_attempt_counts": {},
            "processed_event_keys": set(),
        },
    )

    widget_state = widget.value if widget is not None else {}
    check_nonce = int(widget_state.get("check_nonce", 0) or 0)
    last_check_correct = bool(widget_state.get("last_check_correct", False))
    last_check_question_id = str(widget_state.get("last_check_question_id", "") or "")
    event_question_key = last_check_question_id or active_question_key
    event_key = f"{event_question_key}:{check_nonce}"
    processed_new_attempt = False
    processed_attempt_correct = False

    if check_nonce > 0 and event_key not in session_state["processed_event_keys"]:
        session_state["attempts"] += 1
        if last_check_correct:
            session_state["correct"] += 1
        session_state["last_processed_check_nonce"] = check_nonce
        session_state["processed_event_keys"].add(event_key)
        counts = session_state["question_attempt_counts"]
        counts[event_question_key] = counts.get(event_question_key, 0) + 1
        processed_new_attempt = True
        processed_attempt_correct = last_check_correct

        session_pending_stats = SESSION_PENDING_LIFETIME_STORE.setdefault(
            start_session_id,
            {
                "pending_total_attempts": 0,
                "pending_total_correct": 0,
                "pending_by_target_language": {},
                "last_flushed_event_key": "",
            },
        )
        session_pending_stats["pending_total_attempts"] += 1
        if last_check_correct:
            session_pending_stats["pending_total_correct"] += 1
        target_key = str(target_language or "").strip()
        if target_key:
            per_language = session_pending_stats["pending_by_target_language"].setdefault(
                target_key,
                {"attempts": 0, "correct": 0},
            )
            per_language["attempts"] += 1
            if last_check_correct:
                per_language["correct"] += 1

    session_score = {
        "attempts": session_state["attempts"],
        "correct": session_state["correct"],
        "last_processed_check_nonce": session_state["last_processed_check_nonce"],
        "processed_new_attempt": processed_new_attempt,
        "processed_attempt_correct": processed_attempt_correct,
    }
    question_attempt_counts = dict(session_state["question_attempt_counts"])
    return (session_score,)


@app.cell
def _(
    button_main_menu,
    button_next,
    button_prev,
    button_restart_session,
    lifetime_reset_nonce,
    lifetime_stats_widget,
    show_summary_page,
    start_session_id,
):
    widget_payload = (
        lifetime_stats_widget.value if isinstance(lifetime_stats_widget.value, dict) else {}
    )
    last_applied_nonce = int(widget_payload.get("last_applied_nonce", 0) or 0)
    reset_command_nonce = 1_000_000 + int(lifetime_reset_nonce)
    flush_event_nonce = (
        int(button_next.value or 0)
        + int(button_prev.value or 0)
        + int(button_main_menu.value or 0)
        + int(button_restart_session.value or 0)
        + (1 if show_summary_page else 0)
    )
    flush_command_nonce = (
        2_000_000 + (int(start_session_id or 0) * 10_000) + flush_event_nonce
    )
    pending_lifetime_buffer = SESSION_PENDING_LIFETIME_STORE.setdefault(
        start_session_id,
        {
            "pending_total_attempts": 0,
            "pending_total_correct": 0,
            "pending_by_target_language": {},
            "last_flushed_event_key": "",
        },
    )
    flush_event_key = (
        f"{button_next.value}:{button_prev.value}:{button_main_menu.value}:"
        f"{button_restart_session.value}:{1 if show_summary_page else 0}"
    )
    has_pending = int(
        pending_lifetime_buffer.get("pending_total_attempts", 0) or 0
    ) > 0 or any(
        int((counts or {}).get("attempts", 0) or 0) > 0
        for counts in pending_lifetime_buffer.get("pending_by_target_language", {}).values()
    )

    if lifetime_reset_nonce > 0 and last_applied_nonce != reset_command_nonce:
        pending_lifetime_buffer["pending_total_attempts"] = 0
        pending_lifetime_buffer["pending_total_correct"] = 0
        pending_lifetime_buffer["pending_by_target_language"] = {}
        pending_lifetime_buffer["last_flushed_event_key"] = ""
        lifetime_stats_command = {
            "type": "reset",
            "nonce": reset_command_nonce,
        }
    elif (
        has_pending
        and flush_event_key != pending_lifetime_buffer.get("last_flushed_event_key", "")
        and flush_command_nonce != last_applied_nonce
    ):
        lifetime_stats_command = {
            "type": "flush_session_stats",
            "nonce": flush_command_nonce,
            "delta_total_attempts": int(
                pending_lifetime_buffer["pending_total_attempts"] or 0
            ),
            "delta_total_correct": int(
                pending_lifetime_buffer["pending_total_correct"] or 0
            ),
            "delta_by_target_language": dict(
                pending_lifetime_buffer.get("pending_by_target_language", {})
            ),
        }
        pending_lifetime_buffer["last_flushed_event_key"] = flush_event_key
    else:
        if flush_command_nonce == last_applied_nonce and has_pending:
            pending_lifetime_buffer["pending_total_attempts"] = 0
            pending_lifetime_buffer["pending_total_correct"] = 0
            pending_lifetime_buffer["pending_by_target_language"] = {}
        lifetime_stats_command = {"type": "noop", "nonce": 0}
    return (lifetime_stats_command,)


@app.cell
def _():
    lifetime_stats_store = LifetimeStatsStore()
    lifetime_stats_widget = mo.ui.anywidget(lifetime_stats_store)
    return lifetime_stats_store, lifetime_stats_widget


@app.cell
def _(lifetime_stats_command, lifetime_stats_store):
    lifetime_stats_store.command = lifetime_stats_command
    return


@app.cell
def _(lifetime_stats_widget):
    normalized_stats = normalize_lifetime_stats(lifetime_stats_widget.value)

    # Marimo reruns can briefly surface the widget's default trait values before the
    # browser-side anywidget re-syncs its latest IndexedDB-backed state. Keep the
    # last good loaded snapshot to avoid flashing back to zeros between syncs.
    if normalized_stats["loaded"]:
        LIFETIME_STATS_CACHE.update(normalized_stats)
        lifetime_stats = dict(LIFETIME_STATS_CACHE)
    elif LIFETIME_STATS_CACHE["loaded"]:
        lifetime_stats = dict(LIFETIME_STATS_CACHE)
    else:
        lifetime_stats = normalized_stats
    lifetime_stats = overlay_pending_lifetime_stats(lifetime_stats)
    return (lifetime_stats,)


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
def _(dropdown_question_file):
    selected_question_file = dropdown_question_file.value or ""
    direction_applicable = selected_question_file != "cloze_word_choice_questions.json"
    return (direction_applicable,)


@app.cell
def _(LANG_MAP, direction_applicable, source_language, target_language):
    if (not source_language) or (not target_language) or (not direction_applicable):
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


@app.cell
def _(df_raw):
    tag_options: list[str] = []
    family_options: list[str] = []
    family_to_attribute_options: dict[str, list[str]] = {}

    if "tags" in df_raw.columns:
        tag_options = (
            df_raw.select(pl.col("tags").explode().alias("tag"))
            .drop_nulls("tag")
            .with_columns(pl.col("tag").cast(pl.Utf8))
            .unique()
            .sort("tag")
            .get_column("tag")
            .to_list()
        )
        family_options = [tag for tag in tag_options if tag.startswith("family:")]

        if family_options:
            for family in family_options:
                family_to_attribute_options[family] = (
                    df_raw.filter(
                        pl.col("tags")
                        .is_not_null()
                        .and_(pl.col("tags").list.contains(family))
                    )
                    .select(pl.col("tags").explode().alias("tag"))
                    .drop_nulls("tag")
                    .filter(~pl.col("tag").str.starts_with("family:"))
                    .with_columns(pl.col("tag").cast(pl.Utf8))
                    .unique()
                    .sort("tag")
                    .get_column("tag")
                    .to_list()
                )
    return family_options, family_to_attribute_options


@app.cell
def _(family_options: list[str]):
    has_family_tags = len(family_options) > 0

    if has_family_tags:
        dropdown_focus_family = mo.ui.dropdown(
            options=family_options,
            value=family_options[0],
            allow_select_none=False,
            label="Family",
        )
    else:
        dropdown_focus_family = None
    return dropdown_focus_family, has_family_tags


@app.cell
def _(
    dropdown_focus_family,
    family_to_attribute_options: dict[str, list[str]],
    has_family_tags,
):
    if not has_family_tags or dropdown_focus_family is None:
        dropdown_focus_attributes = None
    else:
        _selected_family = (
            dropdown_focus_family.value
            if isinstance(dropdown_focus_family.value, str)
            else str(dropdown_focus_family.value or "")
        )
        _attribute_options = family_to_attribute_options.get(_selected_family, [])
        dropdown_focus_attributes = mo.ui.multiselect(
            options=_attribute_options,
            value=_attribute_options,
            label="Subtype / Attributes",
        )
    return (dropdown_focus_attributes,)


@app.cell
def _(dropdown_focus_attributes, dropdown_focus_family, has_family_tags):
    if has_family_tags and dropdown_focus_family is not None:
        focus_filter_controls = mo.hstack(
            [dropdown_focus_family, dropdown_focus_attributes], gap=0.5
        )
    else:
        focus_filter_controls = None
    return (focus_filter_controls,)


@app.cell
def _(
    dropdown_focus_attributes,
    dropdown_focus_family,
    family_to_attribute_options: dict[str, list[str]],
):
    if dropdown_focus_family is None:
        selected_focus_family = None
        selected_focus_attributes = []
    else:
        _selected_family = (
            dropdown_focus_family.value
            if isinstance(dropdown_focus_family.value, str)
            else str(dropdown_focus_family.value or "")
        )
        attribute_options = family_to_attribute_options.get(_selected_family, [])
        selected_attributes = [
            tag for tag in list(dropdown_focus_attributes.value) if tag in attribute_options
        ]
        selected_focus_family = _selected_family
        # If user clears all attributes, keep family-only filtering active.
        selected_focus_attributes = (
            selected_attributes if selected_attributes else attribute_options
        )
    return selected_focus_attributes, selected_focus_family


@app.cell
def _(
    direction_applicable,
    dropdown_translation_direction,
    focus_filter_controls,
):
    lower_level_controls: list[Any] = []
    if direction_applicable:
        lower_level_controls.append(dropdown_translation_direction)
    if focus_filter_controls is not None:
        lower_level_controls.append(focus_filter_controls)

    if lower_level_controls:
        lower_level_settings = mo.hstack(
            lower_level_controls,
            justify="center",
            wrap=False,
            gap=0.7,
        )
    else:
        lower_level_settings = None
    return (lower_level_settings,)


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
    button_main_menu = mo.ui.button(
        value=0,
        on_click=bump,
        label="Main menu",
    )
    button_restart_session = mo.ui.button(
        value=0,
        on_click=bump,
        label="Start new session",
    )
    button_request_reset_lifetime = mo.ui.button(
        value=0,
        on_click=bump,
        label="Reset lifetime stats",
        kind="warn",
    )
    button_confirm_reset_lifetime = mo.ui.button(
        value=0,
        on_click=bump,
        label="Confirm reset",
        kind="danger",
    )
    button_cancel_reset_lifetime = mo.ui.button(
        value=0,
        on_click=bump,
        label="Cancel",
    )
    mo.hstack([button_start_questions, button_restart_session, button_main_menu])
    return (
        button_cancel_reset_lifetime,
        button_confirm_reset_lifetime,
        button_main_menu,
        button_request_reset_lifetime,
        button_restart_session,
        button_start_questions,
    )


@app.cell
def _(button_main_menu, button_restart_session, button_start_questions):
    start_session_id = button_start_questions.value + button_restart_session.value
    in_question_view = start_session_id > button_main_menu.value
    return in_question_view, start_session_id


@app.cell
def _(
    button_cancel_reset_lifetime,
    button_confirm_reset_lifetime,
    button_request_reset_lifetime,
):
    show_lifetime_reset_confirmation = button_request_reset_lifetime.value > max(
        button_cancel_reset_lifetime.value,
        button_confirm_reset_lifetime.value,
    )
    lifetime_reset_nonce = button_confirm_reset_lifetime.value
    return lifetime_reset_nonce, show_lifetime_reset_confirmation


@app.cell
def _(start_session_id):
    _ = start_session_id


    def handle_navigation(c: int) -> int:
        return c + 1


    button_prev = mo.ui.button(value=0, on_click=handle_navigation, label="◀ Prev")
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
    label = stem.replace("_", " ")
    if label.endswith(" questions"):
        label = label[: -len(" questions")]
    return label


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
    focus_attributes: list[str],
    focus_family: str | None,
    direction_mode: str,
    session_size: int = 10,
    session_id: int | None = None,
) -> pl.DataFrame:
    """Filters and materializes a shuffled session of UI-ready rows."""
    _ = session_id  # kept as a reactive trigger for new sessions
    if df.height == 0:
        return df

    filtered_df = df.filter(pl.col("difficulty_str").is_in(difficulty_list))

    selected_family = str(focus_family).strip() if focus_family else ""
    selected_attributes = [
        str(tag).strip() for tag in focus_attributes if str(tag).strip()
    ]
    if selected_family and "tags" in filtered_df.columns:
        filtered_df = filtered_df.filter(
            pl.col("tags")
            .is_not_null()
            .and_(pl.col("tags").list.contains(selected_family))
        )
        if selected_attributes:
            filtered_df = filtered_df.filter(
                pl.col("tags")
                .is_not_null()
                .and_(
                    pl.col("tags")
                    .list.eval(pl.element().is_in(selected_attributes))
                    .list.any()
                )
            )

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
        q_type = row.get("question_type", "")
        hidden_idx = row.get("hidden_word_index", -1)

        if direction == "l1_to_l2":
            source = row["text_l1"]
            target = row["text_l2"]
            if q_type == "cloze_word_choice" and hidden_idx != -1:
                source = row["text_l2"]
                try:
                    target = row["text_l2"].split()[hidden_idx]
                except IndexError:
                    target = row["text_l2"]

            prepared_rows.append(
                {
                    "question_id": row["question_id"],
                    "question_type": q_type,
                    "response_mode": row.get("response_mode"),
                    "difficulty": row["difficulty"],
                    "difficulty_str": row["difficulty_str"],
                    "direction": direction,
                    "source": source,
                    "source_hint": row.get("hint_l1"),
                    "target": target,
                    "accepted": row["accepted_l2"],
                    "words": row["word_pool_l2"],
                    "hidden_word_index": hidden_idx,
                }
            )
        else:
            source = row["text_l2"]
            target = row["text_l1"]
            if q_type == "cloze_word_choice" and hidden_idx != -1:
                source = row["text_l1"]
                try:
                    target = row["text_l1"].split()[hidden_idx]
                except IndexError:
                    target = row["text_l1"]

            prepared_rows.append(
                {
                    "question_id": row["question_id"],
                    "question_type": q_type,
                    "response_mode": row.get("response_mode"),
                    "difficulty": row["difficulty"],
                    "difficulty_str": row["difficulty_str"],
                    "direction": direction,
                    "source": source,
                    "source_hint": row.get("hint_l2"),
                    "target": target,
                    "accepted": row["accepted_l1"],
                    "words": row["word_pool_l1"],
                    "hidden_word_index": hidden_idx,
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
def make_word_pool(lang_data: dict[str, Any], is_cloze: bool = False) -> list[str]:
    # We now construct the pool from `text` and `distractors`
    words = []
    if is_cloze:
        text = lang_data.get("text", "")
        hidden_idx = lang_data.get("hidden_word_index", -1)
        if hidden_idx != -1:
            try:
                words.append(text.split()[hidden_idx])
            except IndexError:
                words.extend(text.split())
        else:
            words.extend(text.split())
    else:
        words.extend(lang_data.get("text", "").split())

    for accepted in lang_data.get("accepted", []):
        words.extend(accepted.split())
    words.extend(lang_data.get("distractors", []))

    # Strip basic punctuation when deduplicating to avoid duplicates like "word" and "word,"
    import re

    cleaned_pool = []
    seen = set()
    for w in words:
        clean_w = re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()?"\']', "", w).lower()
        if clean_w not in seen:
            seen.add(clean_w)
            cleaned_pool.append(w)

    return cleaned_pool


@app.function
def normalize_tags(raw_tags: Any) -> list[str]:
    if not isinstance(raw_tags, list):
        return []

    cleaned = []
    for tag in raw_tags:
        if tag is None:
            continue
        tag_value = str(tag).strip()
        if tag_value:
            cleaned.append(tag_value)
    return list(dict.fromkeys(cleaned))


@app.function
def extract_translation_fields(lang_data: dict[str, Any]) -> dict[str, Any]:
    """Normalizes translation fields across schema versions."""
    text = lang_data.get("text", "")
    hint = lang_data.get("hint")

    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    if not isinstance(hint, str) or not hint.strip():
        hint = None

    return {"text": text, "hint": hint}


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
        tags = normalize_tags(row.get("tags", []))

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
                    "tags": tags,
                    "language_1": language_1,
                    "language_2": language_2,
                    # Keep both sides aligned for cloze so direction does not drop rows.
                    "prompt_l1": practice_fields["text"],
                    "prompt_l2": practice_fields["text"],
                    "text_l1": practice_fields["text"],
                    "text_l2": practice_fields["text"],
                    "hint_l1": extract_translation_fields(
                        translations.get(language_1, {})
                    ).get("text")
                    or practice_fields["hint"],
                    "hint_l2": extract_translation_fields(
                        translations.get(language_1, {})
                    ).get("text")
                    or practice_fields["hint"],
                    "accepted_l1": practice_data.get("accepted", []),
                    "accepted_l2": practice_data.get("accepted", []),
                    "word_pool_l1": make_word_pool(
                        lang_data=practice_data, is_cloze=True
                    ),
                    "word_pool_l2": make_word_pool(
                        lang_data=practice_data, is_cloze=True
                    ),
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
                "tags": tags,
                "language_1": language_1,
                "language_2": language_2,
                "prompt_l1": lang_1_fields["text"],
                "prompt_l2": lang_2_fields["text"],
                "text_l1": lang_1_fields["text"],
                "text_l2": lang_2_fields["text"],
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
        "width": "100%",
        "max-width": "var(--la-max-width-card)",
        "padding": "var(--la-space-card-padding)",
        "margin": "var(--la-space-card-margin) auto",
        "border-radius": "var(--la-radius-lg)",
        "background": "var(--la-card-shell-bg)",
        "border": "var(--la-card-border-width) solid var(--la-card-shell-edge)",
        "box-sizing": "border-box",
    }
    if accent_edge:
        style["border-right"] = f"var(--la-card-accent-width) solid {accent_edge}"
        style["border-bottom"] = f"var(--la-card-accent-width) solid {accent_edge}"
    return style


@app.function
def style_stat_box() -> dict[str, str]:
    return {
        "width": "100%",
        "padding": ".4rem",
        "border-radius": "var(--la-radius-md)",
        "background": "var(--la-bg-surface)",
        "border": "1px solid var(--la-border-subtle)",
        "box-sizing": "border-box",
        "text-align": "center",
        "box-shadow": "var(--la-stat-shadow)",
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
            "Go back to settings and adjust language pair, difficulty, or focus filters."
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
def normalize_lifetime_stats(state: dict[str, Any] | None) -> dict[str, Any]:
    raw = state if isinstance(state, dict) else {}
    if isinstance(raw.get("state"), dict):
        raw = raw["state"]
    raw_by_target_language = (
        raw.get("by_target_language")
        if isinstance(raw.get("by_target_language"), dict)
        else {}
    )
    by_target_language = {}
    for language, counts in raw_by_target_language.items():
        if not isinstance(language, str) or not language.strip():
            continue
        normalized_counts = counts if isinstance(counts, dict) else {}
        by_target_language[language] = {
            "attempts": int(normalized_counts.get("attempts", 0) or 0),
            "correct": int(normalized_counts.get("correct", 0) or 0),
        }
    return {
        "total_attempts": int(raw.get("total_attempts", 0) or 0),
        "total_correct": int(raw.get("total_correct", 0) or 0),
        "by_target_language": by_target_language,
        "available": bool(raw.get("available", False)),
        "loaded": bool(raw.get("loaded", False)),
        "error": str(raw.get("error", "") or ""),
    }


@app.function
def render_lifetime_accuracy(total_correct: int, total_attempts: int) -> str:
    if total_attempts <= 0:
        return "0%"
    return f"{(total_correct / total_attempts * 100):.0f}%"


@app.function
def get_sorted_lifetime_language_rows(
    lifetime_stats: dict[str, Any], lang_map: dict[str, str]
) -> list[dict[str, Any]]:
    rows = []
    by_target_language = lifetime_stats.get("by_target_language", {})
    if not isinstance(by_target_language, dict):
        return rows

    for language_code, counts in by_target_language.items():
        if not isinstance(counts, dict):
            continue
        attempts = int(counts.get("attempts", 0) or 0)
        correct = int(counts.get("correct", 0) or 0)
        rows.append(
            {
                "language_code": language_code,
                "language_name": lang_map.get(language_code, language_code),
                "attempts": attempts,
                "correct": correct,
                "accuracy": render_lifetime_accuracy(correct, attempts),
            }
        )

    return sorted(
        rows,
        key=lambda row: (-row["attempts"], row["language_name"].lower()),
    )


@app.function
def overlay_pending_lifetime_stats(base_stats: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "total_attempts": int(base_stats.get("total_attempts", 0) or 0),
        "total_correct": int(base_stats.get("total_correct", 0) or 0),
        "by_target_language": {
            str(language): {
                "attempts": int((counts or {}).get("attempts", 0) or 0),
                "correct": int((counts or {}).get("correct", 0) or 0),
            }
            for language, counts in base_stats.get("by_target_language", {}).items()
            if isinstance(language, str)
        },
        "available": bool(base_stats.get("available", False)),
        "loaded": bool(base_stats.get("loaded", False)),
        "error": str(base_stats.get("error", "") or ""),
    }

    for pending in SESSION_PENDING_LIFETIME_STORE.values():
        merged["total_attempts"] += int(pending.get("pending_total_attempts", 0) or 0)
        merged["total_correct"] += int(pending.get("pending_total_correct", 0) or 0)
        for language, counts in pending.get("pending_by_target_language", {}).items():
            if not isinstance(language, str) or not language.strip():
                continue
            row = merged["by_target_language"].setdefault(
                language,
                {"attempts": 0, "correct": 0},
            )
            row["attempts"] += int((counts or {}).get("attempts", 0) or 0)
            row["correct"] += int((counts or {}).get("correct", 0) or 0)

    return merged


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Render ui - non reusable
    """)
    return


@app.cell
def _():
    def render_options_intro() -> mo.Html:
        return mo.md(
            "Choose source and target language, question set, and difficulty, then press start."
        ).center()

    return (render_options_intro,)


@app.cell
def _(
    dropdown_difficulty,
    dropdown_question_file,
    dropdown_source_language,
    dropdown_target_language,
):
    def render_core_settings_section() -> mo.Html:
        core_heading = mo.md("**Settings**").center()
        top_level_options_row = mo.hstack(
            [
                dropdown_source_language,
                dropdown_target_language,
                dropdown_question_file,
                dropdown_difficulty,
            ],
            justify="space-between",
            wrap=True,
        )
        return mo.vstack([core_heading, top_level_options_row], gap=0.4, align="center")

    return (render_core_settings_section,)


@app.cell
def _(lower_level_settings):
    def render_advanced_settings_section() -> mo.Html | None:
        if lower_level_settings is None:
            return None
        advanced_heading = mo.md("**Advanced settings**").center()
        return mo.vstack(
            [advanced_heading, lower_level_settings], gap=0.4, align="center"
        )

    return (render_advanced_settings_section,)


@app.cell
def _(
    button_start_questions,
    render_advanced_settings_section,
    render_core_settings_section,
    render_options_intro,
):
    def render_options_section() -> mo.Html:
        section_divider = mo.Html(
            '<div class="menu-section-divider" aria-hidden="true"></div>'
        )
        sections: list[Any] = [render_options_intro(), render_core_settings_section()]
        advanced_settings_section = render_advanced_settings_section()
        if advanced_settings_section is not None:
            sections.append(section_divider)
            sections.append(advanced_settings_section)
        sections.append(section_divider)
        sections.append(button_start_questions.center())
        return mo.vstack(
            sections,
            gap=1,
        ).style(
            style_card(
                accent_edge="var(--la-accent-secondary-soft)",
            )
        )

    return (render_options_section,)


@app.cell
def _(current_sentence, df, row_number, session_score):
    # stats = button_check_answer.value


    def render_stats() -> mo.Html:
        return mo.hstack(
            [
                render_difficulty_indicator(
                    difficulty_int=current_sentence["difficulty"],
                    difficulty_str=current_sentence["difficulty_str"],
                ),
                render_score(
                    correct=session_score["correct"], tries=session_score["attempts"]
                ),
                render_progress(current_idx=row_number, total_count=len(df)),
            ],
            widths="equal",
            wrap=True,
        )

    return (render_stats,)


@app.cell
def _(button_main_menu, button_next, button_prev):
    def render_navigation_buttons():
        return mo.hstack(
            [button_prev, button_main_menu, button_next],
            justify="center",
            wrap=True,
            gap=0.4,
        ).style({"margin-top": "1rem"})

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
def _(button_main_menu):
    def render_footer() -> mo.Html:
        return mo.vstack([button_main_menu.center()]).style(
            style_card(
                accent_edge="var(--la-accent-secondary-soft)",
            )
        )

    return


@app.cell
def _(
    LANG_MAP,
    button_cancel_reset_lifetime,
    button_confirm_reset_lifetime,
    button_request_reset_lifetime,
    lifetime_stats,
    lifetime_stats_widget,
    show_lifetime_reset_confirmation,
):
    def render_lifetime_stats_section() -> mo.Html:
        lifetime_attempts = lifetime_stats["total_attempts"]
        lifetime_correct = lifetime_stats["total_correct"]
        accuracy = render_lifetime_accuracy(lifetime_correct, lifetime_attempts)
        language_rows = get_sorted_lifetime_language_rows(lifetime_stats, LANG_MAP)

        status_text = "Stored in this browser"
        if not lifetime_stats["loaded"]:
            status_text = "Loading lifetime stats..."
        elif not lifetime_stats["available"]:
            status_text = "Lifetime stats unavailable in this browser"

        elements: list[Any] = [
            lifetime_stats_widget,
            mo.md("### Lifetime progress").center(),
            mo.hstack(
                [
                    render_stat_box(
                        value=str(lifetime_attempts),
                        label="Attempts",
                        caption="All sessions",
                    ),
                    render_stat_box(
                        value=str(lifetime_correct),
                        label="Correct",
                        caption="All sessions",
                    ),
                    render_stat_box(
                        value=accuracy,
                        label="Accuracy",
                        caption="Derived",
                    ),
                ],
                widths="equal",
                wrap=True,
            ),
            mo.md(status_text).center(),
        ]

        if language_rows:
            elements.append(mo.md("#### By target language").center())
            for row in language_rows:
                elements.append(
                    mo.vstack(
                        [
                            mo.md(f"**{row['language_name']}**").center(),
                            mo.hstack(
                                [
                                    render_stat_box(
                                        value=str(row["attempts"]),
                                        label="Attempts",
                                        caption="All sessions",
                                    ),
                                    render_stat_box(
                                        value=str(row["correct"]),
                                        label="Correct",
                                        caption="All sessions",
                                    ),
                                    render_stat_box(
                                        value=row["accuracy"],
                                        label="Accuracy",
                                        caption="Derived",
                                    ),
                                ],
                                widths="equal",
                                wrap=True,
                            ),
                        ],
                        gap=0.5,
                    )
                )

        if lifetime_stats["error"]:
            elements.append(mo.callout(lifetime_stats["error"], kind="warn"))

        if show_lifetime_reset_confirmation:
            elements.append(
                mo.callout(
                    mo.vstack(
                        [
                            mo.md("Reset lifetime stats on this browser and device?"),
                            mo.hstack(
                                [
                                    button_confirm_reset_lifetime,
                                    button_cancel_reset_lifetime,
                                ],
                                justify="center",
                                wrap=True,
                            ),
                        ],
                        gap=0.6,
                    ),
                    kind="warn",
                )
            )
        else:
            elements.append(button_request_reset_lifetime.center())

        return mo.vstack(elements, gap=0.8).style(
            {
                **style_card(accent_edge="var(--la-accent-primary-soft)"),
                "text-align": "center",
            }
        )

    return (render_lifetime_stats_section,)


@app.cell
def _(
    button_main_menu,
    button_restart_session,
    session_score,
    total_questions,
):
    def render_summary_section() -> mo.Html:
        attempts = session_score["attempts"]
        correct = session_score["correct"]
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
                    value=accuracy,
                    label="Accuracy",
                    caption="Session result",
                ),
            ],
            widths="equal",
            wrap=True,
        )

        actions = mo.hstack(
            [button_restart_session, button_main_menu],
            justify="center",
            wrap=True,
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
