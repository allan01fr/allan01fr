"""Hash e conferência de senhas com argon2."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def gerar_hash(senha: str) -> str:
    return _hasher.hash(senha)


def conferir_senha(senha: str, hash_: str) -> bool:
    """Diz se a senha confere com o hash; qualquer falha (inclusive hash inválido) é False."""
    try:
        return _hasher.verify(hash_, senha)
    except (VerificationError, InvalidHashError):
        return False


def normalizar_email(email: str) -> str:
    return email.strip().lower()


# Conferido quando o e-mail não existe, para o login levar o mesmo tempo nos dois casos.
HASH_FICTICIO = gerar_hash("senha-ficticia-sem-uso")
