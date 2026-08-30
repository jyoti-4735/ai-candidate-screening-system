# AI/ML Engineer Knowledge Base

## Supervised Learning Fundamentals
Supervised learning trains a model on labeled input-output pairs so it can generalize to unseen data. Classification predicts discrete labels; regression predicts continuous values. The key risk is overfitting, where a model memorizes training data instead of learning generalizable patterns. Techniques such as train/validation/test splits, k-fold cross-validation, and regularization (L1/L2) help detect and control overfitting.

## Bias-Variance Tradeoff
A model with high bias makes overly simplistic assumptions and underfits; a model with high variance is overly sensitive to training data noise and overfits. Total error decomposes into bias, variance, and irreducible noise. Increasing model capacity typically reduces bias but increases variance, so practitioners tune capacity, regularization strength, and training data volume to find the sweet spot.

## Neural Networks and Backpropagation
A neural network consists of layers of weighted connections and non-linear activation functions (ReLU, sigmoid, tanh). Backpropagation computes the gradient of the loss with respect to each weight using the chain rule, and an optimizer (SGD, Adam) updates weights to minimize loss. Vanishing/exploding gradients are common issues in deep networks, mitigated by careful initialization, normalization layers, and residual connections.

## Convolutional Neural Networks
CNNs use convolutional filters to detect spatial patterns (edges, textures, shapes) in image data, with pooling layers reducing spatial dimensions while preserving important features. Architectures like ResNet introduce skip/residual connections that let gradients flow through very deep networks, solving the degradation problem where deeper plain networks perform worse than shallower ones.

## Transfer Learning and Fine-Tuning
Instead of training from scratch, transfer learning reuses a model pretrained on a large dataset and adapts it to a new, often smaller, dataset. Fine-tuning can freeze early layers (generic features) and retrain later layers (task-specific features), which is faster and needs less data than training from scratch, and is standard practice for both vision (ResNet, EfficientNet) and language models.

## Large Language Models and Prompt Engineering
LLMs are transformer-based models trained on massive text corpora to predict the next token, and can be adapted to tasks through prompting rather than retraining. Prompt engineering techniques include few-shot examples, chain-of-thought prompting to elicit step-by-step reasoning, system prompts to set behavior/persona, and structured output constraints (e.g., asking for strict JSON). Prompt quality strongly affects output reliability, and iterative testing against edge cases is essential.

## Retrieval-Augmented Generation (RAG)
RAG grounds an LLM's output in external knowledge by retrieving relevant text chunks from a vector database and injecting them into the prompt as context, rather than relying purely on the model's parametric memory. A typical pipeline: (1) ingest documents, (2) split into overlapping chunks to preserve context across boundaries, (3) embed chunks into vectors, (4) store in a vector index, (5) at query time, embed the user query and retrieve the top-k most similar chunks, (6) construct a prompt combining the query and retrieved context, (7) generate a grounded answer. RAG reduces hallucination and allows updating knowledge without retraining the model.

## Chunking Strategy and Context Preservation
Chunk size is a tradeoff: chunks too small lose surrounding context; chunks too large dilute relevance and waste context-window tokens. Overlapping chunks (e.g., 15-20% overlap) prevent important information from being split exactly at a chunk boundary. Semantic chunking (splitting on paragraph/section boundaries) generally outperforms fixed-size character splitting for retrieval quality.

## Embeddings and Vector Similarity
Embeddings map text into dense numeric vectors such that semantically similar text is close in vector space, typically measured with cosine similarity or dot product. Dense embeddings (from transformer encoders) capture semantic meaning; sparse methods like TF-IDF or BM25 capture exact keyword overlap and remain strong baselines, especially combined with dense retrieval in a hybrid approach.

## Model Evaluation Metrics
Classification uses accuracy, precision, recall, F1-score, and ROC-AUC; accuracy alone is misleading on imbalanced datasets. Regression uses MAE, MSE/RMSE, and R-squared. For generative/LLM systems, evaluation is harder and often combines automated metrics (BLEU/ROUGE for text overlap, embedding similarity) with human or LLM-as-judge evaluation for relevance, groundedness, and coherence.

## Data Preprocessing and Feature Engineering
Real-world ML pipelines spend most effort on data quality: handling missing values, removing duplicates, normalizing/scaling numeric features, encoding categorical variables (one-hot, target encoding), and engineering domain-specific features. Data leakage — where information from outside the training set (often from the future or the target itself) leaks into features — is a common and serious bug that inflates validation metrics unrealistically.

## Deployment and MLOps Basics
Moving a model to production involves serving it behind an API, monitoring for data/concept drift, logging predictions for auditability, and having a rollback path. Batch inference precomputes predictions on a schedule; online inference serves predictions in real time with latency constraints. Containerization (Docker) and cloud logging/monitoring make deployments reproducible and observable.
