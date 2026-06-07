# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
South San Jose rental housing information is spread across apartment review sites, Reddit threads, university housing pages, and rental listing platforms. It is hard to find reliable advice in one place because official apartment pages usually emphasize amenities, while renter experiences about parking, safety, noise, pests, management, and commute quality are scattered across informal discussions and review pages.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| #  | Source                                                                           | Type                             | URL or file path                                                                                        |
| -- | -------------------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 1  | Reddit / r/SanJose — “1b1b Apartment Recommendations near south San Jose”        | Reddit thread                    | `https://www.reddit.com/r/SanJose/comments/1j0k6gn/1b1b_apartment_recommendations_near_south_san_jose/` |
| 2  | Reddit / r/SanJose — “2 bedroom 2 bath Apartment Recommendations South San Jose” | Reddit thread                    | `https://www.reddit.com/r/SanJose/comments/1m0s17v/2_bedroom_2_bath_apartment_recommendations_south/`   |
| 3  | Reddit / r/SanJose — “Recommended neighborhoods to rent an apartment?”           | Reddit thread                    | `https://www.reddit.com/r/SanJose/comments/1s39tcf/recommended_neighborhoods_to_rent_an_apartment/`     |
| 4  | Reddit / r/SanJose — “Any apartment complexes that don’t suck?”                  | Reddit thread                    | `https://www.reddit.com/r/SanJose/comments/zfdbmt/any_apartment_complexes_that_dont_suck/`              |
| 5  | Reddit / r/SanJose — “Apartment Reviews Advice”                                  | Reddit thread                    | `https://www.reddit.com/r/SanJose/comments/vxoux5/apartment_reviews_advice/`                            |
| 6  | Reddit / r/SanJose — “Apartments that are Modern and Safe?”                      | Reddit thread                    | `https://www.reddit.com/r/SanJose/comments/1fu57xx/apartments_that_are_modern_and_safe/`                |
| 7  | San José State University — Off Campus Housing Resources                         | University housing resource page | `https://www.sjsu.edu/housing/how-we-can-help/off-campus-housing-resources.php`                         |
| 8  | Apartments.com — “5 Best Neighborhoods in San Jose, CA for Renters”              | Neighborhood guide               | `https://www.apartments.com/blog/best-neighborhoods-in-san-jose-for-renters`                            |
| 9  | Apartments.com — Santa Teresa Apartments, San Jose, CA                           | Apartment listing / reviews page | `https://www.apartments.com/santa-teresa-apartments-san-jose-ca/0tn5k10/`                               |
| 10 | Apartments.com — The Woods Apartments, San Jose, CA                              | Apartment listing / reviews page | `https://www.apartments.com/the-woods-apartments-san-jose-ca/75d8npw/`                                  |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
Around 300–500 tokens per chunk for longer pages or guides. For Reddit comments and short apartment reviews, I will keep each review/comment as its own chunk when possible, even if it is shorter than 300 tokens.

**Overlap:**
Around 50 tokens of overlap for longer pages. For short reviews or Reddit comments, I will use little to no overlap because each comment usually stands on its own.

**Why these choices fit your documents:**
My documents are mostly renter reviews, Reddit threads, apartment listing pages, and housing resource pages. Since many useful details are short and opinion-based, such as safety, parking, rent, bugs, noise, commute, or management quality, very large chunks could mix too many unrelated opinions together and make retrieval less accurate.

For long pages like apartment listings or university housing resources, 300–500 tokens is large enough to keep related information together, such as amenities, neighborhood details, or application advice. The 50-token overlap helps when a useful fact is split between two nearby paragraphs, so the retriever can still find enough context. If chunks are too small, search results may miss the full meaning of a renter’s complaint or recommendation. If chunks are too large, results may include too much unrelated information, such as rent, amenities, and reviews all mixed together.

**Final chunk count:**
The final chunk count was **95 chunks** across **10 documents**.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
I will use all-MiniLM-L6-v2 via sentence-transformers. This is a good choice for a small project because it is lightweight, fast, and strong enough for semantic search over short renter reviews, Reddit comments, and housing guide text.

**Production tradeoff reflection:**
If this were deployed for real users and cost was not a constraint, I would consider using a stronger embedding model with better accuracy and longer context support. Since housing advice often depends on opinion-based language, a stronger model could better connect queries like “Is this area safe at night?” with chunks mentioning car break-ins, lighting, noise, or uncomfortable walking conditions, even if the exact word “safe” does not appear.

I would also consider whether the model supports multilingual queries, because some users may search in Chinese or another language while the documents are mostly in English. The main tradeoff is that larger embedding models usually improve retrieval quality but cost more, use more memory, and add latency. For this project, top-k = 5 and all-MiniLM-L6-v2 are a practical balance between speed, simplicity, and useful retrieval quality.

---

## Grounded Generation

**System prompt grounding instruction:**

My system prompt tells the LLM to answer only from the retrieved chunks and to decline if the retrieved documents do not contain enough information. The core instruction is:

```text
You are a grounded RAG assistant for an unofficial South San Jose housing guide.
Answer using ONLY the provided retrieved document chunks.
Do not use outside knowledge.
If the retrieved chunks do not explicitly contain the answer, say exactly:
"I don't have enough information on that from the collected documents."
When answering, cite the relevant source labels like [S1] or [S2].
Do not invent apartment facts, prices, safety claims, policies, or recommendations.
```

**How source attribution is surfaced in the response:**

Source attribution is surfaced in two ways. First, the prompt asks the model to cite retrieved chunks using labels like `[S1]` or `[S2]` inside the answer. Second, the Gradio interface programmatically displays a “Retrieved from” section showing the source title, chunk number, distance score, and URL for each retrieved chunk. This means source visibility does not depend only on the model remembering to cite correctly.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is the estimated budget for 1B1B in San Jose? | Around $3.5k for a 1B/1B South San Jose apartment. | The system answered around $3.5k and cited the South San Jose 1B/1B Reddit source. | Relevant | Accurate |
| 2 | What is the estimated budget for 2B2B in San Jose? | Around $4.5k all-inclusive, except electricity and internet. | The system answered about $4.5k all-inclusive, excluding electricity and internet, and cited the 2B/2B South San Jose Reddit source. | Relevant | Accurate |
| 3 | In Santa Teresa Apartments listing, what bedroom options are available? | Santa Teresa Apartments lists 1 to 3 bedrooms, including one-, two-, and three-bedroom floor plan categories. | The system answered that Santa Teresa Apartments lists 1 to 3 bedroom options. | Relevant | Accurate |
| 4 | For the Santa Teresa Apartments, what should renters do to confirm parking or policy details? | Renters should check the current listing or contact the property directly. | The system answered that parking and policy details should be confirmed through the current listing or by contacting the property. | Relevant | Accurate |
| 5 | For off campus housing, Who is responsible for tenant-landlord agreements? | Tenant-landlord agreements are the responsibility of the tenant and landlord. | The system answered that tenant-landlord agreements are the responsibility of the tenant and landlord, and SJSU’s page is informational. | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
Is parking available in Santa Teresa Apartments?

**What the system returned:**
I don't have enough information on that from the collected documents.

**Root cause (tied to a specific pipeline stage):**
This was mainly a document coverage issue in the ingestion stage, not a retrieval failure. The retrieved Santa Teresa Apartments chunk contained apartment facts such as address, rent range, bedroom options, bathroom options, square footage, and amenities. However, it did not explicitly say whether parking is available. The source text only said that parking and other policy details may require checking the current listing or contacting the property directly. Because the generation prompt requires the model to answer only from the retrieved context, the model correctly declined instead of inventing a yes/no answer.

**What you would change to fix it:**
I would improve the source collection step by adding more complete parking-policy information to data/sources/source9.txt, if that information is available from the original Santa Teresa Apartments listing. Then I would rerun ingestion, chunking, embedding, and retrieval so the vector store contains a chunk that directly answers parking availability. I would not fix this by loosening the generation prompt, because that would make the system less grounded.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
The spec helped by forcing the system into separate pipeline stages: document ingestion, chunking, embedding/vector storage, retrieval, and generation. This made debugging easier because I could test each stage before moving to the next one. For example, I found that retrieval was working because the correct Santa Teresa Apartments chunk appeared first for bedroom-option questions, even before adding the LLM generation layer.

**One way your implementation diverged from the spec, and why:**
My original plan was to scrape several source URLs directly, including Reddit and Apartments.com pages. In practice, multiple pages blocked automated requests with HTTP 403 errors, so I changed the ingestion approach to use local .txt files under data/sources/. This still followed the project requirement because the system loads collected documents from disk, but it made the pipeline more stable and easier to reproduce for grading.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
I gave ChatGPT my Document Sources section, Chunking Strategy section, and pipeline diagram from planning.md. I asked it to implement Milestone 3: a script that loads documents, cleans them, saves raw and cleaned JSONL files, and produces chunks with source metadata.

- *What it produced:*
It produced an initial scripts/ingest_and_chunk.py script that attempted to fetch source URLs, clean HTML, and output data/raw/documents.jsonl, data/clean/clean_documents.jsonl, and data/chunks/chunks.jsonl.

- *What I changed or overrode:*
The first version failed because Reddit and Apartments.com returned HTTP 403 errors. I changed the approach so the script loads local files from data/sources/source1.txt through source10.txt first, using web scraping only as a fallback. I also inspected the printed sample chunks and confirmed that the final output contained 95 readable chunks.

**Instance 2**

- *What I gave the AI:*
I gave ChatGPT my Retrieval Approach section, including the model choice all-MiniLM-L6-v2, the vector store choice ChromaDB, and the requirement to return top-k chunks with source metadata and distance scores.

- *What it produced:*
It produced scripts/embed_and_retrieve.py, which loads data/chunks/chunks.jsonl, embeds each chunk with Sentence Transformers, stores the embeddings in ChromaDB, and prints retrieval results for test queries.

- *What I changed or overrode:*
I verified the retrieval manually before moving to generation. The top results for the 1B/1B budget, 2B/2B budget, and Santa Teresa bedroom-options questions all retrieved the correct source chunks with distance scores under about 0.5. I kept the retrieval settings because the results were relevant.
