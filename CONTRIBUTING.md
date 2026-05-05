# Contribuer au projet

Merci de l'intérêt que vous portez à ce projet ! Voici comment contribuer.

## Signaler un bug

1. Vérifiez que le bug n'est pas déjà signalé dans les [Issues](https://github.com/franznyer/local-hr-rag-chatbot/issues)
2. Ouvrez une nouvelle issue en décrivant :
   - Le comportement observé
   - Le comportement attendu
   - Les étapes pour reproduire le bug
   - Votre OS, version de Python, provider utilisé

## Proposer une amélioration

1. Ouvrez une issue pour discuter de l'idée avant de coder
2. Forkez le dépôt
3. Créez une branche : `git checkout -b feature/ma-fonctionnalite`
4. Committez vos changements avec un message clair
5. Ouvrez une Pull Request

## Ajouter un provider IA

C'est l'une des contributions les plus utiles ! Voir le guide dans le README :
[Ajouter un nouveau provider](README.md#ajouter-un-nouveau-provider)

## Règles générales

- Code Python typé autant que possible
- Fonctions courtes et responsabilités claires
- Pas de dépendances cloud dans l'installation de base (`requirements.txt`)
- Les tests manuels avec `python scripts/check_setup.py` doivent passer
