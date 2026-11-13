"""
Conversão de DOCX para PDF com LibreOffice (soffice em modo headless).

Usa o mesmo binário `soffice` que os demais módulos do projeto. Cada conversão
roda com um perfil de usuário temporário próprio (-env:UserInstallation), para
não brigar com outra instância do LibreOffice aberta pelo usuário.
"""

import os
import shutil
import subprocess
import tempfile


_CAMINHOS_WINDOWS = (r"C:\Program Files\LibreOffice\program\soffice.exe",
                     r"C:\Program Files (x86)\LibreOffice\program\soffice.exe")


def _binario():
    achado = shutil.which("soffice") or shutil.which("libreoffice")
    if achado:
        return achado
    return next((c for c in _CAMINHOS_WINDOWS if os.path.isfile(c)), None)


def _word_disponivel() -> bool:
    """Windows com Microsoft Word e o pacote docx2pdf (pip install docx2pdf)."""
    if os.name != "nt":
        return False
    try:
        import docx2pdf  # noqa: F401
    except ImportError:
        return False
    return True


def motor_pdf():
    """'libreoffice', 'word' ou None — qual programa vai gerar o PDF."""
    if _binario():
        return "libreoffice"
    if _word_disponivel():
        return "word"
    return None


def disponivel() -> bool:
    """True quando há como gerar PDF: LibreOffice (qualquer sistema) ou Word no Windows (docx2pdf)."""
    return motor_pdf() is not None


def docx_para_pdf(caminho_docx, pasta_saida=None, timeout=120) -> str:
    """Converte um .docx em .pdf e devolve o caminho do PDF gerado.

    O PDF é gravado em `pasta_saida` (padrão: mesma pasta do .docx) com o mesmo
    nome base. Levanta RuntimeError se o LibreOffice não estiver instalado ou se
    a conversão falhar.
    """
    binario = _binario()
    if binario is None:
        if _word_disponivel():
            return _docx_para_pdf_word(caminho_docx, pasta_saida)
        raise RuntimeError("Nenhum conversor de PDF: instale o LibreOffice ou, no Windows com Word, "
                           "o pacote docx2pdf (pip install docx2pdf). Também dá para abrir o DOCX e salvar como PDF.")

    origem = os.path.abspath(os.fspath(caminho_docx))
    if not os.path.isfile(origem):
        raise RuntimeError(f"Arquivo DOCX não encontrado: {origem}")

    saida = os.path.abspath(os.fspath(pasta_saida)) if pasta_saida else os.path.dirname(origem)
    os.makedirs(saida, exist_ok=True)

    base = os.path.splitext(os.path.basename(origem))[0]
    destino = os.path.join(saida, base + ".pdf")

    with tempfile.TemporaryDirectory(prefix="lo_perfil_") as perfil:
        cmd = [
            binario,
            f"-env:UserInstallation=file://{perfil}",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", saida,
            origem,
        ]
        try:
            resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Conversão para PDF excedeu {timeout}s.") from exc

    if resultado.returncode != 0 or not os.path.isfile(destino):
        detalhe = (resultado.stderr or resultado.stdout or "").strip()
        raise RuntimeError(f"Falha na conversão para PDF: {detalhe or 'sem saída do LibreOffice'}")

    return destino


def bytes_docx_para_pdf(dados: bytes, nome="documento.docx") -> bytes:
    """Converte o conteúdo de um .docx (bytes) e devolve o PDF em bytes."""
    if not disponivel():
        raise RuntimeError("Nenhum conversor de PDF: instale o LibreOffice ou, no Windows com Word, "
                           "o pacote docx2pdf (pip install docx2pdf).")

    nome_base = os.path.basename(nome) or "documento.docx"
    if not nome_base.lower().endswith(".docx"):
        nome_base += ".docx"

    with tempfile.TemporaryDirectory(prefix="docx_pdf_") as pasta:
        caminho = os.path.join(pasta, nome_base)
        with open(caminho, "wb") as f:
            f.write(dados)
        destino = docx_para_pdf(caminho, pasta_saida=pasta)
        with open(destino, "rb") as f:
            return f.read()


def _docx_para_pdf_word(caminho_docx, pasta_saida=None) -> str:
    """Conversão pelo Microsoft Word (Windows), via docx2pdf."""
    from docx2pdf import convert
    origem = os.path.abspath(os.fspath(caminho_docx))
    saida = os.path.abspath(os.fspath(pasta_saida)) if pasta_saida else os.path.dirname(origem)
    os.makedirs(saida, exist_ok=True)
    destino = os.path.join(saida, os.path.splitext(os.path.basename(origem))[0] + ".pdf")
    convert(origem, destino)
    if not os.path.isfile(destino):
        raise RuntimeError("O Word não gerou o PDF.")
    return destino
