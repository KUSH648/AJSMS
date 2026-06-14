"""
utils/image_helpers.py
======================
Helper functions to resolve product image paths with fallback priority logic.
"""
import os

def get_jewellery_image_path(item):
    """
    Examines an item (dict or object) and returns the relative path (to static/)
    to use for the product image. Follows user priority logic:
    1. If product.image_url exists, is not empty, does not contain 'placeholder', and exists on disk, use it.
    2. Else, map category and product type (name) to category-specific premium jewellery images.
    """
    if not item:
        return 'images/jewelry/others/default_other.webp'
    
    # Handle both dict and object
    image_url = item.get('image_url') if isinstance(item, dict) else getattr(item, 'image_url', None)
    if not image_url:
        image_url = item.get('image_path') if isinstance(item, dict) else getattr(item, 'image_path', None)
        
    category = item.get('category') if isinstance(item, dict) else getattr(item, 'category', 'Other')
    name = item.get('name') if isinstance(item, dict) else getattr(item, 'name', '')
    
    # Clean up categories
    if not category:
        category = 'Other'
    category = category.strip()
    
    # Check if the image_url exists on disk and is not a placeholder
    is_valid_url = False
    if image_url and isinstance(image_url, str) and image_url.strip() != '':
        if 'placeholder' not in image_url.lower():
            # If it's a web url or local relative path
            if image_url.startswith('http'):
                is_valid_url = True
            else:
                # Resolve local path
                # Make sure it points to static/
                clean_path = image_url.replace('/static/', '')
                # Check if file exists under static directory
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                full_path = os.path.join(base_dir, 'static', clean_path.replace('/', os.sep))
                if os.path.exists(full_path) and os.path.getsize(full_path) > 1000:
                    is_valid_url = True
                    image_url = clean_path

    if is_valid_url:
        return image_url

    # Fallback category-specific logic matching category and name/product type
    cat_lower = category.lower()
    name_lower = name.lower()

    if cat_lower == 'ring':
        if 'solitaire' in name_lower or 'diamond' in name_lower or 'platinum' in name_lower:
            return 'images/jewelry/rings/platinum_ring.webp'
        return 'images/jewelry/rings/default_ring.webp'
        
    elif cat_lower == 'necklace':
        if 'royal' in name_lower or 'diamond' in name_lower:
            return 'images/jewelry/necklaces/royal_diamond_necklace.webp'
        return 'images/jewelry/necklaces/default_necklace.webp'
        
    elif cat_lower in ['bracelet', 'anklet', 'bangles']:
        if 'bangle' in name_lower:
            return 'images/jewelry/bangles/default_bangle.webp'
        elif 'kada' in name_lower or 'gold' in name_lower:
            return 'images/jewelry/bracelets/gold_kada.webp'
        elif 'diamond' in name_lower:
            return 'images/jewelry/bracelets/diamond_bracelet.webp'
        elif cat_lower == 'anklet' or 'anklet' in name_lower:
            return 'images/jewelry/anklets/default_anklet.webp'
        return 'images/jewelry/bracelets/default_bracelet.webp'
        
    elif cat_lower == 'earrings':
        if 'rose gold' in name_lower or 'diamond' in name_lower or 'luxury' in name_lower:
            return 'images/jewelry/earrings/rose_gold_earrings.webp'
        return 'images/jewelry/earrings/default_earring.webp'
        
    elif cat_lower == 'pendant':
        if 'diamond' in name_lower or 'elegant' in name_lower:
            return 'images/jewelry/pendants/elegant_diamond_pendant.webp'
        return 'images/jewelry/pendants/default_pendant.webp'
        
    elif cat_lower == 'chain':
        return 'images/jewelry/chains/default_chain.webp'
        
    else:
        return 'images/jewelry/others/default_other.webp'
