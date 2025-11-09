import re
import ast
import pandas as pd
# Pour créer le fichier rbl_alliance.txt, il faut :
    # Se rendre dans getter tools dans la page de l'alliance
    # Ensuite faire un clique droit sur getter_map
    # Afficher le code source du cadre
    # Cliquer sur le lien qui ressemble à ça : src='/ts5.x1.europe.travian.com.7/js/GetterMap.js?t=1633864321&said=142'
    # Depuis la nouvelle fenêtre récupérer ce qu'il y a après "var p =" et le copier dans un fichier txt pour le donner en entrée du script

# Lire le fichier HTML ou JS
with open("rbl_alliance.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Supprimer "var p = " au début
content = content.replace("var p =", "").strip()

# Remplacer /**/ par None (en ajoutant des virgules si nécessaire)
# Ici on ajoute un None correct pour literal_eval
content = re.sub(r',?\s*/\*\*/\s*,?', ', None,', content)

# Nettoyer les virgules doubles éventuelles en trop
content = re.sub(r',\s*,', ',', content)

# Evaluer la liste
p_list = ast.literal_eval(content)

# Extraire les villages et coordonnées
villages = []
for player in p_list:
    player_id, name, color, url, unknown, num, alliance, some_number, coords = player
    for coord in coords:
        x, y, village_name = coord
        villages.append([player_id, name, village_name, x, y])

# Export Excel
df = pd.DataFrame(villages, columns=['PlayerID','PlayerName','VillageName','X','Y'])
df.to_excel("travian_alliance.xlsx", index=False)
print("Fichier Excel créé avec succès !")
