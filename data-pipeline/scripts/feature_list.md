### 🟦 **A. Book-Level Features**

| Feature                      | Description                                            | Source Column                     |
| ---------------------------- | ------------------------------------------------------ | --------------------------------- |
| `title_length_in_characters` | Measures title verbosity                               | `title_clean`                     |
| `title_length_in_words`      | Number of words in title                               | `title_clean`                     |
| `description_length`         | Number of characters in book description               | `description_clean`               |
| `log_ratings_count`          | Log-transform of `ratings_count` to handle skew        | `ratings_count`                   |
| `popularity_score`           | Combined metric = `ratings_count + text_reviews_count` | Both                              |
| `num_genres`                 | Count of unique genres (from `popular_shelves_flat`)   | `popular_shelves_flat`            |
| `is_series`                  | Binary (1 if `series_flat` non-empty, else 0)          | `series_flat`                     |
| `adjusted_average_rating`    | Wilson lower bound (already implemented)               | `average_rating`, `ratings_count` |
| `great`                      | Binary flag for top 20% by adjusted rating             | derived                           |

---

### 🟨 **B. Interaction-Level Features**

| Feature                | Description                                                  | Source Column                       |
| ---------------------- | ------------------------------------------------------------ | ----------------------------------- |
| `num_books_read`       | Count of books read per user                                 | `is_read`                           |
| `avg_rating_given`     | Average rating each user gives                               | `rating`                            |
| `avg_time_to_finish`   | Mean duration between `read_at_clean` and `started_at_clean` | `started_at_clean`, `read_at_clean` |
| `recent_activity_days` | Days since user’s last `date_updated_clean`                  | `date_updated_clean`                |
| `user_activity_count`  | Number of total interactions per user                        | `user_id_clean`                     |

---

### 🟩 **C. Hybrid Features (Join-based)**

After joining users ↔ books on `book_id`:

| Feature                            | Description                                                       |
| ---------------------------------- | ----------------------------------------------------------------- |
| `user_avg_rating_vs_book`          | User’s average rating minus book’s adjusted rating (bias measure) |
| `book_popularity_percentile`       | Percentile rank of book popularity                                |
| `user_previously_read_same_author` | Binary — has user read another book by same author before         |
| `user_previously_read_same_genre`  | Binary — has user read from same shelf before                     |

*(Last two are optional — may be computed later once full user history is available.)*

---

## 🧠 Additional (Future) Feature Ideas

If you later expand, here’s what’s worth exploring:

| Category                  | Example                                                                               |
| ------------------------- | ------------------------------------------------------------------------------------- |
| **Textual/NLP**           | Sentiment polarity of `description_clean` or TF-IDF embeddings for content similarity |
| **Temporal**              | Yearly trends in `ratings_count`, seasonal popularity                                 |
| **Collaborative Signals** | User–user or book–book cosine similarity based on shared shelves or ratings           |
| **Diversity Metrics**     | Genre entropy per user — “how diverse are their reads”                                |
