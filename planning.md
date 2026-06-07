# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
South San Jose rental housing information is spread across apartment review sites, Reddit threads, university housing pages, and rental listing platforms. It is hard to find reliable advice in one place because official apartment pages usually emphasize amenities, while renter experiences about parking, safety, noise, pests, management, and commute quality are scattered across informal discussions and review pages.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

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

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
Around 300–500 tokens per chunk for longer pages or guides. For Reddit comments and short apartment reviews, I will keep each review/comment as its own chunk when possible, even if it is shorter than 300 tokens.

**Overlap:**
Around 50 tokens of overlap for longer pages. For short reviews or Reddit comments, I will use little to no overlap because each comment usually stands on its own.

**Reasoning:**
My documents are mostly renter reviews, Reddit threads, apartment listing pages, and housing resource pages. Since many useful details are short and opinion-based, such as safety, parking, rent, bugs, noise, commute, or management quality, very large chunks could mix too many unrelated opinions together and make retrieval less accurate.

For long pages like apartment listings or university housing resources, 300–500 tokens is large enough to keep related information together, such as amenities, neighborhood details, or application advice. The 50-token overlap helps when a useful fact is split between two nearby paragraphs, so the retriever can still find enough context. If chunks are too small, search results may miss the full meaning of a renter’s complaint or recommendation. If chunks are too large, results may include too much unrelated information, such as rent, amenities, and reviews all mixed together.
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
I will use all-MiniLM-L6-v2 via sentence-transformers. This is a good choice for a small project because it is lightweight, fast, and strong enough for semantic search over short renter reviews, Reddit comments, and housing guide text.

**Top-k:**
I will retrieve the top 5 chunks per query. This should give the LLM enough context to compare multiple renter experiences without overwhelming it with too much repeated or unrelated information.

**Production tradeoff reflection:**
If this were deployed for real users and cost was not a constraint, I would consider using a stronger embedding model with better accuracy and longer context support. Since housing advice often depends on opinion-based language, a stronger model could better connect queries like “Is this area safe at night?” with chunks mentioning car break-ins, lighting, noise, or uncomfortable walking conditions, even if the exact word “safe” does not appear.

I would also consider whether the model supports multilingual queries, because some users may search in Chinese or another language while the documents are mostly in English. The main tradeoff is that larger embedding models usually improve retrieval quality but cost more, use more memory, and add latency. For this project, top-k = 5 and all-MiniLM-L6-v2 are a practical balance between speed, simplicity, and useful retrieval quality.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question                                                                                                  | Expected answer                                                                                                                                                                                                                                        |
| - | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1 | What is the estimated budget for 1B1B in san jose?                | The answer should state that the budget is around **$3.5k** for a 1B/1B apartment near South San Jose.                                                                                                                                        |
| 2 | What is the estimated budget for 2B2B in san jose? | The answer should mention that the budget is around 4-4.5k.                                     |
| 3 | For the Santa Teresa Apartments listing, what room options are there?                   | The answer should state that Santa Teresa Apartments has **one-, two-, and three-bedroom** apartment options.                                                                                                                                          |
| 4 |  For the Santa Teresa Apartments listing, what should renters do to confirm parking details?                                 | The answer should say that parking and other policy details may require checking the current listing or contacting the property directly.                                                                                                |
| 5 | For off campus housing who is responsible for tenant-landlord agreements?    |The answer should say that off-campus housing and tenant-landlord agreements are the responsibility of the tenant and landlord, not SJSU. | |



---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Noisy and inconsistent renter opinions.
Reddit comments and apartment reviews may disagree with each other because renters have different budgets, safety expectations, commute needs, and experiences with management. One person may describe a complex as safe and quiet, while another may complain about theft, noise, or maintenance. The system needs to avoid treating one opinion as a universal fact.

2. Off-topic or overly broad retrieval.
Some sources may discuss San Jose generally instead of South San Jose specifically. If the query asks about South San Jose housing, the retriever might still return chunks about downtown, North San Jose, or general Bay Area rent. This could make the answer less useful unless the system checks whether the retrieved chunk is actually relevant.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
```mermaid
graph LR
    A["Document Ingestion<br/>Python requests /<br/>saved HTML or text files"] --> B["Chunking<br/>Custom chunk_text<br/>function<br/>300-500 tokens,<br/>50-token overlap"]
    B --> C["Embedding + Vector Store<br/>sentence-transformers<br/>all-MiniLM-L6-v2<br/>FAISS or Chroma"]
    C --> D["Retrieval<br/>Semantic search<br/>top-k = 5 chunks"]
    D --> E["Generation<br/>LLM answer with<br/>source attribution"]
    
    style A fill:#1a1a1a,color:#fff
    style B fill:#1a1a1a,color:#fff
    style C fill:#1a1a1a,color:#fff
    style D fill:#1a1a1a,color:#fff
    style E fill:#1a1a1a,color:#fff
```
---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I plan to use ChatGPT to help implement document loading and chunking. I will give it my Document Sources section, Chunking Strategy section, and the requirement that longer pages should use 300–500 token chunks with about 50 tokens of overlap, while short Reddit comments or apartment reviews should stay as individual chunks when possible. I expect it to produce a load_documents() function and a chunk_text() function that keep metadata such as source title, URL, document type, and chunk number. I will verify it by checking that the output chunks are not too short, not too large, and still include the correct source URL.

**Milestone 4 — Embedding and retrieval:**
I plan to use ChatGPT to help implement embeddings and vector search. I will give it my Retrieval Approach section, especially the model choice all-MiniLM-L6-v2, the top-k = 5 setting, and the metadata fields from Milestone 3. I expect it to produce code that embeds each chunk, stores the vectors in a local vector store such as FAISS or Chroma, and retrieves the top 5 most relevant chunks for a user query. I will verify it using the five evaluation questions above and check whether the retrieved chunks actually mention the expected topics.

**Milestone 5 — Generation and interface:**
I plan to use ChatGPT to help design the answer-generation prompt and simple user interface. I will give it the Evaluation Plan, Anticipated Challenges, and Architecture sections, along with the requirement that the answer should use only retrieved chunks and include source attribution. I expect it to produce a prompt template that tells the LLM to answer housing questions, cite the retrieved source titles or URLs, and say when the documents do not contain enough evidence. I will verify it by asking the five test questions and checking whether the answers are specific, grounded in the retrieved documents, and not based on unsupported assumptions.

## Stretch Feature Plan — Metadata Filtering

For the stretch feature, I plan to add metadata filtering to the query interface. Users will be able to choose whether retrieval searches all documents or only a specific source type, such as Reddit threads, apartment listing pages, university housing resources, or neighborhood guides.

This fits my corpus because different source types answer different kinds of questions. Reddit threads are better for renter opinions, warnings, and lived experiences, while apartment listing pages are better for structured facts such as rent range, bedroom options, amenities, and policies. Filtering by source type lets users control what kind of evidence the system retrieves before generation.
