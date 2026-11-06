"""Texto y versión de la política de privacidad.

La versión es la que se guarda junto al consentimiento del usuario. Si el
texto cambia, hay que subir la versión: los consentimientos antiguos quedan
registrados con la versión que la persona realmente aceptó.
"""

from __future__ import annotations

from datetime import date

VERSION = "1.0"
FECHA = date(2026, 11, 5)
TITULO = "Política de privacidad de Cosplay Chile"

TEXTO = """\
Cosplay Chile trata tus datos personales para operar la plataforma de
contenidos, directorio y comunidad de cosplay.

Datos que se recogen: nombre, correo electrónico, región, rol dentro de la
plataforma y, si lo publicas, tu perfil público con biografía, especialidad y
portafolio. La contraseña no se almacena: se guarda un hash irreversible.

Finalidad: autenticar tu cuenta, publicar contenidos que envíes, mostrarte en
el directorio si lo autorizas y moderar la comunidad.

Base de licitud: tu consentimiento, otorgado al crear la cuenta.

Conservación: mientras la cuenta esté activa. Al eliminarla se borran los
datos asociados, salvo los registros que la ley obligue a conservar.

Derechos: puedes solicitar acceso, rectificación, eliminación, oposición y
portabilidad escribiendo al correo de contacto de la plataforma.

Transferencias: los datos se alojan en un proveedor de base de datos en la
nube. No se venden ni se ceden a terceros con fines publicitarios.

Esta política se interpreta conforme a la Ley 21.719 sobre protección de datos
personales.
"""
