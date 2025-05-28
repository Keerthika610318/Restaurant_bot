#  Restaurant Bot

## Project Overview

This is an AI-powered conversational bot designed to help users with restaurant-related queries, such as `(mention specific functionalities, e.g., finding restaurants, making reservations, answering menu questions, providing recommendations, etc.)`. It leverages `(mention key technologies like Large Language Models (LLMs), specific APIs, etc.)` to provide an interactive and helpful experience.

##  Getting Started

Follow these steps to set up and run the Restaurant Bot on your local machine.

### 1. Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.x** (`(e.g., Python 3.9 or higher is recommended)`)
* **pip** (Python package installer, usually comes with Python) 
* **Git** (for cloning the repository)

### 2. Clone the Repository

Open your terminal or command prompt and clone the project:

```bash
git clone [https://github.com/Keerthika610318/Restaurant_bot.git](https://github.com/Keerthika610318/Restaurant_bot.git)
cd Restaurant_bot
```

### 3. Environment Setup (API Keys & Credentials)
* **cp .env.example .env**
* **For Windows users, use: copy .env.example .env**
* **If you are on Windows, you might use: copy .env.example .env**
* **Fill in your Credentials**
* **Install dependency**
* **Run your main_code** 

```bash
python -m uvicorn main_code:app --reload
```


### 4. Architectural Flow: How the Bot Works

1.  **Application Initialization & Data Loading (`main_code.py`):**
    * The FastAPI application (`app`) is initialized.
    * **Menu data (`data_new.csv`)** is loaded using Pandas. This data is pre-processed (e.g., product names are normalized, descriptions and prices are formatted) to be ready for both display and LLM consumption.
    * Global stores for `user_orders` and `last_ordered_item_for_user` are initialized to manage conversational state across sessions.
    * Logging is configured for real-time insights into the bot's operation.

2.  **LLM Configuration (`apisetting.py`):**
    * Environment variables for Azure OpenAI credentials (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME`, `AZURE_OPENAI_API_VERSION`) are loaded using `python-dotenv`.
    * The `AzureChatOpenAI` LLM instance is initialized with these credentials and specific parameters (e.g., `model="gpt-3.5-turbo"`, `temperature=0.3`, `max_tokens=500`). This `llm` instance is then used throughout the LangChain components.

3.  **Prompt Definitions (`prompts.py`):**
    * Various `PromptTemplate`s are defined for different conversational intents. Each prompt is carefully crafted to guide the LLM's behavior for specific tasks. Key prompts include:
        * **`menu_prompt`**: Formats the menu data for display.
        * **`item_order_prompt`**: Guides the LLM to identify items, quantities, and prices for ordering, considering history and last ordered item.
        * **`description_prompt`**: Directs the LLM to provide rich descriptions of menu items.
        * **`price_query_prompt`**: Helps the LLM extract and provide exact prices for requested items.
        * **`order_summary_prompt`**: Instructs the LLM to summarize the user's current order from a structured JSON.
        * **`default_prompt`**: A fallback for unhandled queries.

4.  **Specialized LLM Chains (`chains.py`):**
    * Each specific `PromptTemplate` is paired with the configured LLM (`llm` from `apisetting.py`) to create dedicated `LLMChain`s (e.g., `menu_chain`, `item_order_processor_chain`, `description_chain`). These chains represent the core logic for each conversational intent.

5.  **Intelligent Intent Routing (`chains.py` & `main_code.py`):**
    * A sophisticated `LLMRouterChain` (`router_chain_general`) is set up using `MULTI_PROMPT_ROUTER_TEMPLATE`.
    * This router acts as the brain, analyzing the user's incoming message (`input`) and dynamically directing it to the most appropriate specialized `LLMChain` (from `destination_chains_general`).
    * The router's decision is based on detailed descriptions of each destination chain's purpose (e.g., "Menu Viewer: Shows the full menu with prices...").

6.  **Conversation Memory Management (`main_code.py`):**
    * When a user sends a message to the `/chat` endpoint, `get_user_memory` retrieves or initializes a `ConversationSummaryBufferMemory` instance for that specific `user_id`.
    * This memory (`history`) is continuously updated with the user's input and the bot's response, allowing the LLM to maintain contextual awareness throughout the conversation.

7.  **Order Processing Endpoints (`main_code.py`):**
    * Dedicated FastAPI endpoints handle specific, structured actions:
        * `/order/add`: Processes requests to add items to a user's order. It validates items against `data_new.csv`, updates the `user_orders` dictionary, and calculates current totals. It also handles scenarios like prompting for quantity if not provided.
        * `/order/summary_direct`: Provides a direct summary of the user's current order from the `user_orders` dictionary, formatting it with item details and a grand total.

8.  **Main Chat Endpoint Logic (`main_code.py` - `@app.post("/chat")`):**
    * Upon receiving a user's message, the bot first fetches the user's conversation `memory`.
    * The `router_chain_general` is invoked to determine the user's intent (`tool_name`).
    * Based on the `tool_name`, the corresponding specialized `LLMChain` is selected from `destination_chains_general`.
    * Relevant context (like `menu_items`, `menu_data`, `history`, `last_ordered_item`, and the current `user_current_order_json`) is dynamically passed to the chosen chain.
    * The selected chain processes the input and generates a response.
    * If no specific tool matches, the `default_chain` is used.
    * Finally, the conversation `memory` is updated with the user's input and the bot's output, and the response is returned via the FastAPI API.
