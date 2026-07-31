"""
Script pour générer toutes les icônes PWA
Installation : pip install Pillow
Utilisation : python generate_icons.py
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Créer une icône avec le logo de l'app"""
    
    # Créer une image avec fond gradient
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Dessiner un cercle de fond
    circle_margin = size // 10
    draw.ellipse(
        [circle_margin, circle_margin, size - circle_margin, size - circle_margin],
        fill='#764ba2'
    )
    
    # Ajouter l'emoji de fleur (texte)
    try:
        # Essayer d'utiliser une police système
        font_size = size // 2
        # Sur Windows
        try:
            font = ImageFont.truetype("seguiemj.ttf", font_size)
        except:
            # Sur Linux/Mac
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", font_size)
            except:
                # Police par défaut
                font = ImageFont.load_default()
        
        # Centrer le texte
        emoji = "🌸"
        bbox = draw.textbbox((0, 0), emoji, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), emoji, fill='white', font=font)
    except Exception as e:
        print(f"Erreur police: {e}")
        # Dessiner un simple cercle blanc à la place
        center = size // 2
        radius = size // 4
        draw.ellipse(
            [center - radius, center - radius, center + radius, center + radius],
            fill='white'
        )
    
    # Sauvegarder
    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Icône créée : {output_path} ({size}x{size})")


def generate_all_icons():
    """Générer toutes les icônes nécessaires"""
    
    # Créer le dossier icons s'il n'existe pas
    icons_dir = 'static/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # Tailles d'icônes PWA standard
    sizes = [16, 32, 72, 96, 128, 144, 152, 192, 384, 512]
    
    print("🎨 Génération des icônes PWA...")
    print("-" * 50)
    
    for size in sizes:
        output_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
        create_icon(size, output_path)
    
    # Créer aussi le favicon
    create_icon(32, os.path.join(icons_dir, 'favicon.ico'))
    
    print("-" * 50)
    print("✨ Toutes les icônes ont été générées !")
    print(f"📁 Emplacement : {os.path.abspath(icons_dir)}")


if __name__ == '__main__':
    generate_all_icons()