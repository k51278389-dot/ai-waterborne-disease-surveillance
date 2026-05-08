# AI Waterborne Disease Surveillance & Medical Advisory System

This repository contains a modular AI-assisted public health surveillance system focused on:

* Natural language outbreak report parsing
* Disease normalization and typo handling
* Environmental disease prediction
* Weighted outbreak risk analysis
* Dominant disease detection
* Retrieval-Augmented Generation (RAG)
* Structured medical advisory generation
* Public health interpretation workflows

---

# Repository Structure

```text
ai-waterborne-disease-surveillance/
│
├── aggregator.py                     # Disease aggregation utilities
├── analysis.py                       # Risk analysis + dominant disease detection
├── case_parser.py                    # Main outbreak parsing pipeline
├── cause.py                          # Cause validation and classification
├── cause_mapper.py                   # Maps causes to outbreak categories
├── compare.py                        # User vs sensor disease comparison
├── disease_severity_spreadability.py # Severity + spreadability scoring
├── location_memory_manager.py        # Location outbreak memory handling
├── rag_filter.py                     # Medical retrieval filtering
├── rag_pipeline.py                   # Main RAG medical pipeline
├── response_engine.py                # Structured outbreak response generation
├── risk_analyzer.py                  # Risk categorization engine
├── sensor_adapter.py                 # Sensor → disease prediction system
├── sensor_logs.json                  # Example environmental logs
├── requirements.txt
└── README.md
```

---

# Highlights

* **Natural Language Parsing:** Handles outbreak reports like:

  ```text
  5 cholera, 10 malaria, 15 flu in umden
  ```

* **Disease Normalization:** Supports typo correction and alias mapping.

  Examples:

  * mlria → malaria
  * flue → flu
  * ecoli → e coli
  * ameobiosis → amoebiasis

* **Environmental Intelligence:** Predicts outbreak risks from sensor conditions such as:

  * water pH
  * turbidity
  * contamination indicators

* **Weighted Risk Scoring:** Uses:

  ```text
  impact score = severity × spreadability × case count
  ```

  to prioritize outbreak threats.

* **Dominant Disease Detection:** Identifies the primary outbreak requiring immediate attention.

* **RAG Medical Advisory:** Generates structured medical responses using retrieval-augmented generation.

* **Structured AI Outputs:** Separates:

  * PRIMARY THREAT
  * USER-REPORTED DISEASES
  * PREDICTED RISKS

* **Interpretation Engine:** Compares environmental predictions with reported diseases.

---

# Example Workflow

```text
User Report
     ↓
Case Parser
     ↓
Disease Normalization
     ↓
Risk Analysis
     ↓
Sensor Prediction
     ↓
Comparison Engine
     ↓
Dominant Disease Detection
     ↓
RAG Retrieval Pipeline
     ↓
Structured AI Medical Response
```

---

# Example Input

```text
5 cholera, 10 malaria, 15 flu in umden
```

---

# Example Output

```text
PRIMARY THREAT:
Cholera

Symptoms:
- Severe diarrhea
- Dehydration

Prevention:
- Safe water
- Proper sanitation

Immediate Actions:
- ORS hydration
- Medical isolation
```

---

# Technologies Used

* Python
* Regular Expressions
* Rule-based NLP
* Retrieval-Augmented Generation (RAG)
* FAISS
* Sentence Transformers
* Prompt Engineering
* Risk Scoring Systems
* Public Health Intelligence Logic

---

# Installation

## Clone Repository

```bash
git clone <repository-url>
```

## Install Requirements

```bash
pip install -r requirements.txt
```

## Run Project

```bash
python case_parser.py
```

---


# Future Improvements

* Embedding-based semantic retrieval
* Real vector database integration
* Live environmental sensor ingestion
* GIS outbreak visualization
* Deep learning outbreak prediction
* Dashboard frontend
* Automated outbreak alerts
* Multi-language support

---

# Notes

* Built using modular architecture for maintainability.
* Focused on interpretable AI outputs.
* Designed for SIH-style healthcare and outbreak intelligence use cases.
* Retrieval pipeline intentionally avoids hallucinated medical responses through retrieval filtering.

---


