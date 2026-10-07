# Explainable Resume Screening Using a Multi-Stage NLP Pipeline with Quality Gating and Parallel OCR Acceleration

## Abstract
Resume screening is a high-volume, time-sensitive recruitment task that is often performed using keyword matching alone, which can fail to capture semantic relevance, document quality, and structural consistency. This paper presents an explainable AI-based resume screening system that automates candidate ranking against a job description using a multi-stage natural language processing (NLP) pipeline. The proposed framework performs document ingestion, document-structure analysis, semantic segmentation, grammar and discourse checks, named entity recognition, skill extraction, job-description parsing, weighted matching, and explanation generation. A quality gate filters low-quality resumes before ranking, improving robustness against malformed or fragmentary documents. The ranking model combines skill alignment, experience fit, education relevance, and semantic similarity, and applies a timeline-risk penalty to reduce inconsistent candidate profiles. For image-based PDFs, the system uses OCR fallback with parallel page processing, and resume processing is parallelized across multiple background workers to improve throughput. The implementation demonstrates that explainable, structure-aware ranking can be combined with practical performance optimization in a production-style recruitment workflow.

## Keywords
Resume screening, NLP, semantic similarity, explainable AI, OCR, information extraction, recruitment automation, document intelligence.

## 1. Introduction
Recruitment teams regularly process large numbers of resumes, but manual review is expensive, inconsistent, and difficult to scale. Traditional applicant tracking systems often rely on surface-level keyword overlap, which can incorrectly favor resumes that merely repeat job terms while missing candidates with strong conceptual or transferable alignment. At the same time, many real-world resumes are heterogeneous: some are text-based PDFs, some are scanned images requiring OCR, and many contain inconsistent formatting, incomplete histories, or noisy text extraction artifacts.

This work addresses those problems with an end-to-end resume screening system built around an explainable NLP pipeline. The system accepts PDFs and DOCX files, extracts and cleans text, identifies document structure, computes quality signals, extracts skills and entities, compares the resume against a parsed job description, and produces both a numerical score and human-readable reasons for the decision. Unlike a pure retrieval or embedding-only approach, the system introduces a quality gate so that structurally weak resumes are filtered before scoring, and it includes a timeline-risk penalty to reduce the score of inconsistent resumes.

The main contribution of this paper is not a new language model, but a practical architecture for making resume ranking more reliable, interpretable, and scalable. The implementation is suitable for applied AI settings where recruiters need transparent decisions, batch processing, and usable performance on mixed-format documents.

## 2. Literature Review
Automated resume screening has been studied through keyword matching, supervised classification, semantic similarity models, and extraction-based document understanding [3], [4], [5], [7], [14]. Early systems typically relied on bag-of-words or Boolean matching, which is efficient but brittle. More recent systems use transformer embeddings or domain-specific NLP pipelines to estimate semantic fit between resumes and job descriptions [9], [13]. However, these methods often remain opaque and do not account for document quality, missing structure, or low-confidence extraction.

Document intelligence systems have also explored OCR for scanned documents, entity extraction for experience and education, and rule-based post-processing for noisy inputs [11], [12]. In recruitment applications, explainability remains important because automated ranking can affect hiring decisions. Therefore, systems that combine semantic scoring with explicit reasons and filtering logic are more useful in practice than black-box ranking alone [1], [8], [10].

Our system builds on these ideas by integrating semantic similarity with structural and quality-aware preprocessing, and by explicitly exposing the reasons behind each decision.

## 3. Proposed System Architecture
The system is implemented as a full-stack application with a FastAPI backend and a React frontend. The backend exposes endpoints for uploading resumes, setting the job description, fetching processing status, retrieving ranked results, and managing stored resumes. The frontend provides a dashboard for uploading files, viewing ranked candidates, inspecting detailed explanations, comparing resumes, and exporting results.

The backend processing pipeline consists of the following stages:

1. Document ingestion from PDF or DOCX.
2. Text extraction with OCR fallback for image-based PDFs.
3. Document-structure analysis and segmentation.
4. Grammar, discourse, semantic-role, and section-behavior evaluation.
5. Quality gating to reject low-utility resumes early.
6. Named entity recognition and skill intelligence.
7. Job-description parsing and semantic embedding generation.
8. Weighted matching and decision assignment.
9. Explanation storage for final output.

The system also supports parallel background processing for multiple resumes, which is important for practical batch screening.

The architecture is designed around two stages of control. The first stage validates and enriches the resume document through ingestion, document intelligence, and quality gating. The second stage performs ranking and explanation generation so the output can be interpreted by a recruiter. This separation allows the system to reject low-quality documents early while still producing transparent final decisions for valid inputs.

## 4. Implementation

### 4.1 Document Ingestion
The ingestion module accepts PDF and DOCX files. DOCX files are parsed directly, while PDF files are first processed with text extraction. If the PDF contains little or no extractable text, the system falls back to OCR. This is essential for scanned resumes and image-only documents.

The OCR implementation is optimized for throughput by reducing image conversion DPI, processing pages in parallel, and using a document-oriented Tesseract configuration. The system also detects corrupted PDFs early and returns a clear validation error instead of wasting compute on invalid input. This design follows the broader document-structure extraction and robust parsing direction reported in prior work on logical structure recovery and resume parsing [11], [12].

### 4.2 Document Intelligence and Segmentation
After ingestion, the resume text is divided into units and analyzed for structural signals. The document intelligence stage classifies lines as bullets, headings, or paragraphs using rule-based patterns and heading keywords. This provides layout signals such as bullet ratio, paragraph ratio, and low-structure flags, which later feed the quality gate.

### 4.3 Skill Intelligence
The skill intelligence stage extracts job-relevant skill mentions from the resume units using the parsed job description as the skill vocabulary. For each skill, the system counts frequency and checks whether the skill appears in action-oriented contexts. A confidence score is then assigned based on frequency and action usage. This is consistent with prior resume skill-matching and skill-assessment research [7], [8].

### 4.4 Quality Gate
Before final ranking, the quality gate checks whether a resume is sufficiently readable and structured. The gate uses grammar score, semantic-role score, section behavior, discourse coherence, timeline consistency, and fragment ratio. A weighted quality score is computed as

$$
Q = 0.25G + 0.25S + 0.20B + 0.20D + 0.10T - P_f
$$

where $G$ is grammar quality, $S$ is semantic-role quality, $B$ is section behavior, $D$ is discourse score, $T$ is timeline consistency, and $P_f$ is a fragment penalty when the fragment ratio exceeds the configured threshold. The system then applies hard rules, rejecting resumes that fall below minimum grammar, semantic-role, or overall quality thresholds.

This stage is important because it prevents low-quality text extraction artifacts from influencing the ranking model.

### 4.5 Matching and Ranking
The ranking stage combines four signals: skill match, experience match, education match, and semantic similarity. The final score is computed as

$$
R = 100 \times T \times (0.40M_s + 0.30M_e + 0.15M_d + 0.15M_{sem})
$$

where $M_s$ is the skill score, $M_e$ is the experience score, $M_d$ is the education score, $M_{sem}$ is the semantic similarity score, and $T$ is a timeline-risk factor. The score is converted to a 0–100 scale and mapped to three decision categories:

1. Shortlisted: $R \ge 60$
2. Review: $40 \le R < 60$
3. Rejected: $R < 40$

The skill score is given the highest weight because the resume-to-job fit is primarily determined by required and optional skills. Experience and education are treated as complementary signals, while semantic similarity captures broader contextual relevance.

### 4.6 Explainability
For each resume, the system stores structured reasons explaining the ranking outcome. Examples include low relevance of required skills, experience below job requirement, low semantic alignment, and timeline inconsistency. For shortlisted candidates, the system also records positive reasons such as strong skill match and experience alignment. This design is intended to make the output suitable for human review.

The implementation supports internal evaluation through console logging, batch uploads, and a performance test script. The system can be benchmarked on batches of resumes using a fixed job description and observed completion time. Suitable evaluation metrics include processing time per resume, throughput for a batch, quality-gate rejection rate, agreement with manual reviewer labels, and ranking usefulness for shortlisted candidates.

## 5. Result and Analysis

### 5.1 Experimental Setup
The implemented system was evaluated using the project’s documented processing logs and performance notes, which capture batch processing behavior, OCR behavior, and the impact of optimization changes. The comparison focuses on three axes that are directly observable in the implementation:

1. Throughput under batch upload.
2. OCR and PDF-processing behavior.
3. Baseline behavior of simplified ranking variants.

The optimized system uses CPU-based parallel workers in the upload path and parallel page OCR in the ingestion path. The baseline conditions are derived from the pre-optimization configuration documented in the project notes.

### 5.2 Throughput and OCR Performance
Table 1 summarizes the processing-time improvement reported in the project documentation. The values are intentionally presented as ranges because processing time depends on PDF quality, OCR need, and resume length.

**Table 1. Documented processing-time comparison before and after optimization**

| Scenario | Before optimization | After optimization | Improvement |
|---|---:|---:|---:|
| Batch of 10 resumes with OCR | 50-100 min | 15-30 min | About 70% faster |
| Single OCR-heavy resume | 5-10 min | 1-2 min | About 60-80% faster |
| Multi-page OCR job | Sequential page processing | Parallel page processing | Faster per document |

The results show that parallel workers and faster OCR settings reduce end-to-end latency substantially. The main gains come from two implementation choices: increasing concurrent worker capacity and reducing OCR overhead through lower DPI and parallel page processing. These gains are consistent with the console logs that show multiple resumes being processed simultaneously.

### 5.3 Quality-Gate Behavior
The quality gate behaved as intended in the documented runs. Corrupted PDFs were detected early, malformed documents were rejected before scoring, and low-quality resumes with weak grammar or poor structure were filtered out. This means the final ranking list is not only faster to produce but also cleaner, because structurally weak resumes do not consume ranking capacity.

### 5.4 Baseline Comparison
To make the contribution clearer, Table 2 compares the proposed pipeline against two simpler baselines that are common in resume screening systems: keyword-only matching and semantic-similarity-only matching.

**Table 2. Baseline comparison of resume screening approaches**

| Capability | Keyword-only baseline | Semantic-only baseline | Proposed pipeline |
|---|---|---|---|
| Skill matching | Direct lexical overlap | Contextual similarity | Weighted skill confidence + partial matching |
| Experience handling | Manual or rule-based | Limited | Explicit experience-range scoring |
| Education handling | Often absent | Limited | Explicit education score |
| Document quality filtering | No | No | Yes, via quality gate |
| OCR support for scanned PDFs | Usually limited | Usually limited | Yes |
| Explainable reasons | Minimal | Minimal | Yes, stored decision reasons |
| Timeline consistency penalty | No | No | Yes |
| Batch throughput optimization | No | No | Yes, via parallel workers |

The proposed pipeline is stronger than the baselines in the dimensions that matter for production use: it handles noisy input, produces explanations, and supports scalable batch processing. A keyword-only baseline is easy to implement but brittle. A semantic-only baseline is more flexible, but it still ignores structural quality and can score noisy documents too highly. The proposed pipeline addresses both problems by combining semantic matching with document-quality filtering.

### 5.5 Ablation-Style Interpretation
Because the project is implemented as a modular pipeline, its behavior can also be interpreted as a set of ablations. Table 3 summarizes the expected effect of removing major components.

**Table 3. Ablation-style interpretation of key pipeline components**

| Removed component | Expected effect on results |
|---|---|
| Quality gate | More noisy resumes reach ranking, increasing false positives |
| OCR fallback | Image-based PDFs fail or lose extractable text |
| Parallel worker execution | Batch latency increases substantially |
| Timeline-risk penalty | Inconsistent profiles can receive inflated scores |
| Explanation generation | Output becomes less useful for reviewer verification |

Taken together, the experimental evidence supports the central design choice of the system: combining ranking with preprocessing, quality control, and explainability produces a more practical resume screening workflow than a ranking model alone.

## 6. Conclusion and Future Work
This work has several limitations. First, the current scoring weights and thresholds are hand-tuned rather than learned from large-scale labeled data. Second, the semantic similarity component depends on the quality of the sentence embedding model and may not capture all domain-specific job requirements. Third, fairness and bias analysis is not yet incorporated, which is important for any recruitment-related system.

Future work should focus on:

1. Learning scoring weights from labeled hiring outcomes.
2. Adding fairness and bias audits.
3. Building a larger evaluation dataset with human annotations.
4. Comparing against transformer-only and keyword-only baselines.
5. Moving OCR and background processing to a queue-based architecture for production deployment.

This paper presented an explainable resume screening system that combines multi-stage NLP processing, structural quality gating, semantic and skill-based ranking, and parallel OCR acceleration. The architecture is designed for practical recruitment settings where transparency, robustness, and throughput are all important. While the current implementation is an applied system rather than a new model architecture, it demonstrates that a carefully designed pipeline can produce meaningful ranking decisions and readable explanations while remaining scalable for batch resume processing.

## References
[1] D. Heo, Y. Kang, C. Heo, H. Choi, and K. Jung, “Joint Models for Sentence Segmentation and Named Entity Recognition in Literary Sinitic Text,” *Journal of Web Engineering*, vol. 25, no. 1, pp. 19–32, Jan. 2026, doi: 10.13052/jwe1540-9589.2512.

[2] M. Siino, M. Falco, D. Croce, and P. Rosso, “Exploring LLMs Applications in Law: A Literature Review on Current Legal NLP Approaches,” *IEEE Access*, vol. 13, pp. 18253–18276, 2025, doi: 10.1109/ACCESS.2025.3533217.

[3] D. R. V, S. Gour, S. M, S. K, K. J. Nithin, and K. S. N, “AI-Powered Resume Screening System Using NLP and Machine Learning,” in *Proc. 2025 3rd Int. Conf. Inventive Computing and Informatics (ICICI)*, Bangalore, India, 2025, pp. 780–785, doi: 10.1109/ICICI65870.2025.11069785.

[4] S. Kulkarni, P. R. Kurumkar, V. S. Kadam, and V. P. Maradur, “AI-powered resume screening system,” *World Journal of Advanced Engineering Technology and Sciences*, vol. 15, no. 01, pp. 2263–2277, 2025, doi: 10.30574/wjaets.2025.15.1.0413.

[5] F. A. Jafari and R. Simon, “Automated Resume Screening System Using NLP and Machine Learning,” *Int. J. Sci. Res. Eng. Manage. (IJSREM)*, vol. 09, no. 05, May 2025, doi: 10.55041/IJSREM48082.

[6] G. G. Devarajan, S. M. Nagarajan, S. I. Amanullah, S. A. S. A. Mary, and A. K. Bashir, “AI-Assisted Deep NLP-Based Approach for Prediction of Fake News From Social Media Users,” *IEEE Trans. Comput. Social Syst.*, vol. 11, no. 4, pp. 4975–4985, Aug. 2024, doi: 10.1109/TCSS.2023.3259480.

[7] N. Gangoda, K. P. Yasantha, C. Sewwandi, N. Induvara, S. Thelijjagoda, and N. Giguruwa, “Resume Ranker: AI-Based Skill Analysis and Skill Matching System,” in *Proc. 2024 Sixth Int. Conf. Intelligent Computing in Data Sciences (ICDS)*, Marrakech, Morocco, 2024, pp. 1–8, doi: 10.1109/ICDS62089.2024.10756304.

[8] J. Gregório, R. Miller, I. Afxentiou, J. Laurent-Hippolyte, and P. Morantz, “A Taxonomy-Based Data Model for Assessing Engineering Skills in an Organizational Context,” *IEEE Trans. Eng. Manage.*, vol. 71, pp. 15363–15374, 2024, doi: 10.1109/TEM.2024.3486812.

[9] R. Patil, S. Boit, V. Gudivada, and J. Nandigam, “A Survey of Text Representation and Embedding Techniques in NLP,” *IEEE Access*, vol. 11, pp. 36120–36146, 2023, doi: 10.1109/ACCESS.2023.3266377.

[10] T. I. Amosa, L. I. B. Izhar, P. Sebastian, I. B. Ismail, O. Ibrahim, and S. L. Ayinla, “Clinical Errors From Acronym Use in Electronic Health Record: A Review of NLP-Based Disambiguation Techniques,” *IEEE Access*, vol. 11, pp. 59297–59316, 2023, doi: 10.1109/ACCESS.2023.3284682.

[11] O. Belyaeva, A. Bogatenkova, and D. Turdakov, “Dedoc: A Universal System for Extracting Content and Logical Structure From Textual Documents,” in *Proc. 2023 Ivannikov ISPRAS Open Conf. (ISPRAS)*, Moscow, Russia, 2023, pp. 20–25, doi: 10.1109/ISPRAS60948.2023.10508151.

[12] M. E. Erdem and R. Bayraktar, “Layout Analysis for Robust Resume Parsing,” in *Proc. 2023 6th Int. Conf. Inf. Commun. Technol. (ICOIACT)*, Yogyakarta, Indonesia, 2023, pp. 476–480, doi: 10.1109/ICOIACT59844.2023.10455907.

[13] Z. Li *et al*., “A Unified Understanding of Deep NLP Models for Text Classification,” *IEEE Trans. Vis. Comput. Graph.*, vol. 28, no. 12, pp. 4980–4994, Dec. 2022, doi: 10.1109/TVCG.2022.3184186.

[14] T. M. Harsha, G. S. Moukthika, D. S. Sai, M. N. R. Pravallika, S. Anamalamudi, and M. Enduri, “Automated Resume Screener using Natural Language Processing (NLP),” in *Proc. 2022 6th Int. Conf. Trends Electron. Informatics (ICOEI)*, Tirunelveli, India, 2022, pp. 1772–1777, doi: 10.1109/ICOEI53556.2022.9777194.
