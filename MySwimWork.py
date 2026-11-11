import streamlit as st 
import pandas as pd
from supabase import create_client, Client


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

# --- MENU LATERALE (aggiornato con il Convertitore) ---
with st.sidebar:
    st.subheader("Menu Rapido")
    
    if st.button("📊 Dashboard & Inserimento", use_container_width=True):
        st.session_state.pagina = "Dashboard"
        
    if st.button("🏊‍♂️ Strokes", use_container_width=True):
        st.session_state.pagina = "Strokes"

    if st.button("⏱️ Convertitore", use_container_width=True):
        st.session_state.pagina = "Convertitore"
        
    if st.button("⚙️ Admin Mode", use_container_width=True):
        st.session_state.pagina = "Admin"

# --- PAGINA: DASHBOARD ---
if st.session_state.pagina == "Dashboard":
    st.title("📊 Dashboard")
    st.caption("I tuoi allenamenti, metriche e grafici")
    
    with st.expander("➕ Aggiungi un nuovo allenamento e tempi", expanded=False):
        with st.form("form_nuovo_allenamento", clear_on_submit=True):
            data_input = st.date_input("Data")
            centrale_input = st.text_input("Centrale (es. 10x100 stile)")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                stile_input = st.selectbox("Stile Principale", ["Stile Libero", "Dorso", "Rana", "Delfino", "Misto"])
            with col_s2:
                categoria_input = st.selectbox("Categoria Lavoro", ["A1", "A2", "B1", "B2", "B3", "C1", "C2"])
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                sforzo_input = st.slider("Sforzo (RPE 1-10)", 1, 10, 5)
            with col_f2:
                battiti_input = st.number_input("Battiti (BPM)", min_value=60, max_value=220, value=130, step=1)
                
            tempi_input = st.text_input("Tempi delle ripetute (es. 01:15, 01:14)")
            note_input = st.text_area("Note e Sensazioni")
            
            btn_salva = st.form_submit_button("Salva nel Cloud")
            
            if btn_salva:
                nuovo_record = {
                    "Data": str(data_input),
                    "Centrale": centrale_input,
                    "Stile": stile_input,
                    "Categoria": categoria_input,
                    "Sforzo": sforzo_input,
                    "Battiti": battiti_input,
                    "Note": note_input
                }
                try:
                    res_allenamento = supabase.table("allenamenti").insert(nuovo_record).execute()
                    
                    if res_allenamento.data:
                        allenamento_id = res_allenamento.data[0]["id"]
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
    
    try:
        risposta = supabase.table("allenamenti").select("*").execute()
        dati = risposta.data
        
        if dati:
            df = pd.DataFrame(dati)
            df.columns = [str(col).lower() for col in df.columns]
            
            if "data" in df.columns:
                df["data"] = pd.to_datetime(df["data"])
                df = df.sort_values("data")
            
            totale_sessioni = len(df)
            sforzo_medio = round(df["sforzo"].mean(), 1) if "sforzo" in df.columns and not df["sforzo"].isnull().all() else 0
            battiti_medio = round(df["battiti"].mean(), 1) if "battiti" in df.columns and not df["battiti"].isnull().all() else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Sessioni", f"{totale_sessioni}")
            col2.metric("Sforzo Medio (RPE)", f"{sforzo_medio}/10")
            col3.metric("Battiti Medi", f"{battiti_medio} BPM")
            
            st.markdown("---")
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


# --- PAGINA: CONVERTITORE VASCHE ---
elif st.session_state.pagina == "Convertitore":
    st.title("⏱️ Convertitore Vasca Corta ⇄ Vasca Lunga")
    st.caption("Converti i tuoi tempi tra vasca da 25m (SCM) e vasca da 50m (LCM).")

    tabella_differenziali = {
        "50 stile libero": {"Uomini": 0.80, "Donne": 0.70},
        "100 stile libero": {"Uomini": 1.75, "Donne": 1.50},
        "200 stile libero": {"Uomini": 3.75, "Donne": 3.30},
        "400 stile libero": {"Uomini": 8.50, "Donne": 7.20},
        "800 stile libero": {"Uomini": 18.35, "Donne": 14.80},
        "1500 stile libero": {"Uomini": 37.00, "Donne": 28.50},
        "50 dorso": {"Uomini": 1.45, "Donne": 1.25},
        "100 dorso": {"Uomini": 3.00, "Donne": 2.60},
        "200 dorso": {"Uomini": 6.40, "Donne": 5.60},
        "50 rana": {"Uomini": 0.85, "Donne": 0.70},
        "100 rana": {"Uomini": 2.60, "Donne": 2.20},
        "200 rana": {"Uomini": 5.90, "Donne": 4.90},
        "50 farfalla": {"Uomini": 0.50, "Donne": 0.45},
        "100 farfalla": {"Uomini": 1.40, "Donne": 1.35},
        "200 farfalla": {"Uomini": 3.75, "Donne": 3.30},
        "200 misti": {"Uomini": 5.00, "Donne": 4.50},
        "400 misti": {"Uomini": 11.60, "Donne": 9.80}
    }

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        sesso_scelto = st.selectbox("Sesso", ["Uomini", "Donne"])
    with col_c2:
        gara_scelta = st.selectbox("Gara", list(tabella_differenziali.keys()))

    scelta_conversione = st.radio(
        "Cosa vuoi fare?",
        [
            "LCM -> SCM",
            "SCM -> LCM"
        ]
    )

    tempo_str = st.text_input("Inserisci il tempo (es. 01:05.50 o 28.40)", "01:00.00")

    if st.button("Converti Tempo", use_container_width=True):
        try:
            def stringa_a_secondi(t_str):
                t_str = t_str.strip().replace("'", ":").replace('"', ".")
                parti = t_str.split(":")
                if len(parti) == 2:
                    return int(parti[0]) * 60 + float(parti[1])
                else:
                    return float(parti[0])

            def secondi_a_stringa(sec_tot):
                if sec_tot < 0:
                    sec_tot = 0
                m = int(sec_tot // 60)
                s = sec_tot % 60
                if m > 0:
                    return f"{m:02d}:{s:05.2f}"
                else:
                    return f"{s:05.2f}"

            secondi_input = stringa_a_secondi(tempo_str)
            diff = tabella_differenziali[gara_scelta][sesso_scelto]

            if scelta_conversione == "LCM -> SCM":
                # Da Lunga a Corta (sottrae)
                risultato_sec = secondi_input - diff
                tipo_arrivo = "Vasca Corta (25m - SCM)"
                operazione = f"Sottratti {diff} secondi"
            else:
                # Da Corta a Lunga (aggiunge)
                risultato_sec = secondi_input + diff
                tipo_arrivo = "Vasca Lunga (50m - LCM)"
                operazione = f"Aggiunti {diff} secondi"

            tempo_finale = secondi_a_stringa(risultato_sec)

            st.success(f"Risultato per **{gara_scelta}** ({sesso_scelto}): **{tempo_finale}** in **{tipo_arrivo}**")
            st.info(f"Differenziale: {operazione}")

        except Exception as err:
            st.error(f"Errore nel formato del tempo inserito. Usa un formato valido come 01:15.20 oppure 28.50. Dettaglio: {err}")            

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
