
import os
import psycopg2
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# LLM y memoria
llm = ChatOpenAI(
    temperature=0,
    openai_api_key=os.environ["OPENAI_API_KEY"],
    model_name="gpt-4"
)
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory)

# Conexión a PostgreSQL
def get_pg_connection():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"]
    )

# Traducción básica de intención a SQL
def build_sql(intent: str, month: str = "2025-05", location=None, subsidiary=None):
    filters = [f"period = '{month}'"]

    if intent == "ventas":
        filters.append("cashflowcategory = 'Revenues'")
    elif intent == "gross_margin":
        filters.append("cashflowcategory IN ('Revenues', 'COGS')")
    elif intent == "ebitda":
        filters.append("cashflowcategory IN ('Revenues', 'COGS', 'EBITDA', 'EBITDA4WALL')")

    if location:
        filters.append(f"location = '{location}'")
    if subsidiary:
        filters.append(f"subsidiary = '{subsidiary}'")

    where_clause = " AND ".join(filters)
    return f"SELECT SUM(balance) as total FROM pl_ledger WHERE {where_clause};"

# Interpretar intención desde LLM
def extract_intent_and_filters(question: str):
    system_prompt = """
Eres un analista financiero. Tu tarea es interpretar la intención de una pregunta y extraer:
- intención: ventas / gross_margin / ebitda
- mes: en formato YYYY-MM (ej. 2025-05)
- location: si se menciona una tienda
- subsidiary: si se menciona una subsidiaria

Responde en JSON con las claves: intent, month, location, subsidiary. Si falta algo, deja null.
    """

    prompt = f"{system_prompt}\n\nPregunta: {question}"
    raw = llm.predict(prompt)

    import json
    try:
        parsed = json.loads(raw)
        return parsed
    except:
        return {"intent": None, "month": None, "location": None, "subsidiary": None}

# Función principal del chat
async def chat_with_memory(message: str) -> str:
    context = extract_intent_and_filters(message)

    intent = context.get("intent")
    month = context.get("month") or "2025-05"
    location = context.get("location")
    subsidiary = context.get("subsidiary")

    if intent in ["ventas", "gross_margin", "ebitda"]:
        sql = build_sql(intent, month, location, subsidiary)
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute(sql)
            result = cur.fetchone()
            cur.close()
            conn.close()
            return f"El total para {intent.replace('_', ' ')} en {month} es: {result[0]:,.2f} €"
        except Exception as e:
            return f"Error ejecutando SQL: {str(e)}"
    else:
        return conversation.run(message)
