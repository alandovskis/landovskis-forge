+++
title = "Cityloom"
description = "Streetmix à l'échelle de la ville : les résidents composent et comparent des scénarios pour toute la ville."
date = 2026-10-10
template = "project.html"

[extra]
tags = ["Rust", "WebAssembly", "Leptos", "OpenStreetMap"]
hero_image = "assets/screenshots/map.png"
hero_alt = "La carte de la ville de Cityloom pour le Plateau Mont-Royal, avec les rues et les carrefours tracés sur un fond de carte et un panneau de vérifications."
problem_title = "Le problème"
problem_text = "Streetmix permet à tout le monde de concevoir une seule rue. Cityloom étend l'idée à toute la ville : les résidents composent et comparent des scénarios à l'échelle de la ville, sans outils professionnels d'urbanisme. Il s'adresse aux résidents ordinaires, d'abord dans un navigateur web, puis dans des applications mobiles natives."
surfaces_title = "Les interfaces"
surfaces_intro = "Quatre pages, un seul modèle : trouver un lieu, voir sa ville sur une carte, puis ouvrir n'importe quelle rue ou intersection pour la modifier."
architecture_title = "Architecture"
architecture_caption = "Chaque fonctionnalité est une tranche verticale. Les tranches ne communiquent entre elles que par un modèle, et un modèle de vue n'atteint le navigateur que par des ports : on le teste donc sur l'hôte avec des doublures."
shared_title = "shared/"
shared_text = "Catalogue et unités, ports vers le navigateur (avec doublures de test), noyau réactif."

[[extra.surfaces]]
image = "assets/screenshots/home.png"
title = "Trouver un lieu"
alt = "La page d'accueil de Cityloom : un titre, un champ de recherche pour trouver un lieu et une carte des rues du Plateau Mont-Royal."
text = "Cherchez un lieu par son nom. Ses rues viennent d'OpenStreetMap et deviennent une ville à modifier."

[[extra.surfaces]]
image = "assets/screenshots/map.png"
title = "Carte de la ville"
alt = "La carte de la ville de Cityloom pour le Plateau Mont-Royal, avec les rues et les carrefours tracés sur un fond de carte et un panneau de vérifications."
text = "Toute la ville sur un fond de carte. Chaque rue et chaque carrefour est un lieu qu'on peut ouvrir, et des vérifications indiquent si tout fonctionne encore."

[[extra.surfaces]]
image = "assets/screenshots/street.png"
title = "Éditeur de rues"
alt = "L'éditeur de rues de Cityloom pour l'avenue Laurier Ouest : une coupe transversale avec deux voies cyclables et deux voies de circulation, et un tableau de la répartition de la largeur."
text = "Modifiez la coupe transversale d'une rue. Les règles d'édition vivent dans un modèle, et un lecteur d'écran reçoit le même état en mots."

[[extra.surfaces]]
image = "assets/screenshots/intersection.png"
title = "Éditeur d'intersections"
alt = "L'éditeur d'intersections de Cityloom montrant un carrefour de quatre rues en plan, avec un tableau des virages permis."
text = "Modifiez le carrefour où les rues se croisent, selon la même approche centrée sur le modèle que l'éditeur de rues."

[[extra.slices]]
name = "street/"
text = "Règles d'édition, modèle de vue, vues"

[[extra.slices]]
name = "junction/"
text = "Règles d'édition, géométrie, modèle de vue, vues"

[[extra.slices]]
name = "map/"
text = "Modèle de vue, couche sur le fond de carte, vues"

[[extra.slices]]
name = "city/"
text = "Ville issue d'OpenStreetMap, stockage, liaison avec la page"

[[extra.slices]]
name = "shell/"
text = "Menu des paramètres, panneaux latéraux, onglets de notes"
+++

## Comment il est construit

Cityloom est écrit en Rust et compilé en WebAssembly, avec Leptos pour afficher l'interface dans le navigateur. La logique vit dans des modèles de vue qui ignorent tout de la page ; les vues s'y lient et ne décident de rien. Des tests de navigateur pilotent les pages construites avec Playwright.

L'intégration continue exécute le formatage, les tests unitaires et les tests de navigateur par l'entremise de `just`, avec des actions épinglées à des commits et Dependabot qui propose des mises à jour chaque semaine. L'interface est bilingue, en anglais et en français canadien, avec des fichiers de traduction Fluent.

## Ce qui est ouvert

Le code source est public sur GitHub. Le code ouvert et les données ouvertes sont des principes déclarés du produit : les rues viennent d'OpenStreetMap par Nominatim, Overpass et osm2streets, et le fond de carte de Montréal est construit à partir d'un extrait de Geofabrik avec Planetiler.

## État d'avancement

Cityloom en est à ses débuts. Les largeurs du catalogue, les règles et les débits de capacité sont des valeurs fictives, et non de vraies normes ou mesures. Des applications Android et iOS natives sont prévues après la version web.
