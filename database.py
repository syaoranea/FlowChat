from supabase import create_client, Client

SUPABASE_URL = "https://lnefzhascwowivljwgee.supabase.co"
SUPABASE_KEY = "sb_publishable_jhjF1zVN7FG-ouby95N3dQ_O3ZMZPtQ"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_table_data(table_name: str, limit: int = 10):
    try:
        response = supabase.table(table_name).select("*").limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"❌ ERRO ao buscar tabela '{table_name}':", e)
        return None
