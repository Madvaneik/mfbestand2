from flask import Flask, render_template
import pandas as pd
import requests
from io import StringIO

app = Flask(__name__)

# Hier fügen Sie den Code zum Lesen der CSV-Dateien ein
daten_csv_path = 'files/daten.csv'
lieferant_csv_path = 'files/lieferant.csv'

# Daten aus der CSV-Datei "daten.csv" lesen
daten_df = pd.read_csv(daten_csv_path, delimiter=';')

# Daten aus der CSV-Datei "lieferant.csv" lesen
lieferant_df = pd.read_csv(lieferant_csv_path, delimiter=';')

# Funktion zum Abrufen der externen Daten
def fetch_external_data():
    url = 'https://meisterfids-paff.de/backend/export/index/bestand.csv?feedID=32&hash=07b36ca7be9494d352be0d0a3eb04117'
    response = requests.get(url)
    
    if response.status_code == 200:
        external_data = pd.read_csv(StringIO(response.text), delimiter='|')
        return external_data
    else:
        return None

@app.route('/')
def index():
    external_data = fetch_external_data()
    
    if external_data is not None:
        # Verknüpfen Sie die Daten aus daten.csv, lieferant.csv und bestand.csv basierend auf der Artikelnummer
        merged_data = pd.merge(daten_df, external_data, on='Artikelnummer', how='left')
        data_to_display = []

        for idx, row in merged_data.iterrows():
            artikelnummer = row['Artikelnummer']
            bezeichnung = row['Bezeichnung']
            lagerbestand = row['Lagerbestand']
            nachbestellt = row['Nachbestellt']

            # Filtern Sie Lieferanten für diesen Artikel
            lieferanten = lieferant_df[lieferant_df['Artikelnummer'] == artikelnummer]['Lieferant'].tolist()

            if not any(item['Artikelnummer'] == artikelnummer for item in data_to_display):
                # Wenn der Artikel noch nicht hinzugefügt wurde, fügen Sie ihn einmal hinzu
                data_to_display.append({
                    'Artikelnummer': artikelnummer,
                    'Bezeichnung': bezeichnung,
                    'Lagerbestand': lagerbestand,
                    'Nachbestellt': nachbestellt,
                    'Lieferant': ', '.join(lieferanten)
                })

                # Hier werden die Bestellvorschläge basierend auf den Verkaufsdaten erstellt
                verkauft1 = row['Verkauft1']
                verkauft2 = row['Verkauft2']
                verkauft3 = row['Verkauft3']
                verkauft4 = row['Verkauft4']

                # Liste der Verkaufsdaten mit Werten größer als 0
                verkaufsdaten = [verkauft1, verkauft2, verkauft3, verkauft4]
                verkaufsdaten = [v for v in verkaufsdaten if not pd.isnull(v) and v > 0]

                # Durchschnittlicher Verkauf pro Tag basierend auf tatsächlichen Verkaufsdaten
                durchschnittlicher_verkauf_pro_tag = sum(verkaufsdaten) / len(verkaufsdaten) / 30  # Durchschnitt pro Tag

                # Gewünschter Lagerbestand für verschiedene Reichweiten (in Tagen)
                gewuenschter_lagerbestand_14_tage = durchschnittlicher_verkauf_pro_tag * 14
                gewuenschter_lagerbestand_30_tage = durchschnittlicher_verkauf_pro_tag * 30
                gewuenschter_lagerbestand_60_tage = durchschnittlicher_verkauf_pro_tag * 60
                gewuenschter_lagerbestand_90_tage = durchschnittlicher_verkauf_pro_tag * 90

                # Verfügbare Menge (Lagerbestand + Nachbestellt)
                verfuegbare_menge = lagerbestand + nachbestellt

                # Bestellvorschlag für verschiedene Reichweiten
                bestellvorschlag_14_tage = max(0, gewuenschter_lagerbestand_14_tage - verfuegbare_menge)
                bestellvorschlag_30_tage = max(0, gewuenschter_lagerbestand_30_tage - verfuegbare_menge)
                bestellvorschlag_60_tage = max(0, gewuenschter_lagerbestand_60_tage - verfuegbare_menge)
                bestellvorschlag_90_tage = max(0, gewuenschter_lagerbestand_90_tage - verfuegbare_menge)

                # Anzahl der Tage, auf denen die Berechnung basiert
                tage_fuer_berechnung = len(verkaufsdaten) * 30  # 30 Tage pro Monat angenommen

                # Fügen Sie die Bestellvorschläge und die Anzahl der Tage zur Zeile hinzu
                data_to_display[-1]['Bestellvorschlag 14 Tage'] = bestellvorschlag_14_tage
                data_to_display[-1]['Bestellvorschlag 30 Tage'] = bestellvorschlag_30_tage
                data_to_display[-1]['Bestellvorschlag 60 Tage'] = bestellvorschlag_60_tage
                data_to_display[-1]['Bestellvorschlag 90 Tage'] = bestellvorschlag_90_tage
                data_to_display[-1]['Tage für Berechnung'] = tage_fuer_berechnung

    else:
        # Wenn keine externen Daten verfügbar sind, verwenden Sie nur die Daten aus daten.csv und lieferant.csv
        merged_data = pd.merge(daten_df, lieferant_df, on='Artikelnummer', how='left')
        data_to_display = []

        for idx, row in merged_data.iterrows():
            artikelnummer = row['Artikelnummer']
            bezeichnung = row['Bezeichnung']
            lagerbestand = row['Lagerbestand']
            nachbestellt = row['Nachbestellt']

            # Filtern Sie Lieferanten für diesen Artikel
            lieferanten = lieferant_df[lieferant_df['Artikelnummer'] == artikelnummer]['Lieferant'].tolist()

            if not any(item['Artikelnummer'] == artikelnummer for item in data_to_display):
                # Wenn der Artikel noch nicht hinzugefügt wurde, fügen Sie ihn einmal hinzu
                data_to_display.append({
                    'Artikelnummer': artikelnummer,
                    'Bezeichnung': bezeichnung,
                    'Lagerbestand': lagerbestand,
                    'Nachbestellt': nachbestellt,
                    'Lieferant': ', '.join(lieferanten)
                })

                # Setzen Sie die Bestellvorschläge auf 0, da keine Verkaufsdaten vorliegen
                data_to_display[-1]['Bestellvorschlag 14 Tage'] = 0
                data_to_display[-1]['Bestellvorschlag 30 Tage'] = 0
                data_to_display[-1]['Bestellvorschlag 60 Tage'] = 0
                data_to_display[-1]['Bestellvorschlag 90 Tage'] = 0
                data_to_display[-1]['Tage für Berechnung'] = 0  # Keine Verkaufsdaten vorhanden

    return render_template('index.html', data=data_to_display)

if __name__ == '__main__':
    app.run(debug=True)
