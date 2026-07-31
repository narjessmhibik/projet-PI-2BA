# flower_detector/management/commands/populate_flowers.py

from django.core.management.base import BaseCommand
from flower_detector.models import FlowerInfo

class Command(BaseCommand):
    help = 'Remplit la base de données avec les informations des 5 fleurs'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('IMPORTATION DES DONNÉES DE FLEURS'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        flowers_data = [
            {
                'name': 'marguerite',
                'scientific_name': 'Bellis perennis',
                'common_names': 'Pâquerette, Petite Marguerite',
                'family': 'Asteraceae',
                'genus': 'Bellis',
                'origin': 'Europe, Asie occidentale',
                'colors': 'Blanc, Rose, Rouge',
                'height_min': 10.0,
                'height_max': 20.0,
                'blooming_start': 'Mars',
                'blooming_end': 'Novembre',
                'blooming_description': 'La marguerite produit des fleurs blanches avec un cœur jaune vif caractéristique. Les pétales peuvent être simples ou doubles selon les variétés. La floraison est abondante et continue du printemps à l\'automne, offrant un tapis floral persistant.',
                'sunlight': 'full_sun',
                'water_needs': 'moderate',
                'soil_type': 'Sol bien drainé, légèrement acide à neutre, tolère différents types de sols',
                'hardiness_zone': 'Z3-Z10',
                'planting_tips': 'Plantez au printemps ou en automne dans un sol préparé et ameubli. Espacez les plants de 15-20 cm pour permettre leur développement. Préfère un emplacement ensoleillé mais tolère la mi-ombre. Arrosez bien après plantation.',
                'care_instructions': 'Arrosez régulièrement sans excès, le sol doit rester frais mais jamais détrempé. Retirez les fleurs fanées régulièrement pour prolonger la floraison. Apportez un engrais équilibré au printemps. Divisez les touffes tous les 2-3 ans pour les rajeunir.',
                'pruning_advice': 'Coupez les fleurs fanées au fur et à mesure pour encourager de nouvelles floraisons. Taillez légèrement le feuillage en fin d\'hiver pour stimuler une nouvelle croissance. Rabattez complètement si les plants deviennent trop envahissants.',
                'common_pests': 'Relativement résistante. Peut être affectée par les pucerons (traiter avec du savon noir). Les limaces peuvent s\'attaquer aux jeunes feuilles. Parfois sensible à l\'oïdium en cas d\'humidité excessive. Évitez l\'arrosage par aspersion.',
                'medicinal_uses': 'Utilisée traditionnellement en phytothérapie pour ses propriétés anti-inflammatoires, vulnéraires (cicatrisantes) et expectorantes. Les infusions de fleurs et feuilles aident à apaiser la toux et les affections bronchiques. En usage externe, appliquée en cataplasme pour soigner les contusions et les petites plaies.',
                'culinary_uses': 'Les jeunes feuilles tendres peuvent être ajoutées crues aux salades printanières, apportant une saveur légèrement acidulée. Les boutons floraux peuvent être confits dans le vinaigre comme des câpres. Les fleurs fraîches décorent joliment les plats.',
                'aromatic_properties': 'Parfum doux, frais et légèrement herbacé. L\'arôme est subtil et ne domine pas dans les compositions florales.',
                'other_uses': 'Excellente plante couvre-sol pour les bordures, rocailles et pelouses fleuries. Très appréciée des abeilles et papillons. Peut être utilisée en prairie fleurie naturelle. Idéale pour les jardins sans entretien.',
                'toxicity': 'Non toxique pour les humains, les chiens et les chats. Toutes les parties de la plante sont sans danger. Comestible avec modération.',
                'symbolism': 'Symbole d\'innocence, de pureté et d\'amour loyal. Représente la douceur de l\'enfance et les souvenirs heureux. Dans le langage des fleurs victorien, offrir des marguerites exprime un amour sincère et fidèle.',
                'fun_facts': 'Son nom scientifique "Bellis" vient du latin signifiant "jolie". Les marguerites se ferment la nuit et par temps nuageux, puis s\'ouvrent au lever du soleil - d\'où le nom "pâquerette" (pâques = Pâques, période de floraison). Un seul plant peut produire des centaines de fleurs par saison!',
            },
            {
                'name': 'pissenlit',
                'scientific_name': 'Taraxacum officinale',
                'common_names': 'Dent-de-lion, Florin d\'or, Laitue de chien',
                'family': 'Asteraceae',
                'genus': 'Taraxacum',
                'origin': 'Europe, Asie, naturalisé partout',
                'colors': 'Jaune vif',
                'height_min': 5.0,
                'height_max': 40.0,
                'blooming_start': 'Mars',
                'blooming_end': 'Novembre',
                'blooming_description': 'Fleurs jaune d\'or éclatantes en forme de capitule composé de multiples fleurons. Après la floraison, se transforme en une sphère blanche et duveteuse d\'akènes (fruits secs), communément appelée "horloge" ou "parachute", qui se dispersent au vent.',
                'sunlight': 'full_sun',
                'water_needs': 'low',
                'soil_type': 'S\'adapte à tous types de sols, même pauvres et compactés. Préfère les sols bien drainés',
                'hardiness_zone': 'Z3-Z10',
                'planting_tips': 'Plante spontanée qui se ressème naturellement et abondamment. Si plantation volontaire, semez au printemps ou en automne en surface. Les graines germent facilement. Préfère le plein soleil mais tolère la mi-ombre.',
                'care_instructions': 'Extrêmement rustique et ne nécessite aucun entretien particulier. S\'adapte aux conditions difficiles. Arrosage uniquement en cas de sécheresse prolongée. Aucun fertilisant nécessaire.',
                'pruning_advice': 'Si vous souhaitez limiter sa propagation, coupez les fleurs avant qu\'elles ne montent en graines (avant l\'apparition des akènes blancs). Pour éliminer complètement, il faut retirer la racine pivotante en entier.',
                'common_pests': 'Extrêmement résistant aux maladies et parasites. Peut occasionnellement être affecté par les pucerons noirs. La rouille peut apparaître sur les feuilles en fin de saison mais sans gravité.',
                'medicinal_uses': 'Plante médicinale majeure reconnue pour ses propriétés diurétiques puissantes, dépuratives, cholérétiques et cholagogues. Les feuilles sont très riches en vitamines A, C, K et en minéraux. Utilisé pour détoxifier le foie et les reins.',
                'culinary_uses': 'Entièrement comestible! Les jeunes feuilles tendres sont excellentes en salade. Les feuilles plus âgées peuvent être cuites comme des épinards. Les racines torréfiées servent à préparer un substitut de café. Les fleurs sont utilisées pour faire du vin ou de la gelée.',
                'aromatic_properties': 'Légèrement amer et herbacé. Le latex blanc a une odeur caractéristique.',
                'other_uses': 'Excellent indicateur de sol compacté - sa racine pivotante aide à décompacter naturellement. Plante mellifère importante pour les abeilles, surtout en début de printemps.',
                'toxicity': 'Totalement non toxique. Comestible pour les humains et les animaux. Toutes les parties sont consommables. Attention à ne pas récolter sur des zones traitées chimiquement.',
                'symbolism': 'Symbole de résilience, de persévérance et de transformation. Dans le folklore, souffler sur les akènes blancs en faisant un vœu est censé l\'exaucer.',
                'fun_facts': 'Le nom "pissenlit" provient de ses propriétés diurétiques. Chaque fleur contient entre 150 et 200 graines qui peuvent voyager jusqu\'à 8 km avec le vent! La racine peut atteindre 1 mètre de profondeur.',
            },
            {
                'name': 'rose',
                'scientific_name': 'Rosa spp.',
                'common_names': 'Rose cultivée, Rosier',
                'family': 'Rosaceae',
                'genus': 'Rosa',
                'origin': 'Hémisphère nord (Europe, Asie, Amérique du Nord)',
                'colors': 'Rouge, Rose, Blanc, Jaune, Orange, Violet, Multicolore',
                'height_min': 30.0,
                'height_max': 200.0,
                'blooming_start': 'Mai',
                'blooming_end': 'Octobre',
                'blooming_description': 'Fleurs emblématiques parfumées aux pétales soyeux et délicats. La forme varie de simples (5 pétales) à très doubles (plus de 100 pétales) selon les variétés. Les roses modernes sont remontantes avec plusieurs vagues de floraison.',
                'sunlight': 'full_sun',
                'water_needs': 'high',
                'soil_type': 'Sol riche, profond, bien drainé et légèrement acide (pH 6-6.5). Éviter les sols lourds et argileux',
                'hardiness_zone': 'Z3-Z10 selon variétés',
                'planting_tips': 'Plantez de préférence en automne (octobre-novembre) ou au début du printemps (mars). Creusez un trou de 40-50 cm de profondeur. Enrichissez le fond avec du compost. Paillez le pied.',
                'care_instructions': 'Arrosez régulièrement et profondément (15-20L par semaine en été). Évitez de mouiller le feuillage. Fertilisez au printemps et après chaque floraison. Renouvelez le paillage pour maintenir la fraîcheur du sol.',
                'pruning_advice': 'Taillez en fin d\'hiver (février-mars) avant le débourrement. Supprimez le bois mort et les branches qui se croisent. Coupez régulièrement les fleurs fanées en saison pour stimuler de nouvelles floraisons.',
                'common_pests': 'Pucerons verts, cochenilles, acariens. Principales maladies: oïdium, marsonia (taches noires), rouille. Traitez préventivement avec du soufre au débourrement.',
                'medicinal_uses': 'L\'eau de rose apaise les irritations cutanées. Les pétales en infusion ont des propriétés astringentes. L\'huile essentielle possède des vertus calmantes et régénérantes. Le cynorrhodon est riche en vitamine C.',
                'culinary_uses': 'Les pétales parfument délicatement confitures, gelées, sirops et pâtisseries. L\'eau de rose aromatise les desserts. Les boutons peuvent être confits dans le sucre. Utilisez uniquement des roses non traitées.',
                'aromatic_properties': 'Parfum intense, complexe et envoûtant allant du fruité au musqué. L\'absolu de rose est un ingrédient de base en parfumerie de luxe.',
                'other_uses': 'Production d\'huile essentielle (il faut 4 tonnes de pétales pour 1 kg d\'huile!), d\'eau de rose pour l\'industrie cosmétique. Fleurs coupées de premier choix.',
                'toxicity': 'Non toxique. Les pétales sont comestibles. Attention aux épines acérées qui peuvent causer des blessures.',
                'symbolism': 'Symbole universel de l\'amour et de la passion. Chaque couleur porte sa signification: rouge = amour passionné, blanc = pureté, rose = tendresse, jaune = amitié.',
                'fun_facts': 'Il existe plus de 30 000 variétés de roses! La plus ancienne rose connue a environ 1000 ans et pousse toujours sur la cathédrale d\'Hildesheim en Allemagne. Les roses fossiles remontent à 35 millions d\'années.',
            },
            {
                'name': 'tournesol',
                'scientific_name': 'Helianthus annuus',
                'common_names': 'Soleil, Grand soleil, Hélianthe',
                'family': 'Asteraceae',
                'genus': 'Helianthus',
                'origin': 'Amérique du Nord (États-Unis, Mexique)',
                'colors': 'Jaune d\'or, Orange, Rouge bordeaux, Bicolore',
                'height_min': 80.0,
                'height_max': 300.0,
                'blooming_start': 'Juillet',
                'blooming_end': 'Septembre',
                'blooming_description': 'Inflorescences spectaculaires pouvant atteindre 30-50 cm de diamètre. Pétales jaunes rayonnants entourant un grand cœur brun. Phénomène d\'héliotropisme: les jeunes fleurs suivent le soleil.',
                'sunlight': 'full_sun',
                'water_needs': 'moderate',
                'soil_type': 'Sol profond, riche en humus, bien drainé. Tolère les sols légèrement alcalins',
                'hardiness_zone': 'Z2-Z11 (plante annuelle)',
                'planting_tips': 'Semez directement en place après les dernières gelées (avril-mai) à 2-3 cm de profondeur. Espacez de 30-50 cm pour les variétés naines, 60-80 cm pour les géantes. Choisissez un emplacement très ensoleillé.',
                'care_instructions': 'Arrosez régulièrement et copieusement (20-30L par semaine en pleine terre), surtout pendant la croissance. Tuteurez les très grandes variétés. Apportez un engrais riche en potassium.',
                'pruning_advice': 'Aucune taille nécessaire. Pour la production de graines, laissez les capitules sécher complètement sur pied. Pour des bouquets, coupez quand les pétales sont bien ouverts.',
                'common_pests': 'Les oiseaux raffolent des graines - utilisez un filet. Les limaces s\'attaquent aux jeunes plantules. Pucerons noirs possibles. Sensible au mildiou en conditions humides.',
                'medicinal_uses': 'Les graines sont très riches en vitamine E, vitamines B, magnésium et acides gras essentiels. L\'huile de tournesol a des propriétés anti-inflammatoires et protectrices cardiovasculaires.',
                'culinary_uses': 'Les graines décortiquées sont consommées grillées comme snack. Elles enrichissent salades, pains et mueslis. L\'huile de tournesol est une huile alimentaire majeure. Les jeunes bourgeons peuvent se cuisiner comme des artichauts.',
                'aromatic_properties': 'Parfum doux, légèrement miellé et herbacé. Les graines grillées dégagent une odeur de noisette.',
                'other_uses': 'Culture commerciale majeure pour l\'huile alimentaire et le biocarburant. Les tiges servent de tuteurs naturels. Excellent pour les abeilles. Phytoremédiation: absorbe les métaux lourds.',
                'toxicity': 'Totalement non toxique. Toutes les parties sont comestibles pour humains et animaux.',
                'symbolism': 'Symbole universel de joie, bonheur, vitalité et optimisme. Représente l\'adoration et la loyauté. Fleur emblématique de l\'été.',
                'fun_facts': 'Un seul capitule peut contenir 1000 à 2000 graines! Record de hauteur: 9,17 mètres. Les graines sont disposées selon une spirale de Fibonacci. Van Gogh a immortalisé les tournesols dans sa célèbre série de peintures.',
            },
            {
                'name': 'tulipe',
                'scientific_name': 'Tulipa spp.',
                'common_names': 'Tulipe des jardins',
                'family': 'Liliaceae',
                'genus': 'Tulipa',
                'origin': 'Asie centrale (Kazakhstan, Ouzbékistan, Turquie)',
                'colors': 'Rouge, Rose, Jaune, Blanc, Orange, Violet, Noir, Panaché, Multicolore',
                'height_min': 15.0,
                'height_max': 70.0,
                'blooming_start': 'Mars',
                'blooming_end': 'Mai',
                'blooming_description': 'Fleurs élégantes en forme de coupe, composées de 6 tépales. Immense diversité de formes: simples, doubles, frangées, perroquet... La floraison varie selon les variétés.',
                'sunlight': 'full_sun',
                'water_needs': 'moderate',
                'soil_type': 'Sol léger, meuble, bien drainé, légèrement sableux. Déteste l\'humidité stagnante',
                'hardiness_zone': 'Z3-Z8',
                'planting_tips': 'Plantez les bulbes en automne (octobre-novembre) à 10-15 cm de profondeur, pointe vers le haut. Espacez de 10-15 cm. Choisissez un emplacement ensoleillé et bien drainé. Les bulbes ont besoin du froid hivernal pour fleurir.',
                'care_instructions': 'Arrosez modérément à la plantation puis en période de croissance. Stoppez complètement l\'arrosage après la floraison. Laissez le feuillage jaunir naturellement (6-8 semaines) avant de le couper.',
                'pruning_advice': 'Coupez les fleurs fanées en laissant la tige. IMPORTANT: Ne coupez JAMAIS le feuillage tant qu\'il est vert - attendez qu\'il soit complètement jauni.',
                'common_pests': 'Principal problème: pourriture des bulbes causée par l\'excès d\'humidité. Pucerons sur feuilles et boutons. Les rongeurs déterrent et mangent les bulbes. Limaces sur jeunes pousses.',
                'medicinal_uses': 'Aucun usage médicinal reconnu. Historiquement utilisée dans la médecine traditionnelle turque mais ces usages ne sont plus recommandés. Les bulbes contiennent des allergènes.',
                'culinary_uses': 'ATTENTION: Les bulbes de tulipe sont TOXIQUES et ne doivent PAS être consommés. Peuvent causer des troubles digestifs graves. Les pétales sont techniquement comestibles mais déconseillés.',
                'aromatic_properties': 'Variable selon variétés: certaines sont parfumées (tulipes botaniques), d\'autres sont inodores. Les parfumées dégagent un doux parfum floral.',
                'other_uses': 'Fleurs coupées de premier choix pour l\'art floral. Production commerciale intensive aux Pays-Bas (70% de la production mondiale). Symbole national néerlandais.',
                'toxicity': 'ATTENTION - TOXIQUE: Tous les parties, en particulier les bulbes, contiennent des glycosides allergènes. Peut provoquer dermatites, nausées, vomissements. Toxique pour chiens, chats, chevaux. Tenir hors de portée des enfants et animaux.',
                'symbolism': 'Symbole de l\'amour parfait et du renouveau printanier. Chaque couleur a sa signification: rouge = amour profond, jaune = joie, blanc = pardon, rose = affection, violet = royauté.',
                'fun_facts': 'La fameuse "Tulipomanie" (1637): certains bulbes valaient le prix d\'une maison! Il existe plus de 5000 variétés. Les tulipes continuent de pousser dans le vase après avoir été coupées. Le festival des tulipes d\'Ottawa est le plus grand au monde.',
            },
        ]

        success_count = 0
        error_count = 0

        for flower in flowers_data:
            flower_name = flower['name']
            try:
                obj, created = FlowerInfo.objects.update_or_create(
                    name=flower_name,
                    defaults=flower
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ CRÉÉE: {flower_name.capitalize()} ({flower["scientific_name"]})')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'🔄 MISE À JOUR: {flower_name.capitalize()} ({flower["scientific_name"]})')
                    )
                success_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ ERREUR pour {flower_name}: {str(e)}')
                )
                error_count += 1

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎉 IMPORTATION TERMINÉE!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\nRésumé:')
        self.stdout.write(f'  - Succès: {success_count}')
        self.stdout.write(f'  - Erreurs: {error_count}')
        self.stdout.write(f'  - Total en BDD: {FlowerInfo.objects.count()}\n')