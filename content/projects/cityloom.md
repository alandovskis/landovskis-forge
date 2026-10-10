+++
title = "Cityloom"
description = "Streetmix at city scale: residents compose and compare whole-city scenarios."
date = 2026-10-10
template = "project.html"

[extra]
tags = ["Rust", "WebAssembly", "Leptos", "OpenStreetMap"]
hero_image = "assets/screenshots/map.png"
hero_alt = "The Cityloom city map of the Plateau Mont-Royal, with streets and junctions drawn over a basemap and a panel of checks."
problem_title = "The problem"
problem_text = "Streetmix lets anyone design a single street. Cityloom lifts that to the whole city: residents compose and compare city-wide scenarios without professional planning tools. It is built for ordinary residents, first in a web browser and later in native mobile apps."
surfaces_title = "The surfaces"
surfaces_intro = "Four pages, one model: find a place, see its city on a map, then open any street or intersection to edit it."
architecture_title = "Architecture"
architecture_caption = "Each feature is a vertical slice. Slices reach one another only through a model, and a view-model reaches the browser only through ports, so it is tested on the host with fakes."
shared_title = "shared/"
shared_text = "Catalogue and units, ports to the browser (with test fakes), the reactive core."

[[extra.surfaces]]
image = "assets/screenshots/home.png"
title = "Find a place"
alt = "The Cityloom home page: a headline, a search field for finding a place, and a map of the Plateau Mont-Royal's streets."
text = "Search for a place by name. Its streets come from OpenStreetMap and become a city to edit."

[[extra.surfaces]]
image = "assets/screenshots/map.png"
title = "City map"
alt = "The Cityloom city map of the Plateau Mont-Royal, with streets and junctions drawn over a basemap and a panel of checks."
text = "The whole city on a basemap. Every street and junction is a place that can be opened, and checks say whether it all still works."

[[extra.surfaces]]
image = "assets/screenshots/street.png"
title = "Street editor"
alt = "The Cityloom street editor for Avenue Laurier Ouest: a cross-section with two bike lanes and two driving lanes, and a table of where the width goes."
text = "Edit the cross-section of a street. The editing rules live in a model, and a screen reader is given the same state in words."

[[extra.surfaces]]
image = "assets/screenshots/intersection.png"
title = "Intersection editor"
alt = "The Cityloom intersection editor showing a four-street junction as a plan, with a table of the turns allowed."
text = "Edit the junction where streets meet, built the same model-first way as the street editor."

[[extra.slices]]
name = "street/"
text = "Editing rules, view-model, views"

[[extra.slices]]
name = "junction/"
text = "Editing rules, geometry, view-model, views"

[[extra.slices]]
name = "map/"
text = "View-model, basemap overlay, views"

[[extra.slices]]
name = "city/"
text = "City from OpenStreetMap, storage, page binding"

[[extra.slices]]
name = "shell/"
text = "Settings menu, sidebars, notes tabs"
+++

## How it is built

Cityloom is written in Rust and compiled to WebAssembly, with Leptos rendering the interface in the browser. Logic lives in view-models that know nothing about the page; views bind to them and decide nothing. Browser tests drive the built pages with Playwright.

Continuous integration runs formatting, unit tests and browser tests through `just`, with actions pinned to commits and Dependabot proposing weekly updates. The interface is bilingual, English and Canadian French, with Fluent translation files.

## What is open

The source is public on GitHub. Open source and open data are stated product principles: streets come from OpenStreetMap through Nominatim, Overpass and osm2streets, and the Montréal basemap is built from a Geofabrik extract with Planetiler.

## Status

Cityloom is early. Catalogue widths, rules and capacity rates are synthetic placeholders, not real standards or measurements. Native Android and iOS apps are planned after the web release.
