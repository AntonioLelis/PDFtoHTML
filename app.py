import streamlit as st
import fitz  # PyMuPDF
import base64
import zipfile
import io

# --- Configuração da Página ---
st.set_page_config(page_title="Conversor PDF > HTML para IA", layout="centered")


# --- Função de Conversão ---
def convert_pdf_to_html(pdf_bytes, escolha_modo):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    html_content = """
    <html>
    <head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: auto; }
        p { margin: 15px 0; }
        img { max-width: 100%; height: auto; display: block; margin: 10px 0; padding: 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .page-break { border-top: 2px dashed #ccc; margin: 30px 0; padding-top: 10px; color: #999; font-weight: bold;}
    </style>
    </head>
    <body>\n
    """

    for page_num in range(len(doc)):
        page = doc[page_num]
        html_content += f'<div class="page-break">Página {page_num + 1}</div>\n'

        # --- LÓGICA DE DETECÇÃO DE MODO ---
        usar_modo_visual = False

        if escolha_modo == "Visual":
            usar_modo_visual = True
        elif escolha_modo == "Automático":
            # Conta quantas formas vetoriais (linhas/retângulos) existem na página
            qtd_desenhos = len(page.get_drawings())
            # Se houver mais de 15 desenhos, assume que é um fluxograma/diagrama
            if qtd_desenhos > 15:
                usar_modo_visual = True

        # --- PROCESSAMENTO DA PÁGINA ---
        if usar_modo_visual:
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            image_bytes = pix.tobytes("png")

            base64_img = base64.b64encode(image_bytes).decode('utf-8')
            img_src = f"data:image/png;base64,{base64_img}"
            html_content += f'<img src="{img_src}" alt="Página {page_num + 1} renderizada integralmente (Detectado Fluxograma/Diagrama)"/>\n'

        else:
            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])
            blocks.sort(key=lambda b: b["bbox"][1])

            for block in blocks:
                if block["type"] == 0:
                    paragraph_text = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()

                            if text:
                                try:
                                    text = text.encode('latin-1').decode('utf-8')
                                except UnicodeError:
                                    pass
                                text = text.replace('', '').replace('¿', '')

                                if "bold" in span.get("font", "").lower():
                                    paragraph_text += f"<b>{text}</b> "
                                else:
                                    paragraph_text += f"{text} "

                    if paragraph_text.strip():
                        html_content += f"<p>{paragraph_text.strip()}</p>\n"

                elif block["type"] == 1:
                    bbox = block.get("bbox")
                    zoom = 2
                    mat = fitz.Matrix(zoom, zoom)
                    try:
                        pix = page.get_pixmap(matrix=mat, clip=bbox)
                        image_bytes = pix.tobytes("png")

                        if image_bytes and len(image_bytes) > 1024:
                            base64_img = base64.b64encode(image_bytes).decode('utf-8')
                            img_src = f"data:image/png;base64,{base64_img}"
                            html_content += f'<img src="{img_src}" alt="Elemento visual isolado"/>\n'
                    except Exception:
                        pass

    html_content += "</body></html>"
    return html_content


# --- Interface de Usuário ---
st.title("📄 Conversor: PDF para HTML")
st.markdown(
    "Suba um ou mais PDFs. O sistema irá extrair os textos e imagens preservando o contexto para leitura da IA.")

st.write("### Configuração de Extração")
modo_selecionado = st.radio(
    "Como o documento deve ser lido pela IA?",
    (
        "🤖 Automático (Recomendado: Detecta fluxogramas página por página)",
        "🧠 Estruturado (Força a extração apenas de textos e imagens separadas)",
        "🖼️ Visual (Força a renderização de todas as páginas como imagens completas)"
    )
)

# Filtra a string do radio para passar para a função
if "Automático" in modo_selecionado:
    escolha_modo = "Automático"
elif "Estruturado" in modo_selecionado:
    escolha_modo = "Estruturado"
else:
    escolha_modo = "Visual"

st.write("---")

uploaded_files = st.file_uploader("Escolha o(s) arquivo(s) PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    qtd_arquivos = len(uploaded_files)
    st.info(f"{qtd_arquivos} arquivo(s) carregado(s). Clique no botão abaixo para processar.")

    if st.button("Converter para HTML"):

        if qtd_arquivos == 1:
            with st.spinner("Estruturando documento para a IA..."):
                file = uploaded_files[0]
                html_content = convert_pdf_to_html(file.read(), escolha_modo)

                st.success("Conversão concluída com sucesso!")

                st.download_button(
                    label="📥 Baixar Arquivo HTML",
                    data=html_content,
                    file_name=f"{file.name.replace('.pdf', '')}_ia.html",
                    mime="text/html"
                )

        else:
            zip_buffer = io.BytesIO()
            progress_bar = st.progress(0)

            with st.spinner("Processando lote de PDFs..."):
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, uploaded_file in enumerate(uploaded_files):
                        pdf_bytes = uploaded_file.read()

                        html_content = convert_pdf_to_html(pdf_bytes, escolha_modo)

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