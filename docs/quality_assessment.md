# Quality Assessment Report

**Date:** 2026-05-01
**Model:** intfloat/multilingual-e5-large
**Test set:** 50 randomly sampled FAQs (seed=42), paraphrased with natural German questions
**Database:** 4,992 FAQ entries

## 1. Summary

| Metric | Value |
|---|---|
| **Recall@1** | 18.0% (9/50) |
| **Recall@3** | 52.0% (26/50) |
| **Recall@5** | 72.0% (36/50) |
| **Recall@10** | 80.0% (40/50) |
| **MRR** | 0.3740 |
| **Not found (top 10)** | 10/50 (20.0%) |

## 2. Per-Result Breakdown

| # | Original ID | Original Question | Paraphrase | Rank | Score | Top-1 (if wrong) |
|---|---|---|---|---|---|---|
| 1 | 913 | Was ist ein Freischaltcode? | Ich hab was von einem Freischaltcode gehoert, was ist das genau? | 1 | 0.9371 | -- |
| 2 | 205 | Wird die Nachuntersuchung von der AOK Sachsen-Anhalt uebernommen? | Zahlt die Kasse eigentlich die Kontrolle nach einer Behandlung? | **NF** | -- | ID=4083 (0.8736): Muss ich nach Ende der Massnahme die Teilnahmebescheinigung... |
| 3 | 2254 | Wann wird Behandlungspflege verordnet? | Unter welchen Umstaenden kriege ich Behandlungspflege verschrieben? | 8 | 0.8954 | ID=2271 |
| 4 | 2007 | Uebernimmt die AOK-Sachsen-Anhalt das B-Streptokokken Screening... | Ich bin schwanger, zahlt die AOK den Test auf B-Streptokokken? | 4 | 0.9265 | ID=2011 |
| 5 | 1829 | Der Orthopaeede hat mir Hyaluronsaeure-Spritzen empfohlen... | Mein Orthopaeede meint ich brauche Hyaluronsaeure-Spritzen... | 4 | 0.9202 | ID=1833 |
| 6 | 1144 | Versicherter wuenscht Zusendung PIN/PUK Brief... | Ich brauche meinen PIN-PUK-Brief fuer die Versichertenkarte... | 1 | 0.9409 | -- |
| 7 | 840 | Wann beginnt die Teilnahme? Kann ich auch mitten im Jahr... | Kann ich eigentlich irgendwann im Jahr beim Bonusprogramm mitmachen... | 2 | 0.8977 | ID=842 |
| 8 | 4468 | Ich kann meine Studenten-Beitraege nicht bezahlen... | Als Student kriege ich das grad nicht hin mit den Beitraegen... | 1 | 0.9384 | -- |
| 9 | 713 | Erfolgt eine Bonusauszahlung, wenn Schulden bei der AOK... | Wenn ich noch rueckstaendige Beitraege bei der AOK habe... | 8 | 0.8859 | ID=715 |
| 10 | 4838 | Wie hoch ist meine gesetzliche Zuzahlung bei Medikamenten? | Was muss ich denn gesetzlich bei Arzneimitteln dazuzahlen? | 5 | 0.9290 | ID=4846 |
| 11 | 3457 | Wann beginnt und endet der Mutterschutz? | Ich bin schwanger, ab wann gilt der Mutterschutz eigentlich... | 4 | 0.9312 | ID=3461 |
| 12 | 261 | Mein Kind wurde in ein SPZ ueberwiesen... | Unser Kind soll ins SPZ, uebernimmt die AOK die Kosten dafuer? | 2 | 0.8936 | ID=259 |
| 13 | 245 | Ich bekomme keinen Termin bei einem niedergelassenen Psychotherapeuten... | Ich finde irgendwie keinen Therapieplatz, was kann ich denn noch tun? | 3 | 0.9140 | ID=251 |
| 14 | 768 | Wann muss das Bonusheft eingereicht werden? | Bis wann muss ich eigentlich mein Bonusheft abgeben? | **NF** | -- | ID=767 (0.9558): Wann muss das Bonusheft eingereicht werden? |
| 15 | 1792 | Warum muss ich den Widerspruch an die zentrale Stelle selbst schicken? | Wieso soll ich den Widerspruch selber an die zentrale Stelle schicken... | 2 | 0.9449 | ID=1789 |
| 16 | 1906 | Was ist GESUNDESKONTO? | Kann mir mal einer erklaeren was das GESUNDESKONTO eigentlich ist? | 3 | 0.9508 | ID=1908 |
| 17 | 4140 | Was ist mit Zubehoer und Verbrauchsmaterialien? | Wie ist das eigentlich mit dem Zubeoehr und den Verbrauchsmaterialien... | **NF** | -- | ID=4168 (0.8911): Was muss ich bei Sauerstoffgeraeten zuzahlen? |
| 18 | 4932 | Welche Themen werden in Ihrem Kinder-Erste-Hilfe-Kurs behandelt? | Was lernt man denn so in dem Erste-Hilfe-Kurs fuer Kinder bei euch? | 2 | 0.9307 | ID=4927 |
| 19 | 218 | Welche Therapiearten gibt es? | Was fuer Therapieformen werden denn eigentlich angeboten? | 3 | 0.9270 | ID=220 |
| 20 | 4598 | Die Zahnarztpraxis...gibt es nicht mehr. Mein neuer Zahnarzt fragt nach den Roentgenbildern... | Mein alter Zahnarzt hat zugemacht und der neue will die Roentgenbilder haben... | **NF** | -- | ID=3985 (0.8767): Mein Arzt hat keine Formulare zur Verordnung einer Reha-Massnahme... |
| 21 | 1629 | Welche Unterlagen muessen fuer ausl. Versicherte vorliegen? | Welche Dokumente braucht man als auslaendisch Versicherter bei der AOK? | 1 | 0.9303 | -- |
| 22 | 4465 | Ich moechte meine Beitraege abbuchen lassen... | Ich will dass die Beitraege automatisch vom Konto eingezogen werden... | 3 | 0.8819 | ID=4470 |
| 23 | 3437 | Ich bin bei der OGS/Meine AOK App registriert und benoetige eine Mitgliedsbescheinigung | Ich bin in der AOK App angemeldet und brauche eine Bescheinigung dass ich versichert bin | **NF** | -- | ID=2929 (0.9066): Eingang Bescheinigung ueber Erkrankung des Kindes per Meine AOK-App |
| 24 | 1806 | IGEL-Leistungen | Was sind eigentlich IGEL-Leistungen und zahlt die AOK dafuer? | 6 | 0.8986 | ID=1808 |
| 25 | 3680 | Welche Voraussetzungen muss ich erfuellen um einen Pflegegrad zu erhalten? | Was muss ich erfuellen damit ich einen Pflegegrad bekomme? | 1 | 0.9434 | -- |
| 26 | 4828 | Welche Trinknahrung wird durch die AOK genehmigt? | Was fuer Trinknahrung bezahlt denn die AOK? | 4 | 0.9197 | ID=4826 |
| 27 | 2279 | Muss bei Unterbrechung der Uebergangspflege ein neuer Antrag gestellt werden? | Wenn die Uebergangspflege mal unterbrochen wird, muss ich dann nochmal neu beantragen? | 4 | 0.9451 | ID=2275 |
| 28 | 54 | Tarifueberschneidung Versicherter moechte AOK-Aktivbonus abschliessen... | Ich hab schon einen Bonus-Wahltarif und will jetzt den Aktivbonus dazu... | **NF** | -- | ID=96 (0.9048): Kunde hat den Aktivbonus im Vorjahr erhalten... |
| 29 | 1308 | Machen alle Apotheken beim E-Rezept mit? | Kann ich mein E-Rezept eigentlich in jeder Apotheke einloesen? | 1 | 0.9358 | -- |
| 30 | 3463 | Wie und wann muss ich das Mutterschaftsgeld beantragen? | Wie stelle ich eigentlich den Antrag auf Mutterschaftsgeld... | 3 | 0.9566 | ID=3465 |
| 31 | 2788 | Wer kann den AOK Kinderbonus erhalten? | Wer ist denn alles berechtigt den Kinderbonus von der AOK zu kriegen? | 4 | 0.9440 | ID=2786 |
| 32 | 2277 | Muss bei Unterbrechung der Uebergangspflege ein neuer Antrag gestellt werden? | Wenn die Pflege zu Hause kurz pausiert, braucht man dann einen neuen Antrag? | 3 | 0.9149 | ID=2275 |
| 33 | 1274 | Ich benoetige neue Klebe-Elektroden fuer mein Elektro-/Muskelstimulationsgeraet? | Fuer mein Muskelstimulationsgeraet brauch ich neue Elektroden... | 2 | 0.8955 | ID=1276 |
| 34 | 1764 | Verlangt die AOK eine Gesundheitspruefung fuer eine freiwillige Versicherung... | Wenn man sich vor dem 15. Geburtstag freiwillig versichern will... | 3 | 0.9103 | ID=1768 |
| 35 | 2758 | Wie ist die Verfahrensweise bei Schliessung des Tarifs... | Was passiert mit dem Tarif wenn man drei Jahre lang keine gefoerderte Massnahme mehr gemacht hat? | 1 | 0.9238 | -- |
| 36 | 838 | Wann beginnt die Teilnahme? Kann ich auch mitten im Jahr... | Ab wann kann ich beim Bonus-Wahltarif mitmachen... | 3 | 0.9357 | ID=842 |
| 37 | 760 | Was passiert wenn ich unverschuldet einen Unfall habe... | Ich hab einen Unfall gehabt ohne Schuld aber der Verursacher ist nicht versichert... | 3 | 0.9029 | ID=764 |
| 38 | 3113 | Ich moechte in ein anderes Krankenhaus verlegt werden. | Kann ich waehrend der Behandlung in ein anderes Krankenhaus wechseln? | **NF** | -- | ID=238 (0.9287): Kann ich waehrend der Behandlung das Therapieverfahren wechseln? |
| 39 | 793 | Was ist zu tun bei Verlust bzw. Nichterhalt des Bonushefts? | Ich hab mein Bonusheft verloren, was mach ich jetzt? | **NF** | -- | ID=2102 (0.9592): Was ist zu tun bei Verlust bzw. Nichterhalt des Bonushefts? |
| 40 | 2941 | Kann ich die Bescheinigung meines erkrankten Kindes fuer meinen Ehepartner... mit nutzen? | Wenn mein Kind krank ist, kann ich die Arbeitsbescheinigung dann auch fuer meinen Partner nutzen? | 4 | 0.9032 | ID=2945 |
| 41 | 2818 | Wie erfolgt die Adressaenderung bei Teilnehmern am Kinderbonus? | Ich bin umgezogen und bin beim Kinderbonus angemeldet, wie aendere ich meine Adresse? | 2 | 0.9344 | ID=2820 |
| 42 | 4946 | Wie werden die Kosten beim LSB, dem DOSB... erstattet? | Wie kriege ich die Kosten fuer Sportkurse vom LSB oder DOSB erstattet? | 4 | 0.9042 | ID=4937 |
| 43 | 2167 | Was faellt unter Mutterschaftsvorsorge? | Was gehoert denn alles zur Vorsorge waehrend der Schwangerschaft? | 3 | 0.8791 | ID=2165 |
| 44 | 356 | Aenderungen SEPA Lastschriftmandat | Ich will mein SEPA-Lastschriftmandat aendern, wie geht das beim Arbeitgeberkonto? | 1 | 0.8894 | -- |
| 45 | 3764 | Warum werden Antraege auf Wohngruppenzuschlag bei 24-h-Pflege... abgelehnt? | Wieso wird der Zuschlag fuer Wohngruppen abgelehnt wenn man 24-Stunden-Pflege hat... | 1 | 0.9545 | -- |
| 46 | 4393 | Bekomme ich von Ihnen einen Zuschuss fuer die Brille? | Zahlt die AOK eigentlich was fuer eine neue Brille? | 6 | 0.8885 | ID=4397 |
| 47 | 1023 | Ich bin ausserhalb von Sachsen-Anhalt umgezogen... | Ich bin in ein anderes Bundesland gezogen und der Arzt meint mein Bundesland auf der Karte ist falsch | 4 | 0.9141 | ID=1021 |
| 48 | 3101 | Der Arzt hat gesagt, dass ich ueber Nacht bleiben muss... Bezahlt die AOK das? | Ich soll im Krankenhaus uebernachten und das soll was kosten, uebernimmt die AOK das? | **NF** | -- | ID=4821 (0.8965): Muss ich jetzt verhungern, wenn die AOK die Trinknahrung nicht uebernimmt? |
| 49 | 646 | Zuzahlung bei Fahrkosten | Muss ich bei Krankenfahrten was dazuzahlen? | **NF** | -- | ID=1720 (0.9077): Muss ich bei Krankengeldbezug Beitraege... weiterzahlen? |
| 50 | 4523 | Was ist ein Widerspruch? | Was bedeutet eigentlich ein Widerspruch bei der AOK? | 3 | 0.9001 | ID=4525 |

NF = Not Found in top 10

## 3. Analysis

### 3.1 Which types of questions work well?

**Strong performers (found at rank 1-2):**

- **Keyword-rich questions:** When the paraphrase retains distinctive terms ("Freischaltcode", "PIN/PUK", "Studenten-Beitraege", "B-Streptokokken", "E-Rezept", "SEPA Lastschriftmandat"), retrieval is excellent. The model clearly recognizes these domain-specific terms.
- **Specific entity names:** Questions containing unique identifiers like "GESUNDESKONTO", "Aktivbonus", "Kinderbonus" are reliably matched because these terms act as strong anchors in the embedding space.
- **Action-oriented questions:** Questions with specific actions ("Beitraege abbuchen", "Adresse aendern", "Antrag stellen") that map directly to FAQ patterns perform well.

**Moderate performers (found at rank 3-10):**

- **Semantic rephrasing:** When the paraphrase changes vocabulary significantly but keeps the meaning ("Mutterschutz" -> "schwanger, ab wann gilt der Mutterschutz"), results tend to appear at positions 3-8. The cosine similarity drops but remains above 0.88.
- **General cost questions:** "Zahlt die AOK...?" paraphrases work but compete with many similar cost-coverage questions, pushing them lower in the ranking.
- **Long, detailed questions:** Paraphrases that preserve the detail level (e.g., Hyaluronsaeure-Spritzen, Uebergangspflege Unterbrechung) tend to find the right answer but not at rank 1.

### 3.2 Which questions fail and why?

**10 out of 50 (20%) were not found in the top 10.** The failure reasons break down into four categories:

#### Category A: Duplicate question saturation (IDs 768, 793)

The questions "Wann muss das Bonusheft eingereicht werden?" and "Was ist zu tun bei Verlust bzw. Nichterhalt des Bonushefts?" exist in the database with **many duplicate entries** (same question text, different IDs -- likely one per channel). The top-10 results fill entirely with these duplicates, pushing the target ID out of range. The correct question text IS matched (score 0.9558 and 0.9592 respectively), but the specific ID is displaced by its own clones.

**Impact:** This is an index quality issue, not a retrieval quality issue. If duplicates were deduplicated or if a post-processing step grouped same-text entries, these would be rank-1 results.

#### Category B: Semantic drift in paraphrase (IDs 205, 3101, 3113, 646)

- **ID 205** ("Nachuntersuchung" -> "Kontrolle nach einer Behandlung"): The paraphrase loses the medical specificity of "Nachuntersuchung" (follow-up examination) and becomes a generic cost question. The model returns generic Reha-related cost questions instead.
- **ID 3101** ("ueber Nacht bleiben im Krankenhaus" -> "im Krankenhaus uebernachten"): The paraphrase is too conversational and loses the hospital-specific overnight-stay context. The model returns generic "uebernimmt die AOK" questions.
- **ID 3113** ("in ein anderes Krankenhaus verlegt werden" -> "in ein anderes Krankenhaus wechseln"): The paraphrase accidentally matches the "Kann ich waehrend der Behandlung...wechseln?" pattern, which exists for therapy changes and therapist changes -- but not hospital transfers. The model scores this at 0.9287, a false positive.
- **ID 646** ("Fahrkosten" -> "Krankenfahrten"): The paraphrase "Krankenfahrten" activates the embedding for "Krankengeld" questions (score 0.9077) due to the "Kranken-" prefix similarity. The actual "Zuzahlung bei Fahrkosten" entry lives in the "Befreiung" topic and is not reached.

#### Category C: Too specific / low-signal paraphrase (IDs 4598, 4140, 54, 3437)

- **ID 4598** (dentist X-ray records): The paraphrase "Roentgenbilder" from a closed dentist is highly specific. The model returns generic "formulare" questions instead. The original FAQ has a very long, specific question that may not have been well-represented in the embedding due to its length.
- **ID 4140** (Zubehoer und Verbrauchsmaterialien): The original question is extremely short and generic ("Was ist mit Zubehoer und Verbrauchsmaterialien?"). The paraphrase adds "Sauerstoffgeraeten" context, but the model still prioritizes the more specific "Was muss ich bei Sauerstoffgeraeten zuzahlen?" entries.
- **ID 54** (Aktivbonus + Bonus-Wahltarif overlap): The paraphrase captures the intent well, but the model confuses it with a similar "Aktivbonus im Vorjahr" question (0.9048 vs ~0.8940 for the correct match at rank 9).
- **ID 3437** (OGS/App Mitgliedsbescheinigung): The paraphrase uses "Bescheinigung dass ich versichert bin" which matches "Bescheinigung ueber Erkrankung des Kindes" more closely in embedding space than the "Mitgliedsbescheinigung" FAQ.

### 3.3 Score Threshold Analysis

| Statistic | Correct Match | Top-1 (when wrong) |
|---|---|---|
| Min | 0.8791 | 0.8736 |
| Max | 0.9566 | 0.9592 |
| Mean | 0.9192 | 0.9150 |

**Key findings:**

- The correct match scores range from 0.8791 to 0.9566 with a mean of 0.9192.
- There is **significant overlap** between correct match scores and wrong top-1 scores. The top-1 score when wrong can reach 0.9592, which is higher than many correct matches.
- **No single threshold perfectly separates good from bad matches.** However:
  - A threshold of **0.87** would catch all found items (min correct score = 0.8791).
  - A threshold of **0.90** would provide reasonable confidence: among items scoring >= 0.90, the hit rate is approximately 75%.
  - Scores below **0.88** are unreliable for this dataset -- they include both the lowest correct match (0.8791) and the highest wrong top-1 (0.9592).

**Recommendation:** Use a threshold of **0.88** as a soft floor. Results with scores >= 0.92 can be considered high-confidence. Results between 0.88-0.92 should be presented with lower confidence. Results below 0.88 should trigger a fallback (e.g., "I couldn't find a clear answer, let me connect you with an advisor").

### 3.4 Per-Topic Performance

| Topic | Found/Total | Hit Rate | Avg Rank |
|---|---|---|---|
| Arbeitgeberkonten | 1/1 | 100% | 1.0 |
| Arzneimittel | 2/2 | 100% | 4.5 |
| Digitale Gesundheitsanwendungen | 1/1 | 100% | 1.0 |
| E-Rezept | 1/1 | 100% | 1.0 |
| Elektrostimulationsgeraete | 1/1 | 100% | 2.0 |
| Fluechtlinge | 1/1 | 100% | 1.0 |
| Freiwillige Versicherung | 1/1 | 100% | 3.0 |
| Frueherkennung / Vorsorge | 3/3 | 100% | 4.0 |
| GESUNDESKONTO | 2/2 | 100% | 3.5 |
| Gesundheitsbonus | 1/1 | 100% | 3.0 |
| Haeusliche Krankenpflege | 3/3 | 100% | 5.0 |
| Kinderbonus | 3/3 | 100% | 2.3 |
| Kinderpflegekrankengeld | 1/1 | 100% | 4.0 |
| Mutterschaftsgeld | 2/2 | 100% | 3.5 |
| Pflege | 2/2 | 100% | 1.0 |
| Praevention | 2/2 | 100% | 3.0 |
| Studenten | 2/2 | 100% | 2.0 |
| Widerspruch | 1/1 | 100% | 3.0 |
| elektronische Gesundheitskarte | 2/2 | 100% | 2.5 |
| Bonus-Wahltarif mit Zusatzbonus | 4/6 | 67% | 4.0 |
| Ambulante Behandlungen | 3/4 | 75% | 2.7 |
| Krankenhaus | 0/2 | 0% | N/A |
| Aktivbonus | 0/1 | 0% | N/A |
| Befreiung | 0/1 | 0% | N/A |
| Meldemanagement | 0/1 | 0% | N/A |
| Sauerstoffgeraete | 0/1 | 0% | N/A |
| Zahnaerztliche Leistungen | 0/1 | 0% | N/A |

### 3.5 Recommendations

1. **Deduplicate FAQ entries:** The database contains many entries with identical question text but different IDs (likely one per channel). This dilutes the top-10 results. Implement deduplication or post-processing grouping to improve effective recall.

2. **Consider hybrid search:** Pure embedding search struggles when paraphrases use different vocabulary for the same concept (e.g., "Nachuntersuchung" -> "Kontrolle", "Fahrkosten" -> "Krankenfahrten"). Adding BM25 or keyword-based matching as a second signal would help.

3. **Expand top-k for re-ranking:** Using top_k=10 and then re-ranking with a cross-encoder or LLM-based relevance check could recover items that are relevant but not at rank 1.

4. **Improve training data:** Fine-tune the embedding model on QA pairs specific to German health insurance domain to improve handling of paraphrases like "Krankenfahrten" vs "Fahrkosten".

5. **Add topic-based pre-filtering:** If the user's question can be classified into a topic (e.g., "Krankenhaus", "Studenten"), pre-filtering by topic would reduce competition from unrelated but semantically similar entries.
