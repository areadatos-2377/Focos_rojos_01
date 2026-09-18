"""Normalizacion de nombres de categoria para detectar duplicados.

Se hace en Python (y no con la extension `unaccent` de PostgreSQL) porque esta
queda en un unico lugar documentado y testeable, y no exige CREATE EXTENSION en
el despliegue.
"""
import re
import unicodedata

_ESPACIOS = re.compile(r"\s+")


def normalizar_nombre(valor: str) -> str:
    """Minusculas, sin acentos y con espacios colapsados.

    'Logistica', 'logistica' y 'LOGISTICA' colapsan al mismo valor.
    """
    if not valor:
        return ""
    descompuesto = unicodedata.normalize("NFKD", valor)
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return _ESPACIOS.sub(" ", sin_acentos).strip().casefold()
