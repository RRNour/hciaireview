"""
16_keyword_topic_networks.py
=============================
Lightweight reproducible topic analysis using:
  - Author keywords
  - Title bigrams
  - Abstract bigrams
  - TF-IDF terms
  - Co-word network

Avoids heavy BERTopic unless configured; uses scikit-learn TF-IDF.

Inputs
------
data/final/confidence_scored_records.jsonl  (or final_index_table.jsonl)
config/config.yaml

Outputs
-------
outputs/tables/keyword_frequencies.csv
outputs/tables/title_bigrams.csv
outputs/tables/tfidf_top_terms_by_year.csv
outputs/tables/coword_network_edges.csv
outputs/figures/topic_keyword_network.png
"""

import json, re, yaml, csv
from pathlib import Path
from collections import Counter

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import networkx as nx
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_VIZ = True
except ImportError:
    HAS_VIZ = False


STOPWORDS = set([
    "the","a","an","of","in","to","and","for","with","on","at","is","are",
    "was","were","that","this","which","we","our","their","its","be","have",
    "has","had","do","does","did","can","may","will","would","could","should",
    "from","by","as","or","but","not","it","they","he","she","his","her","ai",
])


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z][a-z\-]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 3]


def bigrams(tokens: list[str]) -> list[tuple]:
    return [(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]


def main():
    print("=== 16_keyword_topic_networks.py ===")
    cfg = load_config()

    in_path = (Path("data/final/confidence_scored_records.jsonl")
               if Path("data/final/confidence_scored_records.jsonl").exists()
               else Path("data/final/final_index_table.jsonl"))

    records = []
    if in_path.exists():
        with open(in_path) as f:
            for line in f:
                l = line.strip()
                if l:
                    records.append(json.loads(l))

    print(f"  Records loaded : {len(records)}")

    out = Path("outputs")
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    # 1. Author keyword frequencies
    kw_counter: Counter = Counter()
    for rec in records:
        for kw in rec.get("keywords", []):
            kw_counter[kw.lower().strip()] += 1

    with open(out/"tables"/"keyword_frequencies.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["keyword","count"])
        w.writerows(kw_counter.most_common(200))

    # 2. Title bigrams
    bigram_counter: Counter = Counter()
    for rec in records:
        tokens = tokenize(rec.get("title",""))
        for bg in bigrams(tokens):
            bigram_counter[bg] += 1

    with open(out/"tables"/"title_bigrams.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bigram","count"])
        for (a,b), cnt in bigram_counter.most_common(200):
            w.writerow([f"{a} {b}", cnt])

    # 3. TF-IDF top terms by year
    years = sorted(set(r.get("year",0) for r in records))
    tfidf_rows = []
    if HAS_SKLEARN and records:
        for yr in years:
            yr_docs = [r.get("title","") + " " + str(r.get("keywords",""))
                       for r in records if r.get("year") == yr]
            if not yr_docs:
                continue
            try:
                vec = TfidfVectorizer(stop_words="english", max_features=30,
                                      ngram_range=(1,2))
                X = vec.fit_transform(yr_docs)
                scores = X.sum(axis=0).A1
                terms = vec.get_feature_names_out()
                top = sorted(zip(terms, scores), key=lambda x: -x[1])[:10]
                for term, score in top:
                    tfidf_rows.append({"year": yr, "term": term,
                                       "tfidf_sum": round(float(score),4)})
            except Exception:
                pass

    with open(out/"tables"/"tfidf_top_terms_by_year.csv","w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year","term","tfidf_sum"])
        w.writeheader()
        w.writerows(tfidf_rows)

    # 4. Co-word network edges
    coword_counter: Counter = Counter()
    for rec in records:
        tokens = list(set(tokenize(rec.get("title","") + " " +
                                    str(rec.get("keywords","")))))
        tokens.sort()
        for i in range(len(tokens)):
            for j in range(i+1, min(i+4, len(tokens))):
                pair = (tokens[i], tokens[j])
                coword_counter[pair] += 1

    with open(out/"tables"/"coword_network_edges.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["term_a","term_b","cooccurrence"])
        for (a,b), cnt in coword_counter.most_common(300):
            w.writerow([a, b, cnt])

    # 5. Network visualisation
    if HAS_VIZ:
        top_edges = coword_counter.most_common(60)
        G = nx.Graph()
        for (a, b), w_val in top_edges:
            G.add_edge(a, b, weight=w_val)

        # Node sizing by degree centrality
        centrality = nx.degree_centrality(G)
        node_sizes = [centrality[n]*5000 + 200 for n in G.nodes()]
        edge_widths = [G[u][v]["weight"]/max(1,max(w for _,w in top_edges))*4
                       for u,v in G.edges()]

        NAVY  = "#1F4E79"
        BLUE  = "#2E75B6"
        LGRAY = "#F2F2F2"
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_facecolor(LGRAY)
        fig.patch.set_facecolor(LGRAY)
        pos = nx.spring_layout(G, seed=42, k=2.5)
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.4, width=edge_widths,
                               edge_color="#AAAAAA")
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes,
                               node_color=BLUE, alpha=0.85)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=8,
                                font_color=NAVY, font_weight="bold")
        ax.set_title("Topic and Keyword Co-occurrence Network (AI-HCI Corpus)",
                     fontsize=13, fontweight="bold", color=NAVY)
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(out/"figures"/"topic_keyword_network.png",
                    dpi=150, bbox_inches="tight", facecolor=LGRAY)
        plt.close(fig)
        print(f"  Network figure saved")

    print(f"  Keywords   : {len(kw_counter)} unique")
    print(f"  Bigrams    : {len(bigram_counter)} unique")
    print(f"  TF-IDF rows: {len(tfidf_rows)}")
    print("  Done.")


if __name__ == "__main__":
    main()
