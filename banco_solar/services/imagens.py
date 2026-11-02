"""Objetivo: Valida fotos de notícias e gera JPEGs orientados, redimensionados e sem metadados."""
# Dependências usadas por este módulo.
from io import BytesIO
import warnings
from PIL import Image, ImageOps


def prepare_photo(data):
    """Retorna bytes JPEG de uma foto validada, orientada e limitada a 2.400 pixels."""
    # Trata imagens desproporcionais como erro antes de processar seus pixels.
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(BytesIO(data)) as image:
            # Aceita apenas formatos conhecidos e limita a área total a 24 megapixels.
            if image.format not in {'JPEG', 'PNG', 'WEBP'} or image.width * image.height > 24000000:
                raise ValueError('Imagem incompatível ou maior que 24 megapixels.')
            image.load()
            # Corrige a orientação da câmera e limita o maior lado da foto.
            image = ImageOps.exif_transpose(image).convert('RGBA')
            image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
            # Substitui transparência por branco e exporta somente os pixels em um JPEG novo.
            background = Image.new('RGB', image.size, 'white')
            background.paste(image, mask=image.getchannel('A'))
            output = BytesIO()
            background.save(output, 'JPEG', quality=90, optimize=True)
            return output.getvalue()
