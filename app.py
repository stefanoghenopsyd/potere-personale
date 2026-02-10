import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. CONFIGURAZIONE E COSTANTI ---
# Scala Likert
OPZIONI_LIKERT = {
    1: "Per nulla d'accordo",
    2: "Poco d'accordo",
    3: "Né d'accordo né in disaccordo",
    4: "Abbastanza d'accordo",
    5: "Totalmente d'accordo"
}

# Elenco Item (Testo)
ITEMS = [
    "1. Generalmente ho molti desideri",
    "2. È meglio concentrarsi sul presente, senza fare troppi progetti futuri",
    "3. Generalmente mi sento privo di risorse",
    "4. Generalmente sento di avere molta influenza su ciò che mi accade nel lavoro",
    "5. Se penso alla mia vita professionale, mi sembra che nel tempo le mie possibilità siano aumentate",
    "6. È meglio restare coi piedi per terra, evitando di avere troppi desideri",
    "7. Generalmente mi è difficile pensarmi in circostanze future",
    "8. Per perseguire i miei desideri avrei bisogno che mi venissero fornite più risorse",
    "9. Generalmente mi sembra di imparare e di crescere nel lavoro",
    "10. Più uno cresce e più aumentano i vincoli e diminuiscono le possibilità",
    "11. Se penso alla mia vita professionale, credo sia importante perseguire i propri desideri",
    "12. Mi piace ciò che immagino del mio futuro",
    "13. Le risorse per perseguire i miei desideri sono innanzitutto mie",
    "14. Generalmente mi sembra di realizzare qualcosa di buono con il mio lavoro",
    "15. Viviamo in un mondo ricco di possibilità, anche professionali",
    "16. Nella vita sono più importanti i desideri dei bisogni",
    "17. Se penso al mio futuro, mi è facile vedere i miei desideri realizzati",
    "18. Se penso alla mia vita professionale, penso di avere molte risorse a disposizione",
    "19. Generalmente mi sembra di incidere su ciò che faccio sul lavoro",
    "20. Generalmente ritengo di avere diverse possibilità tra cui scegliere"
]

# Indici degli item da reversare (l'indice parte da 1 come nel testo, nel codice verrà adattato a 0)
INDICI_REVERSE = [2, 3, 6, 7, 8, 10]

# --- 2. FUNZIONI LOGICHE ---

def salva_su_drive(riga):
    """Tenta il salvataggio su Google Sheets."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Database_Self_Empowerment").sheet1
        sheet.append_row(riga)
        return True
    except Exception as e:
        print(f"Errore salvataggio: {e}") # Log interno
        return False

def calcola_punteggi(risposte_raw):
    """
    Calcola il punteggio medio applicando il reverse agli item specifici.
    Restituisce: media totale, lista punteggi calcolati, flag killer.
    """
    punteggi_calcolati = []
    
    # Calcolo punteggi singoli (con reverse)
    for i, voto_raw in enumerate(risposte_raw):
        idx_item = i + 1  # L'item 1 è all'indice 0
        if idx_item in INDICI_REVERSE:
            # Reverse su scala 1-5: Nuovo = 6 - Vecchio
            punteggio = 6 - voto_raw
        else:
            punteggio = voto_raw
        punteggi_calcolati.append(punteggio)
    
    media_totale = np.mean(punteggi_calcolati)
    
    # Logica Killer Psicologici
    # "Se negli items 3, 8, 10 il punteggio medio è > 4" (Nota: Si intende il voto RAW, cioè l'accordo col killer)
    raw_killer_group = [risposte_raw[2], risposte_raw[7], risposte_raw[9]] # Indici 2,7,9 corrispondono a item 3,8,10
    # "e negli items 17, 18, 20 è < 3" (Voto RAW su risorse positive)
    raw_resource_group = [risposte_raw[16], risposte_raw[17], risposte_raw[19]] # Item 17,18,20
    
    check_killer = (np.mean(raw_killer_group) > 4) and (np.mean(raw_resource_group) < 3)
    
    return media_totale, punteggi_calcolati, check_killer

def crea_tachimetro(valore):
    """Genera il grafico a tachimetro con Plotly."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valore,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Livello Self-Empowerment"},
        gauge = {
            'axis': {'range': [1, 5.5], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#006B54"}, # Verde GENERA
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [1, 3], 'color': '#ffcccc'},
                {'range': [3, 4.4], 'color': '#ffffcc'},
                {'range': [4.4, 5.5], 'color': '#B4D8D0'} # Verde chiaro GENERA
            ],
        }
    ))
    fig.update_layout(width=400, height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# --- 3. INTERFACCIA UTENTE ---

def main():
    st.set_page_config(page_title="Self-Empowerment GENERA", layout="centered")

    # Header con Logo e Titolo responsivi
    col_spacer_l, col_img, col_spacer_r = st.columns([1, 2, 1])
    with col_img:
        st.image("GENERA Logo Colore.png", use_container_width=True)
    
    st.markdown("<h1 style='text-align: center;'>Autovalutazione Potere Personale</h1>", unsafe_allow_html=True)

    # Introduzione
    st.markdown("""
    ### Il Modello del Self-Empowerment
    Il modello di riferimento (Bruscaglioni e Gheno) definisce il potere personale come la possibilità di aprire nuove possibilità. 
    Si basa su 4 fasi operative cicliche:
    
    1.  **Dialettica Bisogno-Desiderio**: All'emergere di un bisogno si attiva la funzione desiderante.
    2.  **Pensabilità Positiva**: Il desiderio diventa progetto.
    3.  **Mobilitazione delle Risorse**: Ricerca delle risorse interne ed esterne.
    4.  **Depotenziamento dei Killer**: Superamento degli ostacoli soggettivi (es. "non sono capace", "è colpa degli altri").
    
    **Obiettivo:** Riflettere sul proprio sentimento di potere personale, inteso come capacità di incidere sulla realtà e realizzare i propri desideri.
    """)
    
    st.info("Proseguendo nella compilazione acconsento a che i dati raccolti potranno essere utilizzati in forma aggregata esclusivamente per finalità statistiche")

    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        with st.form("form_empowerment"):
            # Anagrafica
            st.subheader("Dati Socio-Anagrafici")
            nome = st.text_input("Nome o Nickname")
            genere = st.selectbox("Genere", ["maschile", "femminile", "non binario", "non risponde"])
            eta = st.selectbox("Età", ["fino a 20 anni", "21-30 anni", "31-40 anni", "41-50 anni", "51-60 anni", "61-70 anni", "più di 70 anni"])
            studio = st.selectbox("Titolo di Studio", ["licenza media", "qualifica professionale", "diploma di maturità", "laurea triennale", "laurea magistrale (o ciclo unico)", "titolo post lauream"])
            job = st.selectbox("Job", ["imprenditore", "top manager", "middle manager", "impiegato", "operaio", "tirocinante", "libero professionista"])

            st.markdown("---")
            st.subheader("Questionario")
            st.write("Valuta le seguenti affermazioni da **Per nulla d'accordo** (1) a **Totalmente d'accordo** (5).")

            risposte_raw = []
            for item in ITEMS:
                val = st.radio(
                    item, 
                    options=[1, 2, 3, 4, 5],
                    format_func=lambda x: f"{x} - {OPZIONI_LIKERT[x]}",
                    horizontal=True,
                    index=None  # Nessuna preselezione
                )
                risposte_raw.append(val)

            submitted = st.form_submit_button("Calcola il mio Profilo")

            if submitted:
                if None in risposte_raw or not nome:
                    st.error("Per favore, compila tutti i campi e rispondi a tutte le domande.")
                else:
                    # Elaborazione
                    media, punteggi_calc, is_killer_active = calcola_punteggi(risposte_raw)
                    
                    # Preparazione dati per DB
                    riga_db = [nome, genere, eta, studio, job] + punteggi_calc # Salviamo i punteggi calcolati (o raw? Di solito si salvano i raw, ma qui salvo i calcolati come da richiesta implicita nel calcolo)
                    # Nota: Per chiarezza statistica, salvo i RAW e calcolo dopo in analisi, ma la richiesta dice "punteggio attribuito". Salverò i RAW seguiti dalla Media Finale per completezza.
                    # Riformulo come da richiesta: "punteggio attribuito a ciascun item". Salvo i RAW (quello che l'utente ha cliccato).
                    riga_completa = [nome, genere, eta, studio, job] + risposte_raw

                    saved_ok = salva_su_drive(riga_completa)
                    
                    st.session_state.media = media
                    st.session_state.punteggi_calc = punteggi_calc
                    st.session_state.is_killer_active = is_killer_active
                    st.session_state.saved_ok = saved_ok
                    st.session_state.riga_completa = riga_completa
                    st.session_state.submitted = True
                    st.rerun()

    else:
        # --- PAGINA RISULTATI ---
        media = st.session_state.media
        punteggi = st.session_state.punteggi_calc
        
        # Feedback Tecnico
        if st.session_state.saved_ok:
            st.success("Dati salvati correttamente.")
        else:
            st.warning("Impossibile salvare i dati online. Visualizza comunque il tuo feedback qui sotto.")

        # 1. Grafico Tachimetro
        st.plotly_chart(crea_tachimetro(media), use_container_width=True)

        # 2. Feedback Descrittivo (Segmentazione)
        st.subheader("Il tuo Profilo di Potere Personale")
        
        messaggio = ""
        if media <= 3:
            messaggio = "🔴 **Basso livello di self-empowerment.** Rischio di consolidare un sentimento di impotenza."
        elif 3.1 <= media <= 4.4:
            messaggio = "🟡 **Livello medio di self-empowerment.** Non aver paura di investire di più su ciò che desideri."
        elif 4.5 <= media <= 5.5:
            messaggio = "🟢 **Livello alto di self-empowerment.** I tuoi limiti non sono un freno, a patto che tieni “acceso” il desiderio."
        else: # > 5.5 (Tecnicamente impossibile su scala 1-5, ma inserito per specifica)
            messaggio = "🌟 **Livello molto alto di self-empowerment.** Tutto bene a patto che tu non ti creda onnipotente: un buon esame di realtà è fondamentale."
        
        st.markdown(f"### {messaggio}")

        # 3. Analisi Criticità (2 item più bassi)
        st.subheader("Aree di Attenzione")
        # Creiamo coppie (Punteggio, Testo Item)
        lista_punteggi_testo = []
        for i, pt in enumerate(punteggi):
            lista_punteggi_testo.append((pt, ITEMS[i]))
        
        # Ordiniamo in base al punteggio (crescente)
        lista_punteggi_testo.sort(key=lambda x: x[0])
        worst_2 = lista_punteggi_testo[:2]

        st.write("Le maggiori criticità potenziali emergono in questi ambiti:")
        for pt, testo in worst_2:
            st.warning(f"**{testo}** (Punteggio ricalcolato: {pt}/5)")

        # 4. Check Killer Psicologici
        if st.session_state.is_killer_active:
            st.error("""
            ⚠️ **Attenzione ai Killer Psicologici!** Dal tuo profilo emerge la necessità di lavorare sul depotenziamento dei tuoi ostacoli interni (es. locus of control esterno, sensazione di scarsità di risorse).
            """)

        # Download Button (Backup)
        csv_buffer = pd.DataFrame([st.session_state.riga_completa], 
                                  columns=["Nome", "Genere", "Età", "Studio", "Job"] + [f"Item {i+1}" for i in range(20)]).to_csv(index=False).encode('utf-8')
        st.download_button("Scarica i tuoi risultati (CSV)", csv_buffer, "risultati_empowerment.csv", "text/csv")
        
        if st.button("Ricomincia"):
            st.session_state.submitted = False
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: grey;'>Powered by GÉNERA</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
