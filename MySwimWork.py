import streamlit as st 
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="MySwimWork", page_icon="🏊‍♂️", layout="centered")

# --- CONFIGURAZIONE SUPABASE ---
SUPABASE_URL = "https://lucinfwnhfatkqbkvcmm.supabase.co"
SUPABASE_KEY = "sb_publishable_-B0KFlf9HhJyX61V88X6wQ_7bfu86YD"

# Usa il file caricato direttamente su GitHub
st.set_page_config(
    page_title="MySwimWork", 
    page_icon="Icona.png", 
    layout="centered"
)

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# Inizializza la pagina attiva se non esiste
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Dashboard"

# --- MENU LATERALE ---
with st.sidebar:
    st.subheader("Menu Rapido")
    
    if st.button("📊 Dashboard & Inserimento", use_container_width=True):
        st.session_state.pagina = "Dashboard"
        
    if st.button("🏊‍♂️ Strokes", use_container_width=True):
        st.session_state.pagina = "Strokes"
        
    if st.button("⚙️ Admin Mode", use_container_width=True):
        st.session_state.pagina = "Admin"

# --- PAGINA: DASHBOARD ---
if st.session_state.pagina == "Dashboard":
    st.title("📊 Dashboard")
    st.caption("I tuoi allenamenti, metriche e grafici")
    
    # Form di inserimento rapido
    with st.expander("➕ Aggiungi un nuovo allenamento e tempi", expanded=False):
        with st.form("form_nuovo_allenamento", clear_on_submit=True):
            data_input = st.date_input("Data")
            centrale_input = st.text_input("Centrale (es. 10x100 stile)")
            stile_input = st.selectbox("Stile Principale", ["Stile Libero", "Dorso", "Rana", "Delfino", "Misto"])
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                sforzo_input = st.slider("Sforzo (RPE 1-10)", 1, 10, 5)
            with col_f2:
                battiti_input = st.number_input("Battiti (BPM)", min_value=60, max_value=220, value=130, step=10)
                
            # Campo per inserire più tempi separati da virgola
            tempi_input = st.text_input("Tempi delle ripetute (es. 01:15, 01:14)")
            
            note_input = st.text_area("Note e Sensazioni")
            
            btn_salva = st.form_submit_button("Salva nel Cloud")
            
            if btn_salva:
                # 'Battiti' con la B maiuscola come richiesto dal database
                nuovo_record = {
                    "Data": str(data_input),
                    "Centrale": centrale_input,
                    "Stile": stile_input,
                    "Sforzo": sforzo_input,
                    "Battiti": battiti_input,
                    "Note": note_input
                }
                try:
                    # 1. Inserisci l'allenamento principale e ottieni l'ID generato
                    res_allenamento = supabase.table("allenamenti").insert(nuovo_record).execute()
                    
                    if res_allenamento.data:
                        allenamento_id = res_allenamento.data[0]["id"]
                        
                        # 2. Se hai inserito dei tempi, dividili e salvali nella tabella 'tempi'
                        if tempi_input.strip():
                            lista_tempi = [t.strip() for t in tempi_input.split(",")]
                            for t in lista_tempi:
                                record_tempo = {
                                    "allenamento_id": allenamento_id,
                                    "Tempo": t
                                }
                                supabase.table("tempi").insert(record_tempo).execute()
                                
                    st.success("Allenamento e tempi salvati con successo!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Errore durante il salvataggio: {err}")

    st.markdown("---")
    
    # Lettura dati e visualizzazione
    try:
        risposta = supabase.table("allenamenti").select("*").execute()
        dati = risposta.data
        
        if dati:
            df = pd.DataFrame(dati)
            
            # Normalizziamo i nomi delle colonne in minuscolo per gestirli comodamente in pandas
            df.columns = [str(col).lower() for col in df.columns]
            
            if "data" in df.columns:
                df["data"] = pd.to_datetime(df["data"])
                df = df.sort_values("data")
            
            totale_sessioni = len(df)
            
            sforzo_medio = 0
            if "sforzo" in df.columns and not df["sforzo"].isnull().all():
                sforzo_medio = round(df["sforzo"].mean(), 1)
                
            battiti_medio = 0
            if "battiti" in df.columns and not df["battiti"].isnull().all():
                battiti_medio = round(df["battiti"].mean(), 1)
            
            # Metriche principali
            col1, col2, col3 = st.columns(3)
            col1.metric("Sessioni", f"{totale_sessioni}")
            col2.metric("Sforzo Medio (RPE)", f"{sforzo_medio}/10")
            col3.metric("Battiti Medi", f"{battiti_medio} BPM")
            
            st.markdown("---")
            
            # Grafico Sforzo (solo RPE)
            st.subheader("📈 Andamento dello Sforzo (RPE) nel Tempo")
            if "sforzo" in df.columns and "data" in df.columns:
                df_grafico = df.set_index("data")[["sforzo"]]
                st.line_chart(df_grafico)
            else:
                st.info("Dati insufficienti per generare il grafico dello sforzo.")
            
            st.markdown("---")
            st.subheader("Storico Allenamenti")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nessun allenamento trovato. Usa il riquadro sopra per aggiungere il primo!")
            
    except Exception as e:
        st.warning(f"Errore nel caricamento dei dati: {e}")

# --- PAGINA: STROKES ---
elif st.session_state.pagina == "Strokes":
    st.title("🏊‍♂️ Analisi Tempi e Lavori")
    st.caption("Seleziona un centrale per visualizzare la serie completa dei tempi e la media")
    
    try:
        # 1. Recuperiamo tutti gli allenamenti per mostrare i centrali disponibili
        res_allenamenti = supabase.table("allenamenti").select("id, Data, Centrale, Stile").execute()
        dati_allenamenti = res_allenamenti.data
        
        if dati_allenamenti:
            # Creiamo una lista di opzioni formattate per il menu a tendina
            opzioni = {}
            for row in dati_allenamenti:
                data_str = str(row.get("Data", ""))[:10]
                centrale = row.get("Centrale", "Senza nome")
                stile = row.get("Stile", "")
                etichetta = f"{data_str} - {centrale} ({stile})"
                opzioni[etichetta] = row["id"]
            
            # Menu a tendina per selezionare il lavoro
            scelta = st.selectbox("Seleziona il centrale:", list(opzioni.keys()))
            allenamento_id_selezionato = opzioni[scelta]
            
            st.markdown("---")
            
            # 2. Recuperiamo i tempi legati all'allenamento selezionato
            res_tempi = supabase.table("tempi").select("*").eq("allenamento_id", allenamento_id_selezionato).execute()
            dati_tempi = res_tempi.data
            
            if dati_tempi:
                df_tempi = pd.DataFrame(dati_tempi)
                
                # Pulizia colonne
                df_tempi.columns = [str(col).lower() for col in df_tempi.columns]
                
                st.subheader(f"⏱️ Tempi registrati per: {scelta.split(' - ')[1]}")
                
                # Selezioniamo solo le colonne rilevanti
                if "tempo" in df_tempi.columns:
                    col_mostra = ["tempo"]
                    if "id" in df_tempi.columns:
                        col_mostra.insert(0, "id")
                    
                    st.dataframe(df_tempi[col_mostra], use_container_width=True)
                    
                    # Conteggio ripetute
                    st.info(f"Totale ripetute registrate: **{len(df_tempi)}**")
                else:
                    st.dataframe(df_tempi, use_container_width=True)
            else:
                st.warning("Nessun tempo inserito per questo specifico allenamento.")
        else:
            st.info("Non ci sono allenamenti salvati nel database per mostrare i tempi.")
            
    except Exception as e:
        st.error(f"Errore durante il recupero dei tempi: {e}")

# --- PAGINA: ADMIN ---
elif st.session_state.pagina == "Admin":
    st.title("⚙️ Pannello di Amministrazione")
    st.write("Area configurazioni e gestione avanzata.")
