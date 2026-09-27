# Hierarchical Reinforcement Learning Voice Sales Agent

## 1. Project Title

**Hierarchical Reinforcement Learning for an Adaptive Real-Time Voice Sales Agent**

---

## 2. Abstract

This project proposes an intelligent web-based voice sales agent that interacts with customers through natural speech, understands their requirements, searches and displays suitable products, answers questions, handles objections, recommends alternatives, and guides the customer toward an appropriate purchasing decision.

Unlike traditional LLM-based sales assistants, where a language model independently decides what to say at every turn, this system separates **language generation from decision making**. Reinforcement Learning (RL) is responsible for learning the agent's behavior and strategy, while a Large Language Model (LLM) is responsible for converting the selected strategy into natural conversational language.

The project introduces two RL systems operating at different timescales:

1. **Sales Strategy RL Policy** — determines *what the salesperson should do next*.
2. **Voice Interaction RL Policy** — determines *when and how the agent should participate in the spoken conversation*.

The customer-sales interaction is modeled as a **Partially Observable Markov Decision Process (POMDP)** because important customer characteristics such as purchase intent, price sensitivity, patience, and preferences cannot be directly observed.

The system will be trained primarily using simulated customers with hidden preferences and evaluated against random, rule-based, supervised, and LLM-only agents.

---

# 3. Problem Statement

Most current AI sales assistants operate using the following architecture:

**Customer → LLM → Response**

The LLM simultaneously performs reasoning, strategy selection, and language generation.

This presents several limitations:

* No explicitly learned long-term sales strategy.
* Difficulty optimizing decisions across an entire conversation.
* Limited ability to learn from successful and unsuccessful interactions.
* No explicit trade-off between gathering information and making recommendations.
* Weak modeling of hidden customer preferences.
* Voice interaction is usually controlled by fixed Voice Activity Detection rules.
* Poor handling of interruptions, hesitation, and conversational timing.

This project instead treats sales as a **sequential decision-making problem**.

At each stage the agent must decide:

> Given everything I currently know about this customer, what action should I take next to maximize customer satisfaction and successful task completion?

---

# 4. Core System Concept

The system separates three different responsibilities.

### Reinforcement Learning — WHAT

Determines the strategic action the salesperson should take.

Examples:

* Ask about budget.
* Ask about use case.
* Recommend a product.
* Compare products.
* Handle an objection.
* Present a cheaper alternative.
* Attempt to close the sale.

### Voice RL — WHEN

Determines conversational timing.

Examples:

* Continue listening.
* Start speaking.
* Stop speaking because the user interrupted.
* Wait because the user may continue.
* Give a short acknowledgment.
* Ask for clarification.

### LLM — HOW

Transforms the selected strategy into natural language.

Example:

**RL Action**

`SHOW_CHEAPER_ALTERNATIVE`

**LLM Response**

> "In that case, I don't think you need to spend the extra $300. There's another model with very similar performance that fits your budget better. Let me show you both."

Therefore:

**Strategy RL = WHAT to do**

**Voice RL = WHEN to do it**

**LLM = HOW to express it**

---

# 5. High-Level Architecture

```text
                    USER
                     │
                  Speech
                     │
                     ▼
        ┌───────────────────────────┐
        │ Speech Processing Layer   │
        │                           │
        │ STT                       │
        │ VAD                       │
        │ Audio / Prosody Features  │
        │ Interruption Detection    │
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │ Customer Belief State     │
        │                           │
        │ Budget                    │
        │ Preferences               │
        │ Intent                    │
        │ Price Sensitivity         │
        │ Objections                │
        │ Engagement                │
        │ Conversation Stage        │
        │ Uncertainty               │
        └────────────┬──────────────┘
                     │
          ┌──────────┴───────────┐
          │                      │
          ▼                      ▼
 ┌─────────────────┐    ┌─────────────────┐
 │ Strategy RL     │    │ Voice RL        │
 │                 │    │                 │
 │ WHAT to do      │    │ WHEN to speak   │
 └────────┬────────┘    └────────┬────────┘
          │                      │
          └──────────┬───────────┘
                     │
                     ▼
             ┌───────────────┐
             │ LLM Reasoner  │
             │               │
             │ Generates     │
             │ final wording │
             └───────┬───────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
   Product Tools               TTS
          │                     │
          ▼                     ▼
    Website UI                USER
```

---

# 6. Reinforcement Learning System 1: Sales Strategy Policy

## 6.1 Objective

The first RL system learns the optimal sequence of sales actions throughout the conversation.

The policy is represented as:

$$
\pi_{strategy}(a_t | b_t)
$$

where:

* \(b_t\) = current belief about the customer.
* \(a_t\) = next sales strategy.

---

## 6.2 State / Belief State

The salesperson cannot directly observe everything about the customer.

The belief state may contain:

* Estimated budget.
* Budget confidence.
* Product category.
* Intended use case.
* Performance preference.
* Portability preference.
* Battery preference.
* Brand preference.
* Price sensitivity.
* Estimated purchase intent.
* Customer engagement.
* Current objection.
* Current conversation stage.
* Products previously shown.
* Questions already asked.
* Previous agent actions.
* Number of conversation turns.
* Current recommendation confidence.

Example:

```text
Budget: $1500
Budget Confidence: 0.90
Performance Preference: 0.85
Portability Preference: 0.70
Battery Preference: 0.55
Price Sensitivity: 0.72
Purchase Intent: 0.61
Current Objection: PRICE
Conversation Stage: COMPARISON
Turn Number: 8
```

---

# 7. POMDP Formulation

The sales problem is modeled as a **Partially Observable Markov Decision Process**.

The true customer state may include:

```text
True budget
Maximum budget
Actual purchase intent
Price sensitivity
Patience
Technical knowledge
Hidden preferences
Brand loyalty
Trust
```

These values are hidden from the agent.

The agent instead receives observations such as:

```text
"I mainly need something for machine learning."

"That's more expensive than I expected."

"I carry my laptop to campus every day."
```

The system estimates a belief state:

$$
b_t=P(s_t|o_{1:t},a_{1:t-1})
$$

The RL policy selects actions using this estimated belief.

---

# 8. Strategy Action Space

The initial discrete action space will contain actions such as:

```text
ASK_BUDGET
ASK_USE_CASE
ASK_PRIORITY
ASK_PERFORMANCE_REQUIREMENT
ASK_PORTABILITY
ASK_BATTERY_REQUIREMENT

SEARCH_PRODUCTS
RECOMMEND_PRODUCT
SHOW_ALTERNATIVE
COMPARE_PRODUCTS

EXPLAIN_FEATURE
EXPLAIN_VALUE
HANDLE_PRICE_OBJECTION
HANDLE_FEATURE_OBJECTION
HANDLE_TRUST_OBJECTION

UPSELL
DOWNSELL

ASK_FOR_PURCHASE
ADD_TO_CART
SCHEDULE_FOLLOWUP

WAIT
END_CONVERSATION
```

The RL model selects the strategic action.

It does **not** generate the sentence itself.

---

# 9. Sales Strategy Reward Function

The reward function will optimize multiple objectives rather than simply maximizing purchases.

A general reward can be represented as:

$$
R =
\alpha R_{task}
+\beta R_{recommendation}
+\gamma R_{information}
+\delta R_{satisfaction}
-\lambda R_{friction}
$$

Possible rewards:

```text
Successful purchase                  +10
Correct product recommendation        +4
Add-to-cart                           +3
Important preference discovered       +1
Useful question                       +0.5

Repeated question                     -1
Irrelevant question                   -1
Bad recommendation                    -2
Unnecessary upsell                    -2
Ignored customer preference           -3
Customer leaves                       -5

Every unnecessary turn               -0.1
```

This prevents the policy from learning overly aggressive sales behavior.

---

# 10. Information-Gain Reward

One of the key research components will be rewarding the salesperson for asking questions that reduce uncertainty.

Suppose the agent initially believes:

```text
Performance importance: 33%
Battery importance:     33%
Portability importance: 34%
```

The agent asks:

> "Will you be carrying this laptop every day?"

The customer says:

> "Yes. Weight and battery life are very important."

The belief becomes:

```text
Performance importance: 15%
Battery importance:     30%
Portability importance: 55%
```

The information gain can be calculated using entropy:

$$
R_{info}=H(b_t)-H(b_{t+1})
$$

If uncertainty decreases:

$$
R_{info}>0
$$

The RL policy can therefore learn:

> Ask useful questions when uncertain, but stop asking once enough information has been collected.

This creates a trade-off between **information acquisition and conversational friction**.

---

# 11. Reinforcement Learning System 2: Voice Interaction Policy

The second RL policy controls real-time conversational behavior.

Its purpose is not to decide the sales strategy.

Instead, it decides:

> Should the agent listen, speak, wait, interrupt, stop speaking, or acknowledge the customer?

The policy is:

$$
\pi_{voice}(a_t|o_t,c_t)
$$

where:

* \(o_t\) = current audio observations.
* \(c_t\) = conversational context.

---

# 12. Voice State

The Voice RL system may observe:

```text
User currently speaking
Agent currently speaking
Speech energy
Voice Activity Detection probability
Length of silence
Partial transcript
Sentence completeness
User interruption
Previous interruption
Speaking rate
Turn duration
Current conversation stage
```

Potential future features:

```text
Pitch
Emotion
Prosody
Stress
Speaking tempo
User engagement
```

---

# 13. Voice Action Space

Possible actions:

```text
LISTEN
WAIT
SPEAK
STOP_SPEAKING
YIELD_TURN
BACKCHANNEL
RESUME
ASK_CLARIFICATION
```

Example:

The agent is currently talking.

The customer suddenly says:

> "Wait, what GPU does it have?"

Voice state:

```text
Agent speaking: TRUE
User speech detected: TRUE
Interruption confidence: HIGH
```

Policy:

```text
STOP_SPEAKING = 0.92
CONTINUE = 0.03
WAIT = 0.05
```

The agent immediately stops speaking and listens.

---

# 14. Voice Reward Function

The voice controller will optimize natural conversational timing.

Example reward:

```text
Correct turn handoff                  +0.5
Appropriate backchannel               +0.2
Fast response after completed turn    +0.3

Interrupt meaningful user speech      -1
Continue after user interruption      -2
Long awkward silence                  -0.5
Prematurely assume turn completion    -0.5
Unnecessary interruption              -1
```

The objective is to reduce rigid VAD-based interaction and produce more natural spoken conversations.

---

# 15. Hierarchical RL Structure

The complete system operates on two timescales.

### Slow Policy — Sales Strategy

Runs approximately once per meaningful conversational turn.

Typical frequency:

**5–30 seconds**

Question answered:

> What should the salesperson do next?

---

### Fast Policy — Voice Interaction

Runs continuously or approximately every:

**200–500 milliseconds**

Question answered:

> Should the agent listen, wait, speak, stop, or yield?

---

The combined architecture becomes:

$$
\pi_{strategy}(a|b_t)
$$

for high-level behavior and:

$$
\pi_{voice}(v|audio_t,context_t)
$$

for low-level conversational control.

---

# 16. Customer Simulation Environment — CustomerGym

Training RL policies directly on real customers would be expensive and unsafe.

Therefore the project will contain a simulated environment called:

**CustomerGym**

Each simulated customer will contain hidden characteristics.

Example:

```text
Budget:               $1400
Maximum Budget:       $1550
Use Case:             Machine Learning
GPU Importance:       0.90
Battery Importance:   0.60
Portability:          0.80
Price Sensitivity:    0.75
Technical Knowledge:  0.70
Patience:             0.40
Brand Preference:     0.10
Purchase Intent:      0.50
```

The RL agent does not receive these values.

An LLM may generate natural customer responses consistent with these hidden variables.

---

# 17. Customer Personas

Different simulated customers will be generated.

Examples include:

### Decisive Customer

Already knows what they want.

### Beginner Customer

Has little product knowledge.

### Price-Sensitive Customer

Strongly reacts to expensive products.

### Technical Customer

Asks detailed technical questions.

### Impatient Customer

Leaves if the agent asks too many questions.

### Skeptical Customer

Challenges recommendations.

### Comparison Shopper

Frequently mentions competing products.

### Contradictory Customer

Requests incompatible features.

### Uncertain Customer

Changes preferences during the conversation.

These different profiles create diverse RL trajectories.

---

# 18. RL Training Algorithm

The initial strategy agent will use:

**Proximal Policy Optimization — PPO**

Reasons:

* Supports sequential decision making.
* Suitable for discrete action spaces.
* Works with custom Gymnasium environments.
* Stable implementation available through Stable-Baselines3.
* Supports long-term rewards.

The policy network can initially be a lightweight MLP.

Example:

```text
Belief State
     ↓
MLP Encoder
     ↓
Hidden Representation
     ↓
Policy Head ─────── Value Head
     ↓                   ↓
Strategy             State Value
```

The system may later compare PPO against alternative algorithms.

---

# 19. Voice RL Training

The Voice RL policy will initially be trained separately from the strategy policy.

Potential training data can be generated through simulated conversational timing events.

Example episode:

```text
User begins speaking
↓
Agent listens
↓
User pauses 250 ms
↓
Agent waits
↓
User continues
↓
Positive reward
```

versus:

```text
User pauses 250 ms
↓
Agent starts speaking
↓
User continues
↓
Agent interrupted user
↓
Negative reward
```

The policy should gradually learn more appropriate timing behavior.

---

# 20. LLM Layer

The LLM will not control the full system.

Instead it will receive:

```text
Current conversation
Customer belief state
Selected RL strategy
Product information
Relevant tool results
```

Example input:

```text
Strategy:
HANDLE_PRICE_OBJECTION

Customer:
ML student
Budget approximately $1500
Price sensitive
Needs strong GPU

Product:
Laptop A — $1699
Laptop B — $1449
```

The LLM converts the strategic action into a natural response.

---

# 21. Product Tool System

The agent will have access to product tools such as:

```text
search_products()
filter_products()
compare_products()
get_product_details()
recommend_products()
add_to_cart()
```

The webpage updates dynamically according to tool results.

For example:

User:

> "Show me something cheaper."

The RL policy selects:

```text
SHOW_ALTERNATIVE
```

The tool layer searches the catalog.

The website displays new products.

The voice agent explains them.

---

# 22. Website Interface

The application will include:

### Product Interface

* Product cards.
* Search results.
* Filtering.
* Product comparison.
* Product details.
* Add-to-cart functionality.

### Voice Interface

* Microphone.
* Streaming speech recognition.
* Agent audio response.
* Live transcription.
* Speaking/listening indicator.

### RL Debug Dashboard

A special research/demo interface will visualize the internal system.

Example:

```text
CUSTOMER BELIEF

Budget sensitivity     82%
GPU importance         91%
Portability            76%
Purchase intent        63%

RL STRATEGY POLICY

Compare products       54%
Recommend              28%
Ask budget             12%
Wait                    5%
Upsell                  1%
```

This makes the learned policy visible during demonstrations.

---

# 23. Baseline Systems

The RL system will be compared against several baselines.

### Baseline 1 — Random Policy

Randomly selects valid actions.

### Baseline 2 — Rule-Based Salesperson

Example:

```text
if budget_unknown:
    ASK_BUDGET
elif use_case_unknown:
    ASK_USE_CASE
else:
    RECOMMEND_PRODUCT
```

### Baseline 3 — LLM Sales Agent

The LLM directly decides the next sales action.

### Baseline 4 — Supervised Policy

A neural network predicts the next sales action from labeled examples.

### Proposed System

PPO-based reinforcement learning policy.

This allows the project to experimentally determine whether RL actually provides benefits.

---

# 24. Evaluation Metrics

The system will be evaluated using several metrics.

### Sales Performance

* Successful task completion rate.
* Purchase rate.
* Add-to-cart rate.
* Recommendation quality.
* Product-preference match.

### Conversation Performance

* Average conversation length.
* Number of unnecessary questions.
* Repeated-question rate.
* Customer abandonment rate.

### RL Performance

* Average episode reward.
* Reward convergence.
* Policy entropy.
* Training stability.

### Information Efficiency

A key metric will be:

$$
Information\ Efficiency=
\frac{Uncertainty\ Reduction}
{Number\ of\ Questions}
$$

This measures how efficiently the agent learns about the customer.

### Voice Metrics

* Interruption rate.
* Average response latency.
* Incorrect turn-taking rate.
* Barge-in recovery rate.
* Silence duration.
* Turn completion accuracy.

---

# 25. Generalization Experiment

Customer personas will be divided into:

```text
Training Personas
Validation Personas
Unseen Test Personas
```

The RL agent will be evaluated on customer types not encountered during training.

This experiment investigates whether the policy learns general sales behavior rather than memorizing simulator patterns.

---

# 26. Proposed Technology Stack

### Frontend

* React
* Vite
* WebSocket
* Web Audio API

### Backend

* Python
* FastAPI
* WebSockets

### Reinforcement Learning

* Gymnasium
* Stable-Baselines3
* PyTorch
* PPO

### AI

* LLM API or local LLM
* Embedding model
* Structured outputs

### Voice

* Streaming STT
* Voice Activity Detection
* TTS or speech-to-speech model
* AudioWorklet for real-time PCM streaming

### Database

* PostgreSQL

Optional:

* Redis for state/session caching.

---

# 27. Development Phases

## Phase 1 — CustomerGym

Build the customer simulation environment.

Deliverables:

* Customer hidden state.
* Product catalog.
* Customer personas.
* Sales actions.
* Rewards.
* Gymnasium environment.

---

## Phase 2 — Strategy RL

Train PPO to select sales actions.

Compare against:

* Random.
* Rule based.
* Supervised.
* LLM.

---

## Phase 3 — Web Sales Agent

Integrate the policy into the website.

Add:

* Product search.
* Product display.
* Comparison.
* Shopping interface.

---

## Phase 4 — Voice Integration

Add:

* STT.
* Streaming microphone.
* LLM response generation.
* TTS.
* Real-time conversation.

---

## Phase 5 — Voice RL

Train the second RL system for:

* Listening.
* Speaking.
* Waiting.
* Barge-in.
* Turn yielding.

---

## Phase 6 — Hierarchical System

Combine:

```text
Strategy RL
+
Voice RL
+
LLM
+
Product Tools
+
Voice Pipeline
```

---

## Phase 7 — Evaluation

Run controlled experiments across simulated customers and compare all baselines.

Produce:

* Reward curves.
* Success rates.
* Policy comparisons.
* Ablation experiments.
* Generalization results.

---

# 28. Main Research Questions

The project will investigate:

### RQ1

Can reinforcement learning learn a better sequential sales strategy than rule-based and LLM-only agents?

### RQ2

Can information-gain rewards teach the agent when to gather more customer information and when to stop asking questions?

### RQ3

Can a policy trained on simulated customer populations generalize to unseen customer personas?

### RQ4

Can an RL-based voice interaction controller improve turn-taking compared with traditional fixed Voice Activity Detection logic?

### RQ5

Does combining long-horizon strategy RL with short-timescale voice RL improve overall conversational task performance?

---

# 29. Main Technical Contribution

The central contribution is a **hierarchical RL architecture operating at two timescales**.

The high-level policy learns:

$$
\boxed{\text{WHAT should the salesperson do?}}
$$

The low-level policy learns:

$$
\boxed{\text{WHEN should the voice agent act?}}
$$

The language model handles:

$$
\boxed{\text{HOW should the action be communicated?}}
$$

This separation prevents the language model from controlling every decision and allows the agent's strategic and conversational behavior to be explicitly learned and evaluated.

---

# 30. Expected Final System

A user visits an online store and speaks naturally:

> "I'm looking for a laptop around $1,500 for machine learning."

The agent:

1. Detects the user turn.
2. Transcribes the speech.
3. Updates its belief about the customer.
4. The Strategy RL policy decides to gather more information.
5. The LLM generates a natural question.
6. The Voice RL policy determines when to respond.
7. The customer provides additional requirements.
8. The agent searches the product database.
9. Matching products appear on the webpage.
10. The RL policy chooses whether to recommend, compare, ask another question, or handle an objection.
11. The process continues until the customer purchases, leaves, or completes the task.

The resulting system is therefore not simply a voice-enabled chatbot.

It is an **adaptive sequential decision-making agent whose sales strategy and conversational behavior are learned through reinforcement learning.**
