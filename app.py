import streamlit as st
import fitz  # PyMuPDF
import base64
import zipfile
import io

# --- Configuração da Página ---
st.set_page_config(page_title="Conversor PDF > HTML para IA", layout="centered")


# --- Função de Conversão ---
def convert_pdf_to_html(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # CSS Ajustado:
    # 1. As imagens agora têm margin: 0 e display: block para que "tiras" cortadas pelo PDF se colem perfeitamente.
    # 2. O espaçamento foi movido para a tag <p>.
    html_content = """
    <html>
    <head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: auto; }
        p { margin: 15px 0; }
        img { max-width: 100%; height: auto; display: block; margin: 0; padding: 0; }
        .page-break { border-top: 2px dashed #ccc; margin: 30px 0; padding-top: 10px; color: #999;}
    </style>
    </head>
    <body>\n
    """

    for page_num in range(len(doc)):
        page = doc[page_num]
        html_content += f'<div class="page-break">Página {page_num + 1}</div>\n'

        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        # O PULO DO GATO DA ORDEM:
        # Ordena os blocos verticalmente (coordenada y0) para forçar a leitura de cima para baixo.
        blocks.sort(key=lambda b: b["bbox"][1])

        for block in blocks:
            # Texto
            if block["type"] == 0:
                paragraph_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            if "bold" in span.get("font", "").lower():
                                paragraph_text += f"<b>{text}</b> "
                            else:
                                paragraph_text += f"{text} "

                if paragraph_text.strip():
                    html_content += f"<p>{paragraph_text.strip()}</p>\n"

            # Imagem
            elif block["type"] == 1:
                image_bytes = block.get("image")
                if image_bytes and len(image_bytes) > 1024:
                    ext = block.get("ext", "png")
                    base64_img = base64.b64encode(image_bytes).decode('utf-8')
                    img_src = f"data:image/{ext};base64,{base64_img}"
                    html_content += f'<img src="{img_src}" alt="Captura de tela do sistema"/>\n'

    html_content += "</body></html>"
    return html_content


# --- Interface de Usuário ---
st.title("📄 Conversor: PDF para HTML")
st.markdown(
    "Suba um ou mais PDFs. O sistema irá extrair os textos e imagens preservando a ordem cronológica e a formatação para leitura da IA.")

uploaded_files = st.file_uploader("Escolha o(s) arquivo(s) PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    qtd_arquivos = len(uploaded_files)
    st.info(f"{qtd_arquivos} arquivo(s) carregado(s). Clique no botão abaixo para processar.")

    if st.button("Converter para HTML"):

        # ROTA 1: APENAS 1 ARQUIVO (Baixa o HTML direto)
        if qtd_arquivos == 1:
            with st.spinner("Lendo páginas e estruturando HTML..."):
                file = uploaded_files[0]
                html_content = convert_pdf_to_html(file.read())

                st.success("Conversão concluída com sucesso!")

                st.download_button(
                    label="📥 Baixar Arquivo HTML",
                    data=html_content,
                    file_name=f"{file.name.replace('.pdf', '')}_ia.html",
                    mime="text/html"
                )

        # ROTA 2: MÚLTIPLOS ARQUIVOS (Baixa o ZIP)
        else:
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)

            with st.spinner("Processando lote de PDFs..."):
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, uploaded_file in enumerate(uploaded_files):
                        pdf_bytes = uploaded_file.read()
                        html_content = convert_pdf_to_html(pdf_bytes)

                        html_filename = f"{uploaded_file.name.replace('.pdf', '')}_ia.html"
                        zip_file.writestr(html_filename, html_content)

                        progress_bar.progress((idx + 1) / qtd_arquivos)

            st.success("Conversão em lote concluída com sucesso!")

            st.download_button(
                label="📦 Baixar Arquivo ZIP com os HTMLs",
                data=zip_buffer.getvalue(),
                file_name="manuais_convertidos.zip",
                mime="application/zip"
            )