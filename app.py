import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import numpy as np

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Autovalutazione Potere Personale", layout="centered")

# --- COLORI PERSONALIZZATI ---
COLOR_PRIMARY = "#1E88E5" 
COLOR_SECONDARY = "#FFC107" 
COLOR_BG_RED = "#FFCDD2"
COLOR_BG_GREEN = "#C8E6C9"

# --- FUNZIONI DI UTILITÀ ---

def connect_to_gsheet():
    """Connette a Google Sheet usando i Secrets di Streamlit"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Database_Self_Empowerment").sheet1
        return sheet
    except Exception as e:
        # Log silenzioso in console (non visibile all'utente)
        print(f"Errore connessione DB (Silenzioso): {e}")
        return None

def save_data(data_row):
    """Salva una riga di dati su Google Sheet in modo silenzioso"""
    sheet = connect_to_gsheet()
    if sheet:
        try:
            sheet.append_row(data_row)
            return True
        except Exception as e:
            # Log silenzioso in console
            print(f"Errore salvataggio riga (Silenzioso): {e}")
            return False
    return False

def create_gauge(value, title, min_v, max_v, ranges, colors):
    """Crea un grafico a tachimetro (Gauge) con Plotly"""
    
    steps = []
    for i in range(len(ranges)-1):
        steps.append({'range': [ranges[i], ranges[i+1]], 'color': colors[i]})

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        gauge = {
            'axis': {'range': [min_v, max_v]},
            'bar': {'color': "black"},
            'steps': steps,
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# --- UI PRINCIPALE ---

# 1. HEADER E LOGO
try:
    st.image("GENERA Logo Colore.png", use_container_width=True) 
except:
    # Nessun errore visibile, solo un warning log
    print("Immagine logo non trovata")

st.title("Autovalutazione del Potere Personale")

# 2. SEZIONE INTRODUTTIVA
st.markdown("""
### Il Modello di Riferimento
Il sentimento di potere personale (**Self-Empowerment**) è esito di un processo psicologico di apertura di nuove possibilità di essere e di agire (Bruscaglioni & Gheno, 2000).
Si basa su 4 fasi operative:
1.  **Dialettica bisogno-desiderio**: all'emergere di un bisogno (mancanza di) si attiva la funzione desiderante della persona (tensione verso).
2.  **Costruzione di una pensabilità positiva**: il desiderio si specifica e inizia a diventare progetto.
3.  **Mobilitazione delle risorse**: ricerca delle risorse interne ed esterne per implementare il progetto.
4.  **Depotenziamento dei killer psicologici**: riduzione dell'impatto degli ostacoli soggettivi che accompagnano l'attivarsi del desiderio (paure, incapacità, mancanza di autostima, sfiducia, ecc.).

**Obiettivo:** Questa autovalutazione ti aiuta a riflettere su quanto ti senti dotato di potere personale, inteso come confidenza circa il disporre di possibilità di azione.

---
""")

st.markdown("""
<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-size: 0.8em;'>
<strong>Proseguendo nella compilazione acconsento a che i dati raccolti potranno essere utilizzati in forma aggregata esclusivamente per finalità statistiche.</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# 3. FORM DATI E QUESTIONARIO
with st.form("questionario_form"):
    
    # --- ANAGRAFICA ---
    st.subheader("Informazioni Socio-Anagrafiche")
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome o Nickname")
        eta = st.selectbox("Età", ["fino a 20 anni", "21-30 anni", "31-40 anni", "41-50 anni", "51-60 anni", "61-70 anni", "più di 70 anni"])
        titolo_studio = st.selectbox("Titolo di studio", ["licenza media", "qualifica professionale", "diploma di maturità", "laurea triennale", "laurea magistrale (o ciclo unico)", "titolo post lauream"])
    
    with col2:
        genere = st.selectbox("Genere", ["maschile", "femminile", "non binario", "non risponde"])
        job = st.selectbox("Job", ["imprenditore", "top manager", "middle manager", "impiegato", "operaio", "tirocinante", "libero professionista"])

    st.markdown("---")

    # --- QUESTIONARIO (SCALA LIKERT 6 PUNTI) ---
    st.subheader("Autovalutazione")
    st.write("Valuta le seguenti affermazioni da **1 (Per nulla d'accordo)** a **6 (Totalmente d'accordo)**.")
    
    domande = [
        "1) È meglio evitare di fare troppi progetti per il futuro e concentrarsi sul presente",
        "2) Per lo più mi sembra di avere grande influenza su ciò che mi accade sul lavoro",
        "3) Pensando alla mia vita professionale, mi sembra che le mie possibilità siano aumentate",
        "4) È meglio evitare di avere troppi desideri e restare coi piedi per terra",
        "5) Per lo più mi è difficile pensarmi in circostanze future",
        "6) Per lo più mi sembra di imparare e crescere sul lavoro",
        "7) Per lo più mi sembra che crescendo aumentino i vincoli e diminuiscano le possibilità",
        "8) Per lo più mi sembra di realizzare qualcosa di buono con il mio lavoro",
        "9) Mi sembra di vivere in un mondo ricco di possibilità, anche professionali",
        "10) Pensando al mio futuro, mi è facile vedere i miei desideri realizzati",
        "11) Pensando alla mia vita professionale, mi sembra di avere molte risorse a disposizione",
        "12) Per lo più mi sembra di incidere in ciò che faccio sul lavoro",
        "13) Per lo più mi sembra di avere diverse possibilità tra cui scegliere"
    ]
    
    # Scala a 6 Punti
    opzioni = [
        "1 - Per nulla d'accordo", 
        "2 - Fortemente in disaccordo", 
        "3 - In disaccordo", 
        "4 - D'accordo", 
        "5 - Fortemente d'accordo",
        "6 - Totalmente d'accordo"
    ]
    valori_mapping = {
        opzioni[0]: 1, opzioni[1]: 2, opzioni[2]: 3, 
        opzioni[3]: 4, opzioni[4]: 5, opzioni[5]: 6
    }
    
    risposte = {}
    for i, domanda in enumerate(domande):
        # select_slider permette di scegliere tra le opzioni testuali mappate poi a numeri
        risposta_txt = st.select_slider(domanda, options=opzioni, key=f"q{i}")
        risposte[i+1] = valori_mapping[risposta_txt]

    submitted = st.form_submit_button("Calcola Profilo")

# --- ELABORAZIONE E RISULTATI ---
if submitted:
    if not nome:
        st.error("Per favore inserisci un nome o nickname.")
    else:
        # Indici Items (Python parte da 0)
        idx_reverse = [1, 4, 5, 7] # Items negativi
        idx_potere = [2, 3, 6, 8, 9, 10, 11, 12, 13]
        idx_killer = [1, 4, 5, 7]

        punteggi_calcolati = {}
        
        # Calcolo valori (Reverse su scala 6: 7 - voto)
        for k, v in risposte.items():
            if k in idx_reverse:
                punteggi_calcolati[k] = 7 - v # FORMULA AGGIORNATA PER SCALA 6
            else:
                punteggi_calcolati[k] = v
        
        # Calcolo Medie
        scores_list = list(punteggi_calcolati.values())
        score_globale = np.mean(scores_list)
        
        # Killer Psicologico (Valori grezzi per "quanto è forte il killer")
        vals_killer_raw = [risposte[k] for k in idx_killer]
        score_killer = np.mean(vals_killer_raw)
        
        # Sentimento Potere (Valori standard)
        vals_potere = [risposte[k] for k in idx_potere]
        score_potere = np.mean(vals_potere)
        
        # --- SALVATAGGIO SILENZIOSO ---
        # Proviamo a salvare, se fallisce non diciamo nulla all'utente (richiesta specifica)
        user_id = datetime.now().strftime("%Y%m%d%H%M%S")
        row_data = [user_id, nome, genere, eta, titolo_studio, job]
        for i in range(1, 14):
            row_data.append(risposte[i])
            
        save_data(row_data) # Chiamata senza controllo return visibile

        # --- FEEDBACK GRAFICO ---
        st.markdown("## Il tuo Profilo di Self-Empowerment")
        
        # Quadrante 1: Globale
        # Ranges da Prompt originale: <3.5, 3.5-4.49, 4.5-5.5, >5.5
        # Scala visuale max 6
        fig_globale = create_gauge(
            score_globale, 
            "Self-Empowerment Globale", 
            1, 6, 
            [1, 3.5, 4.5, 5.5, 6], 
            ["#FFCDD2", "#FFF9C4", "#C8E6C9", "#2E7D32"] 
            # Rosso, Giallo, Verde Chiaro, Verde Scuro
        )
        st.plotly_chart(fig_globale, use_container_width=True)

        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Killer Psicologico - Cutoff 3
            fig_killer = create_gauge(
                score_killer,
                "Killer Psicologici",
                1, 6,
                [1, 3, 6],
                [COLOR_BG_GREEN, COLOR_BG_RED] 
            )
            st.plotly_chart(fig_killer, use_container_width=True)
            
        with col_g2:
            # Sentimento di Potere - Cutoff 3
            fig_potere = create_gauge(
                score_potere,
                "Sentimento di Potere",
                1, 6,
                [1, 3, 6],
                [COLOR_BG_RED, COLOR_BG_GREEN]
            )
            st.plotly_chart(fig_potere, use_container_width=True)

        # --- FEEDBACK NARRATIVO ---
        st.markdown("### Interpretazione")
        st.info(f"Punteggio Globale: {score_globale:.2f}/6 | Potere: {score_potere:.2f}/6 | Killer: {score_killer:.2f}/6")

        testo_feedback = ""
        
        # LOGICA SOGLIE ESATTA DA PROMPT INIZIALE
        if score_globale < 3.5:
            testo_feedback = "Attenzione: è molto probabile che il tuo basso livello di self-empowerment ti impedisca di affrontare con coraggio ed energia le sfide che incontri sul cammino. Considera i punteggi del fattore potere personale e killer psicologico e valuta se la tua priorità sia rafforzare la tua auto efficacia e competenza, oppure lavorare a un depotenziamento delle difficoltà soggettive."
        elif 3.5 <= score_globale < 4.5:
            testo_feedback = "Bene ma non benissimo! Un livello di self-empowerment più alto potrebbe aiutarti ad affrontare le sfide in modo più coraggioso ed energico.  Considera i punteggi del fattore potere personale e killer psicologico e valuta se la tua priorità sia rafforzare la tua auto efficacia e competenza, oppure lavorare a un migliore depotenziamento delle difficoltà soggettive."
        elif 4.5 <= score_globale <= 5.5:
            testo_feedback = "Molto bene! Il tuo alto livello di self-empowerment ti mette nella condizione di affrontare le sfide che incontri con coraggio ed energia.  Ora considera i punteggi del fattore potere personale e killer psicologico e valuta se sia più utile rafforzare la tua auto efficacia e competenza, oppure lavorare a un migliore depotenziamento delle difficoltà soggettive."
        else: # > 5.5
            testo_feedback = "Attenzione! Un alto livello di self-empowerment è senz’altro utile per affrontare le sfide che incontri con coraggio ed energia. Tuttavia, non bisogna credere al miraggio dell’onnipotenza: un po’ di paura, incertezza, ansia ci aiutano a stare di fronte alle sfide con realismo e – quindi – affrontarle con baldanza ma senza eccessiva faciloneria. Considera il punteggi del fattore killer psicologico e valuta se averlo così basso è frutto di un buon lavoro sul pensiero negativo negative o, piuttosto, una negazione dei limiti personali."

        st.write(testo_feedback)

# --- FOOTER ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: grey;'>
    Powered by GÉNERA
</div>
""", unsafe_allow_html=True)
