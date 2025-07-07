# 📊 Tableau de Bord de Gestion Simplifié

Ce projet est une application web développée avec **Django** permettant d’importer des fichiers Excel ou CSV contenant des **écritures comptables simplifiées** (recettes et dépenses), puis d’afficher des **statistiques**, **résultats**, et **alertes budgétaires**.

---

## ✅ Fonctionnalités principales

- Import de fichiers `.csv` ou `.xlsx` contenant des opérations comptables
- Affichage du **total des recettes**, **total des dépenses**, et du **résultat net**
- Regroupement par **mois**, **type** (recette/dépense), et éventuellement **catégorie**
- Détection des **solde mensuels négatifs**
- Génération de **graphiques dynamiques** (ex: évolution mensuelle, répartition des dépenses)

---

## 📁 Format attendu des fichiers

Le fichier importé doit contenir au moins les colonnes suivantes :

| Date       | Description         | Montant     | Type     |
|------------|---------------------|-------------|----------|
| 2024-01-01 | Vente produit A     | 1500.00     | recette  |
| 2024-01-02 | Achat fournitures   | -600.00     | dépense  |

- `Date` : date de l'opération (formats acceptés : `YYYY-MM-DD`, `DD/MM/YYYY`)
- `Description` : texte libre
- `Montant` : nombre décimal (positif ou négatif)
- `Type` : soit `recette` soit `dépense`

> **NB :** Le champ `Type` est requis pour bien classer les écritures. Si absent, le système peut l'inférer à partir du signe du montant.

---

## ⚙️ Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/nom-du-projet.git
cd nom-du-projet
