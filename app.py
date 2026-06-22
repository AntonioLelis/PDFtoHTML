import streamlit as st
import fitz  # PyMuPDF
import base64

# --- Configuração da Página ---
st.set_page_config(page_title="Conversor PDF > HTML para IA", layout="centered")


# --- Função de Conversão ---
def convert_pdf_to_html(pdf_bytes):
    # Abre o PDF diretamente da memória
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    html_content = """
    <html>
    <head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: auto; }
        img { max-width: 100%; height: auto; margin: 15px 0; border: 1px solid #ddd; }
        .page-break { border-top: 2px dashed #ccc; margin: 30px 0; padding-top: 10px; color: #999;}
    </style>
    </head>
    <body>\n
    """

    # Barra de progresso para dar feedback visual aos usuários
    progress_bar = st.progress(0)
    total_pages = len(doc)

    for page_num in range(total_pages):
        page = doc[page_num]
        html_content += f'<div class="page-break">Página {page_num + 1}</div>\n'

        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

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

        # Atualiza a barra de progresso
        progress_bar.progress((page_num + 1) / total_pages)

    html_content += "</body></html>"
    return html_content


# --- Interface de Usuário ---
st.title("📄 PDF para HTML (Otimizado para IA)")
st.markdown(
    "Suba um manual ou relatório em PDF. O sistema irá extrair os textos na ordem correta e embutir as imagens para que agentes de IA possam ler o documento perfeitamente.")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.info("Arquivo carregado. Clique no botão abaixo para processar.")

    if st.button("Converter para HTML"):
        with st.spinner("Lendo páginas e extraindo imagens..."):
            # Pega os bytes do arquivo upado
            pdf_bytes = uploaded_file.read()

            # Roda a conversão
            final_html = convert_pdf_to_html(pdf_bytes)

            st.success("Conversão concluída com sucesso!")

            # Botão para download do arquivo gerado
            st.download_button(
                label="📥 Baixar Arquivo HTML",
                data=final_html,
                file_name=f"{uploaded_file.name.replace('.pdf', '')}_ia.html",
                mime="text/html"
            )