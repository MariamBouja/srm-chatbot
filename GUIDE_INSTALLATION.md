# Assistant virtuel SRM-SM — Guide de mise en route

*Documentation technique interne — installation, configuration et lancement du chatbot en local.*

**Projet :** Assistant conversationnel du site srm-sm.ma
**Auteur :** Mariam Bouja
**Mis à jour le :** 7 août 2026

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture du projet](#2-architecture-du-projet)
3. [Prérequis](#3-prérequis)
4. [Installation](#4-installation)
5. [Configuration de la clé API](#5-configuration-de-la-clé-api)
6. [Lancer l'application](#6-lancer-lapplication)
7. [Base de connaissances (maintenance)](#7-base-de-connaissances-maintenance)
8. [Mise à jour du contenu du site](#8-mise-à-jour-du-contenu-du-site)
9. [Démo d'intégration WordPress (optionnel)](#9-démo-dintégration-wordpress-optionnel)
10. [Dépannage](#10-dépannage)

---

## 1. Vue d'ensemble

C'est un chatbot qui répond aux questions des visiteurs du site **srm-sm.ma** en s'appuyant
uniquement sur le contenu officiel du site (missions, procédures d'abonnement, agences,
coordonnées…). Il n'invente rien : s'il ne trouve pas d'information suffisamment pertinente, il
le dit et redirige vers le service client.

Techniquement, c'est un système **RAG** (Retrieval-Augmented Generation) : les pages du site sont
converties en vecteurs numériques et stockées dans une base vectorielle locale ; à chaque
question, on retrouve les passages les plus proches puis on les transmet à un modèle de langage
(OpenAI) qui rédige la réponse à partir de ces passages seulement.

Deux façons d'y accéder sont fournies : une interface web (Streamlit) et une interface en ligne
de commande.

**Indexation du contenu** (à faire une fois, ou après une mise à jour du site) :

```
srm-sm.ma  →  scraper.py  →  data/website/*.txt  →  build_vector_db.py  →  vector_db/
(site officiel)  (extraction & nettoyage)  (76 pages en texte brut)  (découpage & embeddings)  (base vectorielle Chroma)
```

**À chaque question posée par un visiteur :**

```
Question utilisateur  →  conversation.py  →  rag.py  →  Réponse + sources citées
                          (aiguillage)        (recherche vectorielle + appel OpenAI)
```

## 2. Architecture du projet

```
app.py                       interface en ligne de commande
streamlit_app.py             interface web (Streamlit)
chatbot/
  config.py                  réglages centraux (modèle, seuils, chemins)
  conversation.py            orchestration : agences vs question générale
  rag.py                     cœur RAG : recherche vectorielle + génération
  agencies.py                recherche d'agences par région
  prompts.py                 prompts système envoyés au modèle
  scraper.py                 récupère et nettoie le contenu de srm-sm.ma
  build_vector_db.py         construit la base vectorielle
data/website/*.txt           contenu texte scrapé du site (76 pages)
data/agencies.json           liste des agences par région
vector_db/                   base vectorielle Chroma — déjà fournie dans le dépôt
wordpress-demo/              démo d'intégration en iframe (optionnel, voir §9)
.env                         clé API — à créer soi-même, jamais commité
```

## 3. Prérequis

- **Python 3.12** — version utilisée pour le développement et les tests.
- **pip** pour installer les dépendances.
- Une **clé API OpenAI** valide, facturée à l'usage (modèle utilisé : `gpt-4.1-mini`).
- Environ **3 Go** d'espace disque libre — les dépendances de machine learning (torch,
  transformers, sentence-transformers) sont volumineuses.
- Une connexion internet au premier lancement, le temps de télécharger le modèle d'embeddings
  depuis Hugging Face (il est ensuite mis en cache localement).

## 4. Installation

**1. Récupérer le projet**
Placez-vous dans le dossier du projet (celui qui contient `app.py`).

**2. Créer un environnement virtuel**

macOS / Linux :
```bash
python3.12 -m venv venv
source venv/bin/activate
```

Windows (PowerShell ou invite de commandes) :
```bash
py -3.12 -m venv venv
venv\Scripts\activate
```
> Si la commande `py` n'est pas reconnue, remplacez-la par `python -m venv venv` (à condition que
> `python --version` affiche bien une version 3.12).

**3. Installer les dépendances**
```bash
pip install -r requirements.txt
```
> ℹ️ Cette étape peut prendre plusieurs minutes : `torch` et `transformers` représentent à eux
> seuls plus d'1 Go.

## 5. Configuration de la clé API

Créez un fichier nommé `.env` à la racine du projet (au même niveau que `app.py`) contenant :

```
OPENAI_API_KEY=sk-votre-cle-ici
```

Une clé peut être générée sur [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

> ⚠️ **Ne jamais commiter ce fichier.** Il est volontairement exclu par `.gitignore` — chaque
> environnement (poste de dev, serveur) doit avoir sa propre clé, jamais partagée dans le dépôt.

## 6. Lancer l'application

**Interface web (recommandée)**
```bash
streamlit run streamlit_app.py
```
S'ouvre automatiquement dans le navigateur, généralement sur `http://localhost:8501`.

**Interface en ligne de commande**
Pratique pour un test rapide sans interface graphique :
```bash
python app.py
```
Tapez votre question, ou `exit` pour quitter.

## 7. Base de connaissances (maintenance)

Le dossier `vector_db/` est déjà construit et fourni dans le dépôt : il n'y a **rien à faire au
premier lancement**. Il ne faut le reconstruire que si le contenu de `data/website/` a changé
(par exemple après une nouvelle extraction du site, voir §8).

Depuis la racine du projet, environnement virtuel activé :
```bash
python -m chatbot.build_vector_db
```

> ⚠️ Cette commande **supprime et reconstruit entièrement** la base vectorielle à partir de
> `data/website/`, à chaque exécution. Comptez quelques minutes selon la machine.

## 8. Mise à jour du contenu du site

Si le site srm-sm.ma a changé et que le chatbot doit refléter le nouveau contenu, deux étapes
successives :

**1. Ré-extraire les pages du site**
```bash
python -m chatbot.scraper
```
Parcourt le sitemap de srm-sm.ma et régénère les fichiers dans `data/website/` ainsi que
`data/agencies.json`.

**2. Reconstruire la base vectorielle**
```bash
python -m chatbot.build_vector_db
```
Voir §7 ci-dessus — indispensable pour que les réponses reflètent le nouveau contenu.

## 9. Démo d'intégration WordPress (optionnel)

Le dossier `wordpress-demo/` contient une démonstration locale montrant le chatbot intégré en
`<iframe>` dans un site WordPress, sans nécessiter de serveur MySQL (une base SQLite est utilisée
à la place). Utile uniquement pour des démonstrations internes — ce n'est pas un déploiement de
production.

Prérequis supplémentaires : `php` et `wp-cli` (installables via `brew install php wp-cli` sous macOS).

```bash
bash wordpress-demo/setup.sh
php -S localhost:8081 -t wordpress-demo
```

Le site est accessible sur `http://localhost:8081`, l'administration sur `/wp-admin`
(identifiants : `admin` / `srm-demo-2026`).

> 🪟 **Sous Windows**, `setup.sh` est un script bash et ne s'exécute pas nativement. Cette section
> optionnelle (démo interne seulement, pas le chatbot lui-même) nécessite soit **WSL** (Windows
> Subsystem for Linux), soit **Git Bash**, avec PHP et WP-CLI installés manuellement. Le chatbot
> en lui-même (§4 à §8) fonctionne normalement sous Windows sans cette étape.

## 10. Dépannage

| Symptôme | Cause probable & solution |
|---|---|
| Erreur d'authentification / clé API manquante | Le fichier `.env` est absent, mal placé, ou la variable `OPENAI_API_KEY` est vide. Vérifiez qu'il est bien à la racine du projet, puis relancez le terminal. |
| `Collection not found` ou erreur Chroma au démarrage | La base vectorielle est absente ou corrompue. Reconstruisez-la avec `python -m chatbot.build_vector_db` (voir §7). |
| Le port 8501 est déjà utilisé | Lancez sur un autre port : `streamlit run streamlit_app.py --server.port 8502` |
| `pip install` très long ou échoue | Vérifiez l'espace disque disponible et la connexion internet (torch/transformers sont volumineux), puis relancez la commande. |
| Le chatbot répond trop souvent qu'il « ne dispose pas d'informations suffisamment fiables » | Soit le seuil de similarité (`SIMILARITY_THRESHOLD` dans `chatbot/config.py`) est trop strict, soit la base vectorielle n'est plus synchronisée avec `data/website/` — reconstruisez-la (§7). |

*Assistant virtuel SRM-SM — Documentation technique. Contact : Mariam Bouja — maryambouja02@gmail.com*
