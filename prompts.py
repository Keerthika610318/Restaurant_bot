from langchain.prompts import PromptTemplate

# --- Prompt Templates ---
menu_prompt = PromptTemplate(
    input_variables=["menu_data"],
    template=(
        "You are a helpful assistant for displaying the restaurant's menu.\n"
        "Below is the list of available menu items with their prices:\n\n"
        "{menu_data}\n\n"
        "Please list each item exactly once, in a clean and readable format like:\n"
        "- Item Name: $Price\n\n"
        "Avoid duplicates or made-up items. Just format the data cleanly for the user."
    )
)

item_order_prompt = PromptTemplate(
    input_variables=["history", "input", "menu_items", "last_ordered_item"],
    template=(
        "You are an intelligent restaurant order assistant.\n"
        "Here is the menu:\n{menu_items}\n\n"
        "User wants to place an order. Use the context below:\n"
        "- Last ordered item (if any): {last_ordered_item}\n"
        "- Conversation history: {history}\n"
        "- New input: {input}\n\n"
        "Identify item(s), quantity, and price per item from the menu. Respond in this format:\n"
        "- Item: Name\n- Quantity: X\n- Unit Price: ₹Y\n- Total: ₹(X×Y)\n\n"
        "Only respond with the confirmed ordered item summary."
    )
)

description_prompt = PromptTemplate(
    input_variables=["input", "menu_items"],
    template=(
        "You are a restaurant assistant specializing in describing food items.\n"
        "Here is the menu data:\n{menu_items}\n\n"
        "Based on this, provide a brief, sensory-rich description of the item mentioned in the input.\n\n"
        "User input: {input}\n\n"
        "Respond with a friendly, informative description."
    )
)

price_query_prompt = PromptTemplate(
    input_variables=["input", "menu_items"],
    template=(
        "You are a helpful restaurant assistant that provides accurate prices for menu items.\n"
        "Here is the current menu data:\n{menu_items}\n\n"
        "The customer asked the following:\n\"{input}\"\n\n"
        "Please identify the item(s) mentioned in the input and respond with their exact price(s) from the menu.\n"
        "If the item is not on the menu, politely let the user know it isn't available.\n"
        "Format the response like:\n- Item Name: $Price"
    )
)

order_summary_prompt = PromptTemplate(
    input_variables=["history", "input", "user_current_order_json"],
    template=(
        "You are a helpful food ordering assistant. Below is the structured JSON containing the current order placed by the user:\n"
        "{user_current_order_json}\n\n"
        "Your job is to extract the item name, quantity, and unit price for each item.\n"
        "Then calculate the total price for each item as (Quantity × Unit Price).\n"
        "Finally, calculate the grand total for all items.\n\n"
        "Format the output like this:\n"
        "- Item: <name>\n"
        "  - Quantity: <number>\n"
        "  - Unit Price: ₹<amount>\n"
        "  - Total: ₹<quantity × price>\n"
        "\nGrand Total: ₹<sum of all totals>\n\n"
        "Ignore unrelated conversation history.\n"
        "User: {input}\n\n"
        "Summary of ordered items with prices:"
    )
)

default_prompt = PromptTemplate(
    input_variables=["input"],
    template="I'm sorry, I didn't understand that. Could you please rephrase?\n\nUser: {input}"
)

