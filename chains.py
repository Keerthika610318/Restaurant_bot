from langchain.chains import LLMChain
from langchain.chains.router.multi_prompt_prompt import MULTI_PROMPT_ROUTER_TEMPLATE
from langchain.prompts import PromptTemplate
from prompts import ( 
    menu_prompt, description_prompt, price_query_prompt,
    item_order_prompt, order_summary_prompt, default_prompt
)
from langchain.chains import LLMChain
from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser
from apisetting import llm

# --- LLM Chains ---
menu_chain = LLMChain(llm=llm, prompt=menu_prompt)
item_order_processor_chain = LLMChain(llm=llm, prompt=item_order_prompt)
description_chain = LLMChain(llm=llm, prompt=description_prompt)
price_chain = LLMChain(llm=llm, prompt=price_query_prompt)
order_summary_formatter_chain = LLMChain(llm=llm, prompt=order_summary_prompt)
default_chain = LLMChain(llm=llm, prompt=default_prompt)

# --- Routing ---
destination_chains_general = {
    "Menu Viewer": menu_chain,
    "Description Expert": description_chain,
    "Price Checker": price_chain,
    "Order Summary": order_summary_formatter_chain,
    "Item Order Processor": item_order_processor_chain
}

destinations_info_general = [
    {"name": "Menu Viewer", "description": "Shows the full menu with prices..."},
    {"name": "Description Expert", "description": "Gives item descriptions..."},
    {"name": "Price Checker", "description": "Tells the price of an item from the menu"},
    {"name": "Order Summary", "description": "Summarizes the users current order..."},
    {"name": "Item Order Processor", "description": "Handles user requests to add items..."},
]

destinations_general_formatted = [f"{d['name']}: {d['description']}" for d in destinations_info_general]
router_prompt_general = PromptTemplate(
    template=MULTI_PROMPT_ROUTER_TEMPLATE.format(destinations="\n".join(destinations_general_formatted)),
    input_variables=["input"],
    output_parser=RouterOutputParser()
)

router_chain_general = LLMRouterChain.from_llm(llm, router_prompt_general)