import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import os
from hashlib import sha256
from datetime import datetime
import requests
from bs4 import BeautifulSoup


# Constantes pour les fichiers
USER_DATA_FILE = "users.csv"
BASE_DIR = "user_data"  # Répertoire pour stocker les données des utilisateurs


# Initialisation des fichiers et répertoires
def initialize():
    if not os.path.exists(USER_DATA_FILE):
        pd.DataFrame(columns=["Username", "PasswordHash"]).to_csv(USER_DATA_FILE, index=False)
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)


# Hachage des mots de passe pour plus de sécurité
def hash_password(password):
    return sha256(password.encode()).hexdigest()


# Gestion des comptes utilisateurs
def create_account():
    st.title("Créer un compte")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    confirm_password = st.text_input("Confirmez le mot de passe", type="password")
    if st.button("Créer un compte"):
        if not username or not password:
            st.warning("Veuillez remplir tous les champs.")
        elif password != confirm_password:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            users = pd.read_csv(USER_DATA_FILE)
            if username in users["Username"].values:
                st.error("Ce nom d'utilisateur est déjà pris.")
            else:
                password_hash = hash_password(password)
                users = pd.concat([users, pd.DataFrame([{"Username": username, "PasswordHash": password_hash}])], ignore_index=True)

                users.to_csv(USER_DATA_FILE, index=False)
                os.makedirs(os.path.join(BASE_DIR, username))
                st.success("Compte créé avec succès !")


def login():
    st.title("Connexion")
    st.subheader("Veuillez entrer vos identifiants")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if not username or not password:
            st.warning("Veuillez remplir tous les champs.")
        else:
            users = pd.read_csv(USER_DATA_FILE)
            if username in users["Username"].values:
                user_data = users[users["Username"] == username].iloc[0]
                if hash_password(password) == user_data["PasswordHash"]:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["page"] = "Navigation"  # Rediriger après connexion
                    st.success(f"Bienvenue, {username} !")
                else:
                    st.error("Mot de passe incorrect.")
            else:
                st.error("Utilisateur non trouvé.")


# Charger les données spécifiques à l'utilisateur
def load_user_data():
    username = st.session_state["username"]
    user_file = os.path.join(BASE_DIR, username, "data.csv")
    if os.path.exists(user_file):
        return pd.read_csv(user_file)
    else:
        return pd.DataFrame(columns=["Date", "Distance (km)", "Temps (min)", "Calories (kcal)", "FC Moyenne (bpm)"])


# Sauvegarder les données spécifiques à l'utilisateur
def save_user_data(data):
    username = st.session_state["username"]
    user_file = os.path.join(BASE_DIR, username, "data.csv")
    data.to_csv(user_file, index=False)


# Saisie d'une nouvelle session
def add_session():
    st.title("Ajouter une nouvelle session de course")
    st.subheader("Veuillez entrer les détails de votre session")

    with st.form("new_session"):
        date = st.date_input("Date", value=datetime.now())
        distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        time = st.number_input("Temps (min)", min_value=0.0, step=0.1)
        calories = st.number_input("Calories (kcal)", min_value=0.0, step=1.0)
        heart_rate = st.number_input("Fréquence cardiaque moyenne (bpm)", min_value=0, step=1)
        submitted = st.form_submit_button("Enregistrer")

    if submitted:
        new_entry = {
            "Date": date,
            "Distance (km)": distance,
            "Temps (min)": time,
            "Calories (kcal)": calories,
            "FC Moyenne (bpm)": heart_rate,
        }
        data = load_user_data()
        data = pd.concat([data, pd.DataFrame([new_entry])], ignore_index=True)
        save_user_data(data)
        st.success("Session enregistrée avec succès !")


# Visualisation des données
def visualize_data():
    st.title("Visualisation des progrès")
    st.subheader("Graphiques interactifs des performances")
    data = load_user_data()

    if data.empty:
        st.warning("Aucune donnée à visualiser.")
        return

    start_date = pd.to_datetime(st.date_input("Date de début", value=pd.to_datetime(data["Date"]).min()))
    end_date = pd.to_datetime(st.date_input("Date de fin", value=pd.to_datetime(data["Date"]).max()))

    filtered_data = data[(pd.to_datetime(data["Date"]) >= start_date) & (pd.to_datetime(data["Date"]) <= end_date)]

    if not filtered_data.empty:
        fig, ax = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle("Analyse des performances au fil du temps", fontsize=16, fontweight='bold')

        # Distance cumulée
        ax[0].plot(filtered_data["Date"], filtered_data["Distance (km)"], label="Distance (km)", marker='o')
        ax[0].set_title("Distance parcourue (en km)", fontsize=12)
        ax[0].set_ylabel("Kilomètres", fontsize=10)
        ax[0].grid(True)
        ax[0].legend()

        # Temps moyen par kilomètre
        filtered_data["Temps/km (min)"] = filtered_data["Temps (min)"] / filtered_data["Distance (km)"]
        ax[1].plot(filtered_data["Date"], filtered_data["Temps/km (min)"], label="Temps moyen (min/km)", color="orange", marker='o')
        ax[1].set_title("Temps moyen par kilomètre", fontsize=12)
        ax[1].set_ylabel("Minutes par km", fontsize=10)
        ax[1].grid(True)
        ax[1].legend()

        # Calories brûlées
        ax[2].plot(filtered_data["Date"], filtered_data["Calories (kcal)"], label="Calories brûlées", color="green", marker='o')
        ax[2].set_title("Calories brûlées (en kcal)", fontsize=12)
        ax[2].set_ylabel("Calories", fontsize=10)
        ax[2].grid(True)
        ax[2].legend()

        # Rotation des étiquettes des dates
        for axis in ax:
            axis.set_xticks(filtered_data["Date"])
            axis.set_xticklabels(filtered_data["Date"], rotation=45, ha='right', fontsize=9)

        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Ajustement pour le titre global
        st.pyplot(fig)
    else:
        st.warning("Aucune donnée pour cette période.")



# Fonction de scraping pour récupérer des benchmarks
def scrape_articles():
    st.title("Lire Des articles")
    url = "https://www.runnersworld.com"  # Remplacer par un autre site si nécessaire
    response = requests.get(url)
    contenu = BeautifulSoup(response.text, 'html.parser')
    
    # Extraction des titres des articles
    titles_args = contenu.find_all('span', class_='css-1hc7p2m e10ip9lg5')
    titles = [title.text.strip() for title in titles_args]
    
    # Extraction des liens des articles
    link_args = contenu.find_all('a', class_='ee4ms352 css-mg2r4i e1c1bym14')
    links = [url + link['href'] for link in link_args]
    
    # Extraction des images des articles
    pic_args = contenu.find_all('img', class_='css-0 e1g79fud0')
    pics = [pic['src'] for pic in pic_args]
    
    # Afficher les articles avec les titres, images et liens
    for i in range(0, len(titles), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(titles):
                with cols[j]:
                    st.subheader(titles[i + j])
                    st.write(f"[Lire l'article]({links[i + j]})")
                    
                    # Afficher l'image
                    if pics[i + j].startswith('http'):
                        img_url = pics[i + j]
                    else:
                        img_url = url + pics[i + j]
                    st.image(img_url, width=300)
    

# Calculer les statistiques pour la période choisie
def calculate_statistics(data, start_date, end_date):
    filtered_data = data[(pd.to_datetime(data["Date"]) >= start_date) & (pd.to_datetime(data["Date"]) <= end_date)]
    
    if not filtered_data.empty:
        total_distance = filtered_data["Distance (km)"].sum()
        total_time = filtered_data["Temps (min)"].sum()
        total_calories = filtered_data["Calories (kcal)"].sum()
        avg_heart_rate = filtered_data["FC Moyenne (bpm)"].mean()
        
        avg_speed = total_distance / (total_time / 60) if total_time > 0 else 0
        
        statistics = {
            "Total Distance (km)": total_distance,
            "Total Time (min)": total_time,
            "Total Calories (kcal)": total_calories,
            "Average Heart Rate (bpm)": avg_heart_rate,
            "Average Speed (km/h)": avg_speed
        }
    else:
        statistics = {}
    
    return statistics, filtered_data

# Fonction pour générer le PDF
def generate_pdf(statistics, filtered_data, username):
    # Créer le PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Ajouter un titre
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Rapport des Performances de {username}", ln=True, align="C")
    pdf.ln(10)

    # Ajouter les statistiques
    pdf.set_font("Arial", '', 12)
    for key, value in statistics.items():
        pdf.cell(200, 10, f"{key}: {value}", ln=True)
    pdf.ln(10)

    # Ajouter un tableau avec les données détaillées
    pdf.cell(200, 10, "Données des sessions", ln=True, align="C")
    pdf.ln(5)

    # Ajouter l'entête du tableau
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Date", border=1)
    pdf.cell(40, 10, "Distance (km)", border=1)
    pdf.cell(40, 10, "Temps (min)", border=1)
    pdf.cell(40, 10, "Calories (kcal)", border=1)
    pdf.cell(40, 10, "FC Moyenne (bpm)", border=1)
    pdf.ln()

    # Ajouter les lignes du tableau
    pdf.set_font("Arial", '', 10)
    for index, row in filtered_data.iterrows():
        pdf.cell(40, 10, str(row["Date"]), border=1)
        pdf.cell(40, 10, str(row["Distance (km)"]), border=1)
        pdf.cell(40, 10, str(row["Temps (min)"]), border=1)
        pdf.cell(40, 10, str(row["Calories (kcal)"]), border=1)
        pdf.cell(40, 10, str(row["FC Moyenne (bpm)"]), border=1)
        pdf.ln()

    # Sauvegarder le PDF
    output_pdf_path = f"{username}_performance_report.pdf"
    pdf.output(output_pdf_path)
    
    return output_pdf_path

# Fonction pour générer et télécharger le PDF
def download_pdf():
    st.title("Générer un PDF de vos performances")
    data = load_user_data()

    if data.empty:
        st.warning("Aucune donnée disponible pour générer le PDF.")
        return
    
    start_date = pd.to_datetime(st.date_input("Date de début", value=pd.to_datetime(data["Date"]).min()))
    end_date = pd.to_datetime(st.date_input("Date de fin", value=pd.to_datetime(data["Date"]).max()))

    # Calculer les statistiques pour la période
    statistics, filtered_data = calculate_statistics(data, start_date, end_date)

    if not statistics:
        st.warning("Aucune donnée pour la période sélectionnée.")
        return

    # Générer le PDF
    pdf_path = generate_pdf(statistics, filtered_data, st.session_state["username"])
    st.success("Le PDF a été généré avec succès !")
    
    # Ajouter un bouton pour télécharger le PDF
    with open(pdf_path, "rb") as f:
        st.download_button("Télécharger le PDF", f, file_name=pdf_path)

# Application principale
def main():
    initialize()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["page"] = "Accueil"

    if not st.session_state["logged_in"]:
        choice = st.sidebar.radio("Navigation", ["Se connecter", "Créer un compte"])
        if choice == "Créer un compte":
            create_account()
        elif choice == "Se connecter":
            login()
    else:
        if st.session_state["page"] == "Navigation":
            st.sidebar.title("Navigation")
            choice = st.sidebar.radio("Choisissez une option", ["Ajouter une session", "Visualiser les données", "Lire des articles", "Générer un PDF", "Se déconnecter"])

            if choice == "Ajouter une session":
                add_session()
            elif choice == "Visualiser les données":
                visualize_data()
            elif choice == "Lire des articles":
                scrape_articles()
            elif choice == "Générer un PDF":
                download_pdf()
            elif choice == "Se déconnecter":
                st.session_state["logged_in"] = False
                st.session_state["page"] = "Accueil"
                st.session_state.pop("username", None)
                st.success("Déconnexion réussie.")


if __name__ == "__main__":
    main()