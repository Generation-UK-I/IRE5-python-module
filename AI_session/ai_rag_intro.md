# Intro to AI & Transformers

This lesson introduces some of the fundamental concepts of AI, including the building of a Retrieval Augmented Generation (RAG) agent.

## The AI Hierarchy - AI, ML, DL, & GenAI

There are lots of terms and technologies to be aware of, and lots of confusion, let's start by clarifying terms.

- Artificial Intelligence: Systems designed to perform tasks that normally require human intelligence (Siri, Alexa, chess bot).
- Machine Learning: AI that is capable of learning patterns from input data in order to make predictions (Spam filters, fraud detection, recommendations).
- Deep Learning: ML which uses multi-layer neural networks to enable the completion of complex tasks (FaceID, Speech-to-text, image classification).
- Generative AI: Builds upon the layers above in order to generate new content, including text, images, and sound (ChatGPT, CoPilot, Dall-E).

Each of the layers of the hierarchy is a subset of the one above.

### Large Language Models (LLMs)

An LLM is a Generative AI system which is trained on massive datasets in order to understand and generate human-like text, code, and other types of content, learning patterns, grammar, reasoning, general knowledge, coding syntax, everything it can from the training data. Examples include GPT, Gemma, Llama, DeepSeek, etc.

Models which can generate more than just text are known as **multimodal**.

The *large* in LLM refers to the number of parameters that the model is comprised of; In general, models with more parameters can learn more complex patterns, however it will also increase the compute resources required to run the model.

### RNNs vs Transformers

Earlier AI models focused upon one domain, specifically Natural Language Processing (NLP), they used Recurrent Neural Networks (RNNs) which process the input one token at a time, making them slow; Imagine reading a book, and trying to keep every word in your memory, RNNs work like this, and as a result they become less efficient as the input text gets larger, because as it reaches the end of an input sequence it can be difficult to retrieve the earlier tokens.

Transformer models can look at the whole sequence at once, identify the important words immediately, allowing it to jump back to earlier input data. Transformer models can work in a massively parallel approach, and allows the model to maintain accuracy and speed as volumes increase. The drawback is greater hardware requirements.

### Transformer Architecture

Most modern LLMs use a Transformer architecture, which builds the requested output step by step, essentially by asking "*what is the next word most likely to be?*"

Although this sounds simple, repeatedly predicting the next word (or token) allows modern AI systems to generate surprisingly sophisticated responses.

>Consider the predictive text feature on your phone, as you type you'll typically get three options for the next word. This works purely based on what it has learned from your previous input.
>
>A fun challenge spread a while ago about writing a message just by clicking those suggested words, and the output quickly becomes gibberish, because the feature has no understanding of context - it simply knows that, for example, you often type the word "*morning*" after the word "*good*".

We can think of an LLM as working in three stages:

1. Convert text into embeddings (numbers)
2. Process those embeddings using transformer blocks
3. Predict the most likely next token

#### Embeddings

An embedding model transforms human text into mathematical vectors (an ordered sequence of numbers, similar to arrays or lists); Embedding can be done for tokens, words, or sentences.

These vectors are projected into a high-dimensional space (commonly 768 or 1536 dimensions), with similar tokens, words, or semantically similar sentences located closer together within this space.

Simply put, "*dog*", "*canine*", "*wolf*", and "*puppy*" would all ber close together; As would sentences like "*the dog chased the ball*" and "*the puppy ran after the toy*".

Tokens are often whole words, pieces of words, or punctuation, etc. For example, the word "reader" might be represented using tokens similar to "read" and "er". Breaking words into smaller pieces (tokenisation) allows the model to understand and generate words it has never seen before.

There is a useful visualisation of a word-embedding vector space here: [Embedding Projector](https://projector.tensorflow.org/)

>In reality this is overly simplistic, but it illustrates the concept.

To summarise, an embedding is a numerical representation of text that captures its meaning. Because similar words and sentences have similar embeddings (like the dog and puppy example), AI models can compare concepts mathematically rather than treating them as plain text.

Once each token has been matched to a corresponding vector value, **positional encoding** adds an additional *positional vector* to keep track of the position of each token in the input sentence.

#### Transformer Blocks

So far:

1. Input is received, and tokenised
2. Tokens are turned into embeddings
3. Order is recorded with positional encoding

Transformer blocks are where things get trickier; A block is comprised of **Attention** and **Feedforward**.

Attention was proposed in 2017 with the publishing of a revolutionary paper titled [Attention is All You Need](https://arxiv.org/pdf/1706.03762) (*I wouldn't recommend trying to read it yet - it's very high-level*).

For each token Attention takes three parameters query, key, and value:

- Query: What the token is looking for.
- Key: Information about the token that can be matched against queries.
- Value: The information returned when a match is found.

To explain in more detail, the **Key** is like the meaning of the token, so Attention is comparing the **Query** to all of the available keys to find the closest match.

Rather than a binary *match* or *not-match*, each pairing is given a weighting to rank them - All of the weightings must add up to 100%.

Values contain the information that will be combined and passed to the next stage of processing. - returning a new context aware vector.

A common analogy is to think of a library:

- You want to find a book to answer your query
- The keys are the index cards which point to various books (values)
- There are multiple potential matches, so the query --> key matches are ranked
- Some of the keys are a strong match, some a poor match and can be almost ignored
- The matches are combined and averaged, to return the correct, context aware, book (value).

Overview:

```text
Input Text
     ↓
Tokenisation
     ↓
Embeddings
     ↓
Positional Encoding
     ↓
Transformer Blocks (Attention + Feed Forward)
     ↓
Next Token Prediction
     ↓
Generated Response
```

### Limitations of LLMs

Despite their impressive capabilities, LLMs have limitations:

- Their knowledge may be out of date since they are trained on data up to a point-in-time.
- They can generate incorrect information (hallucinations).
- They do not automatically know about private company data.

Retrieval Augmented Generation (RAG) helps address these limitations by providing relevant information to the model before it generates a response.
