# Sentence Builder Manual Review Log

## Summary of Remaining Accepted Items

- Total items reviewed: 12
- Reason counts: {'word_order': 8, 'text_subset': 4}

| file path | question id | language side | accepted reason | decision | rationale | status |
|---|---:|---|---|---|---|---|
| apps/public/de_en/sentence_builder.json | 14 | de | word_order | keep | "Oft reisen sie..." vs "Sie reisen oft...". Same tokens. | done |
| apps/public/de_en/sentence_builder.json | 14 | en | word_order | keep | "They travel... often" vs "They often travel...". Same tokens. | done |
| apps/public/de_en/sentence_builder.json | 33 | de | text_subset | keep | "Es regnet draußen" (It is raining outside) vs "Draußen regnet es gerade" (It is currently raining outside). Valid subset. | done |
| apps/public/de_en/sentence_builder.json | 47 | de | word_order | keep | "Normalerweise trinke ich..." vs "Ich trinke normalerweise...". Same tokens. | done |
| apps/public/de_nl/sentence_builder.json | 14 | de | word_order | keep | "Oft reisen sie..." vs "Sie reisen oft...". Same tokens. | done |
| apps/public/de_nl/sentence_builder.json | 33 | de | text_subset | keep | "Es regnet draußen" vs "Draußen regnet es gerade". Valid subset. | done |
| apps/public/de_nl/sentence_builder.json | 47 | de | word_order | keep | "Normalerweise trinke ich..." vs "Ich trinke normalerweise...". Same tokens. | done |
| apps/public/de_no/sentence_builder.json | 33 | de | text_subset | keep | "Es regnet draußen" vs "Draußen regnet es gerade". Valid subset. | done |
| apps/public/de_no/sentence_builder.json | 47 | de | word_order | keep | "Normalerweise trinke ich..." vs "Ich trinke normalerweise...". Same tokens. | done |
| apps/public/en_nl/sentence_builder.json | 14 | en | word_order | keep | "They travel... often" vs "They often travel...". Same tokens. | done |
| apps/public/en_no/sentence_builder.json | 14 | en | word_order | keep | "They travel... often" vs "They often travel...". Same tokens. | done |
| apps/public/nl_no/sentence_builder.json | 33 | nl | text_subset | keep | "Het regent buiten" vs "Buiten regent het nu". Valid subset. | done |
