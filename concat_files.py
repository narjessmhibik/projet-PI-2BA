import os

def concat_all_files(root_folder, output_file):
    """
    Parcourt récursivement tous les sous-dossiers du dossier racine,
    concatène le contenu de tous les fichiers (sauf ce script lui-même)
    dans un seul fichier texte.
    """
    print(f"🔍 Dossier racine : {root_folder}")

    # Obtenir le chemin absolu de ce script pour ne pas l'inclure
    current_script = os.path.abspath(__file__)

    # Liste de tous les fichiers trouvés
    all_files = []

    # Parcours récursif de tous les sous-dossiers
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)

            # Ignorer le fichier Python lui-même et les fichiers de sortie
            if file_path == current_script or file_path == output_file:
                continue

            # On peut aussi ignorer les fichiers binaires (optionnel)
            if not filename.lower().endswith((".txt", ".js", ".ts", ".tsx", ".json", ".md", ".html", ".css", ".py")):
                continue

            all_files.append(file_path)

    if not all_files:
        print("⚠️ Aucun fichier compatible trouvé.")
        return

    print(f"📂 {len(all_files)} fichiers trouvés. Concaténation en cours...")

    # Écrire tout dans le fichier de sortie
    with open(output_file, "w", encoding="utf-8") as outfile:
        for file_path in all_files:
            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    content = infile.read()
                    outfile.write(f"\n\n=== 📄 {file_path} ===\n\n")
                    outfile.write(content)
                    print(f"✅ Ajouté : {file_path}")
            except Exception as e:
                print(f"⚠️ Erreur lecture {file_path}: {e}")

    print(f"\n✅ Tous les fichiers ont été concaténés dans : {output_file}")


# ==========================================================
# 🚀 Exécution directe
# ==========================================================
if __name__ == "__main__":
    dossier_racine = os.path.dirname(os.path.abspath(__file__))
    fichier_sortie = os.path.join(dossier_racine, "concat_result.txt")

    concat_all_files(dossier_racine, fichier_sortie)
