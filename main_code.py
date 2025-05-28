
import json
import pandas as pd
from langchain.memory import ConversationSummaryBufferMemory
from fastapi import FastAPI, HTTPException,Query
from pydantic import BaseModel
from apisetting import llm
import asyncio
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,  # Use DEBUG for even more detailed logs
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# --- Load Menu Data ---
menu_df = pd.read_csv("data_new.csv")
menu_df['Description'] = menu_df['Description'].astype(str)
menu_df['products'] = menu_df['products'].astype(str)
menu_df['price'] = menu_df['price'].astype(float)
menu_df["normalized_products"] = menu_df["products"].str.lower().str.strip()

# Format menu strings
menu_data_for_llm = "\n".join([f"- {row['products']}: ${row['price']} (Description: {row['Description']})" for _, row in menu_df.iterrows()])
display_menu_str = "\n".join([f"- {row['products']}: ${row['price']}" for _, row in menu_df.iterrows()])

# Global stores
user_orders = {}
last_ordered_item_for_user = {}

from prompts import (
    menu_prompt,
    item_order_prompt,
    description_prompt,
    price_query_prompt,
    order_summary_prompt,
    default_prompt
)

# --- Memory ---
memories = {}

def get_user_memory(user_id):
    if user_id not in memories:
        memories[user_id] = ConversationSummaryBufferMemory(
            llm=llm,
            max_token_limit=2000,
            memory_key="history",
            return_messages=False
        )
    return memories[user_id]

from chains import (
    menu_chain, item_order_processor_chain, description_chain,
    price_chain, order_summary_formatter_chain, default_chain,
    destination_chains_general, router_chain_general
)
# --- FastAPI App ---
app = FastAPI()
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Restaurant Chatbot API!"}

@app.post("/order/add")
async def add_to_order(
    user_id: str = Query(...),
    ordered_item_name: str = Query(...),
    quantity: int = Query(...)
):
    if quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative.")
    try:
        normalized = ordered_item_name.strip().lower()
        # Async-safe menu match
        matched_row = await asyncio.to_thread(
            lambda: menu_df[menu_df["normalized_products"] == normalized]
        )
        if matched_row.empty:
            raise HTTPException(status_code=404, detail=f"No item named '{ordered_item_name}' found in menu.")

        name = matched_row["products"].iloc[0]
        price = float(matched_row["price"].iloc[0])

        if quantity == 0:
            last_ordered_item_for_user[user_id] = name
            return {
                "status": "pending_quantity",
                "message": f"'{name}' selected. Price: ₹{price:.2f}. How many?"
            }

        user_orders.setdefault(user_id, {})
        user_orders[user_id].setdefault(normalized, {"quantity": 0, "price": price})
        user_orders[user_id][normalized]["quantity"] += quantity
        last_ordered_item_for_user.pop(user_id, None)

        total = sum(i["quantity"] * i["price"] for i in user_orders[user_id].values())

        return {
            "status": "success",
            "message": f"Added {quantity} x {name}. Total: ₹{total:.2f}.",
            "current_order_total": round(total, 2),
            "ordered_item_info": {
                "item": name,
                "quantity": quantity,
                "price": price
            }
        }
    except Exception as e:
        logger.exception(f"Error in /order/add for user '{user_id}' and item '{ordered_item_name}'")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    
@app.get("/order/summary_direct")
async def get_order_summary_direct(user_id: str = "default_user"):
    if user_id not in user_orders or not user_orders[user_id]:
        return {"message": "No active order.", "order_items": [], "total_price": 0.0}

    try:
        summary = []
        total = 0.0

        for k, v in user_orders[user_id].items():
            # Get the original product name safely
            original_row = await asyncio.to_thread(
                lambda: menu_df[menu_df["normalized_products"] == k]
            )
            if original_row.empty:
                original_name = k  # fallback
            else:
                original_name = original_row["products"].iloc[0]

            item_total = v["quantity"] * v["price"]
            summary.append({
                "item_name": original_name,
                "quantity": v["quantity"],
                "unit_price": v["price"],
                "item_total": round(item_total, 2)
            })
            total += item_total

        return {
            "message": f"Raw summary for {user_id}:",
            "order_items": summary,
            "total_price": round(total, 2)
        }

    except Exception as e:
        logger.exception(f"Error summarizing order for user '{user_id}'")
        raise HTTPException(status_code=500, detail="Failed to summarize order.")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_id = request.user_id
    user_message = request.message
    logger.info(f"New chat request from user '{user_id}': '{user_message}'")
    try:
        # Assume get_user_memory is sync; run in thread to avoid blocking event loop
        memory = await asyncio.to_thread(get_user_memory, user_id)
        logger.info(f"Memory retrieved for user '{user_id}' (buffer length: {len(memory.buffer) if memory.buffer else 0})")

        logger.info("Getting router decision...")
        router_decision = await router_chain_general.ainvoke({"input": user_message})
        logger.info(f"Router decision: {router_decision}")

        tool_name = router_decision.get("destination")
        inputs = router_decision.get("next_inputs")

        if not isinstance(inputs, dict):
            inputs = {"input": inputs}

        logger.info(f"Selected tool: '{tool_name}', with inputs: {inputs}")

        if tool_name in destination_chains_general:
            chain = destination_chains_general[tool_name]
            logger.info(f"Executing tool chain: '{tool_name}'")

            chain_inputs = {
                **inputs,
                "menu_items": menu_data_for_llm,
                "menu_data": display_menu_str,
                "history": memory.buffer,
                "last_ordered_item": last_ordered_item_for_user.get(user_id, "None"),
                "user_current_order_json": json.dumps(user_orders.get(user_id, {}))
            }
            logger.debug(f"Prepared inputs for chain '{tool_name}': keys={list(chain_inputs.keys())}")

            response_content = await chain.ainvoke(chain_inputs)

            output_text = response_content.get("text") if isinstance(response_content, dict) else str(response_content)
            output_text = str(output_text)
            await asyncio.to_thread(memory.save_context, {"input": user_message}, {"output": output_text})
            logger.info(f"Response from '{tool_name}' saved to memory for user '{user_id}'")
            return {"tool": tool_name, "response": output_text}

        else:
            logger.warning(f"No tool matched for message: '{user_message}', using default chain.")
            response_content = await default_chain.ainvoke(inputs)
            output_text = response_content.get("text") if isinstance(response_content, dict) else str(response_content)
            output_text = str(output_text)
            await asyncio.to_thread(memory.save_context, {"input": user_message}, {"output": output_text})
            logger.info(f"Default response saved to memory for user '{user_id}'")

            return {"tool": "Default", "response": output_text}

    except Exception as e:
        logger.exception(f"Unhandled error in /chat for user '{user_id}' with message '{user_message}'")
        raise HTTPException(status_code=500, detail="Internal server error processing your request.")